# DELIVERABLE A (continued) — STAGE 1C
## GNN / Planner / RL Internals — and the finding that invalidates the headline
**Audit date:** 2026-10-14 · Complements Stages 1 and 1B

---

## 1. ██ CRITICAL — THE 42-FOLD LOO IS NOT OUT-OF-SAMPLE

This was not in my Stage 1 analysis. It was surfaced by the code audit and I have now
**independently verified it** by reading the checkpoint metadata directly.

`scripts/eval_real_cbom_loo.py:79`:
```python
BASE_MODEL = planner/model_gpu_v3.pt      # initialises EVERY fold (:157)
```

Checkpoint metadata (read by unpickling the archive; reproducible via
`verify_ckpt_leak.py`):

```
epochs              = 173
n_graphs            = 100000
n_real_graphs       = 40          <-- fine-tuned on 40 REAL CBOM graphs
best_val_kendall    = 0.9728872535490785
norm                = layer
model_config        = {input_features:6, hidden_dim:256, embedding_dim:128,
                       heads:8, dropout:0.15, variant:"hybrid", norm:"layer"}
```

The 42-CBOM corpus now on disk and the 40-CBOM corpus used to build that checkpoint
**share 40 of 42 files** (the two extra are `real_finance_3.json` and `real_gov_edu_7.json`).

> **Therefore: 40 of 42 "held-out" folds were already in the base model's training set
> before the leave-one-out fine-tune began.** The protocol is documented and named
> *"leave-one-out (host-disjoint CBOMs, real TLS scan)"* and reported as the project's
> flagship out-of-sample result. It is not out-of-sample.

Nothing in the code records or checks this. No artifact contains the overlap count.
`docs/TRUTH_AUDIT.md:9` asserts *"REAL (out-of-sample, 40-fold COMPLETE)"*.

**This invalidates the headline.** `paper/main.tex`'s "honest tie" — the abstract's central
result — is an **in-sample** measurement presented as out-of-sample. It cannot be repaired
by re-analysis; the experiment must be re-run from a checkpoint that has never seen any of
the 42 CBOMs.

For reference, the sibling checkpoint `model_real_v3.pt` records `n_real_graphs = 39` and is
the one `planner/server.py:448` resolves **first** — so its real-CBOM score (τ-b 0.807 in
`benchmark_real_v3.json`) is likewise in-sample, which `eval_real_cbom_loo.py:6-8` itself
concedes.

---

## 2. ██ CRITICAL — THE "BASELINE" IS THE LABEL FUNCTION

`heuristic_order()` (`planner/qtrust_planner/benchmark.py:47-68`) and `_assign_labels()`
(`planner/qtrust_planner/data_generator.py:104-115`) are **the same formula**:

```python
priority  = criticality * 2.0
priority += 1.5              if vendor_pqc_ready
priority += log1p(key_size)/4.0   if not is_pqc(alg)
priority -= 1.0              if     is_pqc(alg)
priority += deadline_pressure * criticality / 5.0
priority -= in_degree * 0.3
order = argsort(-priority)
```

This is why the "baseline" scores `exact_rank = 1.0` and `node_rank = 1.0` on **42/42 folds**.
It is not a competitor; it is the oracle. The project already knows this —
`scripts/build_campaign_notebook.py:234`: *"neither beats the doctrine, because the doctrine
is the label."* Yet `real_cbom_loo_42.json` reports `model_vs_heuristic_tau_b` as a comparison.

> Note the second consequence: **the model has a mathematical ceiling of τ-b = 1.0 at best**,
> and is being scored against a rule it was trained to imitate from synthetic graphs generated
> by that same rule. A negative Δ is the *expected* result and carries no information.

---

## 3. ██ CRITICAL — THE 42 GRAPHS HAVE ZERO EDGES: A GNN RUNS NO MESSAGE PASSING

`cbom_to_dependency_graph()` (`data_generator.py:211-230`) uses `depends_on` if any asset has
one, else a **host-affinity fallback**:
```python
anchor = first_index_by_host.setdefault(host, i)
if anchor != i:
    edge(anchor, i)
```
Every asset in every CBOM is a **distinct host** (277/277, verified), so `anchor == i` always
and **`edge_index = torch.zeros((2, 0))` for all 42 graphs**.

> **The flagship "GNN" real-data benchmark evaluates a per-node MLP.** `GCNConv`/`GATv2Conv`
> degenerate to linear layers when `edge_index` is empty. No message passing occurs. The
> "graph neural network for migration planning" performs no graph reasoning on real data.

This also explains Stage 1 finding F-6 from the code side, and it is worse than I first
described: it is not that topology is "synthesized", it is that there is **no** topology.

---

## 4. ARCHITECTURE AS ACTUALLY BUILT (verified)

### `MigrationGNNv3` — `planner/qtrust_planner/model_v3.py:177`

| Layer | Module | Line |
|---|---|---|
| Input norm | `LayerNorm(6)` | 217 |
| conv1 | `GCNConv(6→256)` | 220 |
| conv2 | **`GATv2Conv(256→32, heads=8, concat=True, share_weights=True, dropout=0.15)`** | 226-229 |
| conv3 | `GCNConv(256→256)` | 236 |
| conv4 | `GCNConv(256→128)` | 241 |
| order_head / risk_head | `MLPHead(128,128,1)` | 246-247 |

Hybrid GCN + GATv2. **Actual parameter count: 302,862.** The artifacts
(`benchmark_v3.json`, `benchmark_real_v3.json`) record **`"params": 237070`** — a discrepancy
of exactly **65,792 = 256×256 + 256**, i.e. one `GCNConv(256,256)`. The reported parameter
count is wrong.

### `MigrationGNN` (v2, legacy) — `model.py:73`
3 × `GCNConv`, hidden 64, emb 32, **9,282 parameters**. Docstring says 4 input features;
`build_node_features()` emits 6.

### Other "GNN/RL" classes are not what they claim

| Class | File:line | Reality |
|---|---|---|
| `TemporalGNN` / `_TGCN` | `qtrust_ai/graph/temporal_gnn.py:275,322` | **No graph ops at all** — `nn.LSTM` + `nn.Linear`, plus a NumPy LSTM fallback |
| `MigrationAgent` | `rl_agent.py:275` | 2 × `GCNConv`, 17,666 params. Docstring says "GCN" at `:278` and "GAT-style" at `:494` — the latter is false |
| `MultiObjectiveRLAgent` | `qtrust_ai/migration/multi_objective_rl.py:380` | `train()` is **random-search hill climbing**, self-labelled `# Stub REINFORCE` (`:406-418`); the torch path is **supervised cross-entropy**, not policy gradient |
| `QPlanGT` | `planner/qtrust_planner/qplan_gt.py:30` | Stub; `simulate_migration_outcome` is `cost = len(order)*0.5 + sum(order)*0.01` |

> **There is no GNN and no gradient-based RL anywhere under `qtrust_ai/`.** The entire
> learned stack lives in `planner/qtrust_planner/`. The `qtrust_ai` "migration" package is
> rules and feature models.

### RL agent — PPO, and the checkpoint is missing

- `train_agent_ppo()` `rl_agent.py:471`. AdamW, lr 3e-4, γ 0.99, 64 envs (8 on CPU),
  4 PPO epochs, clip 0.2, entropy 0.01, value 0.5, grad-norm 0.5, 10,000 episodes, seed 42.
- Reward `rl_agent.py:213-268`: `+100 + 0.1×remaining_days` if all migrated, `−10×unmigrated`
  if the 365-day deadline expires, else `−0.1×risk − 0.01×downtime`, `+5` for early-critical.
  Risk = criticality weight (1/2/3/4) `+2` if RSA and key<3072.
- **`planner/rl_agent_real.pt` — the checkpoint behind the "140.34 ± 8.13" number — does not
  exist in the repository.** It is referenced by `rl_benchmark_real_cbom.json`, `server.py:349`,
  `retrain_rl_real_cbom.py:43`, `eval_rl_real_cbom.py:59`. The RL result is unverifiable.

---

## 5. FURTHER LEAKAGE AND METHOD DEFECTS

1. **`random_order` is not random** — `benchmark.py:71-75` hard-codes
   `np.random.default_rng(0)`, the *same* permutation family for every graph. Random has no
   sampling variance, so **"+0.687 vs random" is not a statistical comparison.**
2. **Labels are time-dependent** — `_cbom_days_until_expiry` (`data_generator.py:141-153`)
   calls `datetime.now()`. `days_to_deadline` and hence `y_order` drift as certificates
   approach expiry, so **the committed JSONs are not reproducible at a later date** despite
   every script being seeded.
3. **`n_hosts` is actually the asset count** — `eval_real_cbom_loo.py:232,252` compute it as
   `sum(g.n_assets)`. It equals 277 only because the corpus is 1 asset per host.
4. **Host-disjointness is asserted at build time, never on the committed corpus.**
   `build_real_cdoms.py:198` asserts `h not in hosts_seen`, but `:200` strips every
   `_`-prefixed key on write — so the committed files contain no `_hosts`/`_provenance`.
   The only test (`test_real_cbom_builder.py:55-62`) builds a **synthetic** 12-host corpus.
   (I verified the 0-overlap property myself; the repo does not.)
5. **Covariate shift** — every real asset has `criticality = medium` (2), while synthetic
   assets draw `criticality = randint(1,5)`. The model must bridge feature 3.
6. **`top5` is degenerate for 4 of 42 folds** (n ≤ 5 ⇒ full set). Random's `top5 = 0.142857`
   is just the single n=7 fold.
7. **Intra-fold validation contamination** — `train_gpu.py:228-231` mixes real graphs into
   train *and* val; best-model selection at `:430` therefore selects on a val set sharing
   the corpus with training.
8. **No early stopping anywhere** — only best-val-τ checkpoint selection.
9. **GATv2 key-shape risk** — checkpoints contain both `conv2.lin_l.*` and `conv2.lin_r.*`.
   Under a PyG version where `share_weights=True` collapses to a single `lin`,
   `load_state_dict(strict=False)` (`train_gpu.py:274`) would **silently drop the entire
   attention projection** while printing and continuing. Worth verifying against your PyG pin.
10. **The 40-fold artifacts came from a leaky corpus** — `EXPERIMENTS.md:38` states the old
    40-CBOM corpus had **11 cross-CBOM duplicate hosts**. `real_cbom_loo_40.json` (τ-b
    0.7263) is still the primary headline in `FINAL_ENGINEERING_REPORT.md:49` and
    `EXPERIMENTS.md:35`.

---

## 6. DATA_CARD CLAIMS THAT ARE FALSE

`planner/data/DATA_CARD.md` states (`:21, :36`):
> *"`dvc.yaml` tracks `planner/data/estates_v1`"* … *"DVC locks `planner/data` and
> `inspector/data` with hashes; CI asserts `dvc status` clean."*

The repo-root `dvc.yaml` declares **exactly one stage**, `evaluate`, and its own header
comment states that the ingest/bronze/silver/gold/splits/model-training stages were
**deliberately not declared**. `planner/data/estates_v1/` does not exist;
`DATASETS.md:119`'s verification step references a non-existent file. The "500 synthetic
estates" appears **nowhere in code** — only in prose.

`DATA_CARD.md:31` is, to its credit, accurate and damning: *"404 TLS-only scans, all medium
criticality, zero expired, zero PQC (expired/PQC/weak-key features constant zero)."*

---

## 7. CONSOLIDATED VERDICT ON THE ML LEG

Six independent defects, each individually sufficient to invalidate the headline:

| # | Defect | Severity |
|---|---|---|
| 1 | LOO base checkpoint trained on 40 of the 42 held-out CBOMs | **Fatal** |
| 2 | Baseline is the label generator (circular; ceiling is τ-b = 1.0 by construction) | **Fatal** |
| 3 | All 42 graphs are edgeless → no message passing; it is an MLP benchmark | **Fatal** |
| 4 | 407 usable pairs → SE ≈ 0.034, \|Δ\|/SE ≈ 0.12 | **Fatal** |
| 5 | `criticality`/`vendor`/`first_seen` have zero variance; 6 distinct risk tuples total | Severe |
| 6 | Random baseline not random; labels time-dependent; param count wrong by 65,792 | Severe |

> **The "honest tie" cannot be published in any form.** It is not an honest tie — it is an
> in-sample, circularly-benchmarked, underpowered comparison between an MLP and its own
> label function, on graphs with no edges.

**This is the most valuable finding in the entire audit.** It is also, notably, exactly the
kind of result that a well-written paper *can* legitimately be about — provided the authors
are willing to retract the "honest tie" framing they currently consider a selling point.

---

## 8. WHAT THIS MEANS FOR THE PAPER

Stage 1 concluded the framing should be an evidence-infrastructure paper. Stage 1C makes
that conclusion **much stronger and much more concrete**. The paper now has a specific,
verified, worked example:

> **"A Case Study in Unverifiable ML Evaluation: six independent failure modes in a
> real-world PQC migration-ordering benchmark."**

For each mode we provide: the exact file and line, the artifact, an independent
recomputation, and the corrective control. That is:

1. **Train/test contamination via warm-start** — detectable by reading checkpoint metadata
   (`n_real_graphs`) against the evaluation corpus. A one-line check nobody performed.
2. **Circular baselines** — detectable by diffing the baseline function against the label
   function. They were byte-identical.
3. **Degenerate graph structure** — detectable by counting `edge_index` elements.
4. **Tie-saturated rank metrics** — detectable by counting discordant pairs; reported here
   with a power analysis (SE ≈ 0.034).
5. **Vacuous top-k metrics** — `k > n` makes them identically 1.0, *including for random*.
6. **Non-random "random" baselines** — a hard-coded RNG seed gives the baseline zero variance.
7. **Time-dependent labels** — deterministic seeds do not make wall-clock-dependent labels
   reproducible.

Plus, from Stage 1: circular label generation in discovery, undisclosed negative robustness
results, synthetic metrics presented as flagship, and documentation that contradicts its own
artifacts.

**This is publishable, novel, useful, and fully supported by evidence that is in the public
repository today.** It requires no unavailable data. It is a real contribution to the
reproducibility literature — provided the authors accept that the headline becomes a
retraction rather than a result.

---

## 9. STAGE GATE — STAGE 1 NOW COMPLETE

All three deep audits are in. Nothing is pending.

**Final tally:** 14/14 headline numbers reproduce arithmetically; **0 arithmetic
mismatches**; **30 substantive defects** identified (7 critical, 11 high, 12 medium);
**3 inaccessible/missing resources**; **30+ unresolved documentation contradictions**;
**2 claims found actively false about the repo's own artifacts**
(`TRUTH_AUDIT.md:7` epoch count; `DATA_CARD.md:21,36` DVC tracking).

**Recommendation is unchanged and strengthened:** the manuscript cannot be drafted around the
current contribution. It can be drafted around a *better* one — an evidence-audit paper —
but the authors must first decide whether to retract the "honest tie," the τ 0.975 badge,
and the F1 0.9525 headline.

**Blocking questions from Stage 1 remain open** (two 404 repositories, missing checkpoint,
venue class, real edge source). Stage 2 (evidence ledger) can begin immediately for
everything verifiable in the public repo — it does not depend on those answers.