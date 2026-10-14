# DELIVERABLE G â€” REPRODUCIBILITY PACKAGE

Everything needed to reproduce every number in the manuscript. No GPU, no dataset package,
no checkpoint, and no network access required.

---

## 1. CONTENTS

```
artifact/
â”œâ”€â”€ scripts/
â”‚   â”œâ”€â”€ verify_qtrust_claims.py    # headline-claim verification (STDLIB ONLY)
â”‚   â”œâ”€â”€ verify_ckpt_leak.py        # checkpoint-metadata leakage check (STDLIB ONLY)
â”‚   â”œâ”€â”€ experiments_reaudit.py     # the six re-audit experiments (numpy + scipy)
â”‚   â”œâ”€â”€ validate_eval.py           # 8-mode repo-agnostic checker (STDLIB ONLY)  ** NEW **
â”‚   â”œâ”€â”€ clean_warmstart_loo.py     # clean warm-start 42-fold LOO (torch + PyG)    ** NEW **
â”‚   â”œâ”€â”€ fair_baseline_system2.py   # second-system fair baseline (sklearn)          ** NEW **
â”‚   â”œâ”€â”€ make_figure1.py            # Figure 1 (numpy, scipy, matplotlib)
â”‚   â””â”€â”€ check_tex.py               # manuscript self-consistency check (STDLIB ONLY)
â”œâ”€â”€ paper/
â”‚   â”œâ”€â”€ main.tex                   # IEEEtran two-column source
â”‚   â”œâ”€â”€ figure1_structural_findings.pdf
â”‚   â””â”€â”€ figure1_structural_findings.png
â”œâ”€â”€ results/
â”‚   â””â”€â”€ experiments_output.txt     # verbatim output of the six experiments
â”œâ”€â”€ DELIVERABLE_A_TECHNICAL_AUDIT.md
â”œâ”€â”€ DELIVERABLE_A_STAGE1B.md
â”œâ”€â”€ DELIVERABLE_A_STAGE1C.md
â”œâ”€â”€ DELIVERABLE_B_RESEARCH_STRATEGY.md
â””â”€â”€ DELIVERABLE_C_EVIDENCE_LEDGER.md
```

---

## 2. ENVIRONMENT

| Component | Requirement | Used for |
|---|---|---|
| Python | 3.10 or later | all |
| NumPy | any recent | `experiments_reaudit.py`, `make_figure1.py` |
| SciPy | any recent | `experiments_reaudit.py`, `make_figure1.py` |
| Matplotlib | any recent | `make_figure1.py` only |
| **Everything else** | **none** | --- |
| GPU | **not required** | --- |
| Network | **not required** | --- |
| Dataset package | **not required** | --- |

Verified on Python 3.15, NumPy 2.5.4, SciPy 1.18.1, Matplotlib 3.11.2.

**Note on `torch`:** the audited repository's training code requires PyTorch and
PyTorch Geometric. We deliberately do **not** require them. Every claim in the paper is
derived either from committed JSON artifacts or from the committed CBOM corpus, so the
audit is fully reproducible without the training stack. This is a property of the audit,
not a limitation of it.

---

## 3. EXECUTION

```bash
git clone --depth 1 https://github.com/[SYSTEM A].git
cd q-trust

# Pass the repo root explicitly to every script.

# 1. Verify every headline claim (stdlib only; no third-party packages)
python ../artifact/scripts/verify_qtrust_claims.py .

# 2. Inspect the LOO checkpoint metadata for warm-start contamination
python ../artifact/scripts/verify_ckpt_leak.py

# 3. Run the six new experiments
python -m pip install numpy scipy
python ../artifact/scripts/experiments_reaudit.py .

# 4. Regenerate Figure 1
python -m pip install matplotlib
python ../artifact/scripts/make_figure1.py . .

# 5. Self-check the manuscript source
python ../artifact/scripts/check_tex.py
```

---

## 4. EXPECTED OUTPUT AND HOW TO READ IT

### Step 1 â€” `verify_qtrust_claims.py`

Prints four sections (C1 corpus, C2 discovery, C3 adversarial, C4 GNN LOO) and a summary.
The summary must read:

```
headline claims reproduced exactly : 14
headline claims MISMATCHED         : 0
```

A nonzero MISMATCHED count means the repository has changed since the audit. That is the
intended behaviour: the harness is a regression test on the project's own artifacts.

### Step 2 â€” `verify_ckpt_leak.py`

Reads `planner/model_gpu_v3.pt` with a stubbed `torch` (the file is a zip archive of a
pickle). Must print:

```
n_real_graphs     = 40
epochs            = 173
n_graphs          = 100000
norm              = layer
model_config      = {'input_features': 6, 'hidden_dim': 256, 'embedding_dim': 128,
                     'heads': 8, 'dropout': 0.15, 'variant': 'hybrid', 'norm': 'layer'}
```

This single line, `n_real_graphs = 40`, establishes failure mode **M1**.

### Step 3 â€” `experiments_reaudit.py`

Runs X1--X6. Key lines to verify:

```
X1 ... RECONSTRUCTION VALIDATED (42/42 folds bit-exact against the committed artifact)
X2 ... IDENTICAL metric vectors on 42/42 folds.
X3 ... 95% CI = [-0.012727, +0.000000]
X4 ... MDE at 80% power = 0.0138 | Observed |delta| = 0.004242
X5 ... mean tau-b = 0.0447 sd = 0.0570 | P(random >= 0.6867) = 0.0000
X6 ... macro-F1 = 0.5929 | vs rules-only: -0.0801 (vs micro: +0.2795)
```

Runtime is dominated by X5 (400 randomisation draws x 42 folds). Expect 2-5 minutes.
A verbatim transcript is in `results/experiments_output.txt`.

**Determinism.** All bootstrap and permutation seeds are fixed
(`np.random.default_rng(20260918)`, `np.random.default_rng(42)`). Repeated runs on the same
NumPy version produce identical output.

### Step 4 â€” `make_figure1.py`

Writes `figure1_structural_findings.pdf` and `.png`. Requires Matplotlib.

### Step 5 â€” `check_tex.py`

Must print:

```
ENVIRONMENT ERRORS: none
DANGLING REFS : none
MISSING BIBITEM: none
UNCITED BIBITEM: none
```

---

## 5. DATA PROVENANCE AND LICENSING

| Item | Provenance | License / status |
|---|---|---|
| 42 CBOM files | Live TLS scan of 277 public hosts, grouped by industry | MIT (project repo) |
| `real_cbom_loo_42.json` | Project artifact | MIT |
| `training_report_real.json` | Project artifact | MIT |
| `benchmark_comparison.json` | Project artifact | MIT |
| `benchmarks/external/` | CryptoAPI-Bench + Apache jars | MIT / Apache-2.0 (vendored in-repo) |
| Checkpoint metadata | Project artifact, read-only | MIT |

**Privacy.** The corpus contains public TLS certificate metadata (host, issuer, subject,
validity, public-key algorithm and size). It contains no private keys, no payloads, and no
personal data beyond certificate subject fields, which are public by construction. The
grouping labels use the RFC 2606 placeholder domain \code{acme-*.example}; no real
organisation is represented as an "estate owner".

**No dataset is redistributed.** The 42 CBOMs and 5 trace files already ship in the
repository. The project's separately hosted dataset package was inaccessible during the
audit and is therefore not required, referenced, or redistributed here.

---

## 6. WHAT IS NOT IN THIS PACKAGE, AND WHY

| Not included | Reason |
|---|---|
| The fine-tuned CodeBERTa checkpoint | Absent from the audited repository (`.gitignore`); the audit does not need it |
| The code corpus | Absent; discovery claims are audited from the committed evaluation artifact only |
| The 500 synthetic estates | Absent; referenced in documentation but generated by no code path |
| `rl_agent_real.pt` | Absent; the RL result is therefore excluded from the paper |
| Any re-run training | Would require the absent dataset plus a GPU; adds nothing, since every audited claim comes from committed artifacts |

**This is itself a finding.** A reader can reproduce our entire analysis but cannot
reproduce the project's headline training runs. That asymmetry is the strongest available
evidence for the paper's central argument, and it is why we did not paper over it.

---

## 7. VERIFICATION CHECKLIST FOR REVIEWERS

- [ ] `verify_qtrust_claims.py` reports **0 mismatches**
- [ ] `verify_ckpt_leak.py` reports **`n_real_graphs = 40`**
- [ ] X1 reports **42/42 folds bit-exact**
- [ ] X2 reports identical metric vectors on **42/42 folds**
- [ ] X6 reports macro-F1 **0.5929** and a **$-0.0801$** delta vs rules-only
- [ ] Table 1 of the paper matches `results/experiments_output.txt`
- [ ] `check_tex.py` reports no dangling references and no missing bibitems