# DELIVERABLE A (continued) — STAGE 1B
## Scanner / Contracts / Attestation / CI Audit
**Audit date:** 2026-10-14 · Complements `DELIVERABLE_A_TECHNICAL_AUDIT.md`

Findings below are independent of Stage 1 and add **18 further documentation defects**.
Several are more serious than anything in Stage 1, because they concern the parts of the
system that are otherwise the project's strongest assets.

---

## 1. THE HEADLINE ARCHITECTURE CLAIMS ARE OVERSTATED

### 1.1 "11 UUPS registries" → actually 10

`grep '^contract'` over `contracts/src/` (13 `.sol` files):

- 10 registries inherit `UUPSUpgradeable, IPausable`: `AssetRegistry.sol:17`,
  `AuditRegistry.sol:18`, `ComplianceAttestation.sol:18`, `EvidenceRegistry.sol:19`,
  `MigrationRegistry.sol:17`, `PolicyCommitment.sol:17`, `RevocationAnchor.sol:18`,
  `SchemaRegistry.sol:17`, `TrustAnchorRegistry.sol:17`, `VendorRegistry.sol:16`
- **`QTrustGovernance.sol:22` is `contract QTrustGovernance is AccessControl`** — a
  timelock-governance wrapper, **not UUPS**.

> Correct phrasing: **"10 UUPS registries + 1 timelock-governance contract."**
> Claimed in `README.md:101,280,334,509`, `docs-v2/index.md:11,42`.

### 1.2 "10 scanner modules" → table has 8, one is unimplemented

The README's own "Scanner modules — full matrix" (`README.md:236-246`) lists **eight** rows.
Of those, the **"Config scanner" (YAML/TOML/JSON, "Cipher suites, crypto settings") does not
exist** — `scan_directory()` (`scanner.py:682-699`) only calls `scan_pem_files()` and
`scan_ssh_directory()`. Meanwhile two genuinely substantial real modules are **not listed**:

- `ast_scanner.py` (40.5 KB) — real AST/structural detection
- `parallel_scanner.py` — asyncio fan-out over 1,000+ hosts

**Detection method — verified:** `ast_scanner.py:139-145` declares
`python → stdlib-ast`, `javascript/typescript → tree-sitter-js or regex-fallback`, and
**`go, java, rust, c, cpp, csharp, ruby, php, swift, kotlin → regex-fallback`.**

> Only Python gets real AST parsing. JS/TS get tree-sitter *if installed*. Ten languages
> are pure regex. "12+ source languages" is true in the sense that strings are matched in
> 12 languages — not that 12 languages are semantically analyzed.

### 1.3 "54 real liboqs timing trace sets" → 5 exist

- **5** trace files on disk: `traces_{MLDSA44_sign,MLDSA44_verify,MLKEM512_encaps,
  MLKEM512_decaps,MLKEM768_decaps}.txt`, 10,000 samples each.
- **No RSA/ECC baseline trace set exists**, despite `README.md:367` claiming
  "(PQC + **RSA/ECC baselines**)" and naming the 3 misses as FALCON-1024/512 and SLH-DSA-256s
  keygen. **Those inputs are not in the repository.**
- `README.md:363` says "54"; `README.md:376-377`, eight lines later, says "**5**". The same
  document contradicts itself.
- `docs/TRUTH_AUDIT.md:16` **still says "REAL (5/5 class-accurate)"** — the truth audit was
  never updated for experiment E-07.

---

## 2. NO EVALUATION RESULT ARTIFACTS EXIST FOR THE ENGINEERING CLAIMS

Exhaustive filesystem and content scan:

| Claim | Result artifact | Status |
|---|---|---|
| 211 / 213 contract tests | none | **No `out/`, no `coverage/`, no `.gas-snapshot`, no `lcov.info`, no logs anywhere** |
| 54/54 clean, 51/54 leak-injected | none | **No side-channel JSON exists in the entire repository** |
| Inspector benchmark P/R | none | `inspector/benchmarks/score.py:130-141` prints to stdout and **never writes JSON** |

**Only 2 evaluation results are committed in the whole repo**, both in `benchmarks/external/`
— and I independently recomputed both and they are exact (§4).

**Contract test count: three different numbers, none matching reality.** I counted
**219 entrypoints** (212 `test*` + 3 `invariant_*` + 4 `check_*`) across 23 `.sol` test files.
`README.md` says 211, `CHANGELOG.md:963` says 211, `PROJECT_SCORECARD.md:16` says 213.

**And the contracts cannot be built from a fresh clone:** `.gitmodules` declares
`contracts/lib/forge-std` and `contracts/lib/openzeppelin-contracts`; both directories
contain **0 files**. `foundry.lock` pins `forge-std v1.16.2` / `openzeppelin-contracts v5.7.0`.
Without `git submodule update --init`, `forge build` fails. (CI passes `submodules: recursive`
at `ci.yml:18`, so CI is green — but no external reviewer can reproduce it.)

---

## 3. THREE DIVERGENT RISK ENGINES — AND THE README RECOMMENDS THE WRONG ONE

| Location | Scale | Notes |
|---|---|---|
| `inspector/qtrust_inspector/risk_engine.py:308` | 0–100 | Canonical |
| `backend/src/routes/scanner.ts:111-218` | 0–100 | Line-for-line TS port; unified because "RSA-2048 scored 74 vs 90 before unification" |
| **`sdk/qtrust/risk.py:159-184`** | **0–10** | **Still divergent** |

`sdk/qtrust/risk.py` marks `SHA-256` as `WEAKENED` (`:85`) and `Ed25519` as `WEAKENED`
(`:74-75`), contradicting `risk_engine.py:58` (`SHA-256: SAFE`) and `:42`
(`Ed25519: BROKEN`). Its formula is `overall = vuln_weight * 7.0 + hndl_exposure * 3.0` (`:170`).

**`README.md:489,497-499` tells users to use this SDK engine.** So a user following the
documentation receives risk scores from the engine that disagrees with the canonical one on
whether SHA-256 and Ed25519 are quantum-broken or merely weakened.

> This is a correctness defect in a security product, independent of any paper. It should be
> fixed regardless of publication plans.

**Also:** two CycloneDX 1.7 writers with different component shapes
(`inspector/qtrust_inspector/cyclonedx.py:102` emits `cryptoProperties`;
`sdk/qtrust/cbom_models.py:38` emits snake_case `crypto_properties` and is **not conformant**),
plus a third `cbom.v1` schema. And four different version strings across the repo
(`pyproject 2.2.0`, `__init__ 1.1.0`, CBOM tool `0.1.0`, sample CBOMs `1.1.0`/`0.1.0`).

---

## 4. WHAT IS GENUINELY STRONG — independently verified

I recomputed the only committed raw evaluation records and they reproduce **exactly**:

| Claim | Claimed | My recomputation from raw records | ✓ |
|---|---|---|---|
| CryptoAPI-Bench usage recall | 164/187 = 0.877 | 187 misuse records, 164 flagged → **0.8767** | ✓ |
| Flag rate on secure files | 12/16 = 0.750 | 16 secure, 12 flagged | ✓ |
| File-level misuse precision | 164/176 = 0.932 | **0.9318** | ✓ |
| Apache recall | 33/34 = 0.971 | TP 33, FN 1 | ✓ |
| Apache file-level P / F1 | 0.532 / 0.688 | **0.5323 / 0.6880** | ✓ |

The framing is genuinely honest: *"this tool detects crypto **usage**, not misuse"* and
an explicit refusal to claim superiority over CryptoGuard/CogniCrypt/GPT-4. **This is the
best-evidenced claim in the entire repository** and the only one with per-case raw data.

Other verified strengths:

- **Fail-closed risk defaults.** `risk_engine.py:199-208` treats an unidentifiable algorithm
  as `BROKEN` *"until proven otherwise (audit Critical #8)"*. Correct security posture.
- **Genuine SSRF/target hardening.** `validate_scan_target()` / `validate_scan_cidr()`
  (`scanner.py:46-93`) block private, link-local, loopback and `169.254.169.254` targets;
  SSH packet reads are length-bounded; `MAX_CIDR_HOSTS = 4096`.
- **Correct EIP-712 gasless relay.** Per-chain domain-separator caching (`AssetRegistry.sol:113-136`),
  nonce replay guard (`:174-178`), `REGISTRAR_ROLE` requirement on the recovered signer (`:173`),
  `nonReentrant` + `whenNotPaused`.
- **Sound timelock escalation guards.** `QTrustGovernance.sol:166-175` blocks
  `grantRole`/`revokeRole`/`renounceRole` **and both `upgradeTo` selectors** in the generic
  schedule path; `Deploy.s.sol:64` strips every deployer role and reverts if any admin remains.
- **Evidence ledger v2** genuinely closes the chain-linkage gap (`evidence.py:53-110`).
- **244 inspector tests** across 13 files, including a purpose-built CycloneDX conformance suite.
- **ACVP corpus placed**: 34 algorithm families, 170 JSON files, 223 MB of NIST test vectors.
- **Honest documentation culture** — `docs/CBOM_CONFORMANCE.md` voluntarily lists 6 spec
  deviations and 6 omission gaps; `EXPERIMENTS.md` records a retracted unreproducible result.

---

## 5. THE REPOSITORY IS NOT REPRODUCIBLE FROM A FRESH CLONE

This is the most consequential finding for venue selection.

| Missing | Consequence |
|---|---|
| `qtrust_ai/artifacts/real_datasets/` (corpus, TLS inventory) | Discovery F1 and notebook inventory cannot be re-derived |
| `qtrust_ai/artifacts/crypto_codebert/` (weights, `.gitignore:152-163`) | Discovery model cannot be re-run |
| `KRISHNAPURI/q-trust-datasets` (HTTP 404) | RiskBench, migration outcomes, temporal sets, host-disjoint splits |
| `contracts/lib/*` submodules (empty) | `forge build` fails |
| `/tmp/real_data` (side-channel input) | 54-set evaluation unreproducible |
| `qtrust_data/`, `qtrust_bench/datasets/` (`.gitkeep` only) | Bronze/silver/gold pipeline is an empty scaffold |
| Side-channel, contract, inspector result artifacts | All engineering claims are prose-only |

> `paper/main.tex:82` claims *"Code, data manifests, and the 60-second reproduction path are
> public."* **This is not currently true.** No path reproduces the paper's numbers from a
> fresh clone. This claim must be removed or made true before submission.

---

## 6. THE ONE EXECUTED NOTEBOOK CONTRADICTS TWO HEADLINE NUMBERS

`research/notebooks/03_train_and_benchmark_real.ipynb` **is** genuinely executed (8/8 code
cells carry real stdout, A100-SXM4-80GB, `torch 2.13.0+cu130`, `transformers 5.15.1`). But it
runs in smoke mode — cell 2 prints `FULL = False` — and therefore:

- Sets **`N_HF = 0`**, skipping the CodeBERTa fine-tune entirely
- Reports **discovery F1 `0.71`** (accuracy 0.649, R 0.56) — not the headline 0.9525
- Reports **LOO τ-b `0.6546`** vs heuristic `0.6546` — not the headline 0.7168
- Uses the **old 40-CBOM / 280-asset** corpus, not the 42-CBOM / 277-host one
- Shows **5** trace sets, not 54
- Its RL cell **does** reproduce the headline (140.343 ± 8.126 vs 140.622 vs 136.838) ✓

**Why this matters:** the committed notebook is the closest thing to an end-to-end
reproduction a reviewer has, and it shows the deterministic path — the path a user gets by
default, since the fine-tuned weights are not shipped — producing materially weaker numbers.
This corroborates Stage 1 finding F-2 from an entirely independent direction.

Two notebooks have **zero** executed outputs: `08_bank_pilot.ipynb` (0/7 code cells) and
`showcase/qtrust_quickstart.ipynb` (0/5).

---

## 7. CI GAPS

- **Frontend unit tests are never run.** 17 vitest files / ~143 tests exist and
  `frontend/package.json:10` defines `"test": "vitest run"`, but the `frontend` CI job
  (`ci.yml:146-163`) runs only `npm ci`, `npm run build`, `npm audit` — **no `npm test`**.
  The `backend` job by contrast does run its tests (`ci.yml:141`).
- **`qtrust_ai` CI installs no ML stack.** `ci.yml:289` installs only
  `numpy scipy scikit-learn pytest` — no `torch`, no `transformers`. The one test file in
  `qtrust_ai/tests/` therefore exercises only deterministic code.
- CI triggers only on `main` (`ci.yml:3-7`). `golive-preflight` is tag-gated only (`:351`).
- Otherwise CI is genuinely strong: 13 jobs including `forge coverage --ir-minimum`,
  Halmos symbolic verification, an **ABI-drift gate** (`git diff --exit-code`), a **planner
  promotion gate** (v3 τ must beat v2 τ), Slither, pip-audit, npm-audit, CodeQL-style
  security scanning, and OpenSSF Scorecard.

---

## 8. UPDATED VERDICT

Combining Stage 1 and Stage 1B, the project's evidence profile is:

| Area | Evidence quality | Publishable? |
|---|---|---|
| External head-to-head (`benchmarks/external/`) | **Raw per-case records, recomputable, honestly framed** | **Yes** — strongest asset |
| Scanner / CBOM / risk engine design | Source + 244 tests + conformance suite | **Yes**, as a system contribution |
| EIP-712 attestation + timelock | Source + 23 test files, no result artifacts, no external audit, submodules empty | Yes with caveat |
| CBOM conformance | Documented deviations honestly disclosed | Yes |
| Discovery F1 0.9525 | Circular labels, regex-dominant, +0.084 over majority, corpus & weights absent | **No** |
| GNN τ-b tie | Circular baseline, underpowered, no real edges, degenerate features | **No** — but reframeable |
| Side-channel 54/51 | Prose only, 5 traces on disk, synthetic leak injection | **No** |
| Contract test counts | Three numbers, none matching 219, no artifact | **No** |

### The strongest defensible paper is now clearer than at Stage 1

Not "we built a PQC migration tool." It is:

> **An evidence-infrastructure paper.** We release the artifacts that the PQC migration
> literature currently lacks — a leakage-audited real-TLS corpus (independently verified:
> 277 hosts, 0 cross-group overlap), a public CBOM schema, a reproducible evaluation harness,
> and a candid account of *why* published PQC-ordering and crypto-discovery results are hard
> to verify: circular labels, circular baselines, tie-saturated metrics that cannot separate
> methods (n_eff = 407, SE ≈ 0.034, |Δ|/SE ≈ 0.12), and evaluation protocols whose resolution
> is unstated. We show, with recomputation from committed raw records, which claims survive
> audit and which do not.

This framing uses the project's real strength (transparency, committed raw records, honest
negative results), requires **no unavailable data to state**, and directly serves the venue
classes where artifact evaluation is mandatory.

---

## 9. STILL PENDING

The planner/GNN internals audit (architecture, LOO script, RL algorithm, checkpoints) is
still running and will be delivered as **Stage 1C**. My own independent analysis of
`planner/results/real_cbom_loo_42.json` and the 42-CBOM corpus already covers the metric-level
findings (F-4, F-5, F-6, F-7, F-10, F-11); Stage 1C will add the code-level detail.