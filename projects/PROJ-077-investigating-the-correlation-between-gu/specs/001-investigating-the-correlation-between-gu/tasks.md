# Tasks: Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance

**Input**: Design documents from `/specs/001-investigating-the-correlation-between-gu/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., User Story 1, User Story 2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize project directory structure: Run the following bash script at the repository root: `mkdir -p data/raw data/processed code tests`. **Verification**: Run `ls -d data/raw data/processed code tests` and verify all four paths are listed. **Execution Context**: Run in bash shell at repo root.

Research Question: What is the correlation between gut microbiome diversity and cognitive performance?
Method: Correlation analysis using processed data.
References: N/A

- [X] T002 [P] Initialize Python project: Create `requirements.txt` at the repository root with the EXACT following content (no extra whitespace, no comments):
```
pandas==2.0.3
numpy==1.24.3
scikit-bio==0.5.9
scikit-learn==1.3.0
statsmodels==0.14.0
matplotlib==3.7.2
seaborn==0.12.2
pyyaml==6.0.1
scipy==1.11.1
```
**Verification**: Verify `requirements.txt` content matches the above exactly using a line-by-line comparison (ignoring trailing newlines).

- [X] T003a [P] Create `pyproject.toml`: Initialize the file at the repository root with the EXACT following content:
```toml
[project]
name = "PROJ-077-investigating-the-correlation-between-gu"
version = "1.0.0"
description = "Gut Microbiome and Cognitive Performance Analysis"
requires-python = ">=3.11"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.flake8]
max-line-length = 88
```

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` defining paths (`INPUT_PATHS` dict), `RANDOM_SEED=42`, `SAMPLE_LIMIT=50000` (Per Plan Complexity Tracking), and configuration flags. **Exact Code**:
```python
import os

INPUT_PATHS = {
 "microbiome": "data/raw/microbiome.csv",
 "cognitive": "data/raw/cognitive.csv",
 "dietary": "data/raw/dietary.csv"
}
RANDOM_SEED = 42
SAMPLE_LIMIT = 50000
DQS_REQUIRED = True
ALLOW_LOCAL_DATA = False
```
`DQS_REQUIRED` is set to True to enforce 'fail loudly' on missing covariates until data is verified. `ALLOW_LOCAL_DATA` is set to False to enforce strict data provenance until verified URLs are provided.

- [X] T005 [P] Implement deterministic data loading utility in `code/data_utils.py` to handle chunked reading of large CSVs. **Exact Function Signature**:
```python
def load_chunked(path: str, chunk_size: int = 10000):
 """
 Loads a CSV in chunks. Raises FileNotFoundError if path does not exist.
 Yields pandas DataFrames.
 """
 if not os.path.exists(path):
 raise FileNotFoundError(f"File not found: {path}")
 for chunk in pd.read_csv(path, chunksize=chunk_size):
 yield chunk
```
**Verification**: Run `python -c "from code.data_utils import load_chunked; list(load_chunked('data/raw/test.csv'))"` on a dummy file and verify it yields chunks.

- [X] T006 [P] Setup logging infrastructure in `code/logging_config.py` to record provenance and warnings (e.g., zero variance detection). **Exact Configuration**:
```python
import logging
import os

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
 filename="logs/provenance.log",
 level=logging.INFO,
 format='%(asctime)s - %(levelname)s - %(message)s',
 datefmt='%Y-%m-%d %H:%M:%S'
)
```

- [X] T049 [P] Create README.md: Initialize `README.md` at the repository root with the EXACT following content:
```markdown
# Gut Microbiome and Cognitive Performance Analysis

## Getting Started
## Prerequisites
- Python 3.11+
## Data Access
1. Apply for UK Biobank access at https://www.ukbiobank.ac.uk/
2. Download microbiome, cognitive, and dietary data.
3. Place files in `data/raw/` with names: `microbiome.csv`, `cognitive.csv`, `dietary.csv`.
4. Ensure checksums match the registry in `state/projects/PROJ-077...yaml`.
```
**Verification**: Verify `README.md` exists and contains the exact text above.

- [X] T050 [P] Implement `code/data_fetcher.py` to load UK Biobank data. **CRITICAL**: If the remote dataset is unavailable and local files are missing, raise `FileNotFoundError` immediately. Do NOT proceed. **Dependency**: T049. **Exact Logic**: Check `ALLOW_LOCAL_DATA`. If False, raise `FileNotFoundError` if files missing. If True, check local files; if missing, raise `FileNotFoundError`.
**Verification**: Run `python -c "from code.data_fetcher import fetch_data; fetch_data()"` without data and verify `FileNotFoundError` is raised.

- [X] T051 [P] Implement streaming loader: Update `code/data_utils.py` to support `streaming=True` via `datasets.load_dataset` or chunked CSV reading. Ensure the `SAMPLE_LIMIT=50000` is enforced via `itertools.islice(stream, SAMPLE_LIMIT)` to hard-stop at 50,000 rows. Log a warning if the stream contained more rows. **Dependency**: T050. **Exact Logic**: `stream = itertools.islice(stream, SAMPLE_LIMIT)`. **Verification**: Run loader on a file with >50k rows and verify output has exactly 50k rows and a warning log.

- [X] T052 [P] Add data provenance check: In `code/main.py` (or a dedicated script), verify that the input files in `data/raw/` match the checksums recorded in `state/projects/PROJ-077-investigating-the-correlation-between-gu.yaml`. **Dependency**: T050. **Execution order**: T052 MUST run BEFORE T011. **Logic**: If files exist, calculate checksums and compare. If mismatch, raise `ValueError`. If registry empty and data expected, raise `FileNotFoundError`. If registry empty and data not expected (fresh run), proceed.
**Verification**: Run the script with mismatched checksums and verify `ValueError` is raised.

- [X] T052a [P] Initialize State Checksum Registry: Create `state/projects/PROJ-077-investigating-the-correlation-between-gu.yaml` if it does not exist. Add an `artifact_hashes` map. **Logic**: If files exist in `data/raw/`, calculate MD5/SHA256 checksums and record them. If `data/raw/` is empty, log a warning and create an empty registry. **Dependency**: T050. **Verification**: Run the script with data files and verify checksums are recorded in the YAML.

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Load UK Biobank data, filter for complete outcomes, and impute covariates correctly (Mode for Sex, Median for others).

**Independent Test**: Run `code/data_ingestion.py` and verify the output CSV contains non-null values for alpha diversity, fluid intelligence, and covariates, with correct imputation logic applied.

- [X] T008a [P] Create test fixture: Generate `tests/fixtures/sample_imputation.csv` with the data described in T009 (columns: age, sex, bmi, dqs, with specific NaN values).
**Verification**: Verify file exists and contains expected columns and NaN values.

- [X] T009 [P] [User Story 1] Write failing test stub `test_imputation_sex_mode_returns_most_frequent` in `tests/unit/test_data_ingestion.py`.
**Verification**: Run `pytest tests/unit/test_data_ingestion.py::test_imputation_sex_mode_returns_most_frequent` and verify it fails as expected.

- [X] T010 [P] [User Story 1] Write failing test stub `test_filtering_excludes_null_primary_outcomes` in `tests/unit/test_data_ingestion.py`.
**Verification**: Run `pytest tests/unit/test_data_ingestion.py::test_filtering_excludes_null_primary_outcomes` and verify it fails as expected.

- [X] T011 [User Story 1] Implement `code/data_ingestion.py` to load raw microbiome and cognitive data from `data/raw/` and merge by participant ID column `participant_id` (FR-001). **Dependency**: T004, T005, T052. **Logic**: Check for column 'participant_id'. If missing, check for 'eid', then 'subject_id'. If multiple candidates exist, prefer 'eid' over 'subject_id'. If none found, raise `FileNotFoundError` with message: "Missing required ID column: expected 'participant_id', 'eid', or 'subject_id'". Merge strategy: `how='inner'`.
**Verification**: Run `python code/data_ingestion.py` on valid data and verify `data/processed/cleaned_data.csv` is created with merged data.

- [X] T012 [User Story 1] Implement filtering logic: In `code/data_ingestion.py`, filter out participants with missing primary outcomes. **Dependency**: T011.
**Verification**: Run on data with missing outcomes and verify they are excluded from output.

- [X] T013 [User Story 1] Implement imputation logic: In `code/data_ingestion.py`, apply Median for Age, BMI, DQS; Mode for Sex. **Dependency**: T012.
**Verification**: Run on data with NaNs and verify imputation values match Median/Mode.

- [X] T015 [User Story 1] Save cleaned dataset: Write the processed DataFrame to `data/processed/cleaned_data.csv`. **Verification**: Verify `data/processed/cleaned_data.csv` exists and has > 1 row.

- [X] T016 [User Story 1] Add error handling: Implement checks for missing files and empty datasets. **Verification**: Run on missing files and verify appropriate error is raised.

## Phase 4: User Story 2 - Correlation and Regression Analysis (Priority: P2)

**Goal**: Compute Shannon index, apply CLR only to taxa (not Shannon), run Spearman correlation, and fit multivariate regression (Primary Path) AND Lasso regression (Secondary Path).

- [X] T017 [P] [User Story 2] Create test fixture: Generate `tests/fixtures/sample_taxa_matrix.csv`.
**Verification**: Verify file exists and contains expected taxa matrix.

- [X] T018 [P] [User Story 2] Create test fixture: Generate `tests/fixtures/sample_clr_taxa.csv`.
**Verification**: Verify file exists and contains CLR-transformed data.

- [X] T019a [P] [User Story 2] Create test fixture: Generate `tests/fixtures/mock_correlation.csv`.
**Verification**: Verify file exists and contains mock correlation data.

- [X] T019b [P] [User Story 2] Write failing test stub `test_spearman_correlation_pvalue_calc` in `tests/integration/test_analysis.py`.
**Verification**: Run `pytest tests/integration/test_analysis.py::test_spearman_correlation_pvalue_calc` and verify it fails as expected.

- [X] T020 [User Story 2] Implement `code/diversity.py` to calculate Shannon Index (alpha diversity) from **raw** counts using `scikit-bio`.
**Verification**: Run on raw counts and verify Shannon index is calculated correctly.

- [X] T020b [User Story 2] Verify Input Integrity: Implement a validation function in `code/diversity.py` to raise ValueError if input is float, and add a unit test in `tests/unit/test_diversity.py` verifying this exception is raised for float inputs.
**Verification**: Run `pytest tests/unit/test_diversity.py` and verify the test passes.

- [X] T021 [User Story 2] Implement `code/transformation.py` to apply Centered Log-Ratio (CLR) transformation **only** to taxa abundance matrices (Secondary Path).
**Verification**: Run on taxa matrix and verify CLR output matches expected values.

- [X] T022 [User Story 2] Implement Spearman rank correlation in `code/analysis.py` between **raw** `shannon_index` and fluid intelligence. **Verification**: Check that `data/processed/correlation_results.csv` exists and contains columns `r_value`, `p_value`, `n_obs`.

- [X] T023 [User Story 2] Implement multivariate linear regression (Primary Path) in `code/analysis.py` using `statsmodels`. **Dependency**: T015. **Logic**: Handle missing DQS gracefully if `DQS_REQUIRED` is False (exclude column), else raise error.
**Verification**: Run on cleaned data and verify regression coefficients are calculated.

- [X] T024 [User Story 2] Implement multicollinearity diagnostics (VIF) in `code/analysis.py`. **Verification**: Save VIF values to `data/processed/vif_results.json` and verify JSON contains keys for all predictors and values > 0.

- [X] T025b [User Story 2] Implement Residual Normality Validation (Primary Path). **Verification**: Save report to `data/processed/regression_diagnostics.json` and verify it contains a key `shapiro_p_value`.

- [X] T025c [User Story 2] Implement Residual Normality Validation (Secondary Path). **Verification**: Save report to `data/processed/lasso_diagnostics.json` and verify it contains a key `shapiro_p_value`.

- [X] T026 [User Story 2] Save correlation results: Write `r_value`, `p_value`, `n_obs` to `data/processed/correlation_results.csv`. **Verification**: Verify CSV exists and has correct columns.

- [X] T027 [User Story 2] Save regression summary: Write `coefficient`, `std_err`, `p_value` for all predictors (Primary Path) to `data/processed/regression_results.csv`. **Verification**: Verify CSV exists and has correct columns.

- [X] T028 [User Story 2] Implement validation script `code/validate_sc001.py`. **Verification**: Run script and verify it exits with code 0.

- [X] T029 [User Story 2] Implement validation script `code/validate_sc002.py`. **Verification**: Run script and verify it exits with code 0.

- [X] T029a [User Story 2] Implement Lasso regression. **Dependency**: T021, T015. **Logic**: Use CLR-transformed taxa.
**Verification**: Run on CLR data and verify Lasso coefficients are calculated.

- [X] T029b [User Story 2] Save Lasso results: Write Lasso coefficients, non-zero feature count, and performance metrics to `data/processed/lasso_results.csv`. **Verification**: Verify CSV has columns `coefficient`, `non_zero_features`, `cv_score`.

- [X] T029c [User Story 2] Implement Residual Normality Validation (Secondary Path). **Verification**: Save report to `data/processed/lasso_diagnostics.json` and verify it contains a key `shapiro_p_value`.

## Phase 5: User Story 3 - Statistical Correction and Visualization (Priority: P3)

**Goal**: Apply FDR correction to p-values and generate publication-quality plots.

- [X] T030 [User Story 3] Implement FDR correction (Benjamini-Hochberg) in `code/analysis.py`.
**Verification**: Run on mock p-values and verify q-values are calculated correctly.

- [X] T031 [P] [User Story 3] Create test fixture: Generate `tests/fixtures/mock_plot_data.csv`.
**Verification**: Verify file exists and contains expected plot data.

- [X] T032 [User Story 3] Implement FDR correction in `code/analysis.py`. **Verification**: Verify `data/processed/corrected_results.csv` contains column `q_value` and values are <= 1.0.

- [X] T033 [User Story 3] Save corrected q-values: Write the adjusted p-values to `data/processed/corrected_results.csv`. **Verification**: Verify CSV has column `q_value` and row count matches input.

- [X] T034a [User Story 3] Implement scatter plot generation: In `code/visualization.py`, generate the scatter plot object.
**Verification**: Run on data and verify plot object is created.

- [X] T034b [User Story 3] Save scatter plot: Save the plot object to `data/processed/plots/scatter_shannon_fi.png`. **Verification**: Verify file exists and is > 1KB.

- [X] T035 [User Story 3] Implement histogram generation: In `code/visualization.py`, generate the histogram.
**Verification**: Run on data and verify histogram is created.

- [X] T036 [User Story 3] Save plots: Ensure all plots are saved as high-resolution PNGs to `data/processed/plots/`. **Verification**: Verify all expected PNG files exist in the directory and are > 1KB.

- [X] T037 [User Story 3] Implement negative result labeling: If all q-values > 0.05, generate a report file `data/processed/negative_results_report.txt` explicitly stating "No significant association found". **Verification**: Verify file exists and contains the exact text "No significant association found".

- [X] T039 [User Story 3] Implement validation script `code/validate_sc003.py`. **Verification**: Run the script and verify it exits with code 0 if all q-values < 0.05, else 1.

- [X] T039b [User Story 3] Implement validation script `code/validate_data_completeness.py`. **Verification**: Run the script and verify it logs 'PASS' or 'FAIL' based on the metric.

## Phase N: Polish & Cross-Cutting Concerns

- [X] T040 [P] Create `code/main.py` to orchestrate the full pipeline. **Verification**: Run `python code/main.py --config config.yaml` and verify exit code 0.

- [X] T041 [P] Write `README.md` with instructions to run the pipeline and expected outputs. **Verification**: Verify `README.md` contains sections: "Installation", "Running the Pipeline", "Expected Outputs" with at least one sentence each.

- [X] T042 [P] Add `pytest` configuration and run full test suite to ensure CI compatibility. **Verification**: Run `pytest` and verify all tests pass.

- [X] T043 [P] Verify all output files match the schema defined in `contracts/`. **Verification**: Run `python code/validate_schemas.py` and verify it exits with code 0.

- [X] T044 [P] Run quickstart.md validation to ensure the project is reproducible in a fresh environment. **Verification**: Verify the virtualenv creation, pip install, and main.py execution all complete with exit code 0.