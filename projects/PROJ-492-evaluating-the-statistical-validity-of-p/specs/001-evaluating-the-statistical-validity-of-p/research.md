# Research: Evaluating the Statistical Validity of Public A/B Test Summaries  

## Dataset Strategy
| Source | Access Method | Notes |
|--------|---------------|-------|
| User‑provided CSV of URLs | `pandas.read_csv` | No verified external dataset exists for the target corpus (see “Verified datasets” block). The pipeline expects a column `url`. |
| Synthetic validation set (FR‑008) | Programmatic generation (Python) | Stored as `data/synthetic_validation.csv`. No external URL required. |

> **Important**: Because the spec does not provide a verified public dataset of A/B test summaries, the audit relies on a user‑supplied list of URLs. The plan does **not** fabricate any dataset URLs.

## Methodology
1. **Ingestion & Integrity** – Download each URL, compute SHA‑256, and record HTTP status. Failures are logged (`parsing_errors.log`) and counted toward SC‑005.  
2. **Extraction** – Use `BeautifulSoup` to locate HTML elements that contain the required metrics. Regex patterns capture numeric values; confidence intervals are parsed as “lower, upper”.  
   - **Metric‑unit detection**: The extractor scans for keywords (“lift %”, “odds ratio”, “relative risk”, “mean difference”).  
   - **Conversion rules**:  
     * **Lift %** → absolute difference = baseline × lift / 100 (baseline inferred from reported control conversion rate).  
     * **Odds ratio / Relative risk** → converted to absolute risk difference using the reported control conversion rate.  
     * Unsupported or ambiguous units → flagged as “missing metric”.  
   - Missing fields trigger the “missing metric” flag (edge case).  
3. **Statistical Reconstruction** –  
   - **Binary outcomes**: Two‑proportion z‑test (`stats.proportions_ztest`). If any cell ≤ 5, fallback to Fisher’s exact (`stats.fisher_exact`).  
   - **Continuous outcomes**: Welch’s two‑sample t‑test (`stats.ttest_ind` with `equal_var=False`).  
   - All calculations are performed with **SciPy ≥ 1.14**. Parallel calculations of the same tests are performed with **statsmodels.stats** to obtain independent p‑values for cross‑validation (fulfills SC‑003).  
4. **Consistency Evaluation (FR‑004)** – Apply the four tolerance rules; store absolute differences, relative differences, and categorical flags (`inconsistent`, `missing_metric`, `size_mismatch`). Thresholds (0.05 for p‑value, 5 % for effect size and sample size) are justified in the **Threshold Rationale** subsection of the plan and can be overridden via the `--thresholds` CLI flag for sensitivity analysis.  
5. **Aggregate Analyses (FR‑005)** –  
   - **Overall inconsistency proportion** `π̂` is estimated via a **mixed‑effects logistic regression** with `source_domain` as a random effect (Statsmodels `MixedLM`).  
   - A **cluster‑robust binomial test** (source as clustering factor) tests H₀ : π = 0.05 using `statsmodels.stats.proportion.proportion_ztest` with robust variance.  
   - **Wilson 95 % CI** is computed with `stats.proportion_confint` (`method='wilson'`).  
   - **Power analysis**: Using the observed number of audited summaries, we compute achieved power to detect a deviation of 0.10 from the null (π = 0.05) via `statsmodels.stats.power.GofChisquarePower`. Power is reported; if < 0.80, a warning is emitted suggesting a larger corpus.  
   - **Source‑wise rates**: For each source with ≥ 10 summaries, compute rate and a **Fisher’s exact test** comparing that subgroup’s inconsistency count to the overall count. Additionally, the mixed‑effects model provides adjusted source‑level estimates.  
   - **Temporal trends**: Group by month, compute month‑wise proportions, and run a **cluster‑robust proportion‑difference test** (source‑clustered) at α = 0.05.  
6. **Dashboard (FR‑010)** – Generate interactive Plotly charts embedded in a Jinja2 HTML template. Include a table of statistical test results (binomial‑test p‑value, Wilson CI, source‑wise Fisher’s p‑values, mixed‑effects estimates). The HTML is validated with a headless Chrome (via `playwright`) to ensure no console errors (SC‑010).  
7. **Reproducibility (FR‑006)** – Dockerfile pins Python 3.11 and all dependency versions. The pipeline writes MD5 checksums for each output artifact; identical checksums on re‑run confirm SC‑004 and SC‑009.  
8. **CI Execution (FR‑009)** – GitHub Actions workflow (`.github/workflows/ci.yml`) runs the pipeline on a representative sample of URLs, captures runtime (`time`), memory (`psutil`), and asserts limits (SC‑008). Parsing‑error rate is logged and must stay ≤ 5 % (SC‑005).  

## Decision / Rationale
- **CPU‑only**: All statistical tests are analytical; no machine‑learning models are required, guaranteeing compliance with FR‑009 and the free‑tier CI constraints.  
- **Synthetic Validation**: Because no verified corpus exists for ground truth, we generate a synthetic dataset (FR‑008) that mirrors real‑world reporting quirks (rounded p‑values, inequality bounds, missing CIs, mixed effect‑size units, intentional size mismatches). This enables a realistic assessment of detector precision/recall (SC‑002, SC‑011).  
- **Dual‑library verification**: Using both SciPy and Statsmodels eliminates circular validation for p‑values (SC‑003).  
- **Threshold justification & sensitivity**: Thresholds align with conventional α = 0.05 significance and typical reporting variability; the `--thresholds` flag allows users to explore alternative cut‑offs and observe impact on prevalence estimates.  
- **Hierarchical aggregation**: Treating `source_domain` as a random effect and using cluster‑robust variance respects intra‑source correlation, addressing independence violations and providing more reliable inference (SC‑003, scientific soundness).  

## References
- SciPy documentation (v1.14) – https://scipy.org/  
- Statsmodels documentation (v0.14) – https://www.statsmodels.org/  
- Plotly Python API – https://plotly.com/python/  
- Jinja2 templating – https://jinja.palletsprojects.com/  
- Playwright Python – https://playwright.dev/python/  

---

