# DELIVERABLE H â€” SUBMISSION PACKAGE

## 1. TITLE, ABSTRACT, KEYWORDS

**Title.**
> *Provenance Labelling Is Not Evaluative Validity: A Reproducibility Audit of a
> Post-Quantum Cryptography Migration Benchmark*

**Abstract (248 words).**
> Machine-learning evaluations in security engineering increasingly ship with provenance
> metadata classifying each result as real, synthetic, or demonstration data. We show this
> practice is orthogonal to the property that determines whether a result means anything.
> We audit *Q-Trust*, an open post-quantum cryptography migration and attestation system
> maintaining one of the most rigorous provenance audits we have encountered: a document
> classifying every headline metric, an honest-failure data pipeline, and a policy against
> publishing synthetic data as expert results. Using only artifacts committed to the public
> repository, and reconstructing the benchmark's evaluation target so that all 42 held-out
> folds reproduce bit-exactly, we identify six independent and mutually concealing failures
> of *evaluative* validity. The leave-one-out protocol warm-starts from a checkpoint that
> records `n_real_graphs=40` against a 42-fold corpus, so 40 of 42 held-out folds were in the
> base model's training set. The comparison baseline is a byte-identical reimplementation of
> the label generator, making the model's ceiling Ï„_b = 1.0 by construction. All 42 graphs
> have zero edges, so no message passing occurs. 49.3% of candidate pairs are tied, leaving
> 407 discordant pairs and a standard error of 0.034. A reported top-10 accuracy of 1.0 on
> every fold is matched by a random ranker, because graphs hold at most seven nodes. The
> "random" baseline hard-codes one RNG seed. We further show a bare sort on a single feature
> reproduces the learned ranker's metric vector on 42 of 42 folds, and that a reported +0.280
> F1 gain over a deterministic baseline becomes âˆ’0.080 under macro-averaging. We release a
> standard-library-only harness reproducing every headline number exactly, and argue that
> provenance taxonomies must be complemented by, not substituted for, an explicit
> evaluative-validity audit.

**Keywords.** reproducibility; construct validity; data leakage; ranking evaluation;
post-quantum cryptography; cryptographic bill of materials; artifact evaluation; metrics

---

## 2. FIGURE AND TABLE INVENTORY

| # | Float | Type | Status | Source |
|---|---|---|---|---|
| 1 | Two structural findings | `figure*` (2-panel) | âœ… **populated, verified** | `experiments_reaudit.py` X2, X6 |
| 2 | Headline claims recomputed | `table` | âœ… populated, verified | `verify_qtrust_claims.py` |
| 3 | Six failure modes + detection checks | `table*` (wide) | âœ… populated, verified | Deliverable C |
| 4 | Training-free baseline suite | `table` | âœ… populated, verified | X2 |
| 5 | Micro vs macro averaging | `table` | âœ… populated, verified | X6 |
| 6 | Minimum detectable effect | `table` | âœ… populated, verified | X4 |

**All six floats contain only verified values.** No placeholder tables, no illustrative
numbers, no synthetic performance charts.

---

## 3. VENUE RECOMMENDATION

### Ambitious target

| Venue | Fit | What it demands |
|---|---|---|
| **IEEE S&P** or **ACM CCS** | Excellent. Both run **artifact-evaluation processes**, which is precisely this paper's subject | Full artifact review; Â§6 of the audit should be read as a model of what reviewers should check. Expect a rejection rate near 90%; treat as a stretch |

### Realistic alternatives, in preference order

| Venue | Why it fits | Notes |
|---|---|---|
| **RAID (Research in Attacks, Intrusions and Defenses)** | Consistently accepts careful empirical evaluation and negative-result-plus-methodology work; security-practitioner audience | Best probability-weighted target |
| **ACSAC** | Applied, measurement-oriented; publishes audit-style work | Strong fit |
| **USENIX Security â€” Artifacts** | Artifact Evaluation is a first-class, *citable* track; our stdlib-only harness is a natural fit | Strong fit; artifact review is the selling point |
| **IEEE EuroS&P** | SoK and evaluation tracks; publishes supply-chain measurement | Viable |
| **MAgiCS workshop** (co-located with EUROCRYPT; Springer CCIS 3002, open access) | **Best topical fit.** An entire workshop on cryptographic migration and agility, including a chapter on benchmarking pitfalls we cite | Small (10 of 19 accepted). Check whether it recurs |
| **IEEE S&P Workshop on Security and Privacy in ML (SPML)** | Methodological framing fits | Workshop |

### Journal fallback

IEEE TDSC Â· ACM Transactions on Information and System Security Â· **ACM Transactions on
Software Engineering and Methodology (TOSEM)** Â· Journal of Cryptographic Engineering Â·
**Computer Security Review** Â· IEEE Security & Privacy magazine

### Explicitly not recommended

- Any venue without peer review, and in particular the predatory outlets that would accept
  the *original* Q-Trust framing (tool + GNN + CodeBERTa) without demanding the evidence now
  available. **A venue that accepts that framing is telling you something useful about the
  venue.**
- ML conferences (NeurIPS/ICML/ICLR/KDD). The paper has no novel ML method, no new dataset,
  and no learning algorithm. Submitting there would invite exactly the criticism the audit
  levels at the audited system.

### On deadlines and fees

**Not stated, deliberately.** Deadlines, page limits, and fees change annually and I could
not verify current values. Check the official call for papers for each venue. The only
schedule fact relevant to this submission is that **EO 14412 Â§5(d) requires CISA and NIST to
publish CBOM minimum-elements guidance by approximately 19 March 2027** â€” a timing argument
for the paper's relevance, not a deadline for the paper.

---

## 4. FORMAT COMPLIANCE

| Requirement | Status |
|---|---|
| Two-column IEEEtran | âœ… `\documentclass[conference]{IEEEtran}` |
| Abstract 150â€“250 words | âœ… 248 |
| Keywords 3â€“5 terms | âœ… 8 terms; trim to 5 if the venue requires |
| Environment balance | âœ… verified by `check_tex.py` |
| Dangling `\ref` | âœ… none |
| Missing / uncited `\bibitem` | âœ… none (43 = 43) |
| Figures present on disk | âœ… verified |
| Page count | **10 pages, compiled** (IEEEtran V1.8b) |
| Supplementary material | âœ… artifact package (Deliverable G) |

---

## 5. SUBMISSION CHECKLIST

**Before upload**
- [x] ~~Compile `main.tex`~~ âœ… **DONE** â€” TeX Live 2026 + IEEEtran V1.8b; 10-page PDF,
      **0 overfull hbox, 0 underfull hbox, 0 undefined citations, 0 undefined references**.
      Two fatal bugs were found and fixed: the non-existent `balance` package, and two
      missing `\end{}` commands.
- [ ] Anonymise for double-blind: remove the Q-Trust contributor acknowledgements and the
      artifact URL; keep repository references as "an open-source PQC migration system"
- [ ] Verify every number in Â§6 against `results/experiments_output.txt` **one final time**
- [x] ~~Obtain the IMC 2026 "Mind the Gap"~~ âœ… **DONE** â€” preprint obtained. Numbers now
      quoted in Â§1: >2B handshakes / 1M domains / 11 vantage points; PQ key exchange
      31.3%â†’49.2%; **zero PQ signatures ever negotiated**; earlier-deadline jurisdictions
      adopt *less* (32.4% vs 45.7%). No RSA/ECDSA split is attributed â€” the paper reports none.
- [x] ~~Open Rodrigues, Braga & Dahab~~ âœ… **DONE** â€” full text obtained. Split is **80/20,
      no repo-disjointness**; P/R/F1 only; **no CIs, no threats-to-validity**. The
      novelty claim is safe and strengthened; the finding is now stated in Â§2.
- [ ] Upload the artifact package as a supplementary ZIP

**Honest-status statements required at submission**
- [ ] Disclose that the authors are auditing a system whose maintainers they are in contact
      with, **and** that Q-Trust maintainers were offered the chance to respond
- [ ] State plainly that no arithmetic error was found in the audited project
- [ ] State that the dataset package was inaccessible during the audit, and which claims
      were consequently excluded

---

## 6. ARTIFACT PACKAGE

```
artifact/
â”œâ”€â”€ scripts/     verify_qtrust_claims.py Â· verify_ckpt_leak.py Â·
â”‚                experiments_reaudit.py Â· make_figure1.py Â· check_tex.py
â”œâ”€â”€ paper/       main.tex Â· figure1_structural_findings.{pdf,png}
â”œâ”€â”€ results/     experiments_output.txt  (verbatim run transcript)
â””â”€â”€ DELIVERABLE_{A,B,C,D,E,G}*.md
```

**Reviewer verification path (5 commands, no GPU, no dataset):**
```bash
git clone --depth 1 https://github.com/[SYSTEM A].git && cd q-trust
python artifact/scripts/verify_qtrust_claims.py .   # expect: 14 reproduced, 0 mismatched
python artifact/scripts/verify_ckpt_leak.py          # expect: n_real_graphs = 40
python -m pip install numpy scipy matplotlib
python artifact/scripts/experiments_reaudit.py .    # expect: X1 42/42, X2 42/42 identical
python artifact/scripts/make_figure1.py . .
```

---

## 7. WHAT I CANNOT PROMISE

- **No acceptance prediction.** A reproducibility audit of a single system, using
  opportunistic mode discovery, is a first-of-its-kind paper. It may be judged too narrow
  (one system), too negative (no positive result), or too obvious (all six checks are cheap).
  Each of those is a legitimate reviewer objection and the paper does not fully preempt any.
- **Scope is one system.** The taxonomy's generality is argued, not demonstrated. Deliverable
  E's **P8** â€” auditing a second system â€” is the experiment that would convert argument into
  evidence, and I recommend it before any top-tier submission.
- **The paper is compiled and verified.** Layout was checked from the LaTeX log rather
  than visually: `pymupdf`'s DLL is blocked by an Application Control policy on this
  machine, so I could not rasterise the PDF for eyeball inspection.