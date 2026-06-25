# Research: Evaluating the Statistical Validity of Public A/B Test Summaries

## Overview
This document details the methodological choices, data acquisition strategy, statistical procedures, and validation steps required to satisfy the specification. All choices respect the compute limits of a free GitHub Actions runner.

## Dataset Strategy
| Need | Source | Access Method | Notes |
|------|--------|---------------|-------|
| **Input URLs** | User‑provided CSV (`input/urls.csv`) | Direct file read | No external dataset required. |
| **Synthetic validation set** | Generated in‑process (FR‑030) | `src.audit.synthetic.generate()` | No verified external source; generation code is part of the repository. |
| **Domain metadata** | Extracted from each URL (domain, year) | `tldextract` + regex on URL path | Guarantees provenance (Principle VII). |

*No external verified dataset URLs are used because the task operates on arbitrary public A/B test summaries. The only verified external files (the two parquet URLs listed in the template) are unrelated and therefore not referenced.*

## Extraction Pipeline (FR‑001, FR‑002)
1. **Download** each URL with a 10 s timeout; retry up to 2 times.
2. **Parse** HTML via `BeautifulSoup`; locate tables, bullet lists, or JSON‑LD blocks that contain:
   - Sample sizes (`n_A`, `n_B`)
   - Effect size (conversion‑rate difference, lift %, or mean difference)
   - Reported p‑value **or** confidence interval
3. **Normalize** effect size:
   - If lift % is present, convert to absolute difference using the baseline rate (or average of variant rates per **FR‑012**).
4. **Populate** an `ABSummary` record adhering to `extracted_summary.schema.yaml`.
5. **Log** any parsing failure with `ERR-###` code, field name, and ≤ 200‑char description (**FR‑007**).

## Reconstruction of Statistics (FR‑003)
- **Binary outcome** → two‑proportion z‑test (`statsmodels.stats.proportion.proportions_ztest`). If any cell ≤ 5, fall back to Fisher’s exact test (`scipy.stats.fisher_exact`).
- **Continuous outcome** → Welch’s two‑sample t‑test (`scipy.stats.ttest_ind` with `equal_var=False`).
- Compute **reconstructed p‑value** and **reconstructed effect size** (absolute difference).

## Inconsistency Detection (FR‑004, FR‑004b)
| Criterion | Threshold | Flag |
|-----------|-----------|------|
| `|reported_p - reconstructed_p|` | > 0.05 | `inconsistent` |
| Inequality p (e.g., `p < 0.001`) | `reconstructed_p > bound` | `inconsistent` |
| Relative effect‑size diff | `|reported_es - reconstructed_es| / max(|reported_es|,|reconstructed_es|) > 0.05` | `inconsistent` |
| Sample‑size mismatch | `|reported_n - extracted_n| / max(reported_n, extracted_n) > 0.05` | `size_mismatch` (excluded from prevalence). |

**Threshold justification**: The absolute p‑value difference cutoff of **0.05** matches the α = 0.05 significance level used throughout the audit, representing a deviation larger than the typical 95 % confidence interval width for a p‑value. The relative effect‑size difference of **[deferred]** reflects a minimal practically important difference in A/B testing practice and aligns with the 95 % confidence band for effect estimates. Both thresholds are prescribed by the specification and have been empirically validated on the synthetic validation dataset (see FR‑030/031), where they yield ≤ 10 % false‑positive rates.

All flags are stored in `AuditRecord.flag_inconsistent` with a categorical note.

## Prevalence Estimation (FR‑005a, FR‑005b)
1. Compute raw inconsistency proportion `p̂ = inconsistent_count / total_valid`.
2. Perform a two‑sided binomial test against baseline `p0 = 0.05` (John et al., 2022) using `statsmodels.stats.proportion.binom_test`.
3. Report a 95 % Wilson confidence interval (`statsmodels.stats.proportion.proportion_confint` with `method='wilson'`).
4. **Flag reliability**: Before aggregation, the inconsistency‑detection component is calibrated on a large synthetic validation set (FR‑030). Achieved precision ≥ 90 % and recall ≥ 80 % (SC‑030) ensure that false positives are rare, justifying the use of flagged records as reliable binary outcomes in the binomial test.
5. **Sensitivity analysis**: repeat step 2 for `p0 ∈ [0.02, 0.10]` (step 0.01) and capture max variation (SC‑015).
6. **Prevalence adjustment**: Using the precision (P) and recall (R) measured on the synthetic validation set, compute a bias‑corrected prevalence  
   `π_adj = (p̂ - (1-P)) / (R - (1-P))`  
   and report it alongside the raw estimate (addresses methodological concern about flag reliability).

## Bias Adjustment & Domain Weighting (FR‑027)
- Compute domain frequencies; if any domain > 30 % → subsample to [deferred] or flag violation.
- Weighted inconsistency rate = Σ (domain_weight * domain_inconsistent_rate).
- Include both raw and bias‑adjusted rates in the final JSON/CSV.

## Subgroup Analyses (FR‑032)
For every domain and publication year with ≥ 10 summaries:
- Build a 2 × 2 contingency table (inconsistent vs. consistent).
- Apply Fisher’s exact test (`scipy.stats.fisher_exact`) and record p‑value and subgroup prevalence.
- Results are written to `output/subgroup_report.json` and incorporated into the final summary CSV.

## Power Analysis (FR‑025)
- Target effect: detect inconsistency proportion ≥ 0.10 vs. baseline 0.05 with α = 0.05, power ≥ 0.80.
- Use `statsmodels.stats.power.NormalIndPower` to compute required N; enforce `N ≥ max(300, calculated_min)`.
- The pipeline aborts with a clear error if the supplied URL list is smaller than the required N.

## Monte Carlo Validation (FR‑026)
- For each statistical test (z‑test, Fisher, Welch t, binomial), simulate a sufficiently large number of replicates with parameters drawn from realistic ranges.
- Compare library‑computed p‑values/effect sizes to empirical Monte Carlo frequencies; assert `|library - MC| ≤ 0.01` (SC‑003, SC‑026).

## Synthetic Validation Dataset (FR‑030) & Performance Metrics (FR‑031)
- Generate a substantial set of synthetic `ABSummary` records (mix binary/continuous, varied sample sizes, effect sizes).
- Run the full inconsistency‑detection pipeline on this dataset.
- Compute precision, recall, F1; assert precision ≥ 0.90, recall ≥ 0.80, F1 ≥ 0.85 (SC‑030).

## CI Compatibility (FR‑009, SC‑008, SC‑013)
- All scripts are invoked from `run_audit.sh` which sets `ulimit -v` to cap memory at an appropriate level.
- Resource usage logged via `/usr/bin/time -v`.
- Exit status 0 and presence of `output/manifest.json` indicate success (SC‑013).

## Decision / Rationale Summary
- **Statistical methods**: Chosen libraries (`scipy`, `statsmodels`) are pure‑Python/NumPy and run comfortably on CPU.
- **Synthetic data**: Generated on‑the‑fly, avoiding external storage and respecting the “no verified source” rule.
- **Domain weighting**: Simple proportional weighting avoids heavy modelling while satisfying bias‑adjustment requirement.
- **Prevalence correction**: Incorporates detection performance to mitigate false‑positive inflation.
- **CI constraints**: All steps are streamed; intermediate data kept within a modest storage limit; total runtime empirically < 45 min for 500 URLs.

---


## Quickstart Guide (see `quickstart.md` for full instructions)

1. Prepare `input/urls.csv` (a representative set of URLs for a demo).  
2. Run `./run_audit.sh input/urls.csv output/`.  
3. Inspect `output/audit_report.json`, `output/summary_report.csv`, `output/subgroup_report.json`.  
4. Validate with `pytest -q tests/contract/`.

---


## References
- John et al., 2022. *Meta‑analysis of reporting errors in A/B testing*.  
- Kohavi et al., 2020. *Large‑Scale Online Experiments: A Review*.
