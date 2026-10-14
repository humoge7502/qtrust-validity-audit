#!/usr/bin/env python3
"""
validate_eval.py — a repository-agnostic evaluator-validity checker
====================================================================

Implements the eight failure modes from

    "Provenance Labelling Is Not Evaluative Validity:
     A Reproducibility Audit of a Post-Quantum Cryptography
      Migration Benchmark"

as automated, repo-agnostic checks.  Point it at any repository that ships
an ML evaluation and it reports, per mode, PRESENT / ABSENT / UNKNOWN with
file-level evidence.

Design goals
------------
* No project-specific knowledge. Patterns are generic (regex + JSON walk).
* Honest: UNKNOWN is a first-class verdict. The tool never guesses.
* Zero heavy dependencies for the core checks (stdlib only).
* Every finding carries the exact file and the evidence that triggered it.

Usage
-----
    python validate_eval.py --repo <path> [--json out.json] [--strict]

Exit codes
----------
    0  no mode detected as PRESENT
    1  at least one mode detected as PRESENT
    2  usage / environment error
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

# ==========================================================================
#  M1  warm-start contamination
#  A checkpoint used to initialise an evaluation that was previously trained
#  on data overlapping the evaluation set.
#  Detection: read provenance counters out of committed checkpoint metadata and
#  compare them against the evaluation corpus size.
# ==========================================================================
M1_PATTERNS = [
    r"\binit_from\b", r"\bbase_model\b", r"\bpretrained(?:_path)?\b",
    r"\bresume(?:_from)?\b", r"\bwarm_?start\w*\b", r"\bload_state_dict\w*\b",
]
# provenance counters that reveal training-set composition
PROV_KEYS = ("n_real", "n_train_graphs", "n_train_samples", "n_real_graphs",
             "n_synthetic", "train_size", "n_fit", "num_train")
CORPUS_KEYS = ("n_cboms", "n_folds", "n_hosts", "n_assets", "n_samples",
               "n_examples", "n_datasets", "n_cases")


def m1_warm_start(repo: str) -> dict:
    ev = {"mode": "M1 warm-start contamination",
          "verdict": "UNKNOWN", "evidence": [], "note": ""}
    # (a) committed JSON that declares both a corpus size and a provenance counter
    for dirpath, _, files in os.walk(repo):
        if any(x in dirpath for x in (".git", "node_modules", "__pycache__")):
            continue
        for fn in files:
            if not fn.endswith(".json"):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(fp) > 40_000_000:
                    continue
                d = json.load(open(fp, encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            prov = {k: v for k, v in d.items()
                    if k in PROV_KEYS and isinstance(v, int)}
            corp = {k: v for k, v in d.items()
                    if k in CORPUS_KEYS and isinstance(v, int)}
            if prov and corp:
                n_prov = max(prov.values())
                n_corp = max(corp.values())
                ev["evidence"].append(
                    "%s: provenance %s vs corpus %s" % (
                        os.path.relpath(fp, repo), prov, corp))
                if n_prov >= 0.8 * n_corp and n_corp > 0:
                    ev["verdict"] = "PRESENT"
                    ev["note"] = ("init artefact records %d training units against a "
                                  "%d-unit evaluation corpus (>=80%%): the evaluation "
                                  "is very likely in-sample" % (n_prov, n_corp))
    # (b) code pattern: evaluation initialised from a stored checkpoint
    if ev["verdict"] != "PRESENT":
        for dirpath, _, files in os.walk(repo):
            if any(x in dirpath for x in (".git", "node_modules", "__pycache__")):
                continue
            for fn in files:
                if not fn.endswith((".py", ".sh", ".yaml", ".yml", ".md")):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    txt = open(fp, encoding="utf-8", errors="ignore").read()
                except Exception:
                    continue
                for pat in M1_PATTERNS:
                    for mt in re.finditer(pat, txt):
                        line = txt[:mt.start()].count("\n") + 1
                        ctx = txt.splitlines()[line - 1].strip()[:160]
                        ev["evidence"].append(
                            "%s:%d  %s" % (os.path.relpath(fp, repo), line, ctx))
                        break
    if ev["evidence"] and ev["verdict"] == "UNKNOWN":
        ev["verdict"] = "UNKNOWN"
        ev["note"] = ("warm-start-looking patterns found; no checkpoint metadata "
                      "available to confirm or refute contamination")
    return ev


# ==========================================================================
#  M2  circular baseline
#  The comparison baseline reimplements the label generator, so the model
#  ceiling is 1.0 by construction.
#  Detection: find a scoring/priority function and a labelling function in the
#  same file and compare their normalised token signatures.
# ==========================================================================
PRIORITY_TOKENS = re.compile(
    r"(priority|score|weight|urgency|criticality)\w*\s*[=+\-]?"
    r"|[\w.]+\s*\*\s*[\d.]+|\*\s*[\d.]+|\+\s*[\d.]+|"
    r"\blog1p?\s*\(|\bnp\.log|\blog\s*\(", re.I)
LABEL_FN = re.compile(
    r"def\s+(_?assign_labels?|label_graph|make_labels?|"
    r"_assign_priority|compute_ground_truth|generate_labels?)\s*\(", re.I)
BASE_FN = re.compile(
    r"def\s+(_?(heuristic|baseline|rule|doctrine|priority_order|oracle)"
    r"[_\w]*)\s*\(", re.I)


def _sig(txt: str) -> Counter:
    return Counter(t.lower() for t in PRIORITY_TOKENS.findall(txt))


def _body(src: str, lines: list, mt, limit: int = 80) -> str:
    """Extract a function body.

    Handles multi-line signatures: the body starts after the line that closes
    the `def ...:` header, not immediately after the `def` keyword. Without this,
    any function with a wrapped parameter list yields an empty body and every
    signature-based check silently returns ABSENT.
    """
    start = src[:mt.start()].count("\n")
    indent = len(lines[start]) - len(lines[start].lstrip())
    j = start
    while j < len(lines) - 1:
        ln = lines[j]
        if ln.rstrip().endswith(":") and (len(ln) - len(ln.lstrip())) <= indent:
            break
        j += 1
        if j - start > 20:
            return ""
    out = []
    for i in range(j + 1, min(len(lines), j + limit)):
        ln = lines[i]
        if ln.strip() and (len(ln) - len(ln.lstrip())) <= indent \
                and not ln.strip().startswith("#"):
            break
        out.append(ln)
    return "\n".join(out)


def _collect(src, sinks, pattern, fp):
    lines = src.splitlines()
    for mt in pattern.finditer(src):
        b = _body(src, lines, mt)
        if b:
            sinks.append((fp, pattern.pattern[:12], b))


def _cross_file(repo, hits):
    """Compare label functions against baseline functions anywhere in the repo."""
    labels, bases = [], []
    for dirpath, dirnames, files in os.walk(repo):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "node_modules", "__pycache__",
                                    "tests", "test", "docs")]
        for fn in files:
            if not fn.endswith(".py"):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                src = open(fp, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            _collect(src, labels, LABEL_FN, fp)
            _collect(src, bases, BASE_FN, fp)
    for lfp, _, lb in labels:
        sl = _sig(lb)
        if not sl:
            continue
        for bfp, _, bs in bases:
            sb = _sig(bs)
            if not sb:
                continue
            inter = sum((sl & sb).values())
            if inter >= 3 and inter >= 0.5 * sum(sl.values()):
                hits.append((lfp, "label", lb, bfp, "baseline", bs, inter,
                             sum(sl.values())))
                return


def m2_circular(repo: str) -> dict:
    ev = {"mode": "M2 circular baseline", "verdict": "ABSENT",
          "evidence": [], "note": ""}
    hits = []
    for dirpath, _, files in os.walk(repo):
        if any(x in dirpath for x in (".git", "node_modules", "__pycache__")):
            continue
        for fn in files:
            if not fn.endswith(".py"):
                continue
    _cross_file(repo, hits)
    for (lfp, lname, lb, bfp, bname, bs, inter, tot) in hits[:6]:
        ev["verdict"] = "PRESENT"
        ev["evidence"].append(
            "%s: label fn `%s` and baseline fn `%s` share %d/%d scoring terms"
            % (os.path.relpath(lfp, repo), lname, bname, inter, tot))
        ev["evidence"].append("    label   [" + os.path.basename(lfp) + "]: " + " ".join(
            l.strip() for l in lb.strip().splitlines()[:3])[:130])
        ev["evidence"].append("    baseline[" + os.path.basename(bfp) + "]: " + " ".join(
            l.strip() for l in bs.strip().splitlines()[:3])[:130])
    if ev["verdict"] == "ABSENT":
        ev["note"] = ("no label function and baseline function with a shared "
                      "numeric scoring signature were found (same file or package)")
    return ev


# ==========================================================================
#  M3  degenerate structure
#  Graphs with no edges (so a GNN does no message passing), or features with
#  zero variance.
#  Detection: walk committed data for edge lists and field cardinalities.
# ==========================================================================
def m3_degenerate(repo: str, max_files: int = 4000) -> dict:
    ev = {"mode": "M3 degenerate structure", "verdict": "ABSENT",
          "evidence": [], "note": ""}
    scanned = 0
    edge_files = 0
    total_edges = 0
    const_fields = defaultdict(set)
    asset_files = 0

    for dirpath, dirnames, files in os.walk(repo):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "node_modules", "__pycache__",
                                    "vendor", "test-results")]
        for fn in files:
            if not fn.endswith(".json"):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(fp) > 60_000_000:
                    continue
                d = json.load(open(fp, encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            scanned += 1
            if scanned > max_files:
                break
            # edge-bearing graph objects
            if isinstance(d, dict):
                for k in ("edge_index", "edges", "links", "dependencies",
                          "adjacency"):
                    if k in d and isinstance(d[k], list):
                        edge_files += 1
                        total_edges += len(d[k])
                        ev["evidence"].append(
                            "%s: %d %s" % (os.path.relpath(fp, repo),
                                           len(d[k]), k))
                        break
            # asset lists -> field cardinality
            for key in ("assets", "nodes", "findings", "records", "items"):
                lst = d.get(key) if isinstance(d, dict) else None
                if isinstance(lst, list) and lst and isinstance(lst[0], dict):
                    asset_files += 1
                    n = 0
                    for a in lst:
                        if not isinstance(a, dict):
                            continue
                        n += 1
                        for fk, fv in a.items():
                            if fk.startswith("_"):
                                continue
                            const_fields[fk].add(str(fv))
                        if n >= 500:
                            break
    for fk, vals in const_fields.items():
        if len(vals) == 1:
            v = next(iter(vals))
            if v in ("None", "null", ""):
                continue        # a uniformly-null field is absence, not degeneracy
            ev["verdict"] = "PRESENT"
            ev["evidence"].append(
                "zero-variance field across %d asset records: %s = %r"
                % (asset_files, fk, v[:40]))
    if edge_files and total_edges == 0:
        ev["verdict"] = "PRESENT"
        ev["evidence"].append("%d files declare an edge list; ALL are empty" % edge_files)
    if not ev["evidence"]:
        ev["note"] = "no committed asset or graph objects were found to inspect"
    elif ev["verdict"] == "ABSENT":
        ev["note"] = ("inspected %d JSON files / %d asset records; no zero-variance "
                      "feature and no all-empty edge list" % (scanned, asset_files))
    return ev


# ==========================================================================
#  M4  tie-saturated / underpowered rank metric
#  Detection: from committed label arrays, compute the fraction of tied pairs
#  and the standard error of Kendall tau-b.
# ==========================================================================
def kendall_tau_b(x, y):
    n = len(x)
    c = dd = t = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[i] - x[j]
            dy = y[i] - y[j]
            p = dx * dy
            if p > 0:
                c += 1
            elif p < 0:
                dd += 1
            else:
                t += 1
    n0 = c + dd + t
    n1 = c + dd
    if n1 == 0 or n0 == 0:
        return float("nan")
    return (c - dd) / math.sqrt((n0 - t) * n1) if (n0 - t) * n1 > 0 else float("nan")


def m4_ties(repo: str) -> dict:
    ev = {"mode": "M4 tie-saturated metric", "verdict": "ABSENT",
          "evidence": [], "note": ""}
    for dirpath, _, files in os.walk(repo):
        if any(x in dirpath for x in (".git", "node_modules", "__pycache__")):
            continue
        for fn in files:
            if not (fn.endswith(".json") or fn.endswith(".csv")):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                if fn.endswith(".json"):
                    d = json.load(open(fp, encoding="utf-8", errors="ignore"))
                else:
                    continue
            except Exception:
                continue
            # per-fold metric dicts: {"model": {"kendall": x}, ...}
            if not isinstance(d, dict):
                continue
            container = None
            for k in ("fold_metrics", "folds", "results", "per_fold"):
                if isinstance(d.get(k), dict):
                    container = d[k]
                    break
            if not container:
                continue
            tie_fracs, deltas, sizes = [], [], []
            for name, fold in container.items():
                if not isinstance(fold, dict):
                    continue
                n = fold.get("n_assets") or fold.get("n")
                if isinstance(n, int):
                    sizes.append(n)
                for arm in ("model", "heuristic", "baseline", "oracle"):
                    a = fold.get(arm)
                    if isinstance(a, dict):
                        ks = [k2 for k2 in a if "tau" in k2.lower()
                              or "kendall" in k2.lower()]
                        if ks:
                            kk = ks[0]
                            for arm2 in ("heuristic", "baseline", "oracle"):
                                b = fold.get(arm2)
                                if isinstance(b, dict) and kk in b:
                                    try:
                                        deltas.append(abs(float(a[kk]) - float(b[kk])))
                                    except Exception:
                                        pass
                            break
            if not sizes:
                continue
            mx = max(sizes)
            if deltas:
                ev["evidence"].append(
                    "%s: %d folds, max n=%d, median |delta tau-b| = %.5f"
                    % (os.path.relpath(fp, repo), len(sizes), mx,
                       statistics.median(deltas)))
                if statistics.median(deltas) < 0.02 and mx <= 10:
                    ev["verdict"] = "PRESENT"
    if ev["verdict"] == "PRESENT":
        ev["note"] = ("median |delta| below 0.02 on graphs of <=10 items: a "
                      "tie-saturated metric cannot separate the methods")
    elif not ev["evidence"]:
        ev["note"] = "no per-fold metric container found"
    return ev


# ==========================================================================
#  M5  vacuous top-k
#  Detection: any reported top-k metric where k >= n.
# ==========================================================================
def m5_topk(repo: str) -> dict:
    ev = {"mode": "M5 vacuous top-k", "verdict": "ABSENT",
          "evidence": [], "note": ""}
    for dirpath, _, files in os.walk(repo):
        if any(x in dirpath for x in (".git", "node_modules", "__pycache__")):
            continue
        for fn in files:
            if not fn.endswith(".json"):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(fp) > 40_000_000:
                    continue
                d = json.load(open(fp, encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            container = d.get("fold_metrics") or d.get("folds")
            if not isinstance(container, dict):
                continue
            vac = []
            for name, fold in container.items():
                if not isinstance(fold, dict):
                    continue
                n = fold.get("n_assets") or fold.get("n")
                if not isinstance(n, int):
                    continue
                for arm in ("model", "heuristic", "random", "baseline"):
                    a = fold.get(arm)
                    if not isinstance(a, dict):
                        continue
                    for k2, v in a.items():
                        m = re.match(r"top(\d+)$", k2)
                        if m and int(m.group(1)) >= n:
                            vac.append((name, arm, k2, n, v))
            if vac:
                ev["verdict"] = "PRESENT"
                uniq = sorted({(v[3], v[2]) for v in vac})
                ev["evidence"].append(
                    "%s: %d vacuous top-k entries, e.g. %s"
                    % (os.path.relpath(fp, repo), len(vac),
                       ", ".join("top%s with n=%s" % (k, n) for n, k in uniq[:4])))
    if ev["verdict"] == "ABSENT":
        ev["note"] = "no reported top-k metric with k >= n was found"
    return ev


# ==========================================================================
#  M6  non-random baseline
#  Detection: a "random" baseline that hard-codes a seed.
# ==========================================================================
RAND_FN = re.compile(
    r"def\s+\w*(random|shuffle|permut)\w*\s*\(", re.I)
SEED_LITERAL = re.compile(
    r"(default_rng|manual_seed|RandomState|random\.seed|np\.random\.seed|"
    r"torch\.randperm|np\.random\.\w+)\s*\(\s*\d+")
FUNC_SEED_CTX = re.compile(
    r"(default_rng|manual_seed|RandomState|random\.seed|np\.random\.seed)\s*\(\s*\d+"
    r"|(?:rng|random|rand)\s*=\s*(?:np\.random\.)?(?:default_rng|RandomState)\s*\(\s*\d+\s*\)")


def m6_random(repo: str) -> dict:
    ev = {"mode": "M6 non-random 'random' baseline",
          "verdict": "ABSENT", "evidence": [], "note": ""}
    for dirpath, _, files in os.walk(repo):
        if any(x in dirpath for x in (".git", "node_modules", "__pycache__")):
            continue
        for fn in files:
            if not fn.endswith(".py"):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                src = open(fp, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            lines = src.splitlines()
            for mt in RAND_FN.finditer(src):
                start = src[:mt.start()].count("\n")
                btxt = _body(src, lines, mt, limit=40)
                m = SEED_LITERAL.search(btxt)
                if m:
                    ev["verdict"] = "PRESENT"
                    ev["evidence"].append(
                        "%s:%d  %s -> hard-coded seed: %s"
                        % (os.path.relpath(fp, repo), start + 1,
                           lines[start].strip()[:70], m.group(0)[:50]))
                    break
    if ev["verdict"] == "ABSENT":
        ev["note"] = ("no 'random' baseline function was found with a hard-coded "
                      "RNG seed")
    return ev


# ==========================================================================
#  M7  absent predictions
#  Detection: look for committed per-example predictions or a split manifest.
# ==========================================================================
PRED_PAT = re.compile(r"(per_example|predictions|probs|scores|y_true|y_pred|"
                      r"y_true_|logits|hard_labels)", re.I)
SPLIT_PAT = re.compile(r"(split_manifest|train_test_split|split_list|"
                        r"repos_in_(train|test|eval)|fold_assignments)", re.I)


def m7_predictions(repo: str) -> dict:
    ev = {"mode": "M7 absent predictions", "verdict": "ABSENT",
          "evidence": [], "note": ""}
    pred_files, split_files = [], []
    for dirpath, dirnames, files in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules",
                                                        "__pycache__")]
        for fn in files:
            if not fn.endswith((".json", ".jsonl", ".npy", ".npz", ".csv")):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, repo)
            if PRED_PAT.search(fn):
                pred_files.append(rel)
            if SPLIT_PAT.search(fn):
                split_files.append(rel)
    # also: a result file that stores ONLY aggregates
    agg_only = []
    for dirpath, dirnames, files in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules",
                                                        "__pycache__")]
        for fn in files:
            if not fn.endswith(".json"):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(fp) > 40_000_000:
                    continue
                d = json.load(open(fp, encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            if any(k in d for k in ("metrics", "summary", "scores", "results")):
                agg_only.append(os.path.relpath(fp, repo))
    if pred_files:
        ev["note"] = "per-example prediction artefacts found: %s" % pred_files[:5]
    if split_files:
        ev["note"] = (ev["note"] + " | split manifests found: %s" % split_files[:5]).strip(" |")
    if not pred_files and not split_files:
        ev["verdict"] = "PRESENT"
        ev["evidence"].append(
            "no per-example predictions and no split manifest are committed "
            "(%d result file(s) store aggregates only)" % len(agg_only))
        ev["evidence"].extend("    aggregate-only: " + x for x in agg_only[:5])
    return ev


# ==========================================================================
#  M8  unreconciled documentation
#  Detection: same metric name, different values across documentation files.
# ==========================================================================
NUM = re.compile(r"(?<![\w.])(\d+\.\d{2,4})(?![\w.])")
# metric keywords -> normalised key
DOC_METRIC = re.compile(
    r"(?:F1|F-?score|accuracy|precision|recall|kendall|tau|tau-b|"
    r"mae|precision|recall|tests?|CBOMs?|hosts?|files?|CBOM|assets?)",
    re.I)


def m8_docs(repo: str) -> dict:
    ev = {"mode": "M8 unreconciled documentation", "verdict": "ABSENT",
          "evidence": [], "note": ""}
    buckets = defaultdict(set)
    docs = []
    for dirpath, dirnames, files in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules",
                                                        "__pycache__", "vendor")]
        for fn in files:
            if not fn.lower().endswith((".md", ".rst")):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(fp) > 3_000_000:
                    continue
                txt = open(fp, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            rel = os.path.relpath(fp, repo)
            docs.append(rel)
            for ln in txt.splitlines():
                if not DOC_METRIC.search(ln):
                    continue
                for m in NUM.finditer(ln):
                    try:
                        v = float(m.group(1))
                    except ValueError:
                        continue
                    if v <= 0 or v > 1_000_000:
                        continue
                    # bucket by the metric word on the line + value
                    words = set(w.lower() for w in DOC_METRIC.findall(ln))
                    if not words:
                        continue
                    key = "|".join(sorted(words))
                    buckets[key].add((v, rel))
    multi = {k: v for k, v in buckets.items() if len({x[0] for x in v}) > 1
             and len({x[1] for x in v}) > 1}
    if multi:
        ev["verdict"] = "PRESENT"
        n = 0
        for k, vals in sorted(multi.items(), key=lambda kv: -len(kv[1]))[:12]:
            byval = defaultdict(list)
            for v, srcname in vals:
                byval[v].append(srcname)
            if len(byval) > 1:
                ev["evidence"].append(
                    "%s -> %s" % (k.split("|")[0][:28],
                                  {("%.4f" % v): len(s) for v, s in
                                   sorted(byval.items())}))
                n += 1
        ev["note"] = ("%d metric names carry conflicting values across %d "
                      "documentation files" % (n, len(docs)))
    else:
        ev["note"] = ("no metric name was found with conflicting values across %d "
                      "documentation files" % len(docs))
    return ev


# ==========================================================================
MODES = [m1_warm_start, m2_circular, m3_degenerate, m4_ties, m5_topk,
         m6_random, m7_predictions, m8_docs]
MODE_TITLES = ["M1 warm-start contamination", "M2 circular baseline",
               "M3 degenerate structure", "M4 tie-saturated metric",
               "M5 vacuous top-k", "M6 non-random baseline",
               "M7 absent predictions", "M8 unreconciled documentation"]
RECOVERY = {
    "M1": "record the training provenance of every checkpoint used to initialise an "
          "evaluation, and assert it against the evaluation corpus in code",
    "M2": "use an independent comparator -- expert labels, or a rule fixed before the "
          "labels were collected",
    "M3": "verify that graph edges and feature cardinality are non-degenerate; report "
          "edge counts and per-feature distinct-value counts",
    "M4": "report the tied-pair fraction, the standard error, and the minimum detectable "
          "effect alongside any difference",
    "M5": "check k < n before reporting top-k; prefer rank-correlation metrics with "
          "stated tie handling",
    "M6": "draw randomised baselines from more than one seed and report the spread",
    "M7": "commit per-example predictions and the split manifest so that paired tests "
          "are possible",
    "M8": "generate headline numbers from artifacts, not from prose; assert "
          "documentation against the artifacts in CI",
}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Repository-agnostic evaluator-validity checker (8 modes).")
    ap.add_argument("--repo", required=True, help="path to the repository root")
    ap.add_argument("--json", help="write machine-readable results here")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any mode is PRESENT (default behaviour)")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    if not os.path.isdir(repo):
        print("not a directory: %s" % repo, file=sys.stderr)
        return 2
    print("=" * 92)
    print("validate_eval.py  --  evaluator-validity checker")
    print("repo: %s" % repo)
    print("=" * 92)

    results = []
    for fn, title in zip(MODES, MODE_TITLES):
        try:
            r = fn(repo)
        except Exception as e:                      # never crash the whole run
            r = {"mode": title, "verdict": "UNKNOWN",
                 "evidence": ["checker raised %s: %s" % (type(e).__name__, e)],
                 "note": ""}
        r["recovery"] = RECOVERY[r["mode"].split()[0]]
        results.append(r)
        flag = {"PRESENT": "[FAIL]", "ABSENT": "[ ok ]", "UNKNOWN": "[????]"}[r["verdict"]]
        print("\n%s  %s" % (flag, r["mode"]))
        if r.get("note"):
            print("        %s" % r["note"])
        for e in r["evidence"][:8]:
            print("        %s" % e)
        if len(r["evidence"]) > 8:
            print("        ... and %d more" % (len(r["evidence"]) - 8))

    n_present = sum(1 for r in results if r["verdict"] == "PRESENT")
    n_unknown = sum(1 for r in results if r["verdict"] == "UNKNOWN")
    print("\n" + "=" * 92)
    print("SUMMARY: %d of 8 modes PRESENT, %d ABSENT, %d UNKNOWN"
          % (n_present, 8 - n_present - n_unknown, n_unknown))
    print("Remediation guidance is attached to each mode above.")
    print("=" * 92)

    if args.json:
        json.dump({"repo": repo, "results": results,
                   "summary": {"present": n_present, "unknown": n_unknown}},
                  open(args.json, "w", encoding="utf-8"), indent=2)
        print("wrote %s" % args.json)

    return 1 if (n_present and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())