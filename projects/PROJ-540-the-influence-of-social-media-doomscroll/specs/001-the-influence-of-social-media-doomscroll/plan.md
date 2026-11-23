# Implementation Plan: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

**Branch**: `001-doomscrolling-anxiety` | **Date**: 2026-10-28 | **Spec**: `specs/001-doomscrolling-anxiety/spec.md`  
**Input**: Feature specification from `/specs/001-doomscrolling-anxiety/spec.md`

## Summary
The pipeline (1) **attempts** to locate a **verified open‑access survey dataset** that contains all required variables and a validated anxiety instrument; **if none is found**, it halts with a detailed `halt_report`. (2) validates the dataset against a strict JSON schema, (3) performs a priori power analysis for the predictor `news_exposure_freq` (standardized), (4) loads variable‑metadata to verify distinct measurement instruments, (5) handles missing data via listwise deletion (primary) and multiple‑imputation sensitivity (secondary) **only when missingness ≤ 10 %**, (6) validates any anxiety‑score proxy with exploratory factor analysis against a whitelist of validated instruments, (7) **standardizes** `news_exposure_freq` (z‑score) and fits a multiple linear regression while checking for collinearity, coupling risk, and including `social_media_engagement` as a covariate when present, (8) selects Pearson or Spearman correlation based on normality, (9) runs full assumption diagnostics (VIF, Breusch‑Pagan, residual normality, linearity) and records p‑values, (10) executes robustness checks (high‑engagement subset, alternative covariates, robust Huber regression) and **explicitly verifies that the sign and significance of the `news_exposure_freq_std` coefficient match the full‑sample analysis**, satisfying SC‑003, (11) generates a scatter plot with regression line and 95 % CI, (12) assembles a single‑source‑of‑truth JSON result adhering to `contracts/output.schema.yaml`, (13) runs a causal‑language scan to enforce associational wording, (14) validates **all success criteria** (SC‑001 – SC‑005) including adjusted R² ≥ 0.10 and assumption‑check p‑values > 0.05, (15) auto‑generates a reproducible `README.md`, (16) archives the full project, and (17) writes a CI sign‑off report.  

**Note:** The three verified URLs listed in the dataset strategy (see `research.md`) are **not** survey datasets and do **not** contain the required columns (`news_exposure_freq`, `anxiety_score`, etc.). Consequently, the pipeline will halt at **Schema Validation** (FR‑001 edge case) and produce a detailed `halt_report`. When a suitable open‑access survey dataset that includes all required variables and a validated anxiety instrument becomes available, the pipeline will proceed with the subsequent steps.

All functional requirements and success criteria are explicitly addressed by the tasks below.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas>=2.0.0`, `numpy>=1.24.0`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `matplotlib>=3.7.0`, `pyarrow>=14.0.0`, `pyyaml>=6.0`, `jsonschema>=4.19.0`, `factor_analyzer>=0.4.0`, `statsmodels>=0.14.0` (pinned in `requirements.txt`)  
- **Storage**: Local filesystem under `data/` (raw, processed) and `output/` (results, plots)  
- **Testing**: `pytest` + JSON‑schema validation (`contracts/*.schema.yaml`)  
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU cores, ≤7 GB RAM, ≤6 h) – **CPU‑first**; no GPU required  

## Constitution Check
| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | **PASS** | Fixed random seeds, deterministic downloads, SHA‑256 checksums recorded for every raw file. |
| II. Verified Accuracy | **PASS** | All external citations in `idea/`, `technical-design/`, `implementation-plan/`, or `paper/` are drawn from the verified list supplied in the spec. |
| III. Data Hygiene | **PASS** | Raw files are immutable; every transformation produces a new file with a documented derivation. |
| IV. Single Source of Truth | **PASS** | All statistics and flags live in `output/results/regression_results.json`; figures reference this JSON. |
| V. Versioning Discipline | **PASS** | `requirements.txt` pins exact versions; content hashes are recorded in project state. |
| VI. Ethical Human‑Subjects Handling | **PASS** | Only open‑access survey data are used; no PII is stored. |
| VII. Psychometric Validity | **PASS** | Anxiety instruments are cross‑checked against a whitelist (`GAD‑7`, `STAI‑Y`, `PHQ‑9`). Proxy validation uses factor analysis; runs halt if validation fails. |

## Project Structure
```text
specs/001-doomscrolling-anxiety/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── output.schema.yaml

src/
├── ingest.py
├── metadata.py
├── missingness.py
├── proxy_validation.py
├── model.py
├── diagnostics.py
├── robustness.py
├── viz.py
├── assemble_results.py
├── causal_scan.py
├── validate_sc.py
├── generate_readme.py
└── archive.py

tests/
├── contract/
└── unit/
```

## Task Outline (ordered for execution)

| Phase | Task ID | Description | FR / SC addressed | Dependencies |
|-------|---------|-------------|-------------------|--------------|
| 0 | **T010_download** | Download the three verified parquet files, compute SHA‑256 checksums, store under `data/raw/`. | FR‑001 | – |
| 0 | **T010a_acquire_valid_dataset** | Search for and download an open‑access survey dataset that **contains all required columns** **and** a validated anxiety instrument (e.g., GAD‑7). **If none is found**, halt with `HALTED_NO_VALID_DATASET`. | FR‑001, VII | – |
| 0 | **T010b_psychometric_acquisition** | Verify that the chosen dataset includes a validated anxiety scale from the whitelist. Halt if not. | VII | T010a_acquire_valid_dataset |
| 0 | **T011_schema_validation** | Validate each raw file against `contracts/dataset.schema.yaml`. Abort if any required column is missing from **all** sources. | FR‑001 (edge case) | T010_download |
| 0 | **T011b_schema_json_validation** | Run `jsonschema.validate` on the merged dataframe to ensure full compliance. | FR‑001 | T011_schema_validation |
| 0 | **T012_power_analysis** | Compute minimum N to detect **β ≥ 0.10** (standardized) for `news_exposure_freq` using `statsmodels.stats.power.FTestPower` (α = 0.05, power = 0.80). Record target N; halt with “Insufficient Power” if actual N after cleaning < target. | SC‑001, SC‑005 | – |
| 1 | **T013_load_metadata** | Load `variable_metadata.csv` to obtain `instrument_identifier` and `measurement_timepoint` for anxiety variables. | FR‑003 | – |
| 1 | **T014_missingness_assessment** | Perform Little’s MCAR test on all predictors. | FR‑002 | T011b_schema_json_validation |
| 1 | **T015_missingness_handling** | Primary: listwise deletion on rows missing `news_exposure_freq` or `anxiety_score` **if** MCAR holds **and** missingness proportion for these variables ≤ 10 %. Secondary (sensitivity): when missingness ≤ 10 % **and** MCAR fails, run a 10‑fold `IterativeImputer`. Record both analyses per FR‑009. | FR‑002, FR‑009 | T014_missingness_assessment |
| 1 | **T016_proxy_construct_validation** | If `proxy_flag=True`, run exploratory factor analysis on anxiety items; require loading ≥ 0.4 on an “anticipatory anxiety” factor **and** instrument be on whitelist. Halt otherwise. | FR‑008 | T015_missingness_handling |
| 1 | **T017_distinctness_check** | Using metadata, ensure `baseline_anxiety` and `anxiety_score` have different instruments or timepoints. If instruments overlap, set `coupling_risk=True`; **drop** `baseline_anxiety` from the primary model and flag a warning. | FR‑003 | T013_load_metadata |
| 1 | **T018_export_cleaned_csv** | Write the cleaned, validated dataframe to `data/processed/cleaned_survey.csv`. | FR‑001 (output verification) | T017_distinctness_check |
| 2 | **T019_ols** | **Standardize** `news_exposure_freq` (z‑score). Fit OLS regression: `anxiety_score ~ news_exposure_freq_std + baseline_anxiety (if retained) + social_media_engagement (if column present) + age + gender_onehot`. Use listwise‑deleted data when N ≥ 30; otherwise use the imputed dataset from the sensitivity analysis. | FR‑003, FR‑007, scientific_soundness‑349b6aee | T018_export_cleaned_csv |
| 2 | **T020_corr_choice** | Perform Shapiro‑Wilk on `news_exposure_freq_std` and `anxiety_score`. Compute Pearson r if both p > 0.05; else compute Spearman ρ. Record the choice. | FR‑004 | T019_ols |
| 2 | **T021_assumption_checks** | Compute VIF, Breusch‑Pagan test, residual‑vs‑fitted linearity plot, Shapiro‑Wilk on residuals. Store PASS/FAIL **and** the raw p‑values in JSON. | FR‑005, FR‑007 | T019_ols |
| 2 | **T022_robustness_check** | **SC‑003 requirement:** (a) Correlate `social_media_engagement` with `news_exposure_freq_std`; if |r| > 0.3, refit OLS on the top‑75th percentile of engagement. (b) After refit, **compare the sign and p‑value (< 0.05) of the `news_exposure_freq_std` coefficient to the full‑sample result**; set `sign_match` and `pvalue_match` flags accordingly. (c) If the sign or significance differs, raise a `RobustnessSignMismatch` flag. (d) Run a robust Huber regression on the full sample as an additional sensitivity check. This explicit sign‑and‑significance consistency check satisfies SC‑003. Record all results and flag any deviation. | FR‑006, SC‑003 | T021_assumption_checks |
| 2 | **T023_visualization** | Generate `output/plots/scatter_news_anxiety.png` – scatter of `news_exposure_freq_std` vs. `anxiety_score` with regression line and 95 % CI. | US‑3 | T019_ols |
| 3 | **T024_assemble_results** | Create `output/results/regression_results.json` conforming to `contracts/output.schema.yaml`. Include model coefficients, diagnostics, flags, runtime, and, when applicable, `halt_report`. Add `adj_r2_pass` (boolean) reflecting SC‑002 and ensure `assumption_checks` contain raw p‑values for SC‑004. | All FRs, SC‑001‑SC‑005 | T018_export_cleaned_csv, T020_corr_choice, T021_assumption_checks, T022_robustness_check, T023_visualization |
| 3 | **T025_causal_language_check** | Scan generated markdown/text for causal verbs (e.g., “predict”, “cause”) and raise a warning if found; enforce associational phrasing. | Methodology‑a5a5910a | T024_assemble_results |
| 4 | **T026_validate_sc** | Run `code/validate_sc.py` against the JSON; write `outputs/success_criteria_log.txt` with PASS/FAIL/BLOCKED for SC‑001 – SC‑005 **including adjusted R² ≥ 0.10 and assumption‑check p‑values > 0.05**. Halt the pipeline with a clear error if any SC fails. | SC‑001‑SC‑005 | T024_assemble_results |
| 5 | **T027_generate_readme** | Programmatically generate `README.md` summarizing data sources, pipeline steps, runtime, reproducibility instructions, and known limitations (including the current dataset mismatch). | Constitution I, documentation requirement | T026_validate_sc |
| 6 | **T028_archive** | Zip `code/`, `data/`, and `outputs/` into `archive.zip` for external review. | Constitution I | T027_generate_readme |
| 7 | **T029_signoff** | CI writes `outputs/signoff_report.json` summarizing overall run status (OK / HALTED). | Constitution I | T028_archive |
| 8 | **T041_success_criteria_inspection** | Execute `code/validate_sc.py`; capture stdout/stderr and the generated `success_criteria_log.txt` as evidence that SC‑001 – SC‑005 were inspected. | SC‑001‑SC‑005 | T026_validate_sc |
| 9 | **T043_update_readme** | Verify that the auto‑generated `README.md` contains a results summary table (when data are available), known limitations (e.g., missing validated anxiety instrument), and reproducibility steps. | Constitution I | T027_generate_readme |
| 10 | **T044_create_archive** | Ensure `archive.zip` contains the `code/`, `data/processed/`, and `outputs/` directories. | Constitution I | T028_archive |
| 11 | **T045_provide_artifacts** | Produce (a) the cleaned CSV (`data/processed/cleaned_survey.csv`), (b) `output/results/regression_results.json`, (c) diagnostic plots (`output/plots/*`), (d) robustness plot (`output/plots/robustness_subset.png` if run). | US‑1, US‑2, US‑3 | T018_export_cleaned_csv, T023_visualization, T022_robustness_check |

**Ordering rule**: download/acquire → schema validation → power analysis → metadata load → missingness assessment → primary listwise deletion (with power check) → proxy construct validation → distinctness/VIF check → export cleaned CSV → standardization & OLS (including social_media_engagement) → correlation choice → assumption checks → expanded robustness (high‑engagement, alternative covariates, robust regression) → visualization → result assembly → causal‑language scan → comprehensive success‑criteria validation (including adjusted R² and assumption p‑values) → README generation → archiving → sign‑off → verification artifacts (T041‑T045).

All tasks are CPU‑first, comfortably within the GitHub Actions free‑tier limits (dataset < 1 GB, RAM < 7 GB, runtime ≤ 60 s for typical runs). No GPU is required.

---

