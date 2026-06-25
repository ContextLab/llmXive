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
   - Apply a hierarchy of XPath / CSS selectors derived from a small seed set of known blog layouts.  
   - Normalise numeric strings (handle commas, rounding, inequality symbols).  
   - Missing fields trigger a logged parsing failure (FR‑007) and a “missing metric” flag.

2. **Reconstruction of Statistical Tests** (FR‑003)  
   - **Binary outcome** → two‑proportion Z test (`statsmodels.stats.proportion.proportions_ztest`) or Fisher’s exact (`scipy.stats.fisher_exact`) when any cell ≤ 5.  
   - **Continuous outcome** → Welch’s two‑sample t‑test (`scipy.stats.ttest_ind` with `equal_var=False`).  
   - Compute 95 % confidence intervals using the appropriate analytical formula (statsmodels).  

3. **Consistency Decision Rules** (FR‑004)  
   - Absolute p‑value difference tolerance: `max(0.01, 0.2 * reconstructed_p)`.  
   - Inequality‑reported p‑values treated as upper bounds.  
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
   - Enforce marginal distributions via rejection sampling to achieve Jensen‑Shannon divergence ≤ 0.1 relative to a reference corpus of a substantial collection of real summaries (the reference distribution is stored in `data/reference_distribution.json`).  

6. **Statistical Summaries for Dashboard** (FR‑005a, FR‑010)  
   - Overall inconsistency proportion tested against baseline 0.05 using a two‑sided binomial test (`scipy.stats.binom_test`).  
   - Wilson 95 % CI computed with `statsmodels.stats.proportion.proportion_confint(method='wilson')`.  
   - Cluster‑adjusted proportion test (e.g., using `statsmodels.stats.proportion.proportion_test` with cluster robust covariance) – implemented only if source grouping is non‑trivial.

7. **Reproducibility & Versioning** (FR‑006, FR‑014)  
   - Dockerfile pins exact versions of Python and all libraries.  
   - `run_audit.sh` sets `PYTHONHASHSEED=0` and a fixed NumPy random seed.  
   - After each run, compute SHA‑256 hashes of Docker image (via `docker image inspect --format='{{.Id}}'`), JSON report, and HTML dashboard; write to `output/manifest.json`.  

8. **CI Integration** (FR‑009, FR‑016)  
   - GitHub Actions workflow (`.github/workflows/audit.yml`) executes `docker run` with resource limits (`--cpus=2`, `--memory=7g`).  
   - Workflow includes steps to parse the runner’s `time` and `psutil` output for CPU/RAM verification (SC‑008).  
   - Contract tests (`pytest -m contract`) are run after the pipeline to ensure schema compliance.

## Risk Assessment & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **HTML layout variability** may cause extraction failures → ↑ parsing error rate (SC‑005). | Medium | Maintain a fallback regex extractor; log failures; expand selector library iteratively. |
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

All FR and SC items are accounted for in the phases above.

---
