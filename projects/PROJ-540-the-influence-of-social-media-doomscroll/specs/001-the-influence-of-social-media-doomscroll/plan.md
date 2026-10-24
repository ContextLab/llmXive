# Implementation Plan: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

**Branch**: `001-doomscrolling-anxiety` | **Date**: 2026-10-23 | **Spec**: `specs/001-doomscrolling-anxiety/spec.md`  
**Input**: Feature specification from `/specs/001-doomscrolling-anxiety/spec.md`

## Summary
The pipeline will execute the following ordered phases, each mapped to a unique task ID:

1. **Power Analysis** – compute the minimum required sample size to detect the effect‑size thresholds defined in SC‑001 (β ≥ 0.10 or f² ≥ 0.02) with α = 0.05, power = 0.80, and the planned number of predictors (5‑7). Implemented via `statsmodels.stats.power.FTestPower`. This a‑priori analysis runs **before** any data cleaning; if the projected N after cleaning would be below this threshold, the run halts with a clear “Insufficient Power” error. (**Task T012_power_analysis**)

2. **Ingestion & Checksum** – download the three verified parquet URLs, compute SHA‑256 checksums, and store them under `data/raw/`. (**Task T010_download**)

3. **Schema Validation** – validate that each file contains the required columns (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement`). If none of the files provide a complete schema, the pipeline halts with `HALTED_NO_VALID_DATASET` (FR‑001 edge case). (**Task T011_schema_validation**)

4. **Load Variable Metadata** – read `variable_metadata.csv` to obtain `instrument_identifier` and `measurement_timepoint` for each anxiety variable. This enables the distinctness check required by FR‑003. (**Task T013_load_metadata**)

5. **Listwise Deletion & Sample‑Size Check** – perform listwise deletion on rows missing `news_exposure_freq` or `anxiety_score`. Enforce N ≥ 30 hard stop; emit a “Low Power” warning if 30 ≤ N < 100 (per FR‑002). (**Task T014_cleaning**)

6. **Missing‑Data Diagnostics & Sensitivity** – run Little’s MCAR test.  
   - If MCAR (p ≥ 0.05): proceed.  
   - If not MCAR (p < 0.05): add binary missingness indicator variables for each predictor, log a bias warning, **run multiple‑imputation sensitivity analysis** (10‑fold `IterativeImputer`) and aggregate results. (**Task T015_missingness_handling**)

7. **Proxy Anxiety Instrument Validation** – verify that any proxy anxiety instrument is on the validated whitelist (GAD‑7, STAI‑Y, PHQ‑9).  
   - If validated: set `proxy_validated = true` and continue with a construct‑validity warning flag.  
   - If not validated: **halt with explicit error** (FR‑008). (**Task T016_proxy_validation**)

8. **Distinctness Check** – using metadata from step 4, confirm that `baseline_anxiety` and `anxiety_score` have different `instrument_identifier` **or** `measurement_timepoint`. If they match, set `coupling_risk = true`, drop `baseline_anxiety` from the model, and flag the issue (FR‑003). (**Task T017_distinctness_check**)

9. **Model Specification** – fit a multiple linear regression (OLS) with dependent variable `anxiety_score` and independent variables:  
   - `news_exposure_freq`  
   - `baseline_anxiety` (if retained)  
   - `age`  
   - `gender` (one‑hot encoded)  
   - **`SES`** (required confounder)  
   - **`total_media_use`** (required confounder)  
   - **`prior_mental_health_history`** (required confounder)  
   (**Task T018_ols**)

10. **Correlation Choice** – perform Shapiro‑Wilk normality tests on `news_exposure_freq` and `anxiety_score`. Use Pearson r if both p > 0.05; otherwise use Spearman ρ. (**Task T019_corr_choice**)

11. **Assumption Diagnostics** – compute VIF for each predictor (flag VIF > 10), Breusch‑Pagan test for homoscedasticity, residual‑vs‑fitted linearity check, and Shapiro‑Wilk on residuals (FR‑007). (**Task T020_assumption_checks**)

12. **Robustness Check** – compute correlation between `social_media_engagement` and `news_exposure_freq`; if |r| > 0.3 **and** `social_media_engagement` exists, refit the OLS on the top‑percentile (75th) of engagement. Record coefficient, p‑value, and flag any sign flip or loss of significance. If the gate fails, log a warning. (**Task T021_robustness_check**)

13. **Visualization** – generate a scatter plot of `news_exposure_freq` vs. `anxiety_score` with regression line and 95 % confidence interval. Save as PNG/SVG under `output/plots/`. (**Task T022_visualization**)

14. **Result Assembly** – write a single‑source‑of‑truth JSON file `output/results/regression_results.json` containing all model coefficients, diagnostics, flags, runtime, and, if applicable, an embedded `halt_report`. (**Task T023_assemble_results**)

15. **Success‑Criteria Validation** – run `code/validate_sc.py` against the JSON, producing `outputs/success_criteria_log.txt` with PASS/FAIL/BLOCKED for SC‑001 – SC‑005. (**Task T024_validate_sc**)

16. **Documentation Generation** – programmatically create a reproducible `README.md` that lists data sources, pipeline steps, runtime, and how to reproduce the analysis. (**Task T025_generate_readme**)

17. **Archiving** – zip the `code/`, `data/`, and `outputs/` directories into `archive.zip` for external review. (**Task T026_archive**)

18. **Sign‑off** – CI automatically writes `outputs/signoff_report.json` summarizing the run status. (**Task T027_signoff**)

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas>=2.0.0`, `numpy>=1.24.0`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `matplotlib>=3.7.0`, `pyarrow>=14.0.0`, `pyyaml>=6.0`, `jsonschema>=4.19.0` (pinned in `requirements.txt`)  
- **Storage**: Local filesystem under `data/` (raw & processed) and `output/` (results & plots)  
- **Testing**: `pytest` + contract validation against `contracts/*.schema.yaml`  
- **Target Platform**: GitHub Actions free‑tier Linux runner (multiple CPU cores, several GB of RAM, no GPU) – all steps are CPU‑first.  

## Constitution Check
| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Fixed seeds; deterministic downloads; identical SHA‑2 hash each run |
| II. Verified Accuracy | PASS | Only the three verified URLs are cited; no unverified dataset is used |
| III. Data Hygiene | PASS | Raw files stored immutable with SHA‑256; all transformations write new files |
| IV. Single Source of Truth | PASS | All statistics derived from `output/results/regression_results.json` |
| V. Versioning Discipline | PASS | `requirements.txt` pinned; content hashes recorded in `state/...` |
| VI. Ethical Human‑Subjects Handling | PASS | Only open, non‑human‑subject corpora are downloaded; no PII is present |
| VII. Psychometric Validity | BLOCKED | No verified dataset provides a validated anxiety instrument; pipeline halts with `HALTED_NO_VALID_DATASET` unless a validated proxy is supplied (see FR‑008). |

## Task Outline (high‑level)

| Phase | Task ID | Description | Dependencies | Notes |
|-------|---------|-------------|--------------|-------|
| 0 | T010_download | Download the three verified parquet URLs, compute SHA‑256, store under `data/raw/` | – | FR‑001 |
| 0 | T011_schema_validation | Validate schema against required columns; halt if none satisfy | T010_download | FR‑001 edge case |
| 0 | T012_power_analysis | Compute minimum N for β ≥ 0.10 / f² ≥ 0.02 (α = 0.05, 1‑β = 0.80) using `statsmodels` | – | Methodological rigor |
| 1 | T013_load_metadata | Load `variable_metadata.csv` for instrument identifiers & timepoints | – | FR‑003 |
| 1 | T014_cleaning | Listwise deletion of rows missing `news_exposure_freq` or `anxiety_score`; enforce N ≥ 30, warning if 30 ≤ N < 100 | T011_schema_validation, T012_power_analysis | FR‑002 |
| 1 | T015_missingness_handling | Run Little’s MCAR test; if p < 0.05, add missingness indicators **and** run 10‑fold multiple‑imputation sensitivity analysis | T014_cleaning | Methodology concern |
| 2 | T016_proxy_validation | Verify proxy anxiety instrument against whitelist; halt if unvalidated; set construct‑validity flag if validated | T014_cleaning | FR‑008 |
| 2 | T017_distinctness_check | Ensure `baseline_anxiety` and `anxiety_score` have distinct instruments/timepoints; drop baseline if coupled | T013_load_metadata, T014_cleaning | FR‑003 |
| 2 | T018_ols | Fit OLS regression with primary covariates **plus** SES, total_media_use, prior_mental_health_history (required) | T017_distinctness_check, T016_proxy_validation | FR‑003, FR‑007 |
| 2 | T019_corr_choice | Choose Pearson or Spearman correlation based on Shapiro‑Wilk results | T018_ols | FR‑004 |
| 2 | T020_assumption_checks | VIF, Breusch‑Pagan, residual normality, linearity diagnostics | T018_ols | FR‑007 |
| 2 | T021_robustness_check | If |r| > 0.3 between engagement and news exposure, refit OLS on top‑percentile subset | T020_assumption_checks | FR‑006 |
| 2 | T022_visualization | Scatter plot with regression line & 95 % CI | T018_ols | Visualization |
| 3 | T023_assemble_results | Create `regression_results.json` (including halt_report if needed) | All modeling tasks | Single source of truth |
| 4 | T024_validate_sc | Validate SC‑001 – SC‑005, write `success_criteria_log.txt` | T023_assemble_results | Constitution I |
| 5 | T025_generate_readme | Generate reproducible `README.md` summarizing pipeline | T024_validate_sc | Documentation |
| 6 | T026_archive | Zip `code/`, `data/`, `outputs/` into `archive.zip` | T025_generate_readme | Archival artifact |
| 7 | T027_signoff | Write `outputs/signoff_report.json` summarizing run status | T026_archive | CI sign‑off |

**Ordering rule**: download → power analysis → checksum → schema validation → metadata load → cleaning → missingness diagnostics → proxy validation → distinctness check → modeling → correlation → assumptions → robustness → visualization → result assembly → success‑criteria validation → documentation → archiving → sign‑off. All tasks produce real, inspectable artifacts; no placeholder data are fabricated.
