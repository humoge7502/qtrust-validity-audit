# DELIVERABLE E — EXPERIMENTAL PLAN
## Q-Trust · 2026-10-14

Two parts: **(A)** experiments already executed for this paper, and **(B)** the prioritised
forward plan. Part A is complete and its output is in `results/experiments_output.txt`.

---

# PART A — EXECUTED EXPERIMENTS

All six run on the public repository only. No GPU, no dataset package, no checkpoint.

| ID | Experiment | RQ | Status | Key result |
|---|---|---|---|---|
| **X1** | Target reconstruction from source | Can we audit a pipeline we cannot re-run? | ✅ done | **42/42 folds bit-exact**; all 11 headline numbers reproduce |
| **X2** | Training-free baseline suite | Does the ranking task contain information beyond one feature? | ✅ done | **key-size sort == doctrine heuristic on 42/42 folds**, all 5 metrics |
| **X3** | Paired bootstrap + t-test on Δ | Is the reported difference significant? | ✅ done | 95% CI [−0.0127, 0.0000]; paired t = −1.000, **p = 0.32, not significant** |
| **X4** | Minimum detectable effect | What could this design ever detect? | ✅ done | MDE(80%) = **0.0138**; observed \|Δ\| = **0.0042** |
| **X5** | Properly randomised null | Is the "+0.687 vs random" robust? | ✅ done | proper null **0.045 ± 0.057**; reported margin **survives** (P = 0.000) |
| **X6** | Discovery statistics + averaging | Is the reported gain robust to averaging? | ✅ done | **micro +0.280 / macro −0.080 vs rules-only — sign flip** |

### X1 — Reconstruction protocol (the precondition for everything else)

1. Read the label function from `data_generator.py:104-115` and the metric from
   `benchmark.py:97-131`.
2. Reimplement both in NumPy, including the documented tie convention (τ-b = 1 when all
   assets are indistinguishable, `benchmark.py:111-118`).
3. Load the 42 CBOMs and compute per-fold τ-b.
4. Compare to `planner/results/real_cbom_loo_42.json::fold_metrics[*].heuristic.kendall`.

**Initial result: 41/42 folds matched; one did not.** Diagnosis: `real_gov_edu_2.json`
contains `uic.edu` with `key_size: null`. Assuming 256 gave τ-b = 0.690066; the artifact
reports 0.534522. A sweep over plausible default key sizes showed **only 2048 reproduces the
committed value**, identifying the project's substitution rule. After applying it:
**42/42 folds bit-exact.**

> *This is the honest account of the one iteration the method required. It is also the
> clearest evidence that the reconstruction is faithful: a wrong target would not have
> converged on a single asset's handling.*

### X4 — A self-correction worth recording

My Stage-1 audit estimated the design was underpowered from
SE = √((1−τ²)/n_eff) with n_eff = 407 discordant pairs, giving |Δ|/SE ≈ 0.12. **That analysis
was wrong for this question**, because it treats correlated pairs as independent and ignores
that both methods are evaluated on the same 42 graphs. The correct paired analysis gives
σ_Δ = 0.0275 and MDE(80%) = 0.0138. The experiment is **adequately powered** for effects of
0.02–0.05 (needing only 15 and 2 folds). The null is real, not a power artefact — and the
structural result in X2 explains it fully without statistics.

---

# PART B — PRIORITISED FORWARD PLAN

Priority levels: **Essential** (a central claim or a serious validity threat depends on it)
· **High value** (substantially strengthens the contribution) · **Optional**.

## P1 — ESSENTIAL. Make the discovery evaluation non-circular

| Field | Detail |
|---|---|
| Experiment | Human-label 300 files stratified by language, independent of the detector. At minimum: 100 C, 60 Java, 50 Python, 40 Solidity, 50 other |
| RQ | Does the ensemble's measured agreement survive ground truth? |
| Baseline | Majority, rules-only, full ensemble, ensemble **with ML layer disabled** |
| Metrics | Micro **and** macro P/R/F1; per-language recall with Wilson CIs; **McNemar** vs rules-only |
| Why essential | Failure mode M1 for the discovery leg: labels are produced by the detector under test (Deliverable C, I-11). Nothing else breaks the circularity |
| Cost | ~3 person-days for one expert; ~6 h for two annotators plus adjudication |
| Status | **not started; requires author action** |

## P2 — ESSENTIAL. Re-run the LOO from a clean warm start  [EXECUTED]

> **Status: DONE.** `clean_warmstart_loo.py` trains a synthetic-only base
> (`n_real_graphs = 0`, verified) and re-runs the identical 42-fold protocol through
> the project's own `train_gpu()` / `run_loo()`. Runs on **CPU deliberately**:
> `train_gpu()` enables deterministic algorithms and `torch.cumsum` has no
> deterministic CUDA kernel, so weakening determinism would defeat the experiment.
> Consequence: the project's reduced-CPU path caps training at 2,000 graphs / 5 epochs
> (vs 100,000 / 173 in the committed artifact), so this is a **reduced-budget** re-run.
> The confound is disclosed in the manuscript's threats-to-validity.

| Field | Detail |
|---|---|
| Experiment | Retrain the base checkpoint on **synthetic graphs only** (`n_real_graphs=0`), then run the 42-fold LOO |
| RQ | Does the GNN-vs-baseline conclusion survive without warm-start contamination? |
| Baseline | Doctrine heuristic, key-size sort, properly randomised ranker |
| Metrics | τ-b, node-rank, exact-rank, **MDE**, paired bootstrap CI |
| Why essential | Failure mode M1 for the planner leg: 40/42 held-out folds were in the base model's training set |
| Cost | ~4 GPU-hours (A100 or 3060); the code path already exists (`train_gpu.py`, `eval_real_cbom_loo.py`) |
| Expected | **Prediction: the conclusion will not change** — X2 shows the ceiling is set by the label function. But it must be *shown*, not assumed |
| Status | blocked on `torch` for Python 3.15 (no wheel exists) or a Python 3.11/3.12 venv |

## P3 — ESSENTIAL. Ablate the transformer

| Field | Detail |
|---|---|
| Experiment | Five arms: static-only · +AST · +dataflow · **+ML (full)** · ML-only |
| RQ | What does CodeBERTa contribute? |
| Metrics | Micro **and** macro F1, per-language; delta vs each arm |
| Why essential | `code_detector.py:688` makes a single regex hit decisive and the ML layer can contribute at most 0.20 against a 0.5 threshold. The project has **no** such ablation |
| Cost | ~2 GPU-hours, but **blocked**: the corpus and the fine-tuned checkpoint are both absent |
| Status | **blocked on P0 (data access)** |

## P4 — HIGH VALUE. Real graph edges

| Field | Detail |
|---|---|
| Experiment | Rebuild the 42 CBOM graphs with genuine dependency edges (Syft/Grype SBOM output, or import graphs from the same hosts' repos) |
| RQ | Does message passing help once the graphs have structure? |
| Metrics | τ-b vs edge-free graphs; ablation: random edges vs real edges vs no edges |
| Why | Failure mode M3: all 42 graphs have zero edges, so no message passing occurs |
| Cost | ~1 day engineering; no GPU |
| Note | This is the experiment that would make the GNN leg meaningful. **Highest scientific value per unit of cost in the entire plan** |

## P5 — HIGH VALUE. Statistical comparison against a non-circular baseline

| Field | Detail |
|---|---|
| Experiment | Blinded expert pairwise preference labels on 2,000–5,000 asset pairs from the 277-host corpus (the project's `RiskBench` schema is ready) |
| RQ | Is the doctrine heuristic actually near-optimal on real estates? |
| Metrics | Model–expert Kendall τ-b, inter-rater κ, MDE at the resulting n |
| Why | Failure modes M2 and M4 are both consequences of using the label generator as the comparator. Only expert labels break this |
| Cost | 5–10 experts × 2 h, plus adjudication; κ target ≥ 0.6 |
| Status | **blocked on expert availability** |

## P6 — HIGH VALUE. Robustness of the discovery result

| Field | Detail |
|---|---|
| Experiment | Report the withheld adversarial result (F1 0.5333, specificity 0.000) on real, non-synthetic adversarial cases; measure calibration (ECE, reliability diagram) |
| RQ | Is the ensemble robust, and is its confidence meaningful? |
| Metrics | F1 on obfuscated/renamed real code; ECE; Brier |
| Cost | ~1 day + GPU if the corpus is recovered |
| Status | partially blocked on data access |

## P7 — OPTIONAL. Generalisation across corpora

Reproduce X2 on an independent corpus (e.g. an Internet-wide TLS census with real key-size
diversity). If a key-size sort still matches the heuristic there too, the structural finding
generalises and the paper's contribution strengthens considerably.

## P8 — SECOND AUDITED SYSTEM  ✅ **EXECUTED** (the N=1 fix)

Audited **`Priorizacao_PQC_ML_QUBO`** (MIT, 2026) — chosen deliberately as the
**counterexample** the hypothesis predicts: better artifact hygiene than system 1 on every
axis (committed OOF predictions, audited system-disjoint split with zero overlap, bootstrap
CIs on all 20 method comparisons) and **zero documentation contradictions** — yet it still
fails M2. A linear model restricted to the project's own permitted features exceeds its
reported test AUC on **3 of 3 seeds** (mean **+0.0227**), and hyperparameter selection inside
the linear family buys essentially nothing (P(linear ≥ tuned) ≈ 0.42).

This converts the paper from a single case study to a **designed two-system contrast**,
which is the strongest form the generality argument can take without a multi-system corpus
study.

## P9 — OPTIONAL. Domain-diverse third system

Both audited systems concern PQC migration. A third system in a different domain
(vulnerability detection, software supply-chain risk) would test whether the taxonomy
transfers beyond crypto. Not run; acknowledged in threats-to-validity.

---

## PREREQUISITE (P0) — BLOCKS P3, P5, P6

> **Make `qtrust_ai/artifacts/real_datasets/code_corpus.json` and
> `qtrust_ai/artifacts/crypto_codebert/` public, or confirm they are unrecoverable.**

The audit found both absent. P3 cannot run without them. This is the single
highest-leverage action available to the authors, and it costs nothing.

---

## RESULTS-GATE STATUS

| Gate | Status |
|---|---|
| Experiments needed for the paper's claims | ✅ **complete** (X1–X6) |
| Results verified | ✅ all recomputed from committed artifacts |
| Fabricated or estimated values | **none** |
| Experiments that would strengthen but are not required | E, P2, P4, P7, P8 — **none blocking** |
| Experiments blocked on author action | P1, P3, P5, P6 |

**The paper can be submitted on existing evidence.** P4 (real edges) would materially
improve it. P0 unblocks the most.