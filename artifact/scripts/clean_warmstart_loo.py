#!/usr/bin/env python3
"""
clean_warmstart_loo.py — EXPERIMENT P2
========================================
Answers failure mode M1 empirically instead of by argument.

The audited benchmark initialises every leave-one-out fold from
`planner/model_gpu_v3.pt`, whose metadata records `n_real_graphs = 40`.
The 42-CBOM corpus shares 40 of 42 files with the 40-graph set that
checkpoint was fine-tuned on, so 40/42 "held-out" folds were already in
the base model's training set.

This script re-runs the SAME protocol from a checkpoint trained on
synthetic graphs ONLY (`n_real_graphs = 0`), and compares the two runs
fold by fold. It uses the project's own `train_gpu()` and `run_loo()`
so the training path is identical -- only the warm start differs.

Predicted outcome: the conclusion does NOT change, because a bare
single-feature sort already reproduces the heuristic exactly (see
experiments_reaudit.py X2). This script tests that prediction.

Run with the Python 3.12 interpreter that has torch + torch_geometric.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time

REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "q-trust")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "results", "clean_warmstart_loo.json")

BASE_EPOCHS = int(os.environ.get("QW_BASE_EPOCHS", 40))
BASE_GRAPHS = int(os.environ.get("QW_BASE_GRAPHS", 10000))
FOLD_EPOCHS = int(os.environ.get("QW_FOLD_EPOCHS", 30))
N_SYNTH = int(os.environ.get("QW_N_SYNTH", 2000))

sys.path.insert(0, os.path.join(REPO, "planner"))
sys.path.insert(0, os.path.join(REPO, "scripts"))

import torch  # noqa: E402

# The project's train_gpu() calls torch.use_deterministic_algorithms(True).
# On CUDA >= 10.2 that requires CUBLAS_WORKSPACE_CONFIG to be set BEFORE torch
# initialises cuBLAS, or the first GEMM raises. Setting it here (post-import) is
# still early enough because no CUDA context exists until the first tensor op.
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")



def main() -> None:
    print("=" * 92)
    print("P2  CLEAN WARM-START LEAVE-ONE-OUT")
    print("=" * 92)
    print("torch %s | cuda %s | %s"
          % (torch.__version__, torch.cuda.is_available(),
             torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"))

    from qtrust_planner.train_gpu import train_gpu  # noqa: E402

    CLEAN_CKPT = os.path.join(REPO, "planner", "_audit_clean_base.pt")

    # ---------------------------------------------------------------- 1. base model
    if not os.path.exists(CLEAN_CKPT):
        print("\n[1/3] training a SYNTHETIC-ONLY base checkpoint "
              "(no real CBOMs, n_real_graphs must be 0)")
        t0 = time.time()
        train_gpu(
            n_graphs=BASE_GRAPHS,
            epochs=BASE_EPOCHS,
            batch_size=256,
            learning_rate=1e-3,
            weight_decay=1e-4,
            model_path=CLEAN_CKPT,
            seed=42,
            val_split=0.1,
            device_name=os.environ.get("QW_DEVICE", "cpu"),
            extra_graphs=None,          # <-- synthetic only. THIS IS THE FIX.
            norm="layer",
            init_path=None,             # <-- train from scratch. THIS IS THE FIX.
        )
        print("    base training took %.1f s" % (time.time() - t0))
    else:
        print("\n[1/3] reusing existing clean base checkpoint")

    payload = torch.load(CLEAN_CKPT, map_location="cpu", weights_only=True)
    n_real = payload.get("n_real_graphs")
    print("    clean base metadata:")
    for k in ("epochs", "n_graphs", "n_real_graphs", "seed", "norm",
              "best_val_kendall", "learning_rate"):
        if k in payload:
            print("        %-18s = %s" % (k, payload[k]))

    assert n_real in (0, None), (
        "clean checkpoint unexpectedly records n_real_graphs=%r -- the fix failed" % n_real)
    print("    VERIFIED: clean base records n_real_graphs=%r" % n_real)

    contaminated = torch.load(os.path.join(REPO, "planner", "model_gpu_v3.pt"),
                              map_location="cpu", weights_only=True)
    print("    contaminated base (for comparison): n_real_graphs = %s"
          % contaminated.get("n_real_graphs"))

    # ------------------------------------------------------------------ 2. the LOO
    print("\n[2/3] running the SAME 42-fold LOO protocol, warm-started from the clean base")
    import eval_real_cbom_loo as LOO  # noqa: E402

    LOO.BASE_MODEL = __import__("pathlib").Path(CLEAN_CKPT)
    print("    patched LOO.BASE_MODEL -> %s" % LOO.BASE_MODEL)

    out_path = __import__("pathlib").Path(OUT)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    report = LOO.run_loo(
        epochs=FOLD_EPOCHS,
        n_synthetic=N_SYNTH,
        batch_size=64,
        learning_rate=5e-4,
        seed=42,
        device_name=os.environ.get("QW_DEVICE", "cpu"),
        out_path=out_path,
    )
    print("    LOO took %.1f s" % (time.time() - t0))

    # ---------------------------------------------------------------- 3. comparison
    print("\n[3/3] comparing the clean run against the committed (contaminated) artifact")
    old = json.load(open(os.path.join(REPO, "planner", "results",
                                     "real_cbom_loo_42.json")))
    new = json.load(open(out_path))

    METS = ["kendall", "node_rank", "exact_rank", "top5", "top10"]
    print("\n%-12s %14s %14s %12s %12s" % ("metric", "contaminated", "clean warm-start",
                                          "delta", "heuristic"))
    for m in METS:
        a = statistics.mean(fm["model"][m] for fm in old["fold_metrics"].values())
        b = statistics.mean(fm["model"][m] for fm in new["fold_metrics"].values())
        h = statistics.mean(fm["heuristic"][m] for fm in old["fold_metrics"].values())
        print("%-12s %14.6f %14.6f %+12.6f %12.6f" % (m, a, b, b - a, h))

    oc = old["model_vs_heuristic_tau_b"]
    nc = new.get("model_vs_heuristic_tau_b")
    print("\nmodel-vs-heuristic tau-b delta:")
    print("    committed (contaminated warm start) : %+.6f" % oc)
    print("    clean warm start (this experiment)   : %+.6f" % nc)

    # paired test over folds
    names = sorted(new["fold_metrics"])
    d = [new["fold_metrics"][n]["model"]["kendall"]
         - new["fold_metrics"][n]["heuristic"]["kendall"] for n in names]
    import numpy as np
    from scipy import stats as sps
    arr = np.array(d)
    rs = np.random.default_rng(20260918)
    boot = np.array([rs.choice(arr, len(arr), replace=True).mean() for _ in range(50000)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    t = sps.ttest_1samp(arr, 0.0)
    print("\npaired analysis over the %d clean folds:" % len(arr))
    print("    mean delta   = %+.6f   sd = %.6f" % (arr.mean(), arr.std(ddof=1)))
    print("    95%% CI       = [%+.6f, %+.6f]" % (lo, hi))
    print("    paired t     = %.3f   p = %.4f  -> %s"
          % (t.statistic, t.pvalue,
             "significant" if t.pvalue < 0.05 else "NOT significant"))
    print("    folds: %d negative, %d zero, %d positive"
          % ((arr < -1e-9).sum(), (np.abs(arr) < 1e-9).sum(), (arr > 1e-9).sum()))

    mde = (sps.norm.ppf(0.975) + sps.norm.ppf(0.8)) * arr.std(ddof=1) / np.sqrt(len(arr))
    print("    MDE at 80%% power = %.6f ; observed |delta| = %.6f" % (mde, abs(arr.mean())))

    summary = {
        "experiment": "P2 clean warm-start LOO",
        "base_epochs": BASE_EPOCHS, "base_graphs": BASE_GRAPHS,
        "fold_epochs": FOLD_EPOCHS, "n_synthetic_per_fold": N_SYNTH,
        "clean_base_n_real_graphs": n_real,
        "contaminated_base_n_real_graphs": contaminated.get("n_real_graphs"),
        "metrics_contaminated": {m: statistics.mean(
            fm["model"][m] for fm in old["fold_metrics"].values()) for m in METS},
        "metrics_clean": {m: statistics.mean(
            fm["model"][m] for fm in new["fold_metrics"].values()) for m in METS},
        "delta_contaminated": oc,
        "delta_clean": nc,
        "paired_clean": {"mean": float(arr.mean()), "sd": float(arr.std(ddof=1)),
                         "ci95": [float(lo), float(hi)],
                         "t": float(t.statistic), "p": float(t.pvalue),
                         "mde80": float(mde)},
    }
    json.dump(summary, open(out_path, "w", encoding="utf-8"), indent=2)
    print("\nwrote %s" % out_path)
    print("=" * 92)


if __name__ == "__main__":
    main()
