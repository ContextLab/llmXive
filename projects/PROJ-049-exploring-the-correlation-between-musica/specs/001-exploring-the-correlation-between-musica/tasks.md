# Tasks: Exploring the Correlation Between Musical Preference and Personality Traits

**Input**: Design documents from `/specs/001-music-personality-correlation/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create directory structure: `data/raw/`, `data/processed/`, `code/`, `tests/`, `results/`, `logs/`. **Verification**: Assert each directory exists after creation.
- [ ] T001b Create empty `__init__.py` files in `code/` and `tests/`
- [ ] T001c Initialize `requirements.txt` with placeholder dependencies
- [ ] T002 Initialize Python project with dependencies in `requirements.txt`. **Content**: Pin exact versions for `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `numpy`, `datasets`, `requests`, `pytest`, `statsmodels`. **Verification**: Run `pip install -r requirements.txt` successfully; ensure all versions are pinned (e.g., `pandas==2.0.0`).
- [ ] T003a Create `.ruff.toml` configuration file for linting. **Content**: Set `line-length = 88`, `target-version = "py311"`, and enable specific rules (E, F, W).
- [ ] T003b Create `pyproject.toml` with `[tool.black]` configuration for formatting. **Content**: Set `line-length = 88`, `target-version = ['py311']`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T005a Implement `setup_logging()` function in `code/utils.py` returning a logger configured with file rotation to `logs/app.log`.
- [ ] T006b Create `.env.example` file listing expected environment variable names (e.g., `RANDOM_SEED`, `DATA_PATH`) with placeholder values.
- [ ] T006c Populate `.env` with default values: `RANDOM_SEED=42` and `DATA_PATH="data"`. **Verification**: Verify file exists and contains these keys.
- [ ] T006a Implement `load_config()` function in `code/utils.py` returning a dict of environment variables (depends on T006c).
- [ ] T007a Create `contracts/` directory. **Verification**: `ls contracts/` must succeed.
- [ ] T007b Define schema fields in `contracts/dataset.schema.yaml` (fields: `user_id`, `openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism`, `age`, `gender`, `country`) and `contracts/analysis_output.schema.yaml` (fields: `trait`, `genre`, `rho`, `p_value`, `adjusted_p_value`, `is_significant`, `beta`, `std_error`, `effect_size_r`, `effect_size_fisher_z`, `significance_status`). **Verification**: Use `pandera` to validate a sample CSV against the schema.
- [ ] T009 Setup error handling wrappers in `code/utils.py` for HTTP timeouts and 404s.
- [ ] T013b Create Genre Lookup Table: `contracts/genre_lookup.yaml` defining mapping from raw tags (e.g., 'alt', 'rock', 'classical') to standardized categories (Rock, Pop, Hip‑Hop, Classical, Electronic, Jazz, Folk, Country, Metal, Other). **Verification**: Verify file exists and contains all 10 categories.
- [ ] T035 Define `contracts/genre_preference.schema.yaml` for the GenrePreference entity (fields: `user_id`, `genre_name`, `listening_minutes`, `genre_score`). **Verification**: Validate a sample CSV with `pandera`.
- [ ] T036 Verify that `data/processed/merged_data.csv` conforms simultaneously to `contracts/dataset.schema.yaml` (UserRecord) and `contracts/genre_preference.schema.yaml` (GenrePreference). Log any mismatches as errors.
- [ ] T037 Verify that `data/processed/analysis_results.csv` conforms to `contracts/analysis_output.schema.yaml` (AnalysisResult). **Verification**: Use `pandera` and record a checksum of the validated file.
- [ ] T040 **Constitution Amendment**: Draft a PR to amend Principle VI so that Benjamini‑Bonferroni FDR correction (FR‑005) supersedes the original Bonferroni requirement. **Deliverable**: Create `state/constitution_amendment.txt` containing the PR number. **Verification**: Check that `state/constitution_amendment.txt` exists and is non‑empty.

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest OpenML BFI‑2 and Last.fm 1k, clean, map genres, and prepare a unified dataframe.

- [ ] T012a [FR-001] Load OpenML BFI‑2: Implement `code/ingest.py` to download dataset ID 42473 using `openml.datasets.get_dataset`. **Logic**:
  1. Start timer, attempt download with `timeout=300` and `retry_count=3`.
  2. On HTTP 404/Timeout raise `DataUnavailableError` with clear message.
  3. Record elapsed time; **assert** elapsed ≤ 300 seconds, log the duration (`"Download successful in X.YZ s"`).
  4. Save raw data to `data/raw/bfi2_raw.csv`.
  **Verification**: Log must show "Download successful in X.YZ s" or raise `DataUnavailableError`.
- [ ] T012b [FR-001] Load Last.fm 1k: Implement `code/ingest.py` to stream dataset via `datasets.load_dataset("lastfm/lastfm_1k", split="train", streaming=True)`. **Logic** mirrors T012a, including timing assertion ≤ 300 s and saving to `data/raw/lastfm_raw.csv`.
- [ ] T013 [US1] Merge Datasets: Merge `bfi2_raw.csv` and `lastfm_raw.csv` on `user_id` (inner join). **Logic**:
  1. If result has 0 rows, raise `DataUnavailableError`.
  2. Save merged CSV to `data/processed/merged_data.csv`.
  **Verification**: Output file exists and has >0 rows.
- [ ] T014 [US1] Map Genres: Implement `code/mapping.py` that loads `contracts/genre_lookup.yaml` and maps raw genre tags in `merged_data.csv` to the 10 standardized categories plus 'Other'. **Verification**: Test mapping of `['alt', 'rock']` yields `['Rock', 'Rock']`.
- [ ] T015 [US1] Prepare Unified Data: From merged data, select personality traits, standardized genre, and demographics; exclude users with zero listening minutes. Save to `data/processed/unified_data.csv`.
- [ ] T016 [FR-007] Handle Missing Data: Impute numeric demographics with median, categorical with mode, or exclude rows as per strategy. Log exact counts: `"INFO: Imputed X rows using {strategy} | Excluded Y rows"`.
- [ ] T017 Verify schema integrity of `data/processed/unified_data.csv` (non‑empty, correct columns) and log checksum.
- [ ] T010 Define test `tests/test_mapping.py::test_map_raw_tags_to_standard` (writes before T014). **Verification**: Fails until mapping logic is implemented.
- [ ] T011 Define test `tests/test_ingest.py::test_missing_data_imputation` (writes before T016). **Verification**: Checks logging and imputation counts.

## Phase 4: User Story 2 - Statistical Correlation and Regression Analysis (Priority: P2)

**Goal**: Compute Spearman correlations, multiple linear regressions with demographics, apply FDR correction.

- [ ] T020a [US2] Generate Synthetic Merged Dataset for Independent Testing: Create a small CSV (`data/processed/synthetic_merged.csv`) with ≥ 5 users, full trait, genre, and demographic fields. **Verification**: File exists and conforms to `contracts/dataset.schema.yaml` and `contracts/genre_preference.schema.yaml`.
- [ ] T020 [FR-003] Compute Spearman Correlations: In `code/analysis.py`,
  1. Log‑transform `listening_minutes`.
  2. Compute Spearman rho and p‑value for every trait‑genre pair.
  3. Output `data/processed/correlation_results.csv` with columns `trait`, `genre`, `rho`, `p_value`.
  4. Add boolean flag `r_gt_0_3` where `abs(rho) > 0.3` (SC‑001).
  **Note**: When run in test mode, use `data/processed/synthetic_merged.csv`; for full analysis, use `data/processed/unified_data.csv`.
  **Verification**: File exists, columns correct, values match synthetic ground truth within tolerance.
- [ ] T021 Run Multiple Linear Regression: For each trait, fit OLS `trait ~ age + gender + C(country)` using `statsmodels`. Output beta coefficients, standard errors to `data/processed/regression_results.csv`.
- [ ] T022 Detect Collinearity: Compute VIF for covariates; if any VIF > 5, drop that predictor, log warning, and re‑fit. Add `model_definition` JSON column listing actual covariates used.
- [ ] T023 [SC-002] Apply Benjamini‑Hochberg FDR: Use `statsmodels.stats.multitest.multipletests` on all p‑values from T020. Append `adjusted_p_value` and `is_significant` (adjusted p < 0.05) to `correlation_results.csv`. **Verification**: Adjusted p‑values present and significance flag correct.
- [ ] T038 Run Analysis on Synthetic Dataset: Execute the full correlation and regression pipeline (T020‑T023) using `synthetic_merged.csv` and verify that the generated `analysis_results.csv` matches the pre‑computed synthetic expectations within tolerance. This provides an independent, cross‑story test that does not depend on the real merged data from US1.
- [ ] T034 Measure Validity of Demographic Controls: Compute delta between coefficients from models with and without covariates, calculate percent change, flag `validity_status` per SC‑003 logic, and save to `data/processed/coefficient_deltas.csv`.
- [ ] T024 Save Final Analysis Results: Merge correlation, regression, and validity data into `data/processed/analysis_results.csv` (includes FR‑004 fields and FR‑006 effect‑size placeholders).

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate heatmap, compute effect sizes, and produce a summary CSV.

- [ ] T026 [FR-006] Generate Correlation Heatmap: Read `analysis_results.csv` and produce `results/correlation_heatmap.png` (800×600, 150 dpi) using `seaborn.heatmap` with diverging colormap ('coolwarm'), labeled axes, and title. **Verification**: File exists, dimensions correct.
- [ ] T027 [FR-006] Calculate Effect Sizes: Compute **Pearson’s r** from log‑transformed listening minutes for each significant trait‑genre pair, then derive **Fisher’s z** and 95 % CI. Append `effect_size_r` and `effect_size_fisher_z` to `analysis_results.csv`. **Verification**: Columns present and values numeric.
- [ ] T028 [FR-006] Export Summary Report: Create `results/results_report.csv` containing `trait`, `genre`, `effect_size_r`, `effect_size_fisher_z`, `significance_status`. For non‑significant rows, set effect‑size fields to empty and `significance_status` to `"Non‑significant (adjusted p ≥ 0.05)"`. **Verification**: Schema matches `contracts/analysis_output.schema.yaml`.
- [ ] T029 Verify Report Completeness: Test `tests/test_report.py::test_report_completeness` asserts that `results_report.csv` contains rows for all traits across all standardized genres. **Note**: No parallel flag.
- [ ] T054 Deterministic Report Validation: 
  1. Load `results/correlation_heatmap.png` with Pillow; assert that a colorbar region exists (e.g., image width > 0 and presence of a gradient column).
  2. Load `results/results_report.csv` and programmatically compare its header to `contracts/analysis_output.schema.yaml` using `pandera`. 
  **Verification**: Both checks must pass; task fails otherwise.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T030 Documentation updates in `README.md` with execution instructions and real‑data source explanation.
- [ ] T031 Refactor Codebase: 
  - T031a Apply `ruff` linting fixes across `code/`.
  - T031b Apply `black` formatting across `code/`.
  - T031c Ensure all modules have type hints and docstrings per `pyproject.toml` settings.
  **Verification**: Linting (`ruff check`) and formatting (`black --check`) both succeed without errors.
- [ ] T032a Add `tests/test_edge_cases.py::test_empty_dataset` for empty dataset handling.
- [ ] T032b Add `tests/test_edge_cases.py::test_all_missing_demographics` for missing demographic handling.
- [ ] T033 End‑to‑End Pipeline Orchestration: Implement `code/pipeline.py` that sequentially runs ingestion, analysis, and reporting, records total runtime in `logs/timing.log`, and raises `TimeoutError` if execution exceeds 6 hours (SC‑004). **Verification**: `logs/timing.log` exists, contains total seconds, and script aborts on timeout.
- [ ] T042 Documentation: Update `README.md` and `data/README.md` to explicitly state the “Real‑First” strategy, list OpenML 42473 and `lastfm/lastfm_1k` as the exclusive data sources, and remove any mention of synthetic data for production.

## Phase O: Review Resolution & Robustness (Revision Pass)

- [ ] T053 Add Sensitivity Analysis (Optional): In `code/analysis.py`, sweep FDR alpha from 0.01 to 0.10, record count of significant findings per alpha in `data/processed/sensitivity_analysis.csv`. **Verification**: File exists with columns `alpha`, `significant_count`.
- [ ] T054 Deterministic Report Validation (see Phase 5).