# DELIVERABLE D — LITERATURE REVIEW AND GAP ANALYSIS
## Q-Trust · 2026-10-14

**Verification standard.** Every entry below was confirmed against a publisher page, DOI
record (Crossref), the standards body's own publication index, or the artifact itself.
Where a field could not be confirmed it is marked **UNVERIFIED** and is **not cited in the
manuscript**. Search threads: Semantic Scholar, Crossref REST, DBLP (blocked by a bot wall
during this search), arXiv API, IEEE Xplore, ACM DL, publisher pages, and NIST/NSA/CISA/
OASIS standards portals.

---

## 1. VERIFIED POSITIONING TABLE

| System | Task | Labels | Venue / ID | Relevance |
|---|---|---|---|---|
| **CryptoGuard** | misuse detection | rules (Soot slicing) | ACM CCS'19, pp. 2455–2472, `10.1145/3319535.3345659` | the canonical baseline Q-Trust declines to compare against |
| **CogniCrypt / CrySL** | misuse detection | CrySL rules, expert-authored | ASE'17 `10.1109/ASE.2017.8115707`; ECOOP'18 `10.4230/LIPIcs.ECOOP.2018.10` | specification-driven detection |
| **CryptoAPI-Bench** | benchmark | **hand-authored unit tests** | IEEE SecDev'19, pp. 49–61, `10.1109/SecDev.2019.00017` | **the benchmark Q-Trust uses** |
| **ApacheCryptoAPI-Bench** | benchmark | **hand-curated, file/method/line provenance** | Afrose et al., **IEEE TSE 49(2):485–497 (2023)**, `10.1109/TSE.2022.3154717` | **no standalone publication — cite the TSE paper** |
| **Ami et al.** | evaluation / negative result | mutated benchmark | IEEE S&P'22, pp. 614–631, `10.1109/SP46214.2022.9833582`; TOPS 29(2) 2026, `10.1145/3796221` | **closest methodological ancestor: detectors fail under adversarial rewriting** |
| **Zhang et al.** | developer study | 57 reports adjudicated | IEEE TSE 49(1):288–303 (2023), `10.1109/TSE.2022.3150302` | 30 of 57 reports **rejected** by developers |
| **Xia et al.** | misuse detection (LLM) | curated + human adjudication | PACMSE 2(ISSTA), art. ISSTA006, 2025, `10.1145/3728875` | ~90% recall only after scope alignment |
| **Gopher / CryptoGo** | misuse detection (Go) | rules | CCS'24 `10.1145/3658644.3690276`; ACSAC'22 `10.1145/3564625.3567989` | language-specific |
| **Cryptoscope** | usage discovery + inventory | ground-truth test cases | arXiv:2503.19531 (IBM, 2025) | 92% asset identification; does not analyse libraries |
| **Hidden Ciphers** | inventory / discovery | synthetic benchmark + manual reference list | arXiv:2608.04857 (2026) | **F1 0.75**; explicitly *does not* compute migration strategies |
| **BF-CBOM** | CBOM generation at scale | comparative analysis | IEEE/ACM ICPC'26, pp. 463–467, `10.1145/3794763.3794831` | comparative CBOM study |
| **SATAM** | architecture-derived CBOM | design science | MAgiCS'26, CCIS 3002, pp. 20–39, `10.1007/978-3-032-28946-9_2` | argues inventory-derived CBOMs lack intent |
| **Hess** | CBOM standardisation | practice survey | MAgiCS'26, pp. 1–19, `10.1007/978-3-032-28946-9_1` | independent CycloneDX reading |
| **Hasan et al.** | PQC migration **prioritisation** | case-study parameters | IEEE Access 12:23427–23450 (2024), `10.1109/ACCESS.2024.3360412` | **closest prior work; graph-theoretic, NOT learned** |
| **MAgiCS workshop** | migration agility | — | CCIS 3002, Springer 2026, `10.1007/978-3-032-28946-9`, **open access**, co-located EUROCRYPT'26 | the field's home |
| **Riou et al.** | benchmarking methodology | — | MAgiCS'26, pp. 121–142, `10.1007/978-3-032-28946-9_7` | **benchmarking pitfalls — closest methodological relative** |
| **Shaw** | migration sequencing | analytic | arXiv:2610.09029 (2026), preprint | optimal ordering; "not validated against outcomes" |
| **Rodrigues et al.** | misuse detection via **graph embeddings** | UNVERIFIED | ICMLA'20 `10.1109/ICMLA51294.2020.00171`; IEEE TR 72(4):1678–1689 (2023), `10.1109/TR.2023.3237849` | **node2vec/Bag-of-Graphs, not a GNN; split policy UNVERIFIED** |

---

## 2. THE RESEARCH GAP, STATED PRECISELY

### Gap 1 — Migration **ordering** is unstudied as a learning problem. ✅ CONFIRMED

> *"No paper found frames PQC migration ordering as a learning-to-rank problem with real
> ground truth."*

- Hasan et al. (IEEE Access 2024) prioritises migration but is graph-theoretic and
  non-learned, with parameters taken from design documentation.
- Shaw (2026) produces an optimal ordering but analytically, and states its case studies
  are *"illustrative and are not validated against outcomes."*
- Aliyev et al. (arXiv:2505.05959) is the only learned work, and it is 5-way
  classification of a single system on a *"semi-synthetic dataset"* whose labels *are* the
  recommended mitigation — i.e. circular in exactly the way this audit documents.

**Consequence.** There is no published oracle for a "correct" migration order. Any model
claiming one is unfalsifiable. This is the gap the audited system fell into.

### Gap 2 — No GNN for cryptographic asset ranking. ✅ CONFIRMED

Targeted arXiv and DBLP searches return only GNNs used to *attack* crypto. The only
"graph neural network for ranked cryptographic migration" claims located are vendor
marketing (`qcipher.de`), which publish no methods, data, or evaluations. Rodrigues et al.
use graph *embeddings* for *misuse detection*, not ranking, and not a GNN.

### Gap 3 — No host-level labelled corpus for migration ordering. ✅ CONFIRMED

Census corpora exist and are large but **unlabelled**: Censys/IMC'13 (`10.1145/2504730.2504755`),
EFF SSL Observatory (USENIX Sec'11), Chung et al./CCS'16 (~80M certs, restricted),
Heninger et al./USENIX Sec'12 (5.8M certs). None carries a migration-order label, and
Chung et al. note that host identity itself is uncertain without ground truth.

### Gap 4 — No *evaluative* work on migration-ordering benchmarks. ✅ CONFIRMED, and this is ours

The entire MAgiCS workshop is structural. Riou et al. raise benchmarking-pitfalls for
*signature schemes*. **Nobody asks how one would know whether a proposed migration
ordering is correct.** That is the gap this paper fills.

---

## 3. LABELING-PROVENANCE SPECTRUM (used in §Taxonomy of the paper)

| Tier | Method | Examples | Quality |
|---|---|---|---|
| 1 | hand-authored unit tests | CryptoAPI-Bench, Cryptolation, CamBench_Cap | expert curation, but **tool-shaped** — benchmarks matching tool capability overestimate it (Ami et al.) |
| 2 | hand-curated real-world, author-annotated | ApacheCryptoAPI-Bench | best available real corpus; single annotator team, no IRR, no external validation |
| 3 | developer-adjudicated | Zhang et al. TSE'23 | 30 of 57 reports rejected against 9 accepted |
| 4 | manually reverse-engineered | Olaiya & Nadkarni (arXiv:2510.13102) | 5,704 invocations hand-analysed with Ghidra |
| 5 | **tool-derived** | DeepCVA (`10.1109/ASE51524.2021.9678622`) inherits CryptoGuard/CrySL labels | bounded by tool recall |
| 6 | **model-derived (circular)** | CryMisTa (arXiv:2509.10814) | LLM proposes taxonomy *and* labels |
| **7** | **detector labels its own corpus** | **the audited system** | **below tier 6**: the labels are the quantity under test |

**This is the paper's sharpest framing.** The audited system sits one tier below LLM-derived
labels, in a literature where even tier-3 corpora lose 53% of detector reports to
developer adjudication.

---

## 4. CORRECTIONS TO PREMISES I HELD ENTERING THIS REVIEW

Recording these because they are the kind of error that propagates:

1. **CogniCrypt is ASE 2017, not ESEC/FSE 2019.** (`10.1109/ASE.2017.8115707`)
   CogniCryptGEN is CGO 2020, not ESEC/FSE.
2. **ApacheCryptoAPI-Bench has no standalone paper** — it was introduced inside the TSE
   2023 paper. The project's own bibliography cites it as a corpus with no citation at all.
3. **CryptoGuard author order differs between sources** — ACM camera-ready lists
   …Frantz, **Kantarcioglu, Yao**; the arXiv preprint lists …Frantz, **Yao, Kantarcioglu**.
   Use the ACM order.
4. **"Why Crypto-detectors Fail" is pp. 614–631**, not 397–414.
5. **GPTScan is smart contracts**, not source-code crypto APIs.
6. **DeepCVA is not a crypto-misuse benchmark** — its labels come *from* crypto detectors.
7. **NIST IR 8547 is still an Initial Public Draft.** The highest binding authority is
   **Executive Order 14412 §4(b)**: PQC digital signatures by **31 Dec 2031**, key
   establishment by **31 Dec 2030**, for High Value Assets and high-impact systems. IR
   8547's 2030/2035 dates are *proposals* and are *later* than the binding EO deadlines.
8. **NTIA's 2021 SBOM Minimum Elements is superseded** by the **2026 CISA minimum
   elements v2.1 (29 July 2026)**, co-authored by CISA, NSA, FBI and international
   partners.
9. **`cryptoProperties` was introduced in CycloneDX 1.6**, not 1.4 or 1.5 (verified by
   probing the official JSON schemas: 0 occurrences in 1.4/1.5, 1,194 in 1.6).

---

## 5. SEARCH SCOPE AND ITS LIMITS

**Covers:** Cryptographic API misuse detection (2017–2026); crypto discovery/inventory;
CBOM generation and analysis; PQC migration planning and sequencing; ML evaluation
methodology (leakage, reproducibility, statistical power, metric choice); software supply
chain provenance and attestation; the NIST/NSA/CISA/EU regulatory corpus.

**Explicitly not covered, and I cannot rule out:** non-English venues; industry white
papers; patent literature; theses; and the grey literature in which vendor GNN claims
primarily appear. **Absence of evidence in these searches is not proof of absence.** The
gap claims in §2 are therefore stated as *"no peer-reviewed work found"*, with the search
scope given, not as absolute novelty.

**Two items flagged UNVERIFIED and excluded from the manuscript:**
- *"One Hand to Rule Them All" (NDSS 2022)* — not found on any NDSS page or in Crossref.
- *"Mind the Gap: Policy vs Reality in Post-Quantum TLS Deployment"* (IMC 2026,
  `10.1145/3777912.3839797`) — the paper exists and is cited, but its measurements could not
  be retrieved, so **no number from it appears in the manuscript.**

**One item I recommend the authors open before submission:** Rodrigues, Braga & Dahab,
*IEEE Trans. Reliability* 72(4):1678–1689 (2023). It is the only peer-reviewed learned model
adjacent to the GNN question, and I could not verify its split policy. If it used a
repo-disjoint split, the novelty claim in Gap 2 must be narrowed accordingly.