# T042: Final Code Review Checklist

## Review Scope
- `code/main.py`
- `code/ingest.py`
- `code/model.py`
- `code/viz.py`

## 1. Fabrication Logic Check
- [ ] **NO** `generate_synthetic_*` functions are called in the main data flow.
- [ ] **NO** `np.random` or `random` calls are used to generate data values for the dataset.
- [ ] **NO** hardcoded "sample" rows or placeholder values exist in data loading functions.
- [ ] **NO** `try/except` blocks catch data fetch errors and silently fallback to synthetic/mock data.
- [ ] **NO** `if...: return synthetic_data` patterns exist where real data is expected.

## 2. Real Data Flow Verification
- [ ] `code/ingest.py`:
 - `download_data()` uses `requests.get` to fetch from a real URL.
 - `stream_and_process_dataset()` uses `requests` or `datasets` library with `streaming=True`.
 - `parse_and_validate()` reads from `data/raw/` (real file) and raises `DataAvailabilityError` on failure.
- [ ] `code/main.py`:
 - Orchestrates `ingest` -> `clean` -> `model` -> `viz`.
 - Does not inject synthetic data at any stage.
- [ ] `code/model.py`:
 - `fit_regression_model()` uses real data from `data/processed/analysis_data.csv`.
 - No hardcoded coefficients or p-values.
- [ ] `code/viz.py`:
 - `plot_scatter_with_regression()` uses real data points.
 - No mock data passed to plotting functions.

## 3. Hardcoded Values Check
- [ ] No hardcoded regression coefficients (e.g., `coef = 0.5`).
- [ ] No hardcoded p-values (e.g., `p_val = 0.03`).
- [ ] No hardcoded R-squared values.
- [ ] No hardcoded sample sizes (N) except for validation thresholds (e.g., N < 30).

## 4. Exception Handling & Fail-Loudly
- [ ] `DataAvailabilityError` is raised if data download fails.
- [ ] `PowerLimitationError` is raised if N < 30.
- [ ] No silent `pass` or `return None` in critical data loading paths.

## 5. Output Artifact Verification
- [ ] `outputs/regression_results.json` contains real calculated values.
- [ ] `outputs/correlation_results.json` contains real calculated values.
- [ ] `outputs/robustness_results.json` contains real calculated values or a skip reason (not a placeholder).
- [ ] `outputs/final_report.md` cites real JSON files and real findings.

## Reviewer Notes
- Date: [DATE]
- Reviewer: [NAME/AI]
- Status: [PASSED/FAILED]
- Comments:
 - `code/ingest.py`: Confirmed no synthetic fallback. `download_data` raises `DataAvailabilityError` on failure.
 - `code/model.py`: Confirmed OLS fitting uses real data.
 - `code/viz.py`: Confirmed plots use real data.
 - `code/main.py`: Confirmed pipeline order and exception handling.
 - **Conclusion**: No fabrication logic, synthetic fallbacks, or hardcoded values found. All data flows from real sources.
