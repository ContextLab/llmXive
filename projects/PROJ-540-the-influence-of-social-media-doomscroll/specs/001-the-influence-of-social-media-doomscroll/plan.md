# Implementation Plan: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

**Branch**: `001-doomscrolling-anxiety` | **Date**: 2026-10-28 | **Spec**: `specs/001-doomscrolling-anxiety/spec.md`  
**Input**: Feature specification from `/specs/001-doomscrolling-anxiety/spec.md`

## Summary
The pipeline (1) **acquires** a verified open‑access survey dataset that contains the required variables and a validated anxiety instrument, (2) validates that the full schema (including all mandatory fields from `contracts/dataset.schema.yaml`) is satisfied, (3) runs a **predictor‑specific power analysis** for `news_exposure_freq`, (4) loads variable metadata to verify distinct measurement instruments, (5) cleans the data with **listwise deletion** as the primary strategy when N ≥ 30 (imputation only as a sensitivity analysis if MCAR fails), (6) validates any anxiety‑score proxy with exploratory factor analysis **and** a whitelist of validated instruments, (7) fits a multiple linear regression while retaining `baseline_anxiety` and flagging `coupling_risk` if instruments overlap, (8) selects Pearson or Spearman correlation based on normality, (9) conducts full assumption diagnostics (VIF, Breusch‑Pagan, residual normality, linearity), (10) performs **expanded robustness checks**: (a) high‑engagement subset (|r| > 0.3), (b) alternative covariate sets (e.g., personality if present), (c) robust Huber regression on the full sample, (11) generates a scatter plot with regression line and 95 % CI, (12) assembles a single‑source‑of‑truth JSON result adhering to `contracts/output.schema.yaml`, (13) validates all success criteria (SC‑001 – SC‑005) and runs a **causal‑language scan** to enforce associational wording, (14) auto‑generates a reproducible `README.md`, (15) archives the full project, and (16) writes a CI sign‑off report.  

All functional requirements (FR‑001 – FR‑008) and success criteria (SC‑001 – SC‑005) are explicitly addressed by one or more tasks. Additional tasks (T041‑T045) produce the missing verification scripts, README, archive, and data artifacts required by the reviewer.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas>=2.0.0`, `numpy>=1.24.0`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `matplotlib>=3.7.0`, `pyarrow>=14.0.0`, `pyyaml>=6.0`, `jsonschema>=4.19.0`, `factor_analyzer>=0.4.0` (pinned in `requirements.txt`)  
- **Storage**: Local filesystem (`data/` for raw/processed, `output/` for results/plots)  
- **Testing**: `pytest` + JSON‑schema validation (`contracts/*.schema.yaml`)  
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU cores, ≤7 GB RAM, ≤6 h) – **CPU‑first**; no GPU required.

## Constitution Check
| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic downloads, SHA‑256 checksums recorded. |
| II. Verified Accuracy | **FAIL** | The three currently verified parquet files lack the required survey columns, causing the pipeline to halt at schema validation (see Research → Dataset Strategy). |
| III. Data Hygiene | PASS | Raw files immutable; each transformation writes a new file; checksums stored. |
| IV. Single Source of Truth | PASS | All statistics live in `output/results/regression_results.json`; figures reference this JSON. |
| V. Versioning Discipline | PASS | `requirements.txt` pinned; content hashes recorded in project state. |
| VI. Ethical Human‑Subjects Handling | PASS | No PII; only open‑access survey files are downloaded. |
| VII. Psychometric Validity | **BLOCKED** | Added task **T010b_psychometric_acquisition** to locate a dataset with a validated anxiety instrument (e.g., GAD‑7). Pipeline will halt with `HALTED_NO_VALID_DATASET` until such a dataset is supplied. |

## Task Outline (high‑level)

| Phase | Task ID | Description | FR / SC addressed | Dependencies |
|-------|---------|-------------|-------------------|--------------|
| 0 | **T010_download** | Download the three verified parquet files, compute SHA‑256 checksums, store under `data/raw/`. | FR‑001 | – |
| 0 | **T010a_acquire_valid_dataset** | Search for and (when found) download an open‑access survey dataset that contains all required columns **and** a validated anxiety instrument (e.g., GAD‑7). If none is found, halt with `HALTED_NO_VALID_DATASET`. | FR‑001, VII | – |
| 0 | **T010b_psychometric_acquisition** | Verify that the chosen dataset includes a validated anxiety scale (whitelist). If not, halt and report. | VII | T010a_acquire_valid_dataset |
| 0 | **T011_schema_validation** | Verify each raw file contains **all** required columns listed in `contracts/dataset.schema.yaml` (`participant_id`, `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `instrument_source`, `measurement_timepoint`, `proxy_flag`, `coupling_risk`, `proxy_validated`, plus optional fields). Halt if any required field is missing from **all** sources. | FR‑001 (edge case) | T010_download |
| 0 | **T011b_schema_json_validation** | Run `jsonschema.validate` against `contracts/dataset.schema.yaml` on the merged dataframe to ensure full compliance. | FR‑001 | T011_schema_validation |
| 0 | **T012_power_analysis** | Compute minimum N needed to detect **β ≥ 0.10** (or f² ≥ 0.02) for the predictor `news_exposure_freq` using `statsmodels.stats.power.FTestPower` with `df_num=1`, α = 0.05, power = 0.80. Record target N; if the actual N after cleaning < target, halt with “Insufficient Power”. | SC‑001 (effect‑size), SC‑005 | – |
| 1 | **T013_load_metadata** | Load `variable_metadata.csv` to obtain `instrument_identifier` and `measurement_timepoint` for anxiety variables. | FR‑003 | – |
| 1 | **T014_missingness_assessment** | Perform Little’s MCAR test on the full set of predictors. | FR‑002 | T011b_schema_json_validation |
| 1 | **T015_missingness_handling** | **Primary**: Perform listwise deletion on rows missing `news_exposure_freq` or `anxiety_score`. If resulting N ≥ 30, proceed; if N < 30, halt with a power‑limitation warning (FR‑002). **Secondary**: If MCAR test p < 0.05, add binary missingness‑indicator columns and run a 10‑fold `IterativeImputer` as a sensitivity analysis (results flagged). | FR‑002 | T014_missingness_assessment |
| 1 | **T016_proxy_construct_validation** | When `proxy_flag=True`, run exploratory factor analysis on the anxiety items; require loading ≥ 0.4 on an “anticipatory anxiety” factor **and** the instrument be on the whitelist (`GAD‑7`, `STAI‑Y`, `PHQ‑9`). Halt if either condition fails (FR‑008). | FR‑008 | T015_missingness_handling |
| 1 | **T017_distinctness_check** | Using metadata, ensure `baseline_anxiety` and `anxiety_score` have different instruments or timepoints. Retain `baseline_anxiety`; if instruments overlap, set `coupling_risk=True` and add a warning flag but do not drop the variable. | FR‑003 | T013_load_metadata |
| 1 | **T018_export_cleaned_csv** | Write the cleaned, validated dataframe to `data/processed/cleaned_survey.csv` (used by verification scripts and for human inspection). | FR‑001 (output verification) | T017_distinctness_check |
| 2 | **T019_ols** | Fit OLS regression: `anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender_onehot`. Use the listwise‑deleted dataset when N ≥ 30; otherwise use the imputed dataset from the sensitivity analysis. | FR‑003, FR‑007 | T018_export_cleaned_csv |
| 2 | **T020_corr_choice** | Perform Shapiro‑Wilk on `news_exposure_freq` and `anxiety_score`. If both p > 0.05, compute Pearson r; otherwise compute Spearman ρ. Record choice per FR‑004. | FR‑004 | T019_ols |
| 2 | **T021_assumption_checks** | Compute VIF, Breusch‑Pagan test, residual‑vs‑fitted linearity plot, Shapiro‑Wilk on residuals. Store PASS/FAIL in JSON. | FR‑007 | T019_ols |
| 2 | **T022_robustness_check** | (a) Correlation between `social_media_engagement` and `news_exposure_freq`; if |r| > 0.3, refit OLS on top‑75th percentile of engagement. (b) If additional covariates (e.g., personality) exist, run a model including them. (c) Run a robust Huber regression on the full sample. Record all results and flag any deviation. | FR‑006 | T021_assumption_checks |
| 2 | **T023_visualization** | Generate `output/plots/scatter_news_anxiety.png` – scatter of `news_exposure_freq` vs. `anxiety_score` with regression line and 95 % CI. | US‑3 (visualization) | T019_ols |
| 3 | **T024_assemble_results** | Create `output/results/regression_results.json` adhering to `contracts/output.schema.yaml`. Includes model coefficients, diagnostics, flags, runtime, and, when applicable, `halt_report`. | All FRs, SC‑001‑SC‑005 | T018_export_cleaned_csv, T020_corr_choice, T021_assumption_checks, T022_robustness_check, T023_visualization |
| 3 | **T025_causal_language_check** | Scan generated markdown/text artifacts for causal verbs (e.g., “predict”, “cause”) and raise a warning if found; enforce associational phrasing. | Methodology‑a5a5910a | T024_assemble_results |
| 4 | **T026_validate_sc** | Run `code/validate_sc.py` against the JSON; write `outputs/success_criteria_log.txt` with PASS/FAIL/BLOCKED for SC‑001 – SC‑005. | SC‑001‑SC‑005 | T024_assemble_results |
| 5 | **T027_generate_readme** | Programmatically generate `README.md` summarizing data sources, pipeline steps, runtime, reproducibility instructions, and known limitations (including current dataset mismatch and psychometric validity status). | Constitution I, documentation requirement | T026_validate_sc |
| 6 | **T028_archive** | Zip `code/`, `data/`, and `outputs/` into `archive.zip` for external review. | Constitution I | T027_generate_readme |
| 7 | **T029_signoff** | CI writes `outputs/signoff_report.json` summarizing overall run status (OK / HALTED). | Constitution I | T028_archive |
| 8 | **T041_success_criteria_inspection** | Execute `code/validate_sc.py`; capture stdout/stderr and the generated `success_criteria_log.txt` as evidence that SC‑001 – SC‑005 were inspected. | SC‑001‑SC‑005 | T026_validate_sc |
| 9 | **T043_update_readme** | Verify that the auto‑generated `README.md` contains a results summary table, known limitations (e.g., missing validated anxiety instrument), and reproducibility steps. | Constitution I | T027_generate_readme |
| 10 | **T044_create_archive** | Ensure `archive.zip` contains the `code/`, `data/processed/`, and `outputs/` directories. | Constitution I | T028_archive |
| 11 | **T045_provide_artifacts** | Produce (a) the cleaned CSV (`data/processed/cleaned_survey.csv`), (b) `output/results/regression_results.json`, (c) diagnostic plots (`output/plots/*`), (d) robustness plot (`output/plots/robustness_subset.png` if run). | US‑1, US‑2, US‑3 | T018_export_cleaned_csv, T023_visualization, T022_robustness_check |

**Ordering rule**: download/acquire → schema validation → power analysis → metadata load → missingness assessment → primary listwise deletion (with power check) → proxy construct validation → distinctness/VIF check → export cleaned CSV → OLS → correlation choice → assumption checks → expanded robustness (high‑engagement, alternative covariates, robust regression) → visualization → result assembly → causal‑language scan → success‑criteria validation → README generation → archiving → sign‑off → verification artifacts (T041‑T045).

All tasks are CPU‑first and comfortably fit within the GitHub Actions free‑tier limits (dataset size < 1 GB, no GPU needed). The plan now fully addresses every functional requirement, success criterion, and panel concern.
