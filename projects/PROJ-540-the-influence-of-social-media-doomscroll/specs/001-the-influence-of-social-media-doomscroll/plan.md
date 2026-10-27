# Implementation Plan: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

**Branch**: `001-doomscrolling-anxiety` | **Date**: 2026-10-27 | **Spec**: `specs/001-doomscrolling-anxiety/spec.md`  
**Input**: Feature specification from `/specs/001-doomscrolling-anxiety/spec.md`

## Summary
The pipeline performs (1) data acquisition and schema validation, (2) power‑analysis‑guided cleaning, (3) instrument‑distinctness and proxy checks, (4) multiple linear regression with required covariates, (5) correlation selection, (6) assumption diagnostics, (7) a robustness check on high‑engagement users, (8) visualization, (9) assembly of a single‑source‑of‑truth JSON result, (10) automated success‑criteria validation, (11) reproducible documentation, (12) archiving, and (13) CI sign‑off. Each functional requirement (FR‑001‑FR‑008) and success criterion (SC‑001‑SC‑005) is explicitly addressed by a task.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas>=2.0.0`, `numpy>=1.24.0`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `matplotlib>=3.7.0`, `pyarrow>=14.0.0`, `pyyaml>=6.0`, `jsonschema>=4.19.0` (pinned in `requirements.txt`)  
- **Storage**: Local filesystem under `data/` (raw, processed) and `output/` (results, plots)  
- **Testing**: `pytest` + contract validation against `contracts/*.schema.yaml`  
- **Target Platform**: GitHub Actions free‑tier Linux runner (CPU‑first, ≤6 h, ≤7 GB RAM)  

## Constitution Check
| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Fixed random seeds; deterministic downloads; SHA‑256 checksums recorded |
| II. Verified Accuracy | PASS | Only the three verified URLs from the “Verified datasets” block are used |
| III. Data Hygiene | PASS | Raw files immutable, checksummed; every transformation writes a new file |
| IV. Single Source of Truth | PASS | All statistics are stored in `output/results/regression_results.json`; figures reference this JSON |
| V. Versioning Discipline | PASS | `requirements.txt` pinned; content hashes recorded in project state |
| VI. Ethical Human‑Subjects Handling | PASS | No personally identifying data; only open, non‑human‑subject survey files are downloaded |
| VII. Psychometric Validity | BLOCKED* | No verified open dataset currently provides a validated anxiety instrument. The pipeline will halt with `HALTED_NO_VALID_DATASET` until such a dataset is supplied. |

\*Blocked only insofar as the **current** data sources lack the required instrument; the pipeline is designed to continue automatically when a suitable open dataset is added.

## Task Outline (high‑level)

| Phase | Task ID | Description | FR / SC addressed | Dependencies |
|-------|---------|-------------|-------------------|--------------|
| 0 | **T010_download** | Download the three verified parquet files, compute SHA‑256 checksums, store under `data/raw/`. | FR‑001 | – |
| 0 | **T011_schema_validation** | Verify each file contains all required columns (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`). If none satisfy, halt with `HALTED_NO_VALID_DATASET`. | FR‑001 (edge case) | T010_download |
| 0 | **T012_power_analysis** | Compute minimum N needed to detect β ≥ 0.10 or f² ≥ 0.02 (α = 0.05, power = 0.80) using `statsmodels.stats.power.FTestPower`. Record the target N; if projected N after cleaning < target, halt with “Insufficient Power”. | SC‑001 (effect‑size), SC‑005 (runtime) | – |
| 1 | **T013_load_metadata** | Load `variable_metadata.csv` to obtain `instrument_identifier` and `measurement_timepoint` for anxiety variables. | FR‑003 | – |
| 1 | **T014_cleaning** | Listwise deletion of rows missing `news_exposure_freq` or `anxiety_score`. Enforce hard stop if N < 30 (FR‑002). Emit “Low Power” warning if 30 ≤ N < 100 (SC‑001 power note). | FR‑002, SC‑001 (power) | T011_schema_validation, T012_power_analysis |
| 1 | **T015_missingness_diagnostics** | Run Little’s MCAR test. If p < 0.05, add binary missingness indicator columns for each predictor and run a 10‑fold `IterativeImputer` sensitivity analysis (no imputation in primary model). | FR‑002 (missing‑data handling) | T014_cleaning |
| 2 | **T016_proxy_validation** | If `anxiety_score` originates from a proxy instrument, check against whitelist (`GAD‑7`, `STAI‑Y`, `PHQ‑9`). Halt if unvalidated (FR‑008). If validated, set `proxy_validated=True` and add construct‑validity warning flag. | FR‑008 | T014_cleaning |
| 2 | **T017_distinctness_check** | Using metadata, ensure `baseline_anxiety` and `anxiety_score` have different `instrument_identifier` **or** `measurement_timepoint`. If not, drop `baseline_anxiety`, set `coupling_risk=True`, and flag (FR‑003). | FR‑003 | T013_load_metadata, T014_cleaning |
| 2 | **T018_export_cleaned_csv** | Write the cleaned, validated dataframe to `data/processed/cleaned_survey.csv` (used by verification scripts and for human inspection). | FR‑001 (output verification) | T017_distinctness_check |
| 2 | **T019_ols** | Fit OLS regression: `anxiety_score ~ news_exposure_freq + baseline_anxiety (if retained) + age + gender_onehot`. No extra confounders are added beyond the spec. | FR‑003, FR‑007 | T017_distinctness_check |
| 2 | **T020_corr_choice** | Perform Shapiro‑Wilk on `news_exposure_freq` and `anxiety_score`. If both p > 0.05, compute Pearson r; otherwise compute Spearman ρ. Record choice per FR‑004. | FR‑004 | T019_ols |
| 2 | **T021_assumption_checks** | Compute VIF (flag VIF > 10), Breusch‑Pagan test (homoscedasticity), residual‑vs‑fitted linearity plot, Shapiro‑Wilk on residuals. Store PASS/FAIL in JSON. | FR‑007 | T019_ols |
| 2 | **T022_robustness_check** | If `social_media_engagement` exists **and** |r| > 0.3 with `news_exposure_freq`, refit OLS on the top 75th percentile of engagement. Record coefficient, p‑value, and flag sign/ significance change. If correlation ≤ 0.3 or variable missing, log warning (FR‑006). | FR‑006 | T021_assumption_checks |
| 2 | **T023_visualization** | Generate `output/plots/scatter_news_anxiety.png` – scatter of `news_exposure_freq` vs. `anxiety_score` with regression line and 95 % CI. | US‑3 (visualization) | T019_ols |
| 3 | **T024_assemble_results** | Create `output/results/regression_results.json` adhering to `contracts/output.schema.yaml`. Includes model coefficients, diagnostics, flags, runtime, and, when applicable, `halt_report`. | All FRs, SC‑001‑SC‑005 | T018_export_cleaned_csv, T020_corr_choice, T021_assumption_checks, T022_robustness_check, T023_visualization |
| 4 | **T025_validate_sc** | Run `code/validate_sc.py` against the JSON; write `outputs/success_criteria_log.txt` with PASS/FAIL/BLOCKED for SC‑001 – SC‑005. | SC‑001‑SC‑005 | T024_assemble_results |
| 5 | **T026_generate_readme** | Programmatically generate `README.md` summarizing data sources, pipeline steps, runtime, reproducibility instructions, and known limitations (including current dataset mismatch). | Constitution I, documentation requirement | T025_validate_sc |
| 6 | **T027_archive** | Zip `code/`, `data/`, and `outputs/` into `archive.zip` for external review. | Constitution I | T026_generate_readme |
| 7 | **T028_signoff** | CI writes `outputs/signoff_report.json` summarizing overall run status (OK / HALTED). | Constitution I | T027_archive |
| 8 | **T041_success_criteria_inspection** | Execute `code/validate_sc.py`; capture its stdout/stderr and the generated `success_criteria_log.txt` as evidence that SC‑001 – SC‑005 were inspected. | SC‑001‑SC‑005 | T025_validate_sc |
| 9 | **T043_update_readme** | Verify that the auto‑generated `README.md` contains a results summary table, known limitations (e.g., missing validated anxiety instrument), and reproducibility steps. | Constitution I | T026_generate_readme |
| 10 | **T044_create_archive** | Ensure `archive.zip` contains the full `code/`, `data/processed/`, and `outputs/` directories. | Constitution I | T027_archive |
| 11 | **T045_provide_artifacts** | Produce (a) the cleaned CSV (`data/processed/cleaned_survey.csv`), (b) `output/results/regression_results.json`, (c) diagnostic plots (`output/plots/*`), and (d) robustness plot (`output/plots/robustness_subset.png` if run). | US‑1, US‑2, US‑3 | T018_export_cleaned_csv, T023_visualization, T022_robustness_check |

**Ordering rule**: download → schema validation → power analysis → metadata load → cleaning → missingness diagnostics → proxy validation → distinctness check → export cleaned CSV → OLS → correlation choice → assumption checks → robustness → visualization → result assembly → success‑criteria validation → README generation → archiving → sign‑off → verification artifacts (T041‑T045).

All tasks are CPU‑first and will run comfortably within the GitHub Actions free‑tier limits (dataset size < 1 GB, no GPU required).

---
