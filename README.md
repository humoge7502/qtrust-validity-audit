# Provenance Labelling Is Not Evaluative Validity

**A reproducibility audit of two post-quantum cryptography migration benchmarks**

> Post-quantum cryptography migration has become a dated legal obligation: Executive Order
> 14412 (22 June 2026) requires PQC for digital signatures by 31 December 2031 on federal
> High Value Assets and high-impact systems, and its Â§5(d) directs CISA and NIST to publish
> **cryptographic bill of materials minimum elements by approximately 19 March 2027** for the
> "automated assessment of cryptographic assets". Organisations are therefore making real
> ordering decisions under a real deadline â€” with no validated tooling and no oracle against
> which to validate a tool.

This repository contains the paper, its artifact, and the full audit trail behind it.

---

## What the paper argues

Machine-learning evaluations in security engineering increasingly ship with **provenance
metadata** classifying each result as real, synthetic, or demonstration. We show that this
practice is **orthogonal** to the property that determines whether a result means anything.

We identify **eight independent and mutually concealing failures of evaluative validity**
across two benchmarks, each with a cheap detection check:

| Mode | Failure | Detection check |
|---|---|---|
| M1 | Warm-start contamination | Read checkpoint provenance counters against the eval corpus |
| M2 | Circular baseline | Diff the baseline function against the label generator |
| M3 | Degenerate structure | Count edges and per-feature distinct-value counts |
| M4 | Tie-saturated rank metric | Count discordant pairs; report SE and MDE |
| M5 | Vacuous top-*k* | Check *k* â‰¥ *n* |
| M6 | Non-random "random" baseline | Grep the baseline for a fixed seed |
| M7 | Absent predictions | Look for a predictions file or split manifest |
| M8 | Unreconciled documentation | Diff numbers across docs and artifacts |

### Three headline results

1. **A learned ranker cannot beat a one-column sort.** A bare sort on key size produces
   metric vectors *identical* to the doctrine heuristic on **42 of 42** held-out folds â€”
   because the label function degenerates to `log1p(key_size)/4 + constant`.
2. **A reported gain reverses sign under a different averaging strategy.** +0.280 F1 over a
   deterministic baseline under micro-averaging; **âˆ’0.080** under macro-averaging.
3. **Better documentation hygiene did not produce better validity.** The second audited
   system commits per-example predictions, audits its splits, reports bootstrap confidence
   intervals, and has *zero* documentation contradictions â€” and still fails M2, because a
   fixed linear model beats its reported classifier on 3 of 3 seeds.

### The clean warm-start re-run, which overturned our own prediction

Re-training from a synthetic-only checkpoint (`n_real_graphs = 0`) and re-running the
identical 42-fold protocol changes the result:

| Metric | Contaminated warm start | Clean | Î” | Heuristic |
|---|---|---|---|---|
| Ï„-b (tie-aware) | 0.7168 | **0.6009** | **âˆ’0.1159** | 0.7210 |
| exact rank | 0.0238 | **0.2619** | +0.2381 | 1.0000 |
| node rank | 0.3136 | **0.5986** | +0.2850 | 1.0000 |
| top-5 | 0.5000 | **0.7143** | +0.2143 | 1.0000 |

Paired: mean Î” = âˆ’0.1201, 95% CI [âˆ’0.1948, âˆ’0.0567], *t* = âˆ’3.34, **p = 0.0018**.
The reported "tie" was partly an artifact of contamination, and **the two families of rank
metric now disagree about which model is better**.

---

## Reproducing everything

No GPU, no dataset, no checkpoint, no network required.

```bash
git clone --depth 1 https://github.com/[SYSTEM A].git
cd q-trust

python artifact/scripts/verify_qtrust_claims.py .     # 14 claims, 0 mismatches
python artifact/scripts/verify_ckpt_leak.py            # n_real_graphs = 40
python -m pip install numpy scipy matplotlib
python artifact/scripts/experiments_reaudit.py .       # X1 42/42, X2 42/42
python artifact/scripts/validate_eval.py --repo .      # 7/8 modes PRESENT
```

Or everything at once: `bash artifact/build.sh /path/to/q-trust`

Optional, needs `torch` + `torch_geometric`:

```bash
python artifact/scripts/clean_warmstart_loo.py . results/clean_warmstart_loo.json
```

---

## Layout

```
paper/     main.tex Â· main.pdf (11 pp, IEEEtran) Â· Figure 1
artifact/  build.sh Â· scripts/ (8) Â· results/ (4 result transcripts)
audit/     Deliverables A-I Â· Evidence Ledger Â· Gap-Closure Report
```

## Provenance and integrity

Every number in the paper is recomputed from files committed to the audited repository at
commit `8e47891` by a script included here. Nothing is transcribed from project
documentation, and no value is estimated or simulated.

**We found no arithmetic error in the audited project.** All fourteen headline numbers
reproduce exactly. Every failure documented here is a failure of *construct validity*, and
each is detectable from artifacts the project has already made public.

We also found and corrected two defects in our own work, both disclosed in the paper: an
unseeded RNG in our randomised-null experiment (the exact failure mode M6 we criticise), and
an initially unfair baseline in the second-system comparison.

## Limitations

Stated plainly in Â§Threats to Validity: this is a **negative-result paper** with **two**
audited systems, both in PQC migration. It is a designed contrast, not a survey. No new
method, dataset, or algorithm is proposed.

## License

MIT. See [LICENSE](LICENSE).