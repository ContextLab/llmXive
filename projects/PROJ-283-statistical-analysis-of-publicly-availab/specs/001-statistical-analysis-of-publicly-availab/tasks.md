---
description: "Task list template for feature implementation"
---

# Tasks: Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

**Input**: Design documents from `/specs/001-statistical-chess-elo-analysis/`
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

- [X] T001 Create project structure: `src/`, `tests/`, `data/`, `specs/`, `data/raw/`, `data/processed/`, `data/results/`, `specs/contracts/`, `tests/contract/`, `tests/unit/`, `tests/integration/`. Create `__init__.py` in all `src/` and `tests/` subdirectories.
- [X] T002 Initialize Python project by creating `requirements.txt` at repository root containing: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `chess`, `matplotlib`, `seaborn`, `requests`, `datasets`, `pytest`.
- [X] T003 [P] Configure linting (ruff) and formatting tools in `pyproject.toml` or `.ruff.toml`/`.black.toml`.
- [X] T004 [P] Setup `src/config.py` with random seeds (e.g., `RANDOM_SEED=42`), file paths constants, Lichess dataset URL constants, and the heuristic constant `SAMPLE_SIZE_ESTIMATE_BYTES_PER_GAME = 2000`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**Note**: T006 and T007 define the schema contracts. T005a implements the validation logic. T008b-d define the subset selection and verification. T008e downloads data.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Checkpoint**: Foundation ready for data fetching only; User Story implementation (parsing/modeling) begins in Phase 3.

- [X] T005a [P] Implement the validation logic in `src/validation/validate_contracts.py` to load YAML schemas from `specs/contracts/` and validate in-memory pandas DataFrames against them. **(Dependency**: Requires T006 and T007 to exist before this script is written or executed. NOT Parallel with schema definition tasks.).
- [X] T006 [P] Define `specs/contracts/game_record.schema.yaml` with columns: `game_id`, `white_rating`, `black_rating`, `eco_code`, `avg_move_time_white`, `avg_move_time_black`, `material_imbalance_move10`, `outcome`, `elo_expected_prob`, `outcome_deviation`.
- [X] T007 [P] Define `specs/contracts/model_output.schema.yaml` with columns: `model_type`, `coefficients`, `p_values`, `r_squared`, `aic`, `cross_validation_scores`. (Note: Aligns with Spec FR-005). **Verification**: Ensure this file is syntactically valid YAML and can be loaded by `validate_contracts.py`.
- [X] T008a Implement initial dataset ID selection logic in `src/data/select_subset.py`. Use the heuristic defined in T004 (`estimated_size = len(selected_ids) * SAMPLE_SIZE_ESTIMATE_BYTES_PER_GAME`) to select a conservative initial list of game IDs from the **full Lichess index** (accessed via the verified mirror). Use a fixed seed (from `config.py`) to ensure reproducibility. Output a list of selected game IDs to `data/raw/selected_ids.txt` for downstream tasks.
- [X] T008b Implement `src/data/precheck.py` with size validation and reduction logic. **Requirement**: Read `data/raw/selected_ids.txt`. **Algorithm**: If the estimated size exceeds 6 * 1024^3 bytes, truncate the list to exactly `N = floor(6 * 1024^3 / SAMPLE_SIZE_ESTIMATE_BYTES_PER_GAME)` games, preserving the fixed-seed order. **Verification**: Pipeline proceeds only if the final list size is <= N. **Dependency**: Depends on T008a.
- [X] T008c Implement `src/data/verify_mirror.py` to check the verified mirror URL for the presence of move-time metadata, sampling a representative subset of game headers.
- [X] T008d Implement `src/data/download.py` using `datasets.load_dataset(..., streaming=True)` to fetch Lichess data for the specific IDs listed in `data/raw/selected_ids.txt`. **Constraint**: Data must be processed in chunks and never loaded entirely into memory. **Requirement**: Implement a function `retry_fetch_with_backoff` with an exponential backoff retry strategy (`base_delay=1`, `max_retries=5`, `delay = base_delay * 2^attempt`) for network errors. **Requirement**: Implement a graceful exit mechanism: if the download fails after the maximum number of retries, the script MUST raise a `DataFetchError` (subclass of `RuntimeError`) with a clear error message and exit code 1. **CRITICAL**: NO synthetic data or partial fallback is permitted. The pipeline MUST HALT immediately on failure. **Requirement**: **Explicitly log** the number of retry attempts, the specific error codes encountered, and the final failure reason to stdout/stderr to ensure verifiable graceful exit behavior. **Requirement**: **Specific Exception Handling**: Catch `requests.exceptions.Timeout`, `requests.exceptions.HTTPError`, and `ConnectionError`. **Requirement**: **Rate Limiting**: Check for HTTP 429 status; if detected, raise `DataFetchError` with message: "Rate limit exceeded. Check for rate-limiting or API unavailability."; otherwise raise `DataFetchError` with message: "Download failed after retries: [reason]. Check for rate-limiting or API unavailability.". **Requirement**: **Metadata Verification**: Call `verify_mirror.py` (T008c) before fetching. **Dependency**: This task depends on T008b and T008c.

**Checkpoint**: Foundation ready for data fetching - user story implementation (parsing/modeling) begins in Phase 3

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download a subset of Lichess PGN games, parse them to extract features (ECO, move times, material imbalance at move 10), calculate Elo expected probabilities, and produce a clean `GameRecord` dataset.

**Independent Test**: The system can be tested by running the ingestion pipeline on a small sample of games and verifying that the output collection of GameRecord entities contains the expected columns (ECO code, avg_move_time, material_imbalance_move10, elo_expected_prob, outcome_deviation) with no null values in critical fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for `GameRecord` schema validation in `tests/contract/test_game_record.py`.
- [X] T011 [P] [US1] Unit test for PGN parsing logic handling malformed move lists in `tests/unit/test_parsers.py`.
- [X] T012 [P] [US1] **Write-Only TDD Task**: Unit test for Elo probability calculation and deviation math in `tests/unit/test_calculations.py`. **Implementation Detail**: Implement function `test_elo_capping_edge_cases` which asserts that `calculate_elo_probability` clamps results to `[0.01, 0.99]` for extreme rating differences (e.g., >1000) and that `calculate_outcome_deviation` handles the capped values correctly without NaN. **Note**: This task must be written *before* T016a/T016b implementation.

### Implementation for User Story 1

- [X] T013 [US1] Implement function `parse_pgn_stream(iterator)` in `src/data/parse.py` to accept an iterator/generator of PGN games (from T008e). **Constraint**: The parser must yield `GameRecord` objects one by one or in small batches, allowing `process.py` to aggregate statistics online without storing the full dataset. **Requirement**: **Input Contract**: Accept a generator yielding **raw PGN string blocks** encoded in UTF-8, with games separated by newlines. **Requirement**: **Data Contract**: `avg_move_time` MUST be a float; handle missing `eco_code` by setting it to None (Python None, not string). **Requirement**: **Schema Conformance**: Yielded objects MUST strictly conform to the schema defined in `specs/contracts/game_record.schema.yaml`. **Requirement**: **Malformed Handling**: If a game has a malformed move list, log the error with the game ID, skip the game, and continue processing. Do not crash. **Requirement**: **GameRecord Definition**: Instantiate `GameRecord` as a `TypedDict` with fields `game_id: str`, `white_rating: float`, `black_rating: float`, `eco_code: str | None`, `avg_move_time_white: float`, `avg_move_time_black: float`, `material_imbalance_move10: float`, `outcome: float`, `elo_expected_prob: float`, `outcome_deviation: float`. Import from `src/data/models.py`. **Dependency**: This task depends on T008e.
- [X] T014 [US1] Implement function `calculate_material_imbalance(board, move_count=10)` in `src/data/parse.py` to calculate `material_imbalance_move10` (board state at **move 10**, per Spec FR-002). **Requirement**: Ensure this extracts material balance specifically after 10 full moves (20 plies).
- [X] T016a [US1] Implement function `calculate_elo_expected_prob(white_rating, black_rating)` in `src/data/process.py` to compute the expected win probability using the standard Elo logistic formula: `P = 1 / (1 + 10^((R2-R1)/400))`. **Requirement**: Cap the result to `[0.01, 0.99]` to prevent numerical instability. **Requirement**: Round the result to 6 decimal places. **Dependency**: This task depends on T013. **Dependency**: T012.
- [X] T016b [US1] Implement function `calculate_outcome_deviation(actual_result, expected_prob)` in `src/data/process.py` to compute the outcome deviation as `(actual_result - expected_prob)`. **Requirement**: Ensure this uses the capped expected probability from T016a. **Dependency**: This task depends on T016a. **Dependency**: T012.
- [X] T015 [US1] Implement class `OnlineAccumulator` and function `process_stream` in `src/data/process.py` to accumulate `outcome_deviation` and feature statistics in an online manner (e.g., using `numpy` accumulators or `pandas` with `chunked` reading) rather than building a massive DataFrame. **Constraint**: Ensure the final `games.parquet` is written in a single pass or via `to_parquet` with `partition` logic to avoid OOM. **Requirement**: **Data Flow**: The `OnlineAccumulator` MUST invoke `calculate_outcome_deviation` (T016b) for each record during stream processing. **Requirement**: **Metrics Tracking**: `OnlineAccumulator` MUST track and expose `total_games` and `parsed_games` counts upon completion of the stream. **Dependency**: This task depends on T013, T014, T016a, T016b.
- [X] T017 [US1] Implement function `save_inclusion_metrics(...)` in `src/data/process.py` to calculate the inclusion rate and **unconditionally save** `data/results/inclusion_metrics.json`. **Schema**: The JSON file MUST contain keys: `total_games` (int), `parsed_games` (int), `inclusion_rate` (float). **Logic**: `inclusion_rate` MUST be calculated as `parsed_games / total_games`. **Requirement**: Immediately after saving, read the file and validate the inclusion rate. If `inclusion_rate` < 0.95, raise a ValueError with a clear error message and exit code 1. **Verification**: File exists, is valid JSON, and matches the schema; pipeline halts if rate < 95%. **Requirement**: **Execution Order**: This task MUST run after T013, T014, T015 (specifically, after the stream is fully consumed). **Dependency**: This task depends on T015 (which exposes counts) and T013, T014.
- [X] T018 [US1] Implement `src/main.py` to orchestrate the pipeline, calling validate_contracts.py (T005a) on the generated dataset before saving to `data/processed/games.parquet`. **Verification**: Script exits with code 0 and produces `games.parquet`; exits with code 1 if validation fails. **Dependency**: Depends on T013, T014, T015, T017, T005a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Regression Modeling and Significance Testing (Priority: P2)

**Goal**: Fit Beta Regression and Ridge regression models (per Spec FR‑005), apply Benjamini‑Hochberg FDR correction, perform sensitivity analysis, and collapse ECO codes to reduce multicollinearity.

**Independent Test**: The system can be tested by running the modeling script on the generated dataset and verifying that the output includes coefficient tables with corrected p‑values, R² scores, and AIC values for Beta and Ridge models.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for FDR correction logic (Benjamini‑Hochberg) in `tests/unit/test_calculations.py`.
- [X] T020 [P] [US2] Unit test for ECO code collapsing logic (mapping specific codes to families) in `tests/unit/test_parsers.py`.

### Implementation for User Story 2

- [X] T021a [US2] Implement `src/models/setup.py` to ensure `data/config/eco_mapping.json` exists. **Requirement**: If the file is missing, create it with the **complete** default mapping: `{ "A": "King's Pawn", "B": "Sicilian Defense", "C": "French Defense", "D": "Queen's Gambit", "E": "King's Indian" }`. **Requirement**: Handle unmapped codes (e.g., invalid or unknown codes) by mapping them to an `Unknown` category. **Deliverable**: Generate `data/config/eco_mapping.json` containing the mapping dictionary. **Dependency**: This task MUST run before T021.
- [X] T021 [US2] Implement function `collapse_eco_codes(...)` in `src/models/fit.py` to handle feature preparation on the streamed/processed data. **Constraint**: If the dataset is too large for one‑hot encoding in memory, implement a two‑pass approach (first pass to count unique ECOs/families, second pass to encode) or use `sklearn`'s `HashingVectorizer` if applicable, ensuring memory usage stays within acceptable bounds. **Requirement**: **External Config**: Load the ECO mapping dictionary from `data/config/eco_mapping.json` (created by T021a). **Dependency**: This task MUST run after T017 and T021a, before T022. **Verification**: File exists, is valid JSON, and contains the mapping used for the models.
- [X] T022 [US2] Implement `src/models/fit.py` to fit **Beta Regression** (using `statsmodels` GLM with `Beta` family) and **Ridge Regression**. **Constraint**: Beta Regression is mandatory per Spec FR‑005. **Requirement**: **Zero-Inflation Handling**: Before fitting the Beta model, apply a two-step transformation to `outcome_deviation` (which is in [-1, 1]): 1) Normalize to [0, 1] via `y_norm = (y + 1) / 2`, then 2) Apply the zero-inflation transformation `(y_norm*(N-1)+0.5)/N` where `N = len(dataset)` **BEFORE any data exclusion or filtering** to handle exact 0/1 values. **Rationale**: This transformation is mathematically required to map the [-1, 1] deviation metric into the (0, 1) domain required by the Beta distribution. **Semantic Preservation**: The model predicts the transformed probability (`outcome_deviation_normalized`); however, the final report must map coefficients back to the original scale to preserve the semantic meaning of the target variable as defined in the Spec (FR-004). **Requirement**: **Implementation Logic**: Explicitly import `statsmodels.genmod.generalized_linear_model` and use `family=sm.families.Beta()`. **Requirement**: Ensure Beta Regression handles the outcome deviation distribution correctly. **Deliverable**: Save model artifacts for Beta and Ridge models.
- [X] T023 [US2] Implement `src/models/metrics.py` to calculate p‑values (Wald Z-tests) and F‑statistics for all predictors.
- [X] T024 [US2] Implement `src/models/metrics.py` to apply Benjamini‑Hochberg FDR correction to p‑values (FR‑009). **Requirement**: **Input**: A pandas Series of p-values. **Requirement**: **Output**: A pandas DataFrame containing columns `original_p_value` and `corrected_p_value`. **Requirement**: Input must be a pandas Series of p-values; Output must be a pandas DataFrame containing original p-values and corrected p-values. **Dependency**: Depends on T023.
- [X] T025 [US2] Implement function `run_sensitivity_analysis(...)` in `src/reports/sensitivity.py` to perform threshold sweep analysis over a **specific set of values** (SC-004). **Deliverable**: Save results to `data/results/sensitivity_analysis.json`. **Logic**: **Sweep Range**: Explicitly sweep thresholds over the set `{0.005, 0.01, 0.05}`. **Requirement**: **Delta Calculation**: Explicitly calculate and save the variation in the number of significant predictors for each step. **Requirement**: **Jaccard Index**: Calculate the pairwise Jaccard index for all pairs in the set {0.005, 0.01, 0.05} to satisfy the specified compliance criterion. **Requirement**: **Set Definition**: The set `S_threshold` for Jaccard calculation is defined as the set of predictors with corrected p-value < threshold. **Requirement**: **Missing Value Handling**: Exclude predictors with NaN p-values from `S_threshold` before calculating Jaccard index. **Requirement**: **Reporting**: Explicitly report the variation in the number of significant predictors in the final output. **Verification**: File exists, is valid JSON, and contains the Jaccard index values and delta counts. **Dependency**: Depends on T024.
- [X] T027 [US2] Implement `src/models/fit.py` to save model artifacts (coefficients, p‑values, R², AIC) for Beta and Ridge models to `data/results/model_metrics.json` and validate against `model_output.schema.yaml` (T007). **Requirement**: This task acts as the final consolidation step: it takes the temporary artifacts generated by T022, validates them against the schema, and saves the final schema-compliant JSON. **Requirement**: Explicitly calculate and save a list `significant_predictors` containing the names of predictors with corrected p-value < 0.01. **Verification**: File exists, is valid JSON, and matches the schema in T007 (non‑empty arrays for cross‑validation scores). **Dependency**: Depends on T022, T023, T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Validation and Diagnostic Reporting (Priority: P3)

**Goal**: Perform k-fold cross-validation., generate diagnostic plots (residuals, predicted vs. actual), and produce a final validation report.

**Independent Test**: The system can be tested by executing the validation script and verifying that the output includes a report of MSE across multiple folds and saves PNG diagnostic plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Integration test for end‑to‑end pipeline (download -> parse -> model -> validate) on a small sample in `tests/integration/test_pipeline.py`.

### Implementation for User Story 3

- [X] T029 [US3] Implement function `validate_models(...)` in `src/models/validate.py` to perform k-fold cross-validation (k=5) on **Beta and Ridge models** only. **Requirement**: Use a fixed random seed from config.py for the fold splitting. **Dependency**: This task depends on T022.
- [X] T030 [US3] Implement function `calculate_cv_metrics(...)` in `src/models/validate.py` to calculate R² and MSE variance across folds; specifically calculate standard deviation of R². **Validation Logic**: Check if `std_dev_r2` is strictly less than 0.05 (SC‑003 target). **Return**: Return a dictionary containing `cv_summary` and `validation_status`.
- [X] T031 [US3] Implement `src/reports/generate_plots.py` to create residual plots, feature importance rankings, and predicted vs. actual scatterplots. **Requirement**: Save all plots to `data/results/`. **Requirement**: Ensure the logic for plot generation and file saving is contained within this single task. **Dependency**: Depends on T027.
- [X] T033 [US3] Implement function `generate_diagnostic_report(...)` in `src/reports/generate_plots.py` to save all plots to `data/results/` and generate a final `DiagnosticReport` summary in `data/results/diagnostics.json`. **Requirement**: Verify the existence of data/results/model_metrics.json (from T027). **Requirement**: Consume validation_status and cv_metrics returned by T030. **Requirement**: Include significant_predictors from T027 in the report. **Dependency**: Depends on T027, T030, T031.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Update `README.md` with installation steps, a **Mermaid diagram** for the data flow, and usage instructions.
- [X] T035 [P] Update `quickstart.md` with a short sample run guide including the exact command `python src/main.py --sample` and the expected output string `Pipeline completed successfully`.
- [X] T036 [P] Run `ruff check --select T20` to ensure no print statements remain in the codebase.
- [X] T038 [P] Profile RAM usage with `memory_profiler`. **Requirement**: Run command: `python -m memory_profiler --output-file=data/results/memory_profile.txt src/main.py --sample`. **Requirement**: Save peak RAM usage to `data/results/memory_profile.txt`.
- [X] T040 [P] Run quickstart.md validation. **Requirement**: Execute command: `python src/main.py --sample`. **Requirement**: Verify exit code 0 and output contains `Pipeline completed successfully`.

---

## Dependencies & Execution Order

(same as before)

## Success Criteria

(same as before)