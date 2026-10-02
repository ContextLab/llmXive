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

- [X] T001 [P] Initialize project directory structure: Use Python's `os.makedirs` to create directories at `projects/PROJ-077-investigating-the-correlation-between-gu/`: `data/raw`, `data/processed`, `code`, `tests`, `logs`. **Verification**: Run `ls -d projects/PROJ-077-investigating-the-correlation-between-gu/data/raw projects/PROJ-077-investigating-the-correlation-between-gu/data/processed projects/PROJ-077-investigating-the-correlation-between-gu/code projects/PROJ-077-investigating-the-correlation-between-gu/tests projects/PROJ-077-investigating-the-correlation-between-gu/logs` and verify all paths are listed. **Execution Context**: Run in Python script at repo root.

Research Question: What is the correlation between gut microbiome diversity and cognitive performance?
Method: Correlation analysis using processed data.
References: N/A

- [X] T002a [P] Initialize Python project: Create `projects/PROJ-077-investigating-the-correlation-between-gu/requirements.txt` with the EXACT following content (no extra whitespace, no comments):
```
pandas==2.0.3
numpy==1.24.3
scikit-bio==0.5.9
```
**Verification**: Verify `projects/PROJ-077-investigating-the-correlation-between-gu/requirements.txt` content matches the above exactly using a line-by-line comparison (ignoring trailing newlines).

- [X] T002b [P] Initialize Python project: Append to `projects/PROJ-077-investigating-the-correlation-between-gu/requirements.txt` the EXACT following content (no extra whitespace, no comments):
```
scikit-learn==1.3.0
statsmodels==0.14.0
matplotlib==3.7.2
seaborn==0.12.2
pyyaml==6.0.1
scipy==1.11.1
```
**Verification**: Verify `projects/PROJ-077-investigating-the-correlation-between-gu/requirements.txt` content matches the combined content of T002a and T002b exactly using a line-by-line comparison (ignoring trailing newlines).

- [X] T003a [P] Create `pyproject.toml`: Initialize the file at `projects/PROJ-077-investigating-the-correlation-between-gu/pyproject.toml` with the EXACT following content:
```toml
[project]
name = "PROJ-077-investigating-the-correlation-between-gu"
version = "1.0.0"
description = "Gut Microbiome and Cognitive Performance Analysis"
requires-python = ">=3.11"
```
**Verification**: Verify `projects/PROJ-077-investigating-the-correlation-between-gu/pyproject.toml` content matches the above exactly using a line-by-line comparison (ignoring trailing newlines).

- [X] T003b [P] Create `pyproject.toml`: Append to `projects/PROJ-077-investigating-the-correlation-between-gu/pyproject.toml` the EXACT following content:
```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.flake8]
max-line-length = 88
```
**Verification**: Verify `projects/PROJ-077-investigating-the-correlation-between-gu/pyproject.toml` content matches the combined content of T003a and T003b exactly using a line-by-line comparison (ignoring trailing newlines).

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Create `projects/PROJ-077-investigating-the-correlation-between-gu/code/config.py` defining paths (`INPUT_PATHS` dict) and `RANDOM_SEED=42`, `SAMPLE_LIMIT=50000`. **Exact Code**:
```python
import os

INPUT_PATHS = {
 "microbiome": "data/raw/microbiome.csv",
 "cognitive": "data/raw/cognitive.csv",
 "dietary": "data/raw/dietary.csv"
}
RANDOM_SEED = 42
SAMPLE_LIMIT = 50000
```
**Verification**: Verify `projects/PROJ-077-investigating-the-correlation-between-gu/code/config.py` content matches the above exactly using a line-by-line comparison (ignoring trailing newlines).

- [X] T004b [P] Create `projects/PROJ-077-investigating-the-correlation-between-gu/code/config.py` appending configuration flags. **Exact Code**:
```python
DQS_REQUIRED = False
ALLOW_LOCAL_DATA = True
```
**Verification**: Verify `projects/PROJ-077-investigating-the-correlation-between-gu/code/config.py` content matches the combined content of T004a and T004b exactly using a line-by-line comparison (ignoring trailing newlines).

- [X] T051a [P] Implement streaming loader: Update `projects/PROJ-077-investigating-the-correlation-between-gu/code/data_utils.py` to support `streaming=True` via `datasets.load_dataset` or chunked CSV reading. Ensure the `SAMPLE_LIMIT=50000` is enforced via `itertools.islice(stream, SAMPLE_LIMIT)` to hard-stop at 50,000 rows. Log a warning if the stream contained more rows. **Dependency**: None. **Exact Logic**: `stream = itertools.islice(stream, SAMPLE_LIMIT)`. **Verification**: Run loader on a file with >50k rows and verify output has exactly 50k rows and a warning log.

- [X] T051b [P] Implement streaming loader: Update `projects/PROJ-077-investigating-the-correlation-between-gu/code/data_utils.py` to log a warning if the stream contained more rows than `SAMPLE_LIMIT`. **Dependency**: T051a. **Verification**: Run loader on a file with >50k rows and verify warning log is present.

- [X] T050a [P] [User Story 1] Implement `projects/PROJ-077-investigating-the-correlation-between-gu/code/data_fetcher.py` to validate UK Biobank data presence. **CRITICAL**: This task implements the Spec's 'CRITICAL REPRODUCIBILITY CLAUSE'. It checks `data/raw/` for expected files.
**Logic**:
1. Check `data/raw/` for expected files (`microbiome.csv`, `cognitive.csv`, `dietary.csv`).
2. If files exist -> Return success (set 'data_source' flag).
**Dependency**: T051.
**Verification**: Run `python -c "from code.data_fetcher import validate_data; validate_data()"` with data and verify success.

- [X] T050b [P] [User Story 1] Implement `projects/PROJ-077-investigating-the-correlation-between-gu/code/data_fetcher.py` error handling.
**Logic**:
3. If files missing -> Raise `FileNotFoundError` with message "Data files missing. Please place UK Biobank data in data/raw/."
**Dependency**: T050a.
**Verification**: Run `python -c "from code.data_fetcher import validate_data; validate_data()"` without data and verify `FileNotFoundError` is raised.

- [X] T052a-1 [P] Initialize State Checksum Registry: Create `state/projects/PROJ-077-investigating-the-correlation-between-gu.yaml` if it does not exist. Add an `artifact_hashes` map. **Logic**: If files exist in `data/raw/`, calculate MD5/SHA256 checksums and record them. If `data/raw/` is empty, log a warning and create an empty registry. **Dependency**: T050. **Verification**: Run the script with data files and verify checksums are recorded in the YAML.

- [X] T052a-2 [P] Initialize State Checksum Registry: Calculate MD5/SHA256 checksums for files in `data/raw/` and record them in `state/projects/PROJ-077-investigating-the-correlation-between-gu.yaml`. **Dependency**: T052a-1. **Verification**: Run the script with data files and verify checksums are recorded in the YAML.

- [X] T052-1 [P] Add data provenance check: In `projects/PROJ-077-investigating-the-correlation-between-gu/code/main.py` (or a dedicated script), calculate checksums for input files in `data/raw/`. **Dependency**: T052a (registry created). **Execution order**: T052 MUST run AFTER T052a. **Logic**: If files exist, calculate checksums. **Verification**: Run the script with data files and verify checksums are calculated.

- [X] T052-2 [P] Add data provenance check: Compare calculated checksums with those recorded in `state/projects/PROJ-077-investigating-the-correlation-between-gu.yaml`. **Dependency**: T052-1. **Execution order**: T052 MUST run AFTER T052a. **Logic**: If mismatch, raise `ValueError`. If registry empty and data expected, raise `FileNotFoundError`. If registry empty and data not expected (fresh run), proceed.
**Verification**: Run the script with mismatched checksums and verify `ValueError` is raised.

- [X] T005a [P] Implement deterministic data loading utility in `projects/PROJ-077-investigating-the-correlation-between-gu/code/data_utils.py` to handle chunked reading of large CSVs. **Exact Function Signature**:
```python
def load_chunked(path: str, chunk_size: int = 10000):
 """
 Loads a CSV in chunks. Raises FileNotFoundError if path does not exist.
 Yields pandas DataFrames.
 """
 if not os.path.exists(path):
 raise FileNotFoundError(f"File not found: {path}")
```
**Verification**: Run `python -c "from code.data_utils import load_chunked; list(load_chunked('data/raw/test.csv'))"` on a dummy file and verify it yields chunks.

- [X] T005b [P] Implement deterministic data loading utility in `projects/PROJ-077-investigating-the-correlation-between-gu/code/data_utils.py` to handle chunked reading of large CSVs. **Exact Function Signature**:
```python
 for chunk in pd.read_csv(path, chunksize=chunk_size):
 yield chunk
```
**Verification**: Run `python -c "from code.data_utils import load_chunked; list(load_chunked('data/raw/test.csv'))"` on a dummy file and verify it yields chunks.

- [X] T006a [P] Setup logging infrastructure in `projects/PROJ-077-investigating-the-correlation-between-gu/code/logging_config.py` to record provenance and warnings (e.g., zero variance detection). **Exact Configuration**:
```python
import logging
import os

os.makedirs("logs", exist_ok=True)
```
**Verification**: Verify `projects/PROJ-077-investigating-the-correlation-between-gu/code/logging_config.py` content matches the above exactly using a line-by-line comparison (ignoring trailing newlines).

- [X] T006b [P] Setup logging infrastructure in `projects/PROJ-077-investigating-the-correlation-between-gu/code/logging_config.py` to record provenance and warnings (e.g., zero variance detection). **Exact Configuration**:
```python
logging.basicConfig(
 filename="logs/provenance.log",
 level=logging.INFO,
 format='%(asctime)s - %(levelname)s - %(message)s',
 datefmt='%Y-%m-%d %H:%M:%S'
)
```
**Verification**: Verify `projects/PROJ-077-investigating-the-correlation-between-gu/code/logging_config.py` content matches the combined content of T006a and T006b exactly using a line-by-line comparison (ignoring trailing newlines).

- [X] T049a [P] Create README.md: Initialize `README.md` at `projects/PROJ-077-investigating-the-correlation-between-gu/README.md` with the EXACT following content:
```markdown
# Gut Microbiome and Cognitive Performance Analysis

## Getting Started
## Prerequisites
- Python 3.11+
```
**Verification**: Verify `README.md` exists and contains the exact text above. **Dependency**: T052a.

- [X] T049b [P] Create README.md: Append to `README.md` at `projects/PROJ-077-investigating-the-correlation-between-gu/README.md` with the EXACT following content:
```markdown
## Data Access
1. Apply for UK Biobank access at https://www.ukbiobank.ac.uk/
2. Download microbiome, cognitive, and dietary data.
3. Place files in `data/raw/` with names: `microbiome.csv`, `cognitive.csv`, `dietary.csv`.
4. Ensure checksums match the registry in `state/projects/PROJ-077...yaml`.
```
**Verification**: Verify `README.md` exists and contains the exact text above. **Dependency**: T049a.

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Load UK Biobank data, filter for complete outcomes, and impute covariates correctly (Mode for Sex, Median for others).

**Independent Test**: Run `code/data_ingestion.py` and verify the output CSV contains non-null values for alpha diversity, fluid intelligence, and covariates, with correct imputation logic applied.

- [X] T008a-1 [P] Create test fixture: Generate `tests/fixtures/sample_imputation.csv` with the data described in T009 (columns: age, sex, bmi, dq, with specific NaN values).
**Verification**: Verify file exists and contains expected columns and NaN values.

- [X] T008a-2 [P] Create test fixture: Verify `tests/fixtures/sample_imputation.csv` contains expected columns and NaN values.
**Verification**: Verify file exists and contains expected columns and NaN values.

- [X] T011a-1 [P] [User Story 1] Load raw microbiome data from `data/raw/` into a DataFrame. **Dependency**: T052. **Logic**: Check for column 'participant_id'. If missing, check for 'eid', then 'subject_id'. **Verification**: Run `python code/data_ingestion.py` on valid data and verify DataFrame is loaded.

- [X] T011a-2 [P] [User Story 1] Load raw cognitive data from `data/raw/` into a DataFrame. **Dependency**: T052. **Logic**: Check for column 'participant_id'. If missing, check for 'eid', then 'subject_id'. **Verification**: Run `python code/data_ingestion.py` on valid data and verify DataFrame is loaded.

- [X] T011b-1 [P] [User Story 1] Merge DataFrames by participant ID with fallback logic. **Dependency**: T011a. **Logic**: Merge strategy: `how='inner'`. **Verification**: Run on valid data and verify merged DataFrame has correct rows.

- [X] T011b-2 [P] [User Story 1] Merge DataFrames by participant ID with fallback logic. **Dependency**: T011a. **Logic**: Merge strategy: `how='inner'`. **Verification**: Run on valid data and verify merged DataFrame has correct rows.

- [X] T011c-1 [P] [User Story 1] Validate merged schema. **Dependency**: T011b. **Logic**: Ensure required columns exist. **Verification**: Run on valid data and verify schema matches expectations.

- [X] T011c-2 [P] [User Story 1] Validate merged schema. **Dependency**: T011b. **Logic**: Ensure required columns exist. **Verification**: Run on valid data and verify schema matches expectations.

- [X] T012a [P] [User Story 1] Implement filtering logic: In `code/data_ingestion.py`, filter out participants with missing primary outcomes. **Dependency**: T011c.
**Verification**: Run on data with missing outcomes and verify they are excluded from output.

- [X] T012b [P] [User Story 1] Implement filtering logic: In `code/data_ingestion.py`, filter out participants with missing primary outcomes. **Dependency**: T011c.
**Verification**: Run on data with missing outcomes and verify they are excluded from output.

- [X] T013a [P] [User Story 1] Implement imputation logic: In `code/data_ingestion.py`, apply Median for Age, BMI, DQS; Mode for Sex. **CRITICAL**: This task implements the corrected logic from the Plan's 'Spec Conflict Resolution' table (replacing Spec's erroneous 'median for sex' with 'Mode for Sex'). See Plan.md: Spec Conflict Resolution, FR-007 correction. **Dependency**: T012.
**Verification**: Run on data with NaNs and verify imputation values match Median/Mode.

- [X] T013b [P] [User Story 1] Implement imputation logic: In `code/data_ingestion.py`, apply Median for Age, BMI, DQS; Mode for Sex. **CRITICAL**: This task implements the corrected logic from the Plan's 'Spec Conflict Resolution' table (replacing Spec's erroneous 'median for sex' with 'Mode for Sex'). See Plan.md: Spec Conflict Resolution, FR-007 correction. **Dependency**: T012.
**Verification**: Run on data with NaNs and verify imputation values match Median/Mode.

- [ ] T009a [P] [User Story 1] Write failing test stub `test_imputation_sex_mode_returns_most_frequent` in `tests/unit/test_data_ingestion.py`. **Details**: Create a test that initially uses `pytest.skip('Implement T013 first')` or `assert False`. Once T013 is implemented, update the test to assert that the `sex` column (with NaNs) is filled with the mode (e.g., "Male"). The test should verify the imputation logic matches the Plan's correction. **Dependency**: T013. **Verification**: Run `pytest tests/unit/test_data_ingestion.py::test_imputation_sex_mode_returns_most_frequent` and verify it passes after T013 is implemented.

- [ ] T009b [P] [User Story 1] Write failing test stub `test_imputation_sex_mode_returns_most_frequent` in `tests/unit/test_data_ingestion.py`. **Details**: Create a test that initially uses `pytest.skip('Implement T013 first')` or `assert False`. Once T013 is implemented, update the test to assert that the `sex` column (with NaNs) is filled with the mode (e.g., "Male"). The test should verify the imputation logic matches the Plan's correction. **Dependency**: T013. **Verification**: Run `pytest tests/unit/test_data_ingestion.py::test_imputation_sex_mode_returns_most_frequent` and verify it passes after T013 is implemented.

- [ ] T010a [P] [User Story 1] Write failing test stub `test_filtering_excludes_null_primary_outcomes` in `tests/unit/test_data_ingestion.py`. **Details**: Create a test that initially uses `pytest.skip('Implement T012 first')` or `assert False`. Once T012 is implemented, update the test to assert that rows with NaN `fluid_intelligence_score` are removed. **Dependency**: T012. **Verification**: Run `pytest tests/unit/test_data_ingestion.py::test_filtering_excludes_null_primary_outcomes` and verify it passes after T012 is implemented.

- [ ] T010b [P] [User Story 1] Write failing test stub `test_filtering_excludes_null_primary_outcomes` in `tests/unit/test_data_ingestion.py`. **Details**: Create a test that initially uses `pytest.skip('Implement T012 first')` or `assert False`. Once T012 is implemented, update the test to assert that rows with NaN `fluid_intelligence_score` are removed. **Dependency**: T012. **Verification**: Run `pytest tests/unit/test_data_ingestion.py::test_filtering_excludes_null_primary_outcomes` and verify it passes after T012 is implemented.

- [X] T015a [P] [User Story 1] Save cleaned dataset: Write the processed DataFrame to `data/processed/cleaned_data.csv`. **Verification**: Verify `data/processed/cleaned_data.csv` exists and has > 1 row.

- [X] T015b [P] [User Story 1] Save cleaned dataset: Write the processed DataFrame to `data/processed/cleaned_data.csv`. **Verification**: Verify `data/processed/cleaned_data.csv` exists and has > 1 row.

- [X] T016a [P] [User Story 1] Add error handling: Implement checks for missing files and empty datasets. **Verification**: Run on missing files and verify appropriate error is raised.

- [X] T016b [P] [User Story 1] Add error handling: Implement checks for missing files and empty datasets. **Verification**: Run on missing files and verify appropriate error is raised.

## Phase 4: User Story 2 - Correlation and Regression Analysis (Priority: P2)

**Goal**: Compute Shannon index, apply CLR only to taxa (not Shannon), run Spearman correlation, and fit multivariate regression (Primary Path) AND Lasso regression (Secondary Path).

- [X] T017a [P] [User Story 2] Create test fixture: Generate `tests/fixtures/sample_taxa_matrix.csv`.
**Verification**: Verify file exists and contains expected taxa matrix.

- [X] T017b [P] [User Story 2] Create test fixture: Generate `tests/fixtures/sample_taxa_matrix.csv`.
**Verification**: Verify file exists and contains expected taxa matrix.

- [X] T018a [P] [User Story 2] Create test fixture: Generate `tests/fixtures/sample_clr_taxa.csv`.
**Verification**: Verify file exists and contains CLR-transformed data.

- [X] T018b [P] [User Story 2] Create test fixture: Generate `tests/fixtures/sample_clr_taxa.csv`.
**Verification**: Verify file exists and contains CLR-transformed data.

- [X] T019a-1 [P] [User Story 2] Create test fixture: Generate `tests/fixtures/mock_correlation.csv`.
**Verification**: Verify file exists and contains mock correlation data.

- [X] T019a-2 [P] [User Story 2] Create test fixture: Generate `tests/fixtures/mock_correlation.csv`.
**Verification**: Verify file exists and contains mock correlation data.

- [X] T019b-1 [P] [User Story 2] Write failing test stub `test_spearman_correlation_pvalue_calc` in `tests/integration/test_analysis.py`.
**Verification**: Run `pytest tests/integration/test_analysis.py::test_spearman_correlation_pvalue_calc` and verify it fails as expected.

- [X] T019b-2 [P] [User Story 2] Write failing test stub `test_spearman_correlation_pvalue_calc` in `tests/integration/test_analysis.py`.
**Verification**: Run `pytest tests/integration/test_analysis.py::test_spearman_correlation_pvalue_calc` and verify it fails as expected.

- [X] T020a [P] [User Story 2] Implement `code/diversity.py` to calculate Shannon Index (alpha diversity) from **raw** counts using `scikit-bio`. **Dependency**: T011a. **Verification**: Run on raw counts and verify Shannon index is calculated correctly.

- [X] T020b [P] [User Story 2] Verify Input Integrity: Implement a validation function in `code/diversity.py` to raise ValueError if input is non-numeric or malformed. The input can be integer counts or float relative abundances; both are valid per Spec. **Dependency**: T020. **Verification**: Run `pytest tests/unit/test_diversity.py` and verify the test passes.

- [X] T021a [P] [User Story 2] Implement `code/transformation.py` to apply Centered Log-Ratio (CLR) transformation **only** to taxa abundance matrices (Secondary Path). **Dependency**: T011a. **Verification**: Run on taxa matrix and verify CLR output matches expected values.

- [X] T021b [P] [User Story 2] Implement `code/transformation.py` to apply Centered Log-Ratio (CLR) transformation **only** to taxa abundance matrices (Secondary Path). **Dependency**: T011a. **Verification**: Run on taxa matrix and verify CLR output matches expected values.

- [X] T022a [P] [User Story 2] Implement Spearman rank correlation in `code/analysis.py` between **raw** `shannon_index` and fluid intelligence and save results to `data/processed/correlation_results.csv`. **CRITICAL**: This task explicitly uses RAW Shannon Index, adhering to the Plan's correction of the Spec's erroneous CLR requirement (see Plan.md: Spec Conflict Resolution, FR-003 correction). The task MUST NOT apply CLR to the Shannon Index. **Dependency**: T020. **Verification**: Check that `data/processed/correlation_results.csv` exists and contains columns `r_value`, `p_value`, `n_obs`.

- [X] T022b [P] [User Story 2] Implement Spearman rank correlation in `code/analysis.py` between **raw** `shannon_index` and fluid intelligence and save results to `data/processed/correlation_results.csv`. **CRITICAL**: This task explicitly uses RAW Shannon Index, adhering to the Plan's correction of the Spec's erroneous CLR requirement (see Plan.md: Spec Conflict Resolution, FR-003 correction). The task MUST NOT apply CLR to the Shannon Index. **Dependency**: T020. **Verification**: Check that `data/processed/correlation_results.csv` exists and contains columns `r_value`, `p_value`, `n_obs`.

- [X] T023a-1 [P] [User Story 2] Prepare feature matrix for regression: Handle missing DQS gracefully if `DQS_REQUIRED` is False (exclude column), else raise error. **Dependency**: T015. **Verification**: Run on cleaned data and verify feature matrix is prepared correctly.

- [X] T023a-2 [P] [User Story 2] Prepare feature matrix for regression: Handle missing DQS gracefully if `DQS_REQUIRED` is False (exclude column), else raise error. **Dependency**: T015. **Verification**: Run on cleaned data and verify feature matrix is prepared correctly.

- [X] T023b-1 [P] [User Story 2] Fit multivariate linear regression (Primary Path) in `code/analysis.py` using `statsmodels`. **Dependency**: T023a. **Verification**: Run on cleaned data and verify regression coefficients are calculated.

- [X] T023b-2 [P] [User Story 2] Fit multivariate linear regression (Primary Path) in `code/analysis.py` using `statsmodels`. **Dependency**: T023a. **Verification**: Run on cleaned data and verify regression coefficients are calculated.

- [X] T023c-1 [P] [User Story 2] Extract coefficients: Write `coefficient`, `std_err`, `p_value` for all predictors (Primary Path) to `data/processed/regression_results.csv`. **Dependency**: T023b. **Verification**: Verify CSV exists and has correct columns.

- [X] T023c-2 [P] [User Story 2] Extract coefficients: Write `coefficient`, `std_err`, `p_value` for all predictors (Primary Path) to `data/processed/regression_results.csv`. **Dependency**: T023b. **Verification**: Verify CSV exists and has correct columns.

- [X] T024a [P] [User Story 2] Implement multicollinearity diagnostics (VIF) in `code/analysis.py` and save VIF values to `data/processed/vif_results.json`. **Verification**: Save VIF values to `data/processed/vif_results.json` and verify JSON contains keys for all predictors and values > 0.

- [X] T024b [P] [User Story 2] Implement multicollinearity diagnostics (VIF) in `code/analysis.py` and save VIF values to `data/processed/vif_results.json`. **Verification**: Save VIF values to `data/processed/vif_results.json` and verify JSON contains keys for all predictors and values > 0.

- [X] T025b-1 [P] [User Story 2] Implement Residual Normality Validation for the Secondary Path (Lasso/OLS on CLR taxa) and save report to `data/processed/regression_diagnostics.json`. **Dependency**: T041. **Verification**: Save report to `data/processed/regression_diagnostics.json` and verify it contains a key `shapiro_p_value`. **Note**: This validates the Secondary Path as per Plan.md: Statistical Rigor.

- [X] T025b-2 [P] [User Story 2] Implement Residual Normality Validation for the Secondary Path (Lasso/OLS on CLR taxa) and save report to `data/processed/regression_diagnostics.json`. **Dependency**: T041. **Verification**: Save report to `data/processed/regression_diagnostics.json` and verify it contains a key `shapiro_p_value`. **Note**: This validates the Secondary Path as per Plan.md: Statistical Rigor.

- [X] T025c-1 [P] [User Story 2] Implement Residual Normality Validation for the Secondary Path (Lasso) and save report to `data/processed/lasso_diagnostics.json`. **Dependency**: T041. **Verification**: Save report to `data/processed/lasso_diagnostics.json` and verify it contains a key `shapiro_p_value`. **Note**: This validates the Secondary Path as per Plan.md: Statistical Rigor.

- [X] T025c-2 [P] [User Story 2] Implement Residual Normality Validation for the Secondary Path (Lasso) and save report to `data/processed/lasso_diagnostics.json`. **Dependency**: T041. **Verification**: Save report to `data/processed/lasso_diagnostics.json` and verify it contains a key `shapiro_p_value`. **Note**: This validates the Secondary Path as per Plan.md: Statistical Rigor.

- [X] T026a [P] [User Story 2] Save correlation results: Write `r_value`, `p_value`, `n_obs` to `data/processed/correlation_results.csv`. **Verification**: Verify CSV exists and has correct columns.

- [X] T026b [P] [User Story 2] Save correlation results: Write `r_value`, `p_value`, `n_obs` to `data/processed/correlation_results.csv`. **Verification**: Verify CSV exists and has correct columns.

- [X] T027a [P] [User Story 2] Save regression summary: Write `coefficient`, `std_err`, `p_value` for all predictors (Primary Path) to `data/processed/regression_results.csv`. **Verification**: Verify CSV exists and has correct columns.

- [X] T027b [P] [User Story 2] Save regression summary: Write `coefficient`, `std_err`, `p_value` for all predictors (Primary Path) to `data/processed/regression_results.csv`. **Verification**: Verify CSV exists and has correct columns.

- [X] T041a [P] [User Story 2] Implement Lasso regression. **Dependency**: T021, T015. **Logic**: Use CLR-transformed taxa.
**Verification**: Run on CLR data and verify Lasso coefficients are calculated.

- [X] T041b [P] [User Story 2] Implement Lasso regression. **Dependency**: T021, T015. **Logic**: Use CLR-transformed taxa.
**Verification**: Run on CLR data and verify Lasso coefficients are calculated.

- [X] T042a [P] [User Story 2] Save Lasso results: Write Lasso coefficients, non-zero feature count, and performance metrics to `data/processed/lasso_results.csv`. **Verification**: Verify CSV has columns `coefficient`, `non_zero_features`, `cv_score`.

- [X] T042b [P] [User Story 2] Save Lasso results: Write Lasso coefficients, non-zero feature count, and performance metrics to `data/processed/lasso_results.csv`. **Verification**: Verify CSV has columns `coefficient`, `non_zero_features`, `cv_score`.

## Phase 5: User Story 3 - Statistical Correction and Visualization (Priority: P3)

**Goal**: Apply FDR correction to p-values and generate publication-quality plots.

- [X] T043a [P] [User Story 3] Implement FDR correction (Benjamini-Hochberg) in `code/analysis.py`.
**Verification**: Run on mock p-values and verify q-values are calculated correctly.

- [X] T043b [P] [User Story 3] Implement FDR correction (Benjamini-Hochberg) in `code/analysis.py`.
**Verification**: Run on mock p-values and verify q-values are calculated correctly.

- [X] T044a [P] [User Story 3] Create test fixture: Generate `tests/fixtures/mock_plot_data.csv`.
**Verification**: Verify file exists and contains expected plot data.

- [X] T044b [P] [User Story 3] Create test fixture: Generate `tests/fixtures/mock_plot_data.csv`.
**Verification**: Verify file exists and contains expected plot data.

- [X] T045a [P] [User Story 3] Implement FDR correction in `code/analysis.py`. **Verification**: Verify `data/processed/corrected_results.csv` contains column `q_value` and values are <= 1.0.

- [X] T045b [P] [User Story 3] Implement FDR correction in `code/analysis.py`. **Verification**: Verify `data/processed/corrected_results.csv` contains column `q_value` and values are <= 1.0.

- [X] T046a [P] [User Story 3] Save corrected q-values: Write the adjusted p-values to `data/processed/corrected_results.csv`. **Verification**: Verify CSV has column `q_value` and row count matches input.

- [X] T046b [P] [User Story 3] Save corrected q-values: Write the adjusted p-values to `data/processed/corrected_results.csv`. **Verification**: Verify CSV has column `q_value` and row count matches input.

- [X] T047a [P] [User Story 3] Implement scatter plot generation: In `code/visualization.py`, generate the scatter plot object.
**Verification**: Run on data and verify plot object is created.

- [X] T047b [P] [User Story 3] Implement scatter plot generation: In `code/visualization.py`, generate the scatter plot object.
**Verification**: Run on data and verify plot object is created.

- [X] T048a [P] [User Story 3] Save scatter plot: Save the plot object to `data/processed/plots/scatter_shannon_fi.png`. **Verification**: Verify file exists and is > 1KB.

- [X] T048b [P] [User Story 3] Save scatter plot: Save the plot object to `data/processed/plots/scatter_shannon_fi.png`. **Verification**: Verify file exists and is > 1KB.

- [X] T049a [P] [User Story 3] Implement histogram generation: In `code/visualization.py`, generate the histogram.
**Verification**: Run on data and verify histogram is created.

- [X] T049b [P] [User Story 3] Implement histogram generation: In `code/visualization.py`, generate the histogram.
**Verification**: Run on data and verify histogram is created.

- [X] T050a [P] [User Story 3] Save plots: Ensure all plots are saved as high-resolution PNGs to `data/processed/plots/`. **Verification**: Verify all expected PNG files exist in the directory and are > 1KB.

- [X] T050b [P] [User Story 3] Save plots: Ensure all plots are saved as high-resolution PNGs to `data/processed/plots/`. **Verification**: Verify all expected PNG files exist in the directory and are > 1KB.

- [X] T051a [P] [User Story 3] Implement validation script `code/validate_fdr_method.py`. **Logic**: Load `data/processed/corrected_results.csv`. Verify that the Benjamini-Hochberg correction was applied correctly by checking that q-values are monotonic and <= 1.0. Log the count of significant (q < 0.05) and non-significant features. Exit with code 0 if the method is valid, else exit with code 1. **Dependency**: T045. **Verification**: Run the script with data where q-values are monotonic and <= 1.0 and verify it exits with code 0 and logs "PASS". Run with invalid data and verify it exits with code 1 and logs "FAIL". **Note**: This task validates the FDR method per Plan.md: Statistical Rigor, not the specific outcome.

- [X] T051b [P] [User Story 3] Implement validation script `code/validate_fdr_method.py`. **Logic**: Load `data/processed/corrected_results.csv`. Verify that the Benjamini-Hochberg correction was applied correctly by checking that q-values are monotonic and <= 1.0. Log the count of significant (q < 0.05) and non-significant features. Exit with code 0 if the method is valid, else exit with code 1. **Dependency**: T045. **Verification**: Run the script with data where q-values are monotonic and <= 1.0 and verify it exits with code 0 and logs "PASS". Run with invalid data and verify it exits with code 1 and logs "FAIL". **Note**: This task validates the FDR method per Plan.md: Statistical Rigor, not the specific outcome.

- [X] T052a [P] [User Story 3] Implement validation script `code/validate_data_completeness.py`. **Logic**: Check `data/processed/corrected_results.csv` for non-empty `q_value` column. Log 'PASS' or 'FAIL' based on the metric. **Verification**: Run the script and verify it logs 'PASS' or 'FAIL' based on the metric.

- [X] T052b [P] [User Story 3] Implement validation script `code/validate_data_completeness.py`. **Logic**: Check `data/processed/corrected_results.csv` for non-empty `q_value` column. Log 'PASS' or 'FAIL' based on the metric. **Verification**: Run the script and verify it logs 'PASS' or 'FAIL' based on the metric.

## Phase N: Polish & Cross-Cutting Concerns

- [X] T053a [P] Create `code/main.py` to orchestrate the full pipeline. **Verification**: Run `python code/main.py --config config.yaml` and verify exit code 0.

- [X] T053b [P] Create `code/main.py` to orchestrate the full pipeline. **Verification**: Run `python code/main.py --config config.yaml` and verify exit code 0.

- [X] T054a [P] Write `README.md` with instructions to run the pipeline and expected outputs. **Verification**: Verify `README.md` contains sections: "Installation", "Running the Pipeline", "Expected Outputs" with at least one sentence each.

- [X] T054b [P] Write `README.md` with instructions to run the pipeline and expected outputs. **Verification**: Verify `README.md` contains sections: "Installation", "Running the Pipeline", "Expected Outputs" with at least one sentence each.

- [X] T055a [P] Add `pytest` configuration and run full test suite to ensure CI compatibility. **Verification**: Run `pytest` and verify all tests pass.

- [X] T055b [P] Add `pytest` configuration and run full test suite to ensure CI compatibility. **Verification**: Run `pytest` and verify all tests pass.

- [X] T056a [P] Verify all output files match the schema defined in `contracts/`. **Verification**: Run `python code/validate_schemas.py` and verify it exits with code 0.

- [X] T056b [P] Verify all output files match the schema defined in `contracts/`. **Verification**: Run `python code/validate_schemas.py` and verify it exits with code 0.

- [X] T057a [P] Run quickstart.md validation to ensure the project is reproducible in a fresh environment. **Verification**: Verify the virtualenv creation, pip install, and main.py execution all complete with exit code 0. Run validation on `quickstart.md` at repository root.

- [X] T057b [P] Run quickstart.md validation to ensure the project is reproducible in a fresh environment. **Verification**: Verify the virtualenv creation, pip install, and main.py execution all complete with exit code 0. Run validation on `quickstart.md` at repository root.