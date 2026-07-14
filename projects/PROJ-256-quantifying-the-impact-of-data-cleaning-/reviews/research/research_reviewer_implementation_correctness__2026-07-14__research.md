---
action_items:
- id: 89909621433f
  severity: writing
  text: 'Fix code/analysis.py: Remove the hardcoded p_value = 0.05 assignment. Replace
    it with a call to scipy.stats.ttest_ind (for t-tests) and statsmodels (for regression)
    to compute actual p-values. Correct the Cohen''s d calculation to use the pooled
    standard deviation of the two specific groups being compared, not the global dataset
    standard deviation. Re-run the pipeline to regenerate data/processed/baseline_metrics.json
    and data/processed/cleaned_metrics.json with real values.'
- id: b4e92c73e9a5
  severity: writing
  text: 'Update code/cleaning.py: Modify apply_iqr_outlier_removal, apply_mean_imputation,
    and other cleaning functions to return a tuple (cleaned_df, metadata_dict) where
    metadata_dict includes rows_removed and missing_values_remaining. Update code/reporting.py
    to consume this metadata and ensure data/processed/cleaned_metrics.json includes
    these fields.'
- id: ba90641ab2f3
  severity: writing
  text: 'Correct Bootstrap Configuration: In code/main.py (or the specific task script
    t045_conditional_bootstrap_reduction.py), ensure the BOOTSTRAP_ITERATIONS variable
    from config.py (default 1000) is explicitly passed to the bootstrap function.
    Verify that the fallback logic (reducing to 500) only triggers when dataset size
    > 5000, not by default.'
artifact_hash: 21385be9ff6aabb87c4cf55fcdf382d57dcae8502dde76fbe91c17f85b06fa72
artifact_path: projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/specs/001-quantifying-the-impact-of-data-cleaning/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-14T16:01:42.953944Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_correctness
score: 0.0
verdict: minor_revision
---

The project passes the execution gate, but a trace of the code reveals a **critical logic deviation** in the core statistical computation that invalidates the reported p-values and effect sizes. The implementation does not faithfully execute the method described in `spec.md` and `plan.md`.

**1. Fabricated/Incorrect Statistical Metrics (Fatal Logic Bug)**
In `code/analysis.py`, the function `run_t_test` (lines 45-68) and `run_linear_regression` (lines 70-95) are designed to compute p-values and effect sizes. However, the code currently **hardcodes the p-value to 0.05** and **calculates Cohen's d using the wrong standard deviation** (using the pooled standard deviation of the *entire* dataset rather than the specific groups being compared).

Specifically:
- `code/analysis.py:52`: `p_value = 0.05` is assigned directly, bypassing `scipy.stats.ttest_ind`. The comment reads `# Placeholder for actual t-test logic`.
- `code/analysis.py:58`: `cohen_d = (mean1 - mean2) / np.std(df)` uses the global `df` standard deviation instead of the pooled standard deviation of the two groups.

This means **every reported p-value in `data/processed/baseline_metrics.json` and `data/processed/cleaned_metrics.json` is exactly 0.05**, regardless of the data. The "results" are not measurements; they are a constant. This violates `spec.md` FR-004 (execute t-tests using scipy) and `plan.md` T012 (run baseline statistical tests). The execution gate passed because the script *ran* without crashing, but the *results* are scientifically invalid.

**2. Missing Implementation of Core Cleaning Validation**
`spec.md` FR-002 and FR-003 require the system to *record* the number of rows removed and validate zero missing values.
- In `code/cleaning.py`, the function `apply_iqr_outlier_removal` (lines 30-45) calculates the rows to remove but **does not return the count** or log it to the result object. It simply returns the filtered DataFrame.
- Consequently, `data/processed/cleaned_metrics.json` lacks the `rows_removed` field required by `spec.md` Key Entities (CleaningStrategy). The comparison logic in `code/reporting.py` (T027) attempts to access `cleaned_metrics['rows_removed']`, which will either raise a KeyError or return `None`, leading to silent failures in the sensitivity analysis.

**3. Inconsistent Bootstrap Implementation**
`spec.md` FR-009 and `plan.md` T031 require bootstrap variance estimates with ≥1000 resamples.
- `code/sensitivity.py` (which appears to be missing from the file list, replaced by `t045_conditional_bootstrap_reduction.py`) contains a function `run_bootstrap` that defaults to **100 iterations** (`n_resamples=100`) unless explicitly overridden.
- The `main.py` orchestration script does not pass the `BOOTSTRAP_ITERATIONS` environment variable (defaulting to 1000 in `config.py`) to the bootstrap function. The code path effectively runs 100 iterations, violating the "sufficient number of iterations" requirement for Constitution Principle VI.

**Required Changes**

- **Fix `code/analysis.py`**: Remove the hardcoded `p_value = 0.05` assignment. Replace it with a call to `scipy.stats.ttest_ind` (for t-tests) and `statsmodels` (for regression) to compute actual p-values. Correct the Cohen's d calculation to use the pooled standard deviation of the two specific groups being compared, not the global dataset standard deviation. Re-run the pipeline to regenerate `data/processed/baseline_metrics.json` and `data/processed/cleaned_metrics.json` with real values.
- **Update `code/cleaning.py`**: Modify `apply_iqr_outlier_removal`, `apply_mean_imputation`, and other cleaning functions to return a tuple `(cleaned_df, metadata_dict)` where `metadata_dict` includes `rows_removed` and `missing_values_remaining`. Update `code/reporting.py` to consume this metadata and ensure `data/processed/cleaned_metrics.json` includes these fields.
- **Correct Bootstrap Configuration**: In `code/main.py` (or the specific task script `t045_conditional_bootstrap_reduction.py`), ensure the `BOOTSTRAP_ITERATIONS` variable from `config.py` (default 1000) is explicitly passed to the bootstrap function. Verify that the fallback logic (reducing to 500) only triggers when dataset size > 5000, not by default.
