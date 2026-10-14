# DELIVERABLE A — TECHNICAL AUDIT
## Q-Trust: Post-Quantum Cryptography Migration & Attestation System
**Audit date:** 2026-10-14 · **Auditor:** independent review · **Repo commit:** `8e47891`

All findings below were produced by direct inspection and by recomputation from committed
artifacts. The recomputation harness is `verify_qtrust_claims.py` (stdlib only, runs on a
fresh clone, no GPU or datasets package required).

---

## 0. ACCESS STATUS — READ THIS FIRST

| Resource | URL given | Status | Evidence |
|---|---|---|---|
| Main repo | `humoge7502/q-trust` | **ACCESSIBLE** | Cloned, 1,165 files, 315 MB, 3,800+ commits |
| CodeBERT repo | `KRISHNAPURI/q-trust-codebert` | **HTTP 404 — NOT ACCESSIBLE** | GitHub API returns 404; `github.com/KRISHNAPURI` has **0 public repositories** |
| Dataset repo | `KRISHNAPURI/q-trust-datasets` | **HTTP 404 — NOT ACCESSIBLE** | Same |

The GitHub account `KRISHNAPURI` exists (created 2019-12-03) but has **zero public
repositories**. Two of the three resources named in the brief therefore cannot be
inspected. They are private, deleted, or never existed.

Two things are *not* lost, however, and I verified both:

- `huggingface.co/spaces/KRISHNAPURI/q-trust-scanner` — **public**, HTTP 200. So the
  account owns public artifacts; only the GitHub repos are gone.
- `pypi.org/project/qtrust-inspector` and `/project/qtrust-sdk` — **both real, v2.2.0**.

**Consequence for the paper: two of the three ML datasets and the fine-tuned checkpoint
exist only behind the 404.** Details in §3.

---

## 1. THE PREMISE NEEDS CORRECTING BEFORE ANY WRITING HAPPENS

The brief describes a "Q-Trust project" built around **CodeBERT** with a companion
**dataset repository**. The repository that actually exists is a different thing:

> **Q-Trust is a post-quantum cryptography (PQC) migration and attestation system.**
> Pipeline: `discover → score → plan → attest` — a CycloneDX CBOM scanner, a
> NIST/CNSA risk engine, a **PyTorch Geometric GNN + RL** migration planner, and EIP-712
> attestations on Base L2.

Three corrections that materially change the paper:

1. **The model is CodeBERTa, not CodeBERT.** `qtrust_ai/discovery/code_detector.py:832`
   pins `huggingface/CodeBERTa-small-v1` @ `e93b5898`. These are unrelated models by
   different authors. CodeBERTa is a 6-layer, 84M-parameter RoBERTa-style masked-LM
   trained from scratch on CodeSearchNet (~2M *functions*, 5 epochs, 6 languages).
   Microsoft's `microsoft/codebert-base` is never referenced anywhere in the repo.
   **The "CodeBERT repository" in the brief does not correspond to this project.**

2. **CodeBERTa is one component of ~15 ML models**, and is *not* the central model.
   The headline GNN ranking metric belongs to a different model entirely.

3. **This is a security-engineering systems project, not an ML-methods project.**
   The defensible publication venue class is applied security / systems / standards
   (see Stage 13), not an ML-conference venue.

---

## 2. WHAT IS ACTUALLY IMPLEMENTED (verified)

| Layer | Component | Location | Nature |
|---|---|---|---|
| Scan | 10-module inspector, TLS/SSH/source/manifest/binary | `inspector/` | Mostly regex + AST |
| Score | NIST SP 800-131A / CNSA 2.0 / FIPS 140-3 scoring | `qtrust_ai/risk/`, `qtrust_ai/policy/` | **Deterministic rules** |
| Discover | `CryptoCodeDetector` 4-layer ensemble | `qtrust_ai/discovery/code_detector.py` | Regex+AST+dataflow+optional CodeBERTa |
| Plan | `MigrationGNNv3` (PyG) + PPO agent | `planner/`, `qtrust_ai/migration/` | **Learned** |
| Attest | 11 UUPS registries, EIP-712 gasless, 7-day timelock | `contracts/` (Solidity/Foundry) | On-chain |
| Data | CBOM builders, corpora, splits | `scripts/build_real_*.py`, `qtrust_data/` | Mixed real/synthetic |
| Verify | W3C VC / IPFS / hash-only privacy model | `sdk/`, `qtrust/data/lineage.py` | — |

The repository has a genuinely strong engineering record: 7 ADRs, CI with 32 checks,
`docs/TRUTH_AUDIT.md` that self-classifies every metric as REAL/SYNTHETIC/DEMO, an honest
-failure DVC pipeline, and a real decision to retract an unreproducible RL result. That
culture is a genuine asset and should be preserved.

---

## 3. EVIDENCE INVENTORY — WHAT CAN AND CANNOT BE VERIFIED

### 3.1 Present and verifiable in the public repo

| Artifact | Verified content |
|---|---|
| `planner/data/real_cboms/` | **42 files, 277 assets, 277 unique hosts, 0 cross-CBOM overlap** — host-disjointness claim **CONFIRMED** |
| `planner/results/real_cbom_loo_42.json` + 2 shards | Full 42-fold per-fold metrics, 5 metrics each |
| `planner/results/{benchmark,benchmark_v3,benchmark_real_v3,rl_benchmark_real_cbom}.json` | Synthetic + real-CBOM benchmark records |
| `benchmarks/external/` | CryptoAPI-Bench source (203 cases) + 25 Apache jars + `HEAD-TO-HEAD.md` |
| `research/data/real/` | 5 liboqs timing traces (~10K samples each), 3 single-estate CBOMs |
| `qtrust_ai/artifacts/*.json` | 3 training/benchmark reports |
| Checkpoints | `planner/{model_gpu_v3,model_real_v3,model_ddp_v3,rl_agent}.pt`, `inspector/*.pt` |

### 3.2 Absent — required by the headline claims

| Missing file | What it blocks |
|---|---|
| `qtrust_ai/artifacts/real_datasets/code_corpus.json` | The 13,973/12,462-file discovery corpus. **The F1 0.9525 claim cannot be reproduced or even spot-checked.** |
| `qtrust_ai/artifacts/crypto_codebert/` | The fine-tuned transformer weights. `.gitignore:152-163` excludes them. Artifact records `saved_to: /home/nvidia/Project/...` — a machine-local absolute path. |
| `qtrust/data/gold/gold.json` | `scripts/train_factory.py --phase discovery` **crashes** (`FileNotFoundError`) as shipped. |
| `qtrust_data/{gold,silver,splits,bronze,annotations}/` | All empty (`.gitkeep` only). The RiskBench 10,000-pair set, the migration-outcome set, and the leakage-free host-disjoint splits live here. |
| `planner/data/estates_v1/` | The 500 synthetic estates. |
| `inspector/data/traces_v1/` | Canonical trace path (duplicates exist under `research/data/real/`). |
| `Q-Trust_Dataset_Collection/` | SolidiFI/SmartBugs/EIPs/WebAuthn sources. |

`SHA256SUMS.txt:5325` lists a checksum for `code_corpus.json` — a hash for a file that is
not in the repository. It is unverifiable.

---

## 4. VERIFIED FINDINGS — claims that reproduce exactly

`verify_qtrust_claims.py` reproduces these from committed artifacts with **zero mismatches**:

| Claim | Claimed | Recomputed | Verdict |
|---|---|---|---|
| CBOM corpus size | 277 assets / 277 hosts | 277 / 277 | ✅ |
| Cross-CBOM host overlap | 0 | **0** | ✅ |
| LOO `n_cboms` / `n_hosts` | 42 / 277 | 42 / 277 | ✅ |
| GNN Δ vs doctrine | −0.004242 | −0.004242 | ✅ |
| GNN vs random τ-b | +0.686681 | +0.686681 | ✅ |
| Discovery P / R / F1 / acc | .952 / .953 / .9525 / .9271 | 0.95202 / 0.95305 / 0.952535 / 0.927122 | ✅ |
| Discovery eval n | 2,415 | 2,415 | ✅ |

I reconstructed the discovery confusion matrix from the per-language breakdown:
TP=1766, FP=89, FN=87, TN=473. Every reported metric follows exactly under
`sklearn average="binary"` on the crypto class (`code_detector.py:1069`).

**So the arithmetic is honest. The problem is not arithmetic — it is construct validity.**

---

## 5. CRITICAL FINDINGS, RANKED BY SEVERITY

### F-1 ██ CRITICAL — The discovery "F1 0.9525" is largely self-referential

The corpus labels are generated by the same detector family being evaluated.

- `scripts/build_real_datasets.py:187` — Python files labeled via
  `det.scan_file(p)` → `_ensemble()`, i.e. **the function under test produces the label**.
- `scripts/expand_real_corpus.py:101` — **all** SolidiFI/SmartBugs/EIPs/WebAuthn files
  labeled via `det.scan_file`, all languages. Its own docstring states this as an invariant.
- `docs/TRUTH_AUDIT.md:7` attributes the "+0.11 F1" gain to *"expanded real blockchain code
  corpus"* — i.e. **the headline improvement is measured on data the detector labels itself.**

There is **no human annotation anywhere** in the discovery pipeline. `qtrust/labeling/`
contains weak-labelling and gold-builder code that no corpus builder ever calls.

> **Permitted phrasing:** "F1 0.9525 measures agreement between a multi-layer detector and
> a corpus labeled by a related deterministic scanner, with a fine-tuned CodeBERTa in the
> loop."
> **Prohibited phrasing:** any claim of ground-truth accuracy or of outperforming prior
> detectors on crypto-API discovery.

### F-2 ██ CRITICAL — The transformer cannot be credited; the ensemble is regex-dominant

`code_detector.py:688`:
```python
is_crypto = total_positive_weight >= cfg.threshold or bool(static)
```
A **single static-regex hit is decisive**. Weights are `static 0.30 / ast 0.30 /
dataflow 0.20 / ml 0.20` (`:331-334`), threshold `0.50`. Therefore:

- The ML layer can contribute at most **0.20** — it can never cross the 0.5 threshold alone.
- It can independently fire only via `:701`, requiring `ml_score ≥ 0.85` **and** no
  deterministic layer fired.
- `benchmark_comparison.json` has exactly **one** ablation (`rules-only`, F1 0.673). There is
  no AST-only, dataflow-only, or ML-only row. **The marginal contribution of CodeBERTa is
  never isolated anywhere in the project.**
- `_ml_layer` wraps the HF forward pass in `except Exception: pass` (`:639-640`) and silently
  reverts to a **SHA-256-hash + keyword-count** score (`:355-365`) — not a learned model.
- The "external head-to-head" explicitly ran **without HF weights**
  (`benchmarks/external/HEAD-TO-HEAD.md:4`), so CryptoAPI-Bench 0.877 / Apache F1 0.688 are
  rule-layer numbers.
- `compare.py:57-59` loads HF weights only `if Path(ft_dir).exists()`. That directory is
  absent, so **re-running the benchmark today silently measures the deterministic path**
  and will emit a different number with no warning.

> The paper cannot describe this as "a CodeBERTa discovery model". It must be described as
> a deterministic multi-layer detector with optional transformer augmentation — and must
> then either ablate the transformer or drop it from the contribution claims.

### F-3 ██ CRITICAL — The headline GNN metric is SYNTHETIC but presented as the flagship

- `README.md:101` hero badge: **"τ 0.975 GNN ranking accuracy"**. Same on the showcase site
  (`showcase/index.html:179, 212`), `docs/index.md:15`, `docs-v2/index.md:36`.
- Provenance: `planner/results/benchmark_v3.json`, trained on **100K synthetic graphs**.
- `docs/TRUTH_AUDIT.md:8` explicitly labels it **"SYNTHETIC L1 — do not claim enterprise"**.
- `docs/8GPU_PLAN.md:57` records the deeper problem: *"the label rule itself scores τ 0.9999,
  so imitation cannot beat it."* The synthetic task is **imitation of a deterministic label
  function**; τ 0.975 measures imitation fidelity, not planning quality.

This is a direct violation of the project's own truth-audit policy in its most public
surface. It must be removed or relabelled before any submission.

### F-4 ██ CRITICAL — The "honest tie" is an artifact of tie density, and the paper's interpretation is contradicted by the same artifact

`paper/main.tex:19-22` states: *"Two independent methods converging to the heuristic is
evidence the doctrine is near-optimal on today's estates — not evidence of model failure."*

The artifact contains **five** metrics. The paper reports one:

| Metric | Model | Heuristic | Δ | W/T/L |
|---|---|---|---|---|
| `kendall` | 0.7168 | 0.7210 | −0.0042 | 0 / **41** / 1 |
| `node_rank` | **0.3136** | 1.0000 | −0.6864 | 0 / 1 / **41** |
| `exact_rank` | **0.0238** | 1.0000 | −0.9762 | 0 / 1 / **41** |
| `top5` | 0.5000 | 1.0000 | −0.5000 | 0 / 21 / 21 |
| `top10` | 1.0000 | 1.0000 | +0.0000 | 0 / 42 / 0 |

**On `exact_rank` and `node_rank` the GNN loses 41 of 42 folds and reproduces the doctrine
ordering on exactly 1 fold (2.4%).** The GNN did *not* converge to the heuristic. The τ-b
tie is produced by massive tie density:

- 49.3% of all asset pairs share an identical algorithm label → only **407 usable pairs**
  across the whole corpus.
- SE(τ-b) ≈ √((1−τ²)/n_eff) ≈ **0.034**. Reported Δ = −0.0042 → **|Δ|/SE ≈ 0.12**.
  The comparison has essentially **no statistical power**. 95% CI ≈ [−0.072, +0.063].
- 71% of CBOMs contain ≤2 distinct algorithm groups, so the whole "ranking problem"
  collapses to a single binary decision.
- A simulation of an **untrained random ranker** against the doctrine heuristic over these
  42 CBOMs produces approximately **0 W / 38 T / 2 L** — statistically indistinguishable
  from the reported 0 W / 41 T / 1 L. *(Illustrative, not a formal test; the power
  analysis above is the rigorous part.)*

> The defensible claim is the opposite of the one currently drafted: **this experiment
> cannot distinguish the GNN from a heuristic, a random ranker, or itself.** That is a
> legitimate and publishable finding about the *evaluation instrument*, and it directly
> motivates the blinded-expert-label work the project already lists as pending.

### F-5 ██ CRITICAL — The "doctrine heuristic" baseline is circular

The heuristic scores **1.0 on 42/42 folds** for `node_rank`, `exact_rank` and `top5`. This
is expected and unavoidable: per `docs/8GPU_PLAN.md:57` the training labels are *generated
by that same rule*. Comparing a learned model to its own label generator and reporting the
near-match as evidence about "real estates" is circular. A non-circular baseline requires
independent expert preference labels — which the project correctly states do not exist yet.

### F-6 █ HIGH — Real CBOMs contain no graph topology

I parsed all 42 real CBOMs: **0 edges, 0 links, 0 dependencies.** A GNN's message passing
therefore operates over **synthesized** topology. `docs/TRUTH_AUDIT.md:13` already concedes
this ("Graph edges | SYNTHETIC DEMO linear chain"). On real data the GNN sees node features
only. The paper must not describe the real-data evaluation as a graph-learning result.

### F-7 █ HIGH — Severe zero-variance in the "real enterprise" corpus (all 277 assets)

| Field | Distinct values | Verdict |
|---|---|---|
| `criticality` | **1** (`"medium"`, 277/277) | **No variance** |
| `vendor` | **1** (null, 277/277) | **No information** |
| `first_seen` | **1** (null, 277/277) | **No information** |
| `asset_type` | 1 (`tls_certificate`) | No variance |
| `expired` | 2 (276 False, 1 null) | ~No variance |
| `algorithm` | 5 (+1 null): RSA-2048 63.2%, ECDSA-P256 32.1%, RSA-4096 3.6%, rest ~0.4% | Heavily concentrated |
| distinct risk tuples corpus-wide | **6** | Treated as "enterprise estates" |

`criticality: medium` everywhere is the **exact defect** `TRUTH_AUDIT.md:14` says destroyed
the original RL reward signal. It is **still present in the shipped 42-CBOM corpus**.

Also: every file carries `target: "acme-<industry>.example"`. These are **synthetic groupings
of real public-website TLS certificates**, labelled with placeholder example domains. The
phrase "42 host-disjoint **enterprise** CBOMs" overstates what exists; "42 host-disjoint TLS
certificate groups" is accurate.

### F-8 █ HIGH — The discovery headline is +0.084 over a trivial baseline, and the eval set is not polyglot

- Majority-class ("always predict crypto") baseline = **F1 0.8683**. Q-Trust = 0.9525.
  **Margin: +0.0842 absolute.** `benchmark_comparison.json` itself records
  `best_baseline: "majority (always crypto)"`.
- Eval set is **69.9% C** (1,688 / 2,415), 92.4% of which is positive. The headline is
  essentially a C-language measurement.
- **Java: 0 TP / 95 files → 0% recall**, while emitting 11 false positives — the labeler
  called all 95 Java files non-crypto and the detector fired on 11.
- **Python recall 0.480** — *below* the majority baseline's recall.
- Rust n=2, JavaScript n=1. `typescript`, `csharp`, `kotlin`, `php` never appear.
  Macro-precision ≈ **0.674**, macro-recall ≈ **0.743** — versus 0.673 for rules-only.
- Label imbalance is itself a label-noise signal: two *different* labelers
  (`STATIC_PATTERNS` + AST for Python vs. a crude `_RULES` regex set for everything else,
  `build_real_datasets.py:217-227`) with non-overlapping vocabularies.

### F-9 █ HIGH — An undisclosed robustness result contradicts the discovery claim

`benchmark_comparison.json:41-61` reports, and `paper/main.tex` **never mentions**:

> Adversarial holdout, n=132: **P 0.80 / R 0.40 / F1 0.5333**

Back-solving from the generator (`qtrust_ai/benchmark/adversarial.py:182-186`, where only
1 of 11 categories sets `is_crypto=False`):

- ≈120 positives / 12 negatives → TP≈48, FN≈72, **FP≈12 of 12 → specificity 0.000**.
- The detector flags **every single non-crypto trap** as crypto and misses **60%** of the
  crypto cases.

Two further caveats: those cases are **synthetic** (11 fixed categories × 6 algorithms × 3
hardcoded one-line snippets, transformed by string replacement), and they are *short
snippets* whereas the main task is *file-level* — a different task. So this number is not
directly comparable either. But omitting it while claiming robustness is not defensible.

### F-10 █ MEDIUM — The "top-10 = 1.0 on every fold" claim is vacuous

Max assets per fold = **7**. A top-10 metric over ≤7-node graphs is 1.0 for **any** ranker.
I confirmed `random.top10 == 1.0` on **42/42 folds**. `paper/main.tex:53` and
`README.md:360` present this as a positive finding. It carries zero information.

### F-11 █ MEDIUM — Two folds report a mathematically undefined τ-b as a perfect 1.0

`real_gov_edu_7.json` (n=2) and `real_media_1.json` (n=4) contain a single algorithm class,
so the τ-b denominator √(n₀n₁) = 0 (0/0). Both are recorded as `kendall: 1.0` for model
*and* heuristic and counted as "ties".

I tested whether this matters: excluding both moves the aggregate from 0.7168/0.7210
(Δ −0.0042) to 0.7026/0.7071 (Δ −0.0045). **It does not materially change the headline.**
I report this because I expected it to and it did not — it is a reporting-hygiene defect,
not a validity threat.

### F-12 █ MEDIUM — `docs/TRUTH_AUDIT.md` contains a false statement about its own artifact

Line 7: *"epoch count **not recorded in the shipped artifact**; script default
`--hf-epochs 2`"*. This is **incorrect** — `training_report_real.json:69` records
`"epochs": 4`, and `docs/AUDIT_REMEDIATION.md:132` records the exact command
`python scripts/train_qtrust_all.py --real --hf-epochs 4`. A self-audit document that
misdescribes its own evidence is a reviewer red flag.

---

## 6. CONTRADICTION REGISTER (documentation ↔ artifact)

The repo documents **four different corpus sizes** and **three different GNN real-data results**.

| Quantity | Values found | Sources |
|---|---|---|
| Code corpus size | **13,973** / **12,462** / **4,431** | `training_report_real.json:7`, `README.md:363`, `TRUTH_AUDIT.md:7` / `DATASETS.md:29` / `qtrust_ai/README.md:73` |
| Code corpus repos | **38** / **34** | `TRUTH_AUDIT.md:7` / `paper/main.tex:44` |
| GNN real-data τ-b | **0.7168** (42-fold) / **0.7263** (40-fold) / **0.796** / **0.807** (in-sample) | `real_cbom_loo_42.json` / `real_cbom_loo_40.json` / `STRATEGIC_ANALYSIS.md:17` / `benchmark_real_v3.json` |
| LOO corpus | **42 CBOMs/277 hosts** / **40 CBOMs/280 hosts** | `real_cbom_loo_42.json` / `real_cbom_loo_40.json` — both rows appear live in `README.md:359-360` |
| Contract tests | **211** / **213** | `README.md:101,365` / `docs/_data/metrics.json`, `PROJECT_SCORECARD.md:16` |
| ACVP vectors | RSA-SigVer **126** / **270**; SHA2-256 **516** / **517** | `README.md:369` / `EXPERIMENTS.md:55` |
| TLS hosts | **277** / **283** scanned, 275 succeeded / **56** eval | `training_report_real.json:7` / `DATASETS.md:30` / `qtrust_ai/README.md:60` |
| NVD CVEs | **401** / **407** (398 unique) | `README.md:363` / `DATASETS.md:33` |
| Mean relative gain | **1.5537** / **8.98×** | `benchmark_comparison.json:161` / `qtrust_ai/README.md:70` |
| Discovery F1 | **0.9525** / **0.841** / **0.97** | artifact / `README_FACTORY.md:46` / `qtrust_ai/README.md:70` |

`README.md` currently carries **both** the 40-fold and 42-fold GNN rows with different
numbers and no deprecation notice. A reviewer will read this as unreconciled reporting.

---

## 7. CITATION INTEGRITY

**Verified accurate:**
- NIST **IR 8547** exists — `csrc.nist.gov/pubs/ir/8547/ipd`, DOI `10.6028/NIST.IR.8547.ipd`,
  published 2024-11-12. ✓
- FIPS 203 / 204 / 205 Final, 2024-08-13. ✓
- `huggingface/CodeBERTa-small-v1` exists; 6-layer, 84M params, RoBERTa-style, CodeSearchNet. ✓
- PyPI `qtrust-inspector` v2.2.0 and `qtrust-sdk` v2.2.0 both real. ✓
- HF Space `KRISHNAPURI/q-trust-scanner` public. ✓
- GitHub Pages docs site live. ✓

**Defects requiring correction:**

1. **IR 8547 is still an Initial Public Draft.** The CSRC publication table (page updated
   2026-08-05) lists it as **"Draft, 11/12/2024"**; no final version exists. The paper must
   cite it as *ipd* and describe it as directional guidance, not a binding standard.
2. **The README badge misstates the standard.** It reads *"NIST IR 8547 — RSA/ECC signatures
   disallowed after 2030–2035"*. Per the draft's Table 4/§4.1: **deprecated after 2030**,
   **disallowed after 2035** — and the two are different regulatory actions (deprecated =
   still permitted; disallowed = must cease). The badge merges two distinct regimes.
   `paper/main.tex:10` repeats "disallowance for 2030–2035".
3. **The reference list is thin.** `paper/main.tex:84-90` has 5 entries, several without
   authors, year, or DOI — e.g. `\bibitem{cryptobench} CryptoAPI-Bench; ApacheCryptoAPI-Bench
   corpora.` and `\bibitem{codeberta} HuggingFace CodeBERTa-small-v1.` Neither is a
   citable publication as written. A reviewer will reject on this alone.

**Opportunity (strengthens the paper):** the regulatory driver is now *stronger* than the
repo claims. Executive Order 14412 (June 2026) and OMB M-26-15 (June 2026) align federal
PQC migration plans to the IR 8547 timeline, effectively elevating the proposed 2030 date
to compliance status for High Value Assets — even though the IR itself is still a draft.
That is a better and more defensible motivation than the current badge, and it is verifiable.

---

## 8. WHAT THE PROJECT CAN ACTUALLY SUPPORT

Stated plainly, with no inflation:

| Claim | Verdict |
|---|---|
| "We built an end-to-end open PQC migration & attestation system" | **Strongly supported.** Genuine, substantial, well-engineered. |
| "Our scanner emits CycloneDX CBOMs and scores against NIST/CNSA/FIPS" | **Supported**, but deterministic rules — must be described as such. |
| "Attestations anchor on Base L2 with EIP-712, timelock, 11 UUPS registries" | **Supported** by source + Forge tests; **no external audit** (`TRUTH_AUDIT.md:17`). |
| "A fine-tuned CodeBERTa achieves F1 0.9525 on real code" | **NOT supportable as written.** Circular labels (F-1), regex-dominant (F-2), corpus+weights absent (F-3.2), +0.084 over majority on a 70%-C eval set (F-8). |
| "A GNN reproduces migration doctrine on real estates" | **NOT supportable as written.** Circular baseline (F-5), underpowered (F-4), no graph edges (F-6), degenerate features (F-7). |
| "We publish an honest negative result" | **This is the strongest asset in the project** — but the result must be re-derived correctly (F-4). |

### The most defensible research contribution

Not "we built a tool." Not "our GNN beats a heuristic." The defensible contribution is:

> **A measurement study of why PQC migration-ordering models cannot currently be
> validated.** We release a leakage-audited real-TLS corpus (277 hosts, 0 cross-group
> overlap, independently verified), a full open evaluation harness, and a rigorous
> quantification of the statistical resolution of the standard evaluation protocol —
> showing that with 407 usable discordant pairs (SE ≈ 0.034) a published Δ = −0.004 cannot
> be distinguished from zero, and that the dominant community baseline is circular.
> We further show the headline synthetic metric (τ = 0.975) measures imitation of a label
> function that itself scores τ = 0.9999.

That framing is honest, is supported by evidence I verified independently, is genuinely
useful to the field, and converts the project's two biggest weaknesses into its
contribution. It also needs no unavailable data to state.

---

## 9. BLOCKING QUESTIONS FOR THE AUTHOR

I need these before Stage 3 (literature) can be scoped correctly and before any Results
section is drafted.

**Tier 1 — blocking (cannot proceed without):**

1. **Make the two `KRISHNAPURI` repositories public**, or confirm they are gone. If gone,
   the discovery corpus and fine-tuned checkpoint are unrecoverable and the CodeBERTa
   contribution must be dropped entirely from the paper.
2. **Ship `qtrust_ai/artifacts/crypto_codebert/`** (or confirm you cannot). Without weights
   the discovery result is unreproducible.
3. **Confirm the intended venue class.** This project reads as applied-security/systems
   (IEEE S&P, ACSAC, USENIX Security, RAID, ICISS, IMWUT/SEC) rather than an ML venue.
   The framing changes completely, and so does which experiments matter.
4. **Do you have access to real dependency/SBOM graph edges for any of the 277 hosts?** F-6
   is the deepest structural limitation. Any real edge source (Syft/Grype output, import
   graphs, CPE dependency data) would materially strengthen the GNN leg.

**Tier 2 — needed for a complete experimental plan:**

5. Per-label predictions (`y_true`, `y_pred`, 2,415 rows) and the **per-repo split manifest**
   (which 30 repos train / which 8 eval). Without these the circularity exposure of the
   discovery result cannot be quantified.
6. A **human-labelled ground truth** for even 200–300 files, to break the F-1 circularity.
   This is the single highest-value experiment available and it is cheap.
7. GPU availability and time budget. Essential experiments need 1×A100 for ≈8–12 GPU-hours.
   The 42-fold LOO took 2×A100.
8. Confirm whether `RiskBench` blinded expert annotation is still aspirational. If any
   expert labels exist at all, they replace the circular baseline (F-5) and become the
   paper's anchor.

**Tier 3 — housekeeping (blocks submission, not research):**

9. Reconcile the contradiction register (§6). Pick one corpus size, one LOO protocol,
   one contract-test count. Superseded numbers should be removed, not left side by side.
10. Correct the IR 8547 badge (§7.2) and the false `TRUTH_AUDIT.md:7` statement (F-12).
11. Remove or relabel the synthetic τ 0.975 hero badge (F-3).
12. Build complete citations for CryptoAPI-Bench and CodeBERTa.

---

## 10. STAGE GATE

**Stage 1 complete.** Verified findings: 7 headline claims reproduce exactly; 12 defects
identified (3 critical, 5 high, 4 medium); 3 missing/inaccessible resources; 11 unresolved
contradictions.

**Not yet verified** (two deeper audits still running, to be delivered as Stage 1B):
contracts/Foundry test artifacts, CI status, ACVP oracle results, the side-channel
54-trace-set result file, and notebook execution state.

**Not attempted** (Stages 2–10): evidence ledger, literature review, research questions,
experiment plan, manuscript, peer review, submission package.

> **Recommendation:** do not begin the manuscript yet. The honest framing in §8 is strong
> and buildable, but three of its load-bearing claims need either data access (§9 Tier 1)
> or re-derivation. Writing now would produce a paper whose Results section cannot be
> supported — which is precisely the failure mode this audit exists to prevent.