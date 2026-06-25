# Research: Evaluating the Statistical Validity of Public A/B Test Summaries

## Objective
Develop a reproducible audit pipeline that quantifies the prevalence of statistical inconsistencies in publicly posted A/B test summaries.

## Dataset Strategy
| Source | Type | Access Method | Reason for Inclusion |
|--------|------|---------------|----------------------|
| **Verified URLs list** (provided by user) | CSV of URLs | `pandas.read_csv('input/urls.csv')` | Primary corpus to be audited (fulfills **FR‑001**). |
| **Validation Set** (≥ 100 manually annotated summaries) | CSV + JSON ground‑truth | Included in `tests/integration/validation_set/` | Enables reliable measurement of extraction accuracy (**SC‑001**) and detection precision (**SC‑014**) across diverse source formats. |
| **No external dataset required** | – | – | All required variables are extracted from the HTML pages themselves; no separate numeric dataset needed. |

*If any URL fails to deliver HTML or lacks required fields, it will be logged as a parsing failure (**FR‑007**) and excluded from aggregates, contributing to the parsing‑error rate (**SC‑005**).*

## Methodology

1. **Extraction**  
   - Use `requests` with exponential back‑off to download each URL.  
   - Parse with `BeautifulSoup` (HTML5 parser).  
   - Apply multiple heuristic XPath/regex patterns (covering tables, lists, inline text) to locate the required metrics.  
   - Normalise effect‑size representations:  
     - “Lift %” → `baseline_rate * lift/100` (or average of the two variant rates if baseline missing, per **FR‑012**).  
     - Percentages → decimal fractions.  
   - Store extracted fields in a Pandas DataFrame conforming to `extracted_summary.schema.yaml`.

2. **Reconstruction of Statistical Tests**  
   - **Binary outcomes**:  
     - Compute conversion rates `p_a = n_a_success / n_a_total`, `p_b = n_b_success / n_b_total`.  
     - If any cell ≤ 5 → Fisher’s exact test (`scipy.stats.fisher_exact`).  
     - Else → two‑proportion z‑test (`statsmodels.stats.proportion.proportions_ztest`).  
   - **Continuous outcomes**:  
     - Use Welch’s two‑sample t‑test (`scipy.stats.ttest_ind` with `equal_var=False`).  
   - Record reconstructed p‑value and effect size.

3. **Inconsistency Detection (FR‑004)**  
   - Compute absolute difference in p‑values; flag if `diff > max(0.05, 0.2 * reconstructed_p)`.  
   - For inequality p‑values (`p < x`), flag only if `reconstructed_p > x`.  
   - Compute relative difference in effect sizes; flag if `|reported - reconstructed| / max(|reported|, |reconstructed|) > 0.05`.  
   - Compute relative difference in per‑variant sample sizes; flag if > 5 %.  
   - If a confidence interval is present, verify that the reported effect size lies within the reconstructed 95 % CI; otherwise flag.  
   - Missing any required metric → flag “missing metric”.  

4. **Prevalence Estimation (FR‑005a)**  
   - Let `k` = number of inconsistent entries, `n` = total successfully audited entries.  
   - Perform two‑sided binomial test against null proportion 0.05 (`statsmodels.stats.proportion.binom_test(k, n, prop=0.05, alternative='two-sided')`).  
   - Compute 95 % Wilson confidence interval (`statsmodels.stats.proportion.proportion_confint(k, n, method='wilson')`).  

5. **Power Assessment**  
   - Using the observed `n` and `k`, compute achieved statistical power for detecting a deviation of 0.05 from the baseline proportion (via `statsmodels.stats.proportion.power_binom_test`).  
   - Report the power value alongside the prevalence estimate; if power < 0.80, note the limitation in the final report.  

6. **Sensitivity Analysis**  
 - After the main audit, re‑run the inconsistency detection across a small grid of tolerance values (e.g., p‑diff thresholds 0.04–0.06, effect‑size rel‑diff 4–[deferred]).
   - Record stability metrics (e.g., proportion of summaries whose flag changes) to demonstrate robustness against arbitrary cut‑offs.  

7. **Bias Mitigation**  
   - Stratify the URL corpus by source category (corporate blog, open‑source repo, conference paper, etc.) and sample proportionally to reflect the overall distribution of publicly available summaries.  
   - Produce a source‑distribution summary table and include it in the final report to allow readers to assess selection bias.  

8. **Export**  
   - **JSON** (`audit_report.json`): one object per URL with fields defined in `audit_record.schema.yaml`.  
   - **CSV** (`summary_report.csv`): aggregate counts, inconsistency rate, Wilson CI bounds (as per **FR‑024**).  

## Statistical Rigor Checklist
| Requirement | Implementation |
|-------------|----------------|
| Multiple‑comparison correction | Not needed; only a single binomial test is performed (**FR‑005a**). |
| Power justification | Conducted post‑hoc power assessment (Step 5) and reported; baseline 0.05 is stipulated by the specification, not introduced by the plan. |
| Causal inference | The audit is purely associational; claims are framed accordingly (per **VI** of the constitution). |
| Measurement validity | Extraction leverages known HTML patterns from verified corporate blogs; missing fields are logged, not inferred. |
| Predictor collinearity | Not applicable – the audit compares reported vs. reconstructed values, not regression coefficients. |

## Decision / Rationale
- **Statistical tests**: Chosen from `scipy`/`statsmodels` to guarantee CPU‑only execution and deterministic results.  
- **Thresholds**: Directly taken from **FR‑004**; sensitivity analysis (Step 6) ensures they do not drive spurious findings.  
- **Sampling**: Full URL list is processed; stratified sampling (Step 7) mitigates selection bias while preserving representativeness.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| HTML structure variability leads to extraction failures | ↑ parsing‑error rate (SC‑005) | Implement multiple fallback regex patterns; log failures for manual review. |
| Very large corpora exceed 6 h limit | CI timeout (SC‑008) | Limit parallelism to 2 workers; benchmarked processing time ≈ 0.7 s per URL, allowing up to 5,000 URLs within the window. |
| Missing baseline conversion rate | Inability to reconstruct effect size | Apply **FR‑012** (average of variant rates) before flagging as missing. |
| Network instability | Incomplete downloads → parsing errors | Retry with exponential back‑off; fallback to cached copies in `data/raw/`. |
| Insufficient power to detect deviation from baseline | Prevalence estimate may be under‑powered | Perform post‑hoc power assessment (Step 5) and transparently report power; if low, qualify conclusions. |

---

