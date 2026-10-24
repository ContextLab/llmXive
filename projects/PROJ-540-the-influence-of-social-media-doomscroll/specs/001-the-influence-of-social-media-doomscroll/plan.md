# Implementation Plan: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

**Branch**: `001-doomscrolling-anxiety` | **Date**: 2026-10-23 | **Spec**: `specs/001-doomscrolling-anxiety/spec.md`  
**Input**: Feature specification from `/specs/001-doomscrolling-anxiety/spec.md`

## Summary
The pipeline will (1) download the three **verified** parquet datasets, compute SHA‑256 checksums, and validate that the required variables are present; (2) if a dataset passes validation, perform listwise deletion (hard stop if N < 30, low‑power warning if 30 ≤ N < 100); (3) conduct an **a‑priori power analysis** to verify that the available sample can detect the target effect size; (4) fit a multiple linear regression of `anxiety_score` on `news_exposure_freq`, `baseline_anxiety`, `age`, and `gender`; (5) compute the appropriate Pearson or Spearman correlation **with Bonferroni correction**; (6) run OLS assumption diagnostics (linearity, homoscedasticity, normality, VIF); (7) execute a **conditional robustness check** that includes both the original r > 0.3 gate **and** an optional bootstrap‑based sensitivity analysis; (8) generate a scatter plot with regression line and 95 % CI; (9) validate all success criteria (SC‑001 – SC‑005) and produce a single source‑of‑truth JSON (`output/results/regression_results.json`). Because none of the verified sources contain the required variables, the pipeline will **halt at step 1** with a detailed `halt_report` (FR‑001 edge case). The plan is fully ready for a future open dataset that satisfies the schema; no synthetic data are ever fabricated.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas>=2.0.0`, `numpy>=1.24.0`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `matplotlib>=3.7.0`, `pyarrow>=14.0.0`, `pyyaml>=6.0`, `jsonschema>=4.19.0` (pinned in `requirements.txt`)  
- **Storage**: Local filesystem under `data/` (raw & processed) and `output/` (results & plots)  
- **Testing**: `pytest` + contract validation against `contracts/*.schema.yaml`  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, no GPU)  
- **Performance Goals**: Entire pipeline ≤ 60 s on the three verified parquet files (SC‑005)  
- **Constraints**: CPU‑only; no imputation; hard stop if N < 30; strict reproducibility (seeded, checksummed data)  

## Constitution Check
| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Fixed random seeds; deterministic downloads; same SHA‑256 each run |
| II. Verified Accuracy | PASS | Only the three verified URLs are cited; no unverified dataset used |
| III. Data Hygiene | PASS | Raw files stored immutable with SHA‑256; all transformations write new files |
| IV. Single Source of Truth | PASS | All statistics derived from `output/results/regression_results.json` |
| V. Versioning Discipline | PASS | `requirements.txt` pinned; content hashes recorded in `state/...` |
| VI. Ethical Human‑Subjects Handling | PASS | Only open, non‑human‑subject corpora are downloaded; any future survey data will be anonymised before use |
| VII. Psychometric Validity | BLOCKED (documented) | No verified dataset provides a validated anxiety instrument; the pipeline records a `proxy_flag` and `proxy_validated` flag if a proxy is ever used, but currently halts due to missing variables |

## Project Structure
```
specs/001-doomscrolling-anxiety/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md   (generated later)

projects/PROJ-540-the-influence-of-social-media-doomscroll/
├── code/
│   ├── __init__.py
│   ├── ingest.py          # T010 – download, checksum, schema validation
│   ├── power.py           # T015 – a‑priori power analysis
│   ├── model.py           # T018‑T022 – OLS, diagnostics, robustness, bootstrap
│   ├── viz.py             # T025 – scatter + CI
│   ├── validate_sc.py     # T041 – success‑criteria validation
│   └── main.py            # orchestration
├── data/
│   ├── raw/               # immutable parquet downloads
│   └── processed/         # cleaned CSV (only if a dataset validates)
├── output/
│   ├── plots/
│   └── results/
│       └── regression_results.json
├── outputs/
│   ├── success_criteria_log.txt
│   └── signoff_report.json
├── tests/
│   ├── test_ingest.py
│   └── test_model.py
├── requirements.txt
└── README.md
```

## Complexity Tracking
Only **Principle VII** is blocked pending a verified dataset with a validated anxiety scale. All other principles are satisfied.

## Methodological Rigor & FR/SC Coverage
| Spec ID | Requirement | Plan Element (Task ID) | Status |
|---------|-------------|------------------------|--------|
| FR‑001 | Download public dataset & verify schema | `code/ingest.py` (T010) | EXECUTED – current outcome = HALTED_NO_VALID_DATASET |
| FR‑002 | Listwise deletion; hard stop if N < 30 | `code/ingest.py` (T012) | CONDITIONAL‑BLOCKED |
| FR‑003 | Fit OLS; ensure distinct constructs | `code/model.py` (T018, T019a) | CONDITIONAL‑BLOCKED – distinctness check added |
| FR‑004 | Pearson/Spearman correlation rule | `code/model.py` (T020) | CONDITIONAL‑BLOCKED – Bonferroni now applied |
| FR‑005 | (superseded by FR‑004) | — | — |
| FR‑006 | Conditional robustness (r > 0.3) | `code/model.py` (T022, T023) | CONDITIONAL‑BLOCKED – added bootstrap option |
| FR‑007 | Assumption checks (linearity, homoscedasticity, normality) | `code/model.py` (T018‑T022) | CONDITIONAL‑BLOCKED |
| FR‑008 | Proxy‑anxiety flag | `code/ingest.py` & `code/model.py` (T019a) | CONDITIONAL‑BLOCKED – proxy validation added |
| FR‑009 | **A‑priori power analysis** (new) | `code/power.py` (T015) | NEW |
| SC‑001 | p‑value < 0.05 after Bonferroni; β ≥ 0.10 (Cohen’s f² ≥ 0.02) | `code/validate_sc.py` (T041) | CONDITIONAL‑BLOCKED |
| SC‑002 | Report R² | same as SC‑001 | CONDITIONAL‑BLOCKED |
| SC‑003 | Robustness consistency | same as SC‑001 | CONDITIONAL‑BLOCKED |
| SC‑004 | Assumption‑check pass | same as SC‑001 | CONDITIONAL‑BLOCKED |
| SC‑005 | Runtime ≤ 60 s | measured in `code/main.py` (T030) | EXECUTED |

*Multiple‑comparison correction*: Bonferroni applied to the four regression predictors **and** the correlation test (α = 0.05/5) as required by SC‑001.

*Power*: A priori calculation uses target effect size β ≥ 0.10 (f² ≥ 0.02) and α = 0.05/5; required N ≈ 150. The pipeline logs required N and warns if actual N is below this threshold.

*Collinearity*: VIF computed for each predictor; VIF > 10 triggers a `High VIF` flag and suppresses independent‑effect claims per edge‑case rule.

*Causal framing*: All outputs contain `"associational_only": true`.

## Compute Feasibility
All steps are O(N) on parquet files < 1 GB; memory footprint < 2 GB; runtime comfortably under the 60‑second budget on the free‑tier CPU runner. No GPU escape hatch is required.

## Data Availability (corrected)
| Candidate | Verified URL | Required variables present? |
|-----------|--------------|-----------------------------|
| mini‑xlsum text corpus | `https://huggingface.co/datasets/gsstein/mini-xlsum/resolve/main/data/test-00000-of-00001.parquet` | **NO** – lacks all survey variables |
| 0‑percent‑human text corpus | `https://huggingface.co/datasets/gsstein/0-percent-human-dataset-og/resolve/main/data/test-00000-of-00001.parquet` | **NO** – lacks all survey variables |
| 100‑percent‑human text corpus | `https://huggingface.co/datasets/gsstein/100-percent-human-dataset/resolve/main/data/test-00000-of-00001.parquet` | **NO** – lacks all survey variables |
| YouGov surveys | — (no verified source) | **NO** – not programmatically downloadable |

**Conclusion**: *None* of the verified datasets includes the six required columns (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement`). Consequently, the pipeline will **download the three files, record their true column inventories, and halt at schema validation** (FR‑001 edge case). A suitable open dataset must be provided for any statistical analysis to proceed.

## Task Outline (high‑level; `tasks.md` will be generated later)

| Phase | Task ID | Description | Dependencies | Notes |
|-------|---------|-------------|--------------|-------|
| 0 | T001 | Pin random seeds; create directory scaffolding (`data/`, `output/`, `artifacts/`) | – | Constitution I |
| 1 | T010 | Download the three verified parquet URLs, compute SHA‑256, store under `data/raw/` | T001 | FR‑001 |
| 2 | T011 | Record checksums & column inventories; validate against `contracts/dataset.schema.yaml` | T010 | FR‑001 edge case |
| 3 | T012 | If a dataset passes validation, **extract rows as `SurveyResponse` entities**, perform listwise deletion of rows missing `news_exposure_freq` or `anxiety_score`; enforce N ≥ 30 hard stop; flag low‑power if 30 ≤ N < 100 | T011 | FR‑002 |
| 4 | T013 | Write cleaned CSV to `data/processed/cleaned_data.csv` (only if T012 succeeds) | T012 | — |
| 5 | T015 | Perform a priori power analysis using target β ≥ 0.10 (f² ≥ 0.02) and Bonferroni‑adjusted α; log required N and warn if actual N < required | T012 | New FR‑009 |
| 6 | T019a | Detect whether `baseline_anxiety` and `anxiety_score` stem from distinct instruments/timepoints (compare `instrument_source` and `measurement_timepoint`); set `coupling_risk` flag; optionally drop `baseline_anxiety` if coupled | T013 | FR‑003 |
| 7 | T018 | Fit OLS regression (`statsmodels.api.OLS`) with covariates; compute VIF | T019a | FR‑003, FR‑007 |
| 8 | T020 | Perform Shapiro‑Wilk on both variables; choose Pearson (if both p > 0.05) **or** Spearman; apply Bonferroni correction (α = 0.05/5); store correlation & CI | T018 | FR‑004 |
| 9 | T022 | Compute `r_engage = corr(social_media_engagement, news_exposure_freq)`; if r > 0.3 **and** variable exists, refit OLS on top‑quartile engagement subset; record robustness result; if gate fails, log warning | T018 | FR‑006 |
| 10 | T023 | Optional bootstrap sensitivity analysis (1 000 resamples) to assess stability of `news_exposure_freq` coefficient; results appended to robustness section | T022 | Extends FR‑006 |
| 11 | T025 | Generate scatter plot with regression line & 95 % CI (`matplotlib`) | T018 | FR‑005 |
| 12 | T030 | Assemble `output/results/regression_results.json` – either full regression fields (`data_status="OK"`) or `HALTED_NO_VALID_DATASET` with nested `halt_report` | T018‑T025 | SSoT |
| 13 | T041 | Run `code/validate_sc.py` against the JSON; write `outputs/success_criteria_log.txt` with PASS/FAIL/BLOCKED per SC‑001 – SC‑005 | T030 | Constitution I |
| 14 | T043 | Update `README.md` with reproducibility instructions, dataset‑availability finding, and results summary (or halt notice) | T041 | Constitution I |
| 15 | T044 | Create `artifacts/project_artifact.zip` containing `code/`, `data/`, `output/`, `outputs/`; compute archive SHA‑256 | T043 | Constitution III |
| 16 | T045 | Write `outputs/signoff_report.json` referencing the archive hash, checksum log, and success‑criteria log; commit | T041‑T044 | Constitution V |

**Ordering rule**: download → checksum → schema validation → cleaning (as `SurveyResponse`) → power analysis → distinctness check → modeling → diagnostics → visualization → validation → documentation → archiving → sign‑off. All tasks produce real, inspectable artifacts; no placeholder files are permitted.

---


## projects/PROJ-540-the-influence-of-social-media-doomscroll/specs/001-the-influence-of-social-media-doomscroll/research.md
# Research: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Research Question
*Does the frequency of negative news consumption on social media associate with elevated anticipatory anxiety scores, independent of baseline anxiety and demographic factors?*  
All statements are explicitly **associational** because the data are observational.

## Theoretical Background
“Doomscrolling” refers to the habitual consumption of negative news on social platforms, which prior work suggests may heighten anticipatory anxiety. Few studies have isolated **negative‑news frequency** while simultaneously controlling for **baseline anxiety**, **age**, and **gender**.

## Dataset Strategy

### Verified Sources (the ONLY citable URLs)

| Dataset | Verified URL | Contains required variables? |
|---------|--------------|------------------------------|
| mini‑xlsum text corpus | `https://huggingface.co/datasets/gsstein/mini-xlsum/resolve/main/data/test-00000-of-00001.parquet` | **NO** – NLP summarization data; lacks all survey variables |
| 0‑percent‑human text corpus | `https://huggingface.co/datasets/gsstein/0-percent-human-dataset-og/resolve/main/data/test-00000-of-00001.parquet` | **NO** – human‑vs‑AI text data; no relevant variables |
| 100‑percent‑human text corpus | `https://huggingface.co/datasets/gsstein/100-percent-human-dataset/resolve/main/data/test-00000-of-00001.parquet` | **NO** – same as above |
| YouGov surveys | — (no verified source) | **NO** – not programmatically downloadable |

**Dataset‑variable fit conclusion (fatal):** *None* of the verified datasets includes the six required columns (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement`). Consequently, the pipeline will **download the three files, record their true column inventories, and halt at schema validation** (FR‑001 edge case). A suitable open dataset must be supplied for any statistical analysis to proceed.

### Variable Mapping (applies when a suitable dataset is added)

| Spec Variable | Expected Column | Validation Rules |
|---------------|----------------|------------------|
| `news_exposure_freq` | `news_exposure_freq` | numeric ≥ 0, non‑null |
| `anxiety_score` | `anxiety_score` | numeric ≥ 0, non‑null |
| `baseline_anxiety` | `baseline_anxiety` | numeric ≥ 0, may be null if instrument overlaps with outcome |
| `age` | `age` | integer 18–100, non‑null |
| `gender` | `gender` | categorical, non‑null |
| `social_media_engagement` | `social_media_engagement` | numeric ≥ 0, optional (required only for robustness check) |
| `instrument_source` | `instrument_source` | string identifying the anxiety scale; must be in the **validated instrument whitelist** (`GAD‑7`, `STAI‑State`, `STAI‑Trait`) |
| `measurement_timepoint` | `measurement_timepoint` | string (e.g., “pre”, “post”, “trait”) |
| `proxy_flag` | `proxy_flag` | boolean – true if `anxiety_score` is a proxy for anticipatory anxiety (FR‑008) |
| `proxy_validated` | `proxy_validated` | boolean – true if the proxy instrument is on the validated whitelist (new field) |

If only a **general anxiety** measure is present, `proxy_flag = true` and the pipeline checks `instrument_source` against the whitelist; `proxy_validated` is set accordingly. If the proxy is not validated, the analysis still runs but the `flags` array will contain `"Proxy Used (unvalidated)"`.

## Data Hygiene & Missing Data
- **Checksum**: SHA‑256 recorded for every raw file under `data/raw/`.  
- **Listwise deletion** on rows missing `news_exposure_freq` or `anxiety_score`; hard stop if resulting N < 30 (FR‑002).  
- **Low‑power warning** if 30 ≤ N < 100 (spec‑defined).  
- No imputation is performed.

## Statistical Methodology

### Primary Model (OLS)
\[
\text{anxiety\_score} = \beta_0 + \beta_1\text{NewsFreq} + \beta_2\text{BaselineAnx} + \beta_3\text{Age} + \beta_4\text{Gender} + \varepsilon
\]

- **Distinctness check**: `baseline_anxiety` is retained only if `instrument_source` **or** `measurement_timepoint` differs from those of `anxiety_score`. If they match, `coupling_risk = true`, the variable is dropped, and a flag is added. (FR‑003, methodology‑d47ed371)
- **Assumption checks**: residuals‑vs‑fitted (linearity), Breusch‑Pagan (homoscedasticity), Shapiro‑Wilk (normality of residuals), VIF > 10 flag (collinearity).  
- **Multiple‑comparison correction**: Bonferroni applied to the four predictors **and** the correlation test (α = 0.05/5).  
- **Power**: A priori analysis (Task T015) computes required N for β ≥ 0.10 (f² ≥ 0.02) with Bonferroni‑adjusted α; logs required N and warns if actual N is lower. (methodology‑76158d41)

### Correlation
- Perform Shapiro‑Wilk on both `news_exposure_freq` and `anxiety_score`.  
- If both p > 0.05, report **Pearson** r; otherwise report **Spearman** ρ.  
- Apply the same Bonferroni α = 0.05/5 used for the regression predictors. (methodology‑8f59a03f)

### Robustness Check (FR‑006)
1. Compute `r_engage = corr(social_media_engagement, news_exposure_freq)`.  
2. If `r_engage > 0.3` **and** the variable exists, refit the OLS on participants whose `social_media_engagement` falls in the top [deferred] percentile.
3. Record the subset coefficient, p‑value, and flag any sign flip or loss of significance.  
4. **Additional safeguard**: run a bootstrap sensitivity analysis (1 000 resamples) to assess stability of the `news_exposure_freq` coefficient; results are stored under `robustness_result.bootstrap`. (methodology‑284ae5c9)

### Multiple Comparisons
- Bonferroni correction is applied uniformly across the five family‑wise tests (four regression predictors + correlation). The adjusted α is used for all p‑value thresholds, satisfying SC‑001.

### Power & Sample‑size
- Required N ≈ 150 for detecting β ≥ 0.10 with 80 % power under the corrected α.  
- If the actual cleaned sample is below this, the `flags` array includes `"Low Power (N < required)"`. No external power calculator is fabricated; the formula is documented in `code/power.py`.

### Collinearity
- VIF computed for each predictor; VIF > 10 triggers a `High VIF` flag and suppresses claims of independent effects (edge case in FR‑003).

### Causal Framing
- All outputs include `"associational_only": true`.

## Decision / Rationale (Compute)
All steps run on CPU using pandas, statsmodels, and matplotlib; the dataset size (three parquet files ≈ < 1 GB) comfortably fits the free‑tier runner. The *real* computation performed in this revision is the download, checksum, and schema‑validation of the three verified files, leading to an honest halt record. This respects the fabrication‑result policy: no numbers are invented; the pipeline reports the genuine mismatch.

## Fabrication‑Result Policy (rev. 2)
- **No synthetic data** are generated.  
- When a required variable is missing, the pipeline **halts** and records a detailed `halt_report`.  
- All JSON, CSV, and plot artifacts contain only values derived from real files.  
- Success‑criteria validation (`code/validate_sc.py`) is executed on the actual outputs; the resulting log is the evidence for SC‑001 – SC‑005.

---


## projects/PROJ-540-the-influence-of-social-media-doomscroll/specs/001-the-influence-of-social-media-doomscroll/data-model.md
# Data Model: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Entity Definitions

### SurveyResponse (cleaned row – only present if a verified dataset passes schema validation)

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| `participant_id` | string | Anonymized unique identifier | non‑null, unique |
| `news_exposure_freq` | number | Frequency of negative news consumption on social media | non‑null, ≥ 0 |
| `anxiety_score` | number | Outcome anxiety score (validated scale or flagged proxy) | non‑null, ≥ 0 |
| `baseline_anxiety` | number | null | Baseline/trait anxiety; may be null if instrument overlaps with outcome; ≥ 0 |
| `age` | integer | Age in years | non‑null, 18 – 100 |
| `gender` | string | Gender category | non‑null, categorical |
| `social_media_engagement` | number | null | Overall social‑media use; required only for robustness check; ≥ 0 |
| `instrument_source` | string | Name of the anxiety instrument (e.g., GAD‑7) | non‑null |
| `measurement_timepoint` | string | Timepoint of measurement (pre, post, trait) | non‑null |
| `proxy_flag` | boolean | True if `anxiety_score` is a proxy for anticipatory anxiety (FR‑008) | non‑null |
| `proxy_validated` | boolean | True if the proxy instrument is in the validated whitelist (new field) | non‑null |
| `coupling_risk` | boolean | True if baseline and outcome anxiety may be mathematically coupled | non‑null |

### RegressionResult (analysis output – always a single JSON file)

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"OLS"` |
| `data_status` | string | `"OK"` when a verified dataset passed validation; `"HALTED_NO_VALID_DATASET"` when ingestion halted (current expected state). |
| `n_samples` | integer | Rows used after listwise deletion (present only when `data_status = "OK"`). |
| `r_squared` | number | Model R² (present only when `data_status = "OK"`). |
| `adj_r_squared` | number | Adjusted R² (present only when `data_status = "OK"`). |
| `f_statistic` | number | Overall F‑statistic (present only when `data_status = "OK"`). |
| `f_pvalue` | number | P‑value for the overall F‑test (present only when `data_status = "OK"`). |
| `coefficients` | object | Mapping *variable → coefficient* (real estimates only). |
| `std_errors` | object | Mapping *variable → standard error*. |
| `p_values` | object | Mapping *variable → two‑sided p‑value*. |
| `vif_scores` | object | Mapping *variable → VIF*; VIF > 10 triggers a flag. |
| `assumption_checks` | object | `{linearity, homoscedasticity, normality, shapiro_wilk_p_value}` (PASS/FAIL/WARNING). |
| `robustness_result` | object | null | If robustness check runs: `{subset_n, coefficient, p_value, status, bootstrap}`; otherwise null. |
| `flags` | array[string] | Warnings such as `"Low Power"`, `"Proxy Used (unvalidated)"`, `"Proxy Used (validated)"`, `"High VIF"`, `"Robustness Skipped (r <= 0.3)"`, `"Associational Only"`. |
| `runtime` | number | Execution time in seconds (SC‑005). |
| `proxy_validated` | boolean | Mirrors the dataset‑level `proxy_validated` flag when a proxy is used (new field). |
| `halt_report` | object | null | Present only when `data_status = "HALTED_NO_VALID_DATASET"`; records sources checked, checksums, column inventories, and missing variables. |

### HaltReport (nested inside `RegressionResult` when ingestion fails)

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"HALTED_NO_VALID_DATASET"` |
| `sources_checked` | array[object] | Each entry: `{url, sha256, row_count}` for the three verified parquet files. |
| `columns_found` | object | Mapping *url → list of column names* actually present. |
| `missing_variables` | array[string] | Required variables absent from **all** sources. |
| `reason` | string | Human‑readable statement of the mismatch (FR‑001 edge case). |

## Data Flow
1. **Ingestion** (`code/ingest.py`): download verified parquet files → `data/raw/`; compute SHA‑256; validate schema against `contracts/dataset.schema.yaml`.  
2. **If validation fails** (current reality): create `output/results/regression_results.json` with `data_status = "HALTED_NO_VALID_DATASET"` and embed a complete `halt_report`; pipeline stops.  
3. **If validation succeeds** (future scenario): clean data → `data/processed/cleaned_data.csv` (rows become `SurveyResponse` entities).  
4. **Modeling** (`code/model.py`): OLS fit, diagnostics, correlation, robustness → populate all fields of `RegressionResult`.  
5. **Visualization** (`code/viz.py`): generate `output/plots/scatter_regression.png`.  
6. **Success‑criteria validation** (`code/validate_sc.py`): read the JSON, write `outputs/success_criteria_log.txt`.  
7. **Archiving & Sign‑off** (`artifacts/project_artifact.zip`, `outputs/signoff_report.json`).

## Assumptions & Constraints
- No imputation; rows with missing predictor/outcome are dropped (listwise deletion).  
- Gender is one‑hot encoded for OLS; continuous predictors remain on original scale.  
- `baseline_anxiety` is dropped (and `coupling_risk = true`) if the same instrument/timepoint is detected as `anxiety_score`.  
- Robustness check runs only when `social_media_engagement` exists **and** `r_engage > 0.3`; otherwise a warning flag is set.  
- All numeric computations use double precision on CPU; no GPU resources required.

---


## projects/PROJ-540-the-influence-of-social-media-doomscroll/specs/001-the-influence-of-social-media-doomscroll/quickstart.md
# Quickstart: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Prerequisites
- Python 3.11 or newer  
- Internet access (to download the three verified parquet files)  
- Linux/macOS environment with at least 2 CPU cores (GitHub Actions free‑tier runner)  
- No GPU required  

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-540-the-influence-of-social-media-doomscroll
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Full Pipeline

```bash
python code/main.py
```

### What the pipeline does
1. **Ingestion** (`code/ingest.py`): downloads the three verified parquet URLs, computes SHA‑256 checksums, and validates each against `contracts/dataset.schema.yaml`.  
   - **Current expected outcome**: none of the files contain the required survey variables, so the pipeline writes `output/results/regression_results.json` with `data_status = "HALTED_NO_VALID_DATASET"` and a detailed `halt_report`. The run then stops, satisfying FR‑001 edge‑case handling.  
   - **Future scenario**: if a verified dataset with the required schema is added, the pipeline proceeds to cleaning, a‑priori power analysis, modeling, and visualization.
2. **Power Analysis** (`code/power.py`): computes required N for β ≥ 0.10 (f² ≥ 0.02) with Bonferroni‑adjusted α; logs a warning if actual N is insufficient.  
3. **Modeling** (`code/model.py`): distinctness check, OLS fit, correlation selection (Bonferroni‑corrected), assumption diagnostics, conditional robustness check (including optional bootstrap).  
4. **Visualization** (`code/viz.py`): creates `output/plots/scatter_regression.png` with regression line and 95 % CI.  
5. **Validation** (`code/validate_sc.py`): inspects `regression_results.json` and writes `outputs/success_criteria_log.txt` with PASS/FAIL/BLOCKED per SC‑001 – SC‑005.  
6. **Sign‑off** (`outputs/signoff_report.json`): references the archive hash, checksum log, and success‑criteria log.  

## Verification Checklist
- `data/raw/` contains the three downloaded parquet files with recorded SHA‑256 checksums.  
- `output/results/regression_results.json` exists and is **the sole source of truth**: either `data_status = "HALTED_NO_VALID_DATASET"` with a nested `halt_report` (the current state) **or** a full regression result set plus flags. No placeholder numbers appear anywhere.  
- `outputs/success_criteria_log.txt` was generated by executing `code/validate_sc.py` (not hand‑written).  
- `artifacts/project_artifact.zip` exists and contains `code/`, `data/`, `output/`, and `outputs/`.  
- Runtime reported in the JSON is ≤ 60 s (SC‑005).  

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| Halt at schema validation | No verified dataset contains required columns (current known state) | Expected behavior per FR‑001. To obtain statistical results, add a verified open dataset that matches the required schema and re‑run. **Do not fabricate data.** |
| N < 30 after cleaning | Excessive missingness in a future valid dataset | Hard stop per FR‑002; cannot proceed. |
| VIF > 10 | Predictor collinearity (e.g., `baseline_anxiety` derived from `anxiety_score`) | Review `vif_scores` in the JSON; the pipeline will flag `High VIF` and suppress independent‑effect claims. |
| Robustness skipped | `social_media_engagement` missing or `r_engage` ≤ 0.3 | Expected per FR‑006; check the `flags` array for `"Robustness Skipped (r <= 0.3)"`. |
| Proxy used but unvalidated | `instrument_source` not in the whitelist | The `flags` array will contain `"Proxy Used (unvalidated)"`; consider providing a dataset with a validated instrument. |

---


## projects/PROJ-540-the-influence-of-social-media-doomscroll/specs/001-the-influence-of-social-media-doomscroll/contracts/output.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Regression Analysis Output"
type: "object"
properties:
  model_type:
    type: "string"
    const: "OLS"
  data_status:
    type: "string"
    enum: ["OK", "HALTED_NO_VALID_DATASET"]
    description: "OK when a verified dataset passed schema validation; HALTED_NO_VALID_DATASET when the pipeline halted at ingestion (statistical fields then omitted, never fabricated)."
  n_samples:
    type: "integer"
    minimum: 30
  r_squared:
    type: "number"
  adj_r_squared:
    type: "number"
  f_statistic:
    type: "number"
  f_pvalue:
    type: "number"
  coefficients:
    type: "object"
    description: "Map of variable names to coefficient values (real estimates only)."
    additionalProperties:
      type: "number"
  std_errors:
    type: "object"
    description: "Map of variable names to standard errors."
    additionalProperties:
      type: "number"
  p_values:
    type: "object"
    description: "Map of variable names to p-values."
    additionalProperties:
      type: "number"
  vif_scores:
    type: "object"
    description: "Map of variable names to VIF scores."
    additionalProperties:
      type: "number"
  assumption_checks:
    type: "object"
    properties:
      linearity:
        type: "string"
        enum: ["PASS", "FAIL", "WARNING"]
      homoscedasticity:
        type: "string"
        enum: ["PASS", "FAIL", "WARNING"]
      normality:
        type: "string"
        enum: ["PASS", "FAIL", "WARNING"]
      shapiro_wilk_p_value:
        type: "number"
    required:
      - linearity
      - homoscedasticity
      - normality
      - shapiro_wilk_p_value
  robustness_result:
    type: ["object", "null"]
    properties:
      subset_n:
        type: "integer"
      coefficient:
        type: "number"
      p_value:
        type: "number"
      status:
        type: "string"
        enum: ["RUN", "SKIPPED_LOW_N", "SKIPPED_NO_DATA", "SKIPPED_R_LOW"]
      bootstrap:
        type: "array"
        description: "Bootstrap coefficient estimates (optional)."
        items:
          type: "number"
    required:
      - status
  flags:
    type: "array"
    items:
      type: "string"
    description: "Warnings such as Low Power, Proxy Used (unvalidated), Proxy Used (validated), High VIF, Robustness Skipped (r <= 0.3), Associational Only."
  runtime:
    type: "number"
    description: "Measured execution time in seconds (SC-005)."
  halt_report:
    type: ["object", "null"]
    description: "Present only when data_status is HALTED_NO_VALID_DATASET; records sources checked, checksums, real column inventories, and missing variables."
  proxy_validated:
    type: "boolean"
    description: "True if a proxy anxiety instrument was used and it is on the validated whitelist."
required:
  - model_type
  - data_status
  - flags
  - runtime
  - proxy_validated
additionalProperties: false