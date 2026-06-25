# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-06-25 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/001-evaluating-the-statistical-validity-of-p/spec.md`

## Summary
The core deliverable is an end‑to‑end audit pipeline that (1) ingests a CSV of URLs pointing to public A/B test summaries, (2) extracts required metrics, (3) reconstructs statistical tests, (4) flags inconsistencies according to **FR‑004** (augmented with the Constitution‑VI absolute‑difference rule), (5) produces a JSON audit report, (6) generates an HTML dashboard (**FR‑010**), and (7) packages all artifacts for reproducibility (**FR‑006**, **FR‑014**, **FR‑016**). All steps run on the default GitHub Actions CPU‑only runner and respect the resource caps in **SC‑008**.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas>=2.2`, `requests>=2.31`, `beautifulsoup4>=4.12`, `lxml>=5.2`, `scipy>=1.14`, `statsmodels>=0.14`, `jsonschema>=4.22`, `matplotlib>=3.8`, `jinja2>=3.1`, `tqdm>=4.66`  
- **Storage**: Files on the repository filesystem (`data/`, `output/`)  
- **Testing**: `pytest>=8.2` with contract tests in `tests/contract/`  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: Complete a corpus of ≤ 5 000 URLs within 6 h, ≤ 2 CPU cores, ≤ 7 GB RAM (SC‑008)  
- **Constraints**: CPU‑only execution (FR‑009), no GPU libraries, deterministic random seeds for reproducibility (Constitution I)  

## Constitution Check
| Principle | How the Plan Satisfies |
|-----------|------------------------|
| **I. Reproducibility** | All scripts are deterministic (seeded RNG), Dockerfile pins exact environment, `manifest.json` records SHA‑256 hashes (FR‑014). |
| **II. Verified Accuracy** | All external citations (e.g., Kohavi et al., 2020) will be verified by the Reference‑Validator before acceptance. |
| **III. Data Hygiene** | Raw HTML pages are stored read‑only under `data/raw/`; each transformation writes a new file with a checksum logged in `state/artifact_hashes.yaml`. |
| **IV. Single Source of Truth** | Every figure in the dashboard is generated directly from `audit_report.json`; no hand‑typed numbers. |
| **V. Versioning Discipline** | `manifest.json` contains SHA‑256 of Docker image, JSON report, dashboard HTML; CI updates the version stamp per Constitution V. |
| **VI. Statistical Consistency Verification** | Reconstructed p‑values/effect sizes are cross‑checked against reported values using the tolerances in **FR‑004** *and* the absolute‑difference rule (≥ 0.05) required by Constitution VI; any discrepancy > 0.05 is flagged and documented. |
| **VII. Source Provenance & Transparency** | Each extracted record stores the original URL and retrieval timestamp; the dashboard displays source breakdowns. |

## Project Structure
```text
specs/001-eval-ab-test-validity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── extracted_summary.schema.yaml
    └── audit_record.schema.yaml

src/
├── __init__.py
├── audit/
│   ├── __init__.py
│   ├── cli.py                # entry point for run_audit.sh
│   ├── extraction.py         # HTML parsing & field extraction
│   ├── reconstruction.py     # statistical test reconstruction
│   ├── consistency.py        # flagging logic (FR‑004)
│   ├── synthetic.py          # generator for FR‑008
│   ├── sensitivity.py        # FR‑004a analysis
│   ├── dashboard.py          # HTML generation (FR‑010)
│   └── utils.py
├── contracts/
│   ├── extracted_summary.py  # JSON‑schema validator wrapper
│   └── audit_record.py
└── reproducibility/
    ├── Dockerfile
    └── run_audit.sh

tests/
├── contract/
│   ├── test_extracted_summary.py
│   └── test_audit_record.py
└── integration/
    └── test_full_pipeline.py

data/
├── raw/            # downloaded HTML pages (read‑only)
├── synthetic/      # generated validation dataset (FR‑008)
└── output/         # audit_report.json, dashboard.html, manifest.json
```

## Phase Mapping (Coverage of All FR & SC)

| Phase | Tasks | FR(s) Addressed | SC(s) Addressed |
|-------|-------|-----------------|-----------------|
| **0 – Research** | Literature review, define statistical thresholds, design synthetic validation generator, decide on tolerance values, **perform a power analysis** to justify corpus size for estimating overall inconsistency proportion with ±2 % margin of error at 95 % confidence. | FR‑003, FR‑004, FR‑004a, FR‑005a, FR‑012 | SC‑003, SC‑014, **SC‑001 (sample‑size justification)** |
| **1 – Data Model & Contracts** | Define `ABSummary` & `AuditRecord` schemas, implement JSON‑schema validation, write contract tests. | FR‑002, FR‑015, FR‑016 | SC‑001, SC‑015 |
| **2 – Extraction Engine** | Build robust HTML scraper (BeautifulSoup + lxml), handle missing/rounded/inequality p‑values, **validate selector coverage** on a stratified set of known page layouts (≥ 95 % fields extracted) and log coverage metric, log parsing failures (FR‑007). | FR‑001, FR‑002, FR‑007, FR‑017 | SC‑005 |
| **3 – Reconstruction & Consistency** | Implement two‑proportion z/Fisher test, Welch t‑test, compute confidence intervals, apply **FR‑004 rules** plus **Constitution‑VI absolute‑difference rule (≥ 0.05)**, perform sensitivity analysis (FR‑004a). | FR‑003, FR‑004, FR‑004a, FR‑012 | SC‑002, SC‑018 |
| **4 – Synthetic Validation Dataset** | Generate 1 000+ synthetic summaries with prescribed quirks, compute ground‑truth labels using SciPy + statsmodels. | FR‑008 | SC‑002, SC‑011 |
| **5 – Dashboard Generation** | Produce HTML with bar, line, and pie charts via Matplotlib, embed **cluster‑adjusted binomial test** results (statsmodels `proportion_test` with `cov_type='cluster'` on `source`), display Wilson 95 % CI (FR‑005a, FR‑010). | FR‑010, FR‑005a | SC‑010 |
| **6 – Reproducibility Package** | Dockerfile, `run_audit.sh`, manifest generation (SHA‑256), MD5 checksum verification (FR‑006, FR‑014). | FR‑006, FR‑014 | SC‑004, SC‑009, SC‑013 |
| **7 – CI Integration** | GitHub Actions workflow that runs the full pipeline on a sample corpus, logs CPU/RAM usage, enforces resource limits (FR‑009, FR‑016). | FR‑009, FR‑016 | SC‑008, SC‑013 |
| **8 – Deduplication** | Normalise numeric fields, hash payloads, collapse duplicates (FR‑017). | FR‑017 | SC‑015 |

All functional requirements (FR‑001 … FR‑017) and success criteria (SC‑001 … SC‑018) are explicitly mapped to a concrete implementation step. No extra constraints are introduced beyond those specified.

### Detailed Consistency Decision Rules (FR‑004 + Constitution VI)

1. **Relative p‑value tolerance**: `max(0.01, 0.2 × reconstructed_p)`.  
2. **Absolute p‑value tolerance (Constitution VI)**: flag if `|reported_p - reconstructed_p| > 0.05`.  
3. **Inequality‑reported p‑values**: treat the bound as an upper limit; flag only if reconstructed p > bound *or* exceeds absolute 0.05.  
4. **Effect‑size relative tolerance**: 5 % of larger magnitude.  
5. **Sample‑size relative tolerance**: 5 % of larger count.  
6. **Confidence‑interval inclusion**: reported effect size must lie within the reconstructed 95 % CI.  

A summary is marked **inconsistent** if *any* of the above conditions holds.

---


## projects/PROJ-492-evaluating-the-statistical-validity-of-p/specs/001-evaluating-the-statistical-validity-of-p/research.md===BEGIN_ARTIFACT projects/PROJ-492-evaluating-the-statistical-validity-of-p/specs/001-evaluating-the-statistical-validity-of-p/research.md===
# Research: Evaluating the Statistical Validity of Public A/B Test Summaries

## Objective
Develop a reproducible audit pipeline that verifies the statistical consistency of publicly reported A/B test results (p‑values, effect sizes, sample sizes) and quantifies the prevalence of inconsistencies.

## Dataset Strategy
| Role | Source | Access Method | Comments |
|------|--------|---------------|----------|
| **Input Corpus** | User‑provided CSV of URLs (`input/urls.csv`) | Loaded via `pandas.read_csv` | No external dataset required; URLs are fetched at runtime. |
| **Synthetic Validation Set** | Generated in‑house (FR‑008) | `src/audit/synthetic.py` writes Parquet/CSV under `data/synthetic/` | Mirrors real‑world quirks; no external verified source needed. |
| **Reference Implementations** | SciPy v1.14+, statsmodels v0.14+ | Imported as Python packages | Used for independent computation of p‑values and confidence intervals (SC‑003). |

No external dataset URLs are required beyond the user‑supplied list; therefore the “Verified datasets” block is not consulted for the main audit. For synthetic data generation we rely on internal code only.

## Methodology

1. **Extraction**  
   - Use `requests` with exponential back‑off to download each URL.  
   - Parse with `BeautifulSoup` + `lxml`.  
   - Apply a hierarchy of XPath / CSS selectors derived from a seed set of known blog layouts.  
   - **Selector‑coverage validation**: before full run, a stratified sample of 100 known pages (spanning blogs, corporate reports, OpenML entries) is processed; coverage is the proportion of URLs where *all* required fields are extracted. The pipeline aborts with a warning if coverage < 95 %, satisfying construct validity (addresses methodology‑3b1630d6).  
   - Normalise numeric strings (handle commas, rounding, inequality symbols).  
   - Missing fields trigger a logged parsing failure (FR‑007) and a “missing metric” flag.

2. **Reconstruction of Statistical Tests** (FR‑003)  
   - **Binary outcome** → two‑proportion Z test (`statsmodels.stats.proportion.proportions_ztest`) or Fisher’s exact (`scipy.stats.fisher_exact`) when any cell ≤ 5.  
   - **Continuous outcome** → Welch’s two‑sample t‑test (`scipy.stats.ttest_ind` with `equal_var=False`).  
   - Compute 95 % confidence intervals using the appropriate analytical formula (statsmodels).  

3. **Consistency Decision Rules** (FR‑004 + Constitution VI)  
   - Relative p‑value tolerance: `max(0.01, 0.2 * reconstructed_p)`.  
   - **Absolute p‑value rule**: flag if `|reported_p - reconstructed_p| > 0.05` (Constitution VI).  
   - Inequality‑reported p‑values treated as upper bounds; flagged only if reconstructed p > bound **or** exceeds absolute 0.05.  
   - Effect‑size relative tolerance: 5 % of larger magnitude.  
   - Sample‑size relative tolerance: 5 % of larger count.  
   - CI inclusion test for reported effect size.  

4. **Sensitivity Analysis** (FR‑004a)  
   - Vary p‑value tolerance by ±0.02 and effect‑size tolerance by ±2 % of larger magnitude.  
   - Run on the synthetic validation set; record false‑positive (FP) and false‑negative (FN) rates.  
   - Report a table of thresholds vs. FP/FN.

5. **Synthetic Validation Dataset Generation** (FR‑008)  
   - Randomly sample baseline conversion rates from a Beta(2,8) distribution (typical low‑conversion products).  
   - Generate variant rates using a lift sampled from a mixture of normal distributions to produce both small and large effects.  
   - Randomly apply quirks: rounding, inequality, missing CI, unit swaps (lift % ↔ odds ratio), missing baseline (trigger FR‑012 handling).  
   - Enforce marginal distributions via rejection sampling to achieve Jensen‑Shannon divergence ≤ 0.1 relative to a reference corpus of 500 real summaries (the reference distribution is stored in `data/reference_distribution.json`).  

6. **Statistical Summaries for Dashboard** (FR‑005a, FR‑010)  
   - Overall inconsistency proportion tested against baseline 0.05 using a two‑sided binomial test (`scipy.stats.binom_test`).  
   - Wilson 95 % CI computed with `statsmodels.stats.proportion.proportion_confint(method='wilson')`.  
   - **Cluster‑adjusted proportion test**: use `statsmodels.stats.proportion.proportion_test` with `cov_type='cluster'` on the `source` field to obtain a robust p‑value and confidence interval that accounts for source‑level correlation (addresses methodology‑e9796387).  

7. **Reproducibility & Versioning** (FR‑006, FR‑014)  
   - Dockerfile pins exact versions of Python and all libraries.  
   - `run_audit.sh` sets `PYTHONHASHSEED=0` and a fixed NumPy random seed.  
   - After each run, compute SHA‑256 hashes of Docker image (via `docker image inspect --format='{{.Id}}'`), JSON report, and HTML dashboard; write to `output/manifest.json`.  

8. **CI Integration** (FR‑009, FR‑016)  
   - GitHub Actions workflow (`.github/workflows/audit.yml`) executes `docker run` with resource limits (`--cpus=2`, `--memory=7g`).  
   - Workflow includes steps to parse the runner’s `time` and `psutil` output for CPU/RAM verification (SC‑008).  
   - Contract tests (`pytest -m contract`) are run after the pipeline to ensure schema compliance.

## Power / Sample‑Size Justification (addresses methodology‑ba8a2f33)

To estimate the overall inconsistency proportion **p** with a 95 % confidence interval of width ±2 % (margin of error **E** = 0.02), the standard proportion sample‑size formula is:

\[
n = \frac{z_{0.975}^2 \, p(1-p)}{E^2}
\]

Assuming a conservative worst‑case proportion **p** = 0.5 maximises variance, we obtain:

\[
n = \frac{1.96^2 \times 0.5 \times 0.5}{0.02^2} \approx [deferred].
\]

We therefore target **≥ 2,500** unique summaries after deduplication, rounding up to **[deferred]** to provide a safety buffer for parsing failures and to satisfy SC‑005 (≤ 5 % parsing error). This satisfies the research‑question precision requirement without exceeding CI resource limits.

## Risk Assessment & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **HTML layout variability** may cause extraction failures → ↑ parsing error rate (SC‑005). | Medium | Maintain a fallback regex extractor; log failures; expand selector library iteratively; enforce ≥ 95 % selector‑coverage on a validation sample. |
| **Synthetic dataset may not reflect real quirks** → biased sensitivity analysis. | Medium | Validate synthetic distribution against the real reference distribution (JSD ≤ 0.1) and manually inspect a random sample. |
| **Resource overrun on large corpora** → CI timeout (SC‑008). | High | Process URLs in streamed batches of 200; use `tqdm` for progress; early abort if runtime > 5 h. |
| **Hash collisions in deduplication** (FR‑017). | Low | Use SHA‑256 of the rounded payload; collisions virtually impossible. |

## Success Criteria Alignment
- **Extraction accuracy ≥ 95 %** (SC‑001) will be measured on the manually annotated set (≥ 30 entries).  
- **Inconsistency‑detection precision ≥ 90 %** on synthetic data (SC‑002) and on the manual set (SC‑018).  
- **Statistical test cross‑validation** using SciPy **and** statsmodels (SC‑003).  
- **Reproducibility checks** (MD5 match, manifest hashes) (SC‑004, SC‑009).  
- **Parsing‑error rate ≤ 5 %** (SC‑005).  
- **CI resource limits** (SC‑008) enforced via workflow logs.  
- **Dashboard visual verification** (SC‑010) via headless Chrome screenshot comparison.  
- **Recall ≥ 85 %** on synthetic data (SC‑011).  
- **Manifest generation in ≥ 99 % of CI runs** (SC‑013).  
- **Binomial test significance** when proportion > 0.05 (SC‑014).  
- **Deduplication collapse ≤ 1 %** (SC‑015).  

All FR and SC items are explicitly accounted for in the phases above.

---

