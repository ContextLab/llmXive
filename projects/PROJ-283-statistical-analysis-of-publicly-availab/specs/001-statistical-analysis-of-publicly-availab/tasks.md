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
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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
- [X] T004 [P] Setup `src/config.py` with random seeds (e.g., `RANDOM_SEED=42`), file paths constants, Lichess dataset URL constants, and the heuristic constant `SAMPLE_SIZE_ESTIMATE_BYTES_PER_GAME = 2000`. **Requirement**: Define `USE_MOVE_5 = True` as the default configuration flag to enforce the Plan's methodological choice (Move 5) over the Spec's Move 10.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**Note**: T006 and T007 define the schema contracts. T005a implements the validation logic. T008a-d define the subset selection and verification. T008e downloads data.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Checkpoint**: Foundation ready for data fetching only; User Story implementation (parsing/modeling) begins in Phase 3.

- [X] T006 [P] Define `specs/contracts/game_record.schema.yaml` with columns: `game_id`, `white_rating`, `black_rating`, `eco_code`, `avg_move_time_white`, `avg_move_time_black`, `material_imbalance_move10`, `outcome`, `elo_expected_prob`, `outcome_deviation`.
- [X] T007 [P] Define `specs/contracts/model_output.schema.yaml` with columns: `model_type`, `coefficients`, `p_values`, `r_squared`, `aic`, `cross_validation_scores`. (Note: Aligns with Spec FR-005). **Verification**: Ensure this file is syntactically valid YAML and can be loaded by `validate_contracts.py`.
- [X] T005a Implement the validation logic in `src/validation/validate_contracts.py` to load YAML schemas from `specs/contracts/` and validate in-memory pandas DataFrames against them. **(Dependency**: Requires T006 and T007 to exist before this script is written or executed. NOT Parallel with schema definition tasks.). **Note**: Removed [P] tag to reflect strict dependency on T006/T007.
- [X] T008a Implement initial dataset ID selection logic in `src/data/select_subset.py`. Use the heuristic defined in T004 (`estimated_size = len(selected_ids) * SAMPLE_SIZE_ESTIMATE_BYTES_PER_GAME`) to select a conservative initial list of game IDs from the **full Lichess index** (accessed via the verified mirror). Use a fixed seed (from `config.py`) to ensure reproducibility. Output a list of selected game IDs to `data/raw/selected_ids.txt` for downstream tasks.
- [X] T008b Implement `src/data/precheck.py` with size validation and reduction logic. **Requirement**: Read `data/raw/selected_ids.txt`. **Algorithm**: If the estimated size exceeds a predefined memory threshold, truncate the list to `N = floor(MEMORY_LIMIT / SAMPLE_SIZE_ESTIMATE_BYTES_PER_GAME)` games., preserving the fixed-seed order. **Verification**: Pipeline proceeds only if the final list size is <= N. **Dependency**: Depends on T008a. **Note**: Removed [P] tag to reflect serial dependency chain.
- [X] T008c Implement `src/data/verify_mirror.py` to check the verified mirror URL for the presence of move-time metadata, sampling a representative subset of game headers. **Note**: Removed [P] tag to reflect serial dependency chain.
- [X] T008d Implement `src/data/download.py` using `datasets.load_dataset(..., streaming=True)` to fetch Lichess data for the specific IDs listed in `data/raw/selected_ids.txt`. **Constraint**: Data must be processed in chunks and never loaded entirely into memory. **Requirement**: Implement a function `retry_fetch_with_backoff(url: str, max_retries: int = 5, base_delay: float = 1.0) -> generator` with an exponential backoff retry strategy (`base_delay=1`, `max_retries=5`, `delay = base_delay * 2^attempt`) for network errors. **Requirement**: Implement a graceful exit mechanism: if the download fails after the maximum number of retries, the script MUST raise a `DataFetchError` (subclass of `RuntimeError` with attribute `reason: str`) with a clear error message and exit code 1. **CRITICAL**: NO synthetic data or partial fallback is permitted. The pipeline MUST HALT immediately on failure. **Requirement**: **Explicitly log** the number of retry attempts, the specific error codes encountered, and the final failure reason to stdout/stderr to ensure verifiable graceful exit behavior. **Requirement**: **Specific Exception Handling**: Catch `requests.exceptions.Timeout`, `requests.exceptions.HTTPError`, and `ConnectionError`. **Requirement**: **Rate Limiting**: Check for HTTP 429 status; if detected, raise `DataFetchError` with message: "Rate limit exceeded. Check for rate-limiting or API unavailability."; otherwise raise `DataFetchError` with message: "Download failed after retries: [reason]. Check for rate-limiting or API unavailability.". **Requirement**: **Metadata Verification**: Call `verify_mirror.py` (T008c) before fetching. If the verified mirror URL is unreachable or move-time metadata is missing for >5% of the sample, raise `DataFetchError` immediately with message: "Verified mirror verification failed: URL unreachable or metadata missing >5%. Pipeline HALT.". **Requirement**: **Verification**: Run unit test `test_retry_logic` and verify log output contains retry count. **Dependency**: This task depends on T008b and T008c. **Deliverable**: Save function `retry_fetch_with_backoff` to `src/data/download.py`.

**Checkpoint**: Foundation ready for data fetching - user story implementation (parsing/modeling) begins in Phase 3

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download a subset of Lichess PGN games, parse them to extract features (ECO, move times, material imbalance at move 5 per Plan, move 10 per Spec), calculate Elo expected probabilities, and produce a clean `GameRecord` dataset.

**Independent Test**: The system can be tested by running the ingestion pipeline on a small sample of games and verifying that the output collection of GameRecord entities contains the expected columns (ECO code, avg_move_time, material_imbalance_move5, material_imbalance_move10, elo_expected_prob, outcome_deviation) with no null values in critical fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for `GameRecord` schema validation in `tests/contract/test_game_record.py`.
- [X] T011 [P] [US1] Unit test for PGN parsing logic handling malformed move lists in `tests/unit/test_parsers.py`.
- [X] T012 [P] [US1] **Write-Only TDD Task**: Unit test for Elo probability calculation and deviation math in `tests/unit/test_calculations.py`. **Implementation Detail**: Implement function `test_elo_capping_edge_cases` which asserts that `calculate_elo_probability` clamps results to `[0.01, 0.99]` for extreme rating differences (e.g., >1000) and that `calculate_outcome_deviation` handles the capped values correctly without NaN. **Note**: This task must be written *before* T016a/T016b implementation.

### Implementation for User Story 1

- [X] T013 [US1] Implement function `parse_pgn_stream(iterator)` in `src/data/parse.py` to accept an iterator/generator of PGN games (from T008d). **Constraint**: The parser must yield `GameRecord` objects one by one or in small batches, allowing `process.py` to aggregate statistics online without storing the full dataset. **Requirement**: **Input Contract**: Accept a generator yielding **raw PGN string blocks** encoded in UTF-8, with games separated by newlines. **Requirement**: **Data Contract**: `avg_move_time` MUST be a float; handle missing `eco_code` by setting it to "Unknown" (string) to satisfy the "no null values" requirement. **Requirement**: `eco_code` MUST be defined as `str` (non-nullable) in the `GameRecord` TypedDict. **Requirement**: **Schema Conformance**: Yields objects MUST strictly conform to the schema defined in `specs/contracts/game_record.schema.yaml`. **Requirement**: **Malformed Handling**: If a game has a malformed move list, log the error with the game ID, skip the game, and continue processing. Do not crash. **Requirement**: **GameRecord Definition**: Instantiate `GameRecord` as a `TypedDict` with fields `game_id: str`, `white_rating: float`, `black_rating: float`, `eco_code: str`, `avg_move_time_white: float`, `avg_move_time_black: float`, `material_imbalance_move5: float`, `material_imbalance_move10: float`, `outcome: float`, `elo_expected_prob: float`, `outcome_deviation: float`. Import from `src/data/models.py`. **Dependency**: This task depends on T008d.
- [X] T014 [US1] Implement function `calculate_material_imbalance_move10(board, move_count=10)` in `src/data/parse.py` to calculate `material_imbalance_move10` (board state at **move 10**, per Spec FR-002). **Requirement**: Ensure this extracts material balance specifically after 10 full moves (20 plies). **Note**: This task implements Spec FR-002 (Move 10) for comparative analysis only. The Plan's "Complexity Tracking" table suggests Move 5 to avoid endogeneity; this task is retained for comparison but is NOT the primary feature for modeling. **Dependency**: This task depends on T013.
- [X] T014b [US1] Implement function `calculate_material_imbalance_move5(board, move_count=5)` in `src/data/parse.py` to calculate `material_imbalance_move5` (board state at **move 5**) as the **PRIMARY** feature for modeling. **Requirement**: This task implements the Plan's "Complexity Tracking" requirement to use Move 5 to avoid endogeneity. **Requirement**: The function must extract material balance after 5 full moves (10 plies). **Requirement**: This feature is the default for the main analysis pipeline. **Requirement**: **Dependency**: This task depends on T013 and T004 (for config).
- [X] T014c [US1] Implement `src/config.py` and `src/main.py` logic to select the primary material imbalance feature based on `USE_MOVE_5` flag. **Requirement**: If `USE_MOVE_5` is True (default per Plan), the pipeline MUST use `material_imbalance_move5` for all regression models. If False, use `material_imbalance_move10`. **Requirement**: This task implements the explicit decision rule mandated by the Plan to resolve the Spec/Plan contradiction. **Dependency**: This task depends on T004 and T014b.
- [X] T016a [US1] Implement function `calculate_elo_expected_prob(white_rating, black_rating)` in `src/data/process.py` to compute the expected win probability using the standard Elo logistic formula: `P = 1 / (1 + 10^((R2-R1)/400))`. **Requirement**: Cap the result to `[0.01, 0.99]` to prevent numerical instability. **Requirement**: Round the result to a high degree of precision.. **Dependency**: This task depends on T013. **Dependency**: T012.
- [X] T016b [US1] Implement function `calculate_outcome_deviation(actual_result, expected_prob)` in `src/data/process.py` to compute the outcome deviation as `(actual_result - expected_prob)`. **Requirement**: Ensure this uses the capped expected probability from T016a. **Dependency**: This task depends on T016a. **Dependency**: T012.
- [X] T015 [US1] Implement class `OnlineAccumulator` and function `process_stream` in `src/data/process.py` to accumulate `outcome_deviation` and feature statistics in an online manner (e.g., using `numpy` accumulators or `pandas` with `chunked` reading) rather than building a massive DataFrame. **Constraint**: Ensure the final `games.parquet` is written in a single pass or via `to_parquet` with `partition` logic to avoid OOM. **Requirement**: **Data Flow**: The `OnlineAccumulator` MUST invoke `calculate_outcome_deviation` (T016b) for each record during stream processing. **Requirement**: **Metrics Tracking**: `OnlineAccumulator` MUST track and expose `total_games` and `parsed_games` counts upon completion of the stream. **Requirement**: **Explicit Output**: This task MUST explicitly write the processed data to `data/processed/games.parquet`. **Dependency**: This task depends on T013, T014, T014b, T016a, T016b.
- [X] T017 [US1] Implement function `save_inclusion_metrics(...)` in `src/data/process.py` to calculate the inclusion rate and **unconditionally save** `data/results/inclusion_metrics.json`. **Schema**: The JSON file MUST contain keys: `total_games` (int), `parsed_games` (int), `inclusion_rate` (float). **Logic**: `inclusion_rate` MUST be calculated as `parsed_games / total_games`. **Requirement**: Immediately after saving, read the file and validate the inclusion rate. If `inclusion_rate` < 0.95, raise a `ValueError` with a clear error message and exit code 1. **Verification**: File exists, is valid JSON, and matches the schema; pipeline halts if rate < 95%. **Requirement**: **Execution Order**: This task MUST run after T013, T014, T015 (specifically, after the stream is fully consumed). **Requirement**: **Data Quality Gate**: This task enforces SC-001 as a hard gate; a low inclusion rate is a data quality failure that must halt the pipeline. **Dependency**: This task depends on T015 (which exposes counts) and T013, T014.
- [X] T018 [US1] Implement `src/main.py` orchestration: Create the main entry point script `src/main.py` with a `main()` function that accepts `--sample` flag, initializes logging, and wires the data ingestion flow. **Requirement**: Explicitly wire T015 (OnlineAccumulator) output to T005a (validate_contracts.py) and then to the `save_parquet` step in a single atomic flow. **Requirement**: Ensure the pipeline exits with code 0 on success and code 1 on any validation or data quality failure. **Requirement**: **Dependency**: Depends on T004, T013, T014, T014b, T015, T017, T005a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Regression Modeling and Significance Testing (Priority: P2)

**Goal**: Fit Beta Regression, Gaussian GLM, and Ridge regression models (per Spec FR‑005 and Plan's comparative baseline), apply Benjamini‑Hochberg FDR correction, perform sensitivity analysis, and collapse ECO codes to reduce multicollinearity.

**Independent Test**: The system can be tested by running the modeling script on the generated dataset and verifying that the output includes coefficient tables with corrected p‑values, R² scores, and AIC values for Beta, Gaussian GLM, and Ridge models.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for FDR correction logic (Benjamini‑Hochberg) in `tests/unit/test_calculations.py`.
- [X] T020 [P] [US2] Unit test for ECO code collapsing logic (mapping specific codes to families) in `tests/unit/test_parsers.py`.

### Implementation for User Story 2

- [X] T021 [US2] Implement function `collapse_eco_codes(...)` in `src/models/fit.py` to handle feature preparation on the streamed/processed data. **Constraint**: If the dataset is too large for one‑hot encoding in memory, implement a two‑pass approach (first pass to count unique ECOs/families, second pass to encode) or use `sklearn`'s `HashingVectorizer` if applicable, ensuring memory usage stays within acceptable bounds. **Requirement**: **Dynamic Scanning**: First, scan the dataset to identify all unique ECO codes present. Second, map each code to a family by grouping by the first character (e.g., 'A' -> 'King\'s Pawn', 'B' -> 'Sicilian', etc.) to ensure ALL codes are collapsed. **Requirement**: **Dynamic Mapping**: Do NOT rely on a hardcoded JSON file. Instead, generate a dynamic mapping where any ECO code starting with 'A' maps to 'King\'s Pawn', 'B' to 'Sicilian', etc., and any code not matching standard first-char groups maps to 'Unknown'. **Requirement**: **External Config**: If a config file exists, use it as a fallback, but the primary logic must be dynamic scanning and first-character grouping. **Requirement**: **Primary Feature**: Use `material_imbalance_move5` (from T014b) as the default feature for modeling, unless `USE_MOVE_5` is False. **Dependency**: This task MUST run after T017, before T022a/T022b. **Verification**: File exists, is valid JSON (if generated), and contains the mapping used for the models.
- [X] T022a [US2] Implement `src/models/fit.py` to fit **Beta Regression**. **Constraint**: Beta Regression is mandatory per Spec FR‑005. **Requirement**: **Zero-Inflation Handling**: Before fitting the Beta model, apply a two-step transformation to `outcome_deviation` (which is in [-1, 1]): 1) Normalize to [0, 1] via `y_norm = (y + 1) / 2`, then 2) Apply the zero-inflation transformation `(y_norm*(N-1)+0.5)/N` where `N = len(dataset)` **BEFORE any data exclusion or filtering** to handle exact 0/1 values. **Rationale**: This transformation is mathematically required to map the [-1, 1] deviation metric into the (0, 1) domain required by the Beta distribution. **Semantic Preservation**: The model predicts the transformed probability (`outcome_deviation_normalized`); however, the final report must map coefficients back to the original scale to preserve the semantic meaning of the target variable as defined in the Spec (FR-004). **Requirement**: **Beta Implementation**: Explicitly import `statsmodels.genmod.generalized_linear_model` and use `family=sm.families.Beta()`. **Requirement**: Ensure the model handles the outcome deviation distribution correctly. **Requirement**: **Verification**: Verify the Beta model was successfully fitted and saved to a temporary artifact before proceeding to T023/T029. **Deliverable**: Save Beta model artifact. **Dependency**: This task depends on T021.
- [X] T022b [US2] Implement `src/models/fit.py` to fit **Gaussian GLM** and **Ridge Regression**. **Requirement**: **Gaussian GLM**: Fit a Gaussian GLM with identity link as a comparative baseline per Plan's "Complexity Tracking" table. **Requirement**: **Ridge Implementation**: Fit a Ridge Regression model using `sklearn.linear_model.Ridge`. **Requirement**: Ensure both models handle the outcome deviation distribution correctly. **Requirement**: **Verification**: Verify both Gaussian GLM and Ridge models were successfully fitted and saved to temporary artifacts before proceeding to T023/T029. **Deliverable**: Save Gaussian GLM and Ridge model artifacts. **Dependency**: This task depends on T021.
- [X] T023 [US2] Implement `src/models/metrics.py` to calculate p‑values (Wald Z-tests) and F‑statistics for all predictors for **all three models** (Beta, Gaussian GLM, Ridge). **Dependency**: Depends on T022a and T022b.
- [X] T024 [US2] Implement `src/models/metrics.py` to apply Benjamini‑Hochberg FDR correction to p‑values (FR‑009). **Requirement**: **Input**: A pandas Series of p-values. **Requirement**: **Output**: A pandas DataFrame containing columns `original_p_value` and `corrected_p_value`. **Requirement**: Input must be a pandas Series of p-values; Output must be a pandas DataFrame containing original p-values and corrected p-values. **Dependency**: Depends on T023.
- [X] T025 [US2] Implement function `run_sensitivity_analysis(...)` in `src/reports/sensitivity.py` to perform threshold sweep analysis over a **specific set of values** (SC-004). **Deliverable**: Save results to `data/results/sensitivity_analysis.json`. **Logic**: **Sweep Range**: Explicitly sweep thresholds over a set of small positive values: {0.005, 0.01, 0.05} as per Spec SC-004. **Requirement**: **Delta Calculation**: Explicitly calculate and save the variation in the number of significant predictors for each step. **Requirement**: **Jaccard Index**: Calculate the pairwise Jaccard index for all pairs in the set {0.005, 0.01, 0.05} to satisfy the specified compliance criterion. **Requirement**: **Set Definition**: The set `S_threshold` for Jaccard calculation is defined as the set of predictors with corrected p-value < threshold. **Requirement**: **Missing Value Handling**: Exclude predictors with NaN p-values from `S_threshold` before calculating Jaccard index. **Requirement**: **Reporting**: Explicitly report the variation in the number of significant predictors in the final output. **Requirement**: **Validation Gate**: If the calculated Jaccard index is < 0.8, raise a `ValueError` with a clear error message and exit code 1 to enforce SC-004 as a blocking gate. **Verification**: File exists, is valid JSON, and contains the Jaccard index values and delta counts. **Dependency**: Depends on T024.
- [X] T029 [US2] Implement function `validate_models(...)` in `src/models/validate.py` to perform k-fold cross-validation (k=5) on **Beta, Gaussian GLM, and Ridge models**. **Requirement**: Use a fixed random seed from config.py for the fold splitting. **Requirement**: Save cross-validation scores to a temporary artifact accessible by T027. **Dependency**: This task depends on T022a and T022b.
- [X] T030 [US2] Implement function `calculate_cv_metrics(...)` in `src/models/validate.py` to calculate R² and MSE variance across folds; specifically calculate standard deviation of R². **Validation Logic**: Check if `std_dev_r` meets the SC‑003 target threshold (< 0.05). **Requirement**: If `std_dev_r >= 0.05`, raise a `ValueError` with a clear error message and exit code 1 to enforce SC-003 as a blocking gate. **Return**: Return a dictionary containing `cv_summary` and `validation_status`. **Dependency**: Depends on T029.
- [X] T027 [US2] Implement `src/models/fit.py` to save model artifacts (coefficients, p‑values, R², AIC, cross_validation_scores) for Beta, Gaussian GLM, and Ridge models to `data/results/model_metrics.json` and validate against `model_output.schema.yaml` (T007). **Requirement**: This task acts as the final consolidation step: it takes the temporary artifacts generated by T022a, T022b, T029, and T024, validates them against the schema, and saves the final schema-compliant JSON. **Requirement**: Explicitly calculate and save a list `significant_predictors` containing the names of predictors with corrected p-value < 0.01. **Requirement**: **Execution Order**: This task MUST run AFTER T029 (Cross-Validation) and T024 (FDR) to ensure `cross_validation_scores` and `corrected_p_values` are available. **Verification**: File exists, is valid JSON, and matches the schema in T007 (non‑empty arrays for cross‑validation scores). **Dependency**: Depends on T022a, T022b, T023, T024, T029, T030.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Validation and Diagnostic Reporting (Priority: P3)

**Goal**: Generate diagnostic plots (residuals, predicted vs. actual), and produce a final validation report using the models validated in Phase 4.

**Independent Test**: The system can be tested by executing the validation script and verifying that the output includes a report of MSE across multiple folds (from T030) and saves PNG diagnostic plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Integration test for end‑to‑end pipeline (download -> parse -> model -> validate) on a small sample in `tests/integration/test_pipeline.py`.

### Implementation for User Story 3

- [X] T031 [US3] Implement `src/reports/generate_plots.py` to create residual plots, feature importance rankings, and predicted vs. actual scatterplots for all models. **Requirement**: Save all plots to `data/results/`. **Requirement**: Ensure the logic for plot generation and file saving is contained within this single task. **Requirement**: **Dependency**: This task depends on T022a, T022b, T029, T030 (to access model objects and CV metrics). **Dependency**: Depends on T022a, T022b, T029, T030.
- [X] T033 [US3] Implement function `generate_diagnostic_report(...)` in `src/reports/generate_plots.py` to save all plots to `data/results/` and generate a final `DiagnosticReport` summary in `data/results/diagnostics.json`. **Requirement**: Verify the existence of data/results/model_metrics.json (from T027). **Requirement**: Consume validation_status and cv_metrics returned by T030. **Requirement**: Include significant_predictors from T027 in the report. **Requirement**: **Schema**: The JSON file MUST contain keys: `residual_plot_path` (str), `cv_summary` (dict with keys `mean_r2` (float), `std_r2` (float), `mean_mse` (float)), `significant_predictors` (list of strings). **Requirement**: **Verification**: Verify `diagnostics.json` contains keys: `residual_plot_path`, `cv_summary`, `significant_predictors`. **Dependency**: Depends on T027, T030, T031.

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