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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure: `src/`, `tests/`, `data/`, `specs/`, `data/raw/`, `data/processed/`, `data/results/`, `specs/contracts/`, `tests/contract/`, `tests/unit/`, `tests/integration/`. Create `__init__.py` in all `src/` and `tests/` subdirectories.
- [X] T002 Initialize Python project by creating `requirements.txt` at repository root containing: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `chess`, `matplotlib`, `seaborn`, `requests`, `datasets`, `pytest`.
- [X] T003 [P] Configure linting (ruff) and formatting tools in `pyproject.toml` or `.ruff.toml`/`.black.toml`.
- [X] T004 [P] Setup `src/config.py` with random seeds (e.g., `RANDOM_SEED=42`), file paths constants, and Lichess dataset URL constants.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**Note**: T006 and T007 define the schema contracts. T005 implements the validation logic that loads these contracts. T008a-e download data. While T005 (logic) depends on T006/007 (files), T008a-e (data fetch) is a prerequisite for the *runtime* validation in T018, but the *schema definition* must exist before the validator script is written.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Checkpoint**: Foundation ready for data fetching only; User Story implementation (parsing/modeling) begins in Phase 3.

- [X] T006 [P] Define `specs/contracts/game_record.schema.yaml` with columns: `game_id`, `white_rating`, `black_rating`, `eco_code`, `avg_move_time_white`, `avg_move_time_black`, `material_imbalance_move10`, `outcome`, `elo_expected_prob`, `outcome_deviation`.
- [X] T007 [P] Define `specs/contracts/model_output.schema.yaml` with columns: `model_type`, `coefficients`, `p_values`, `r_squared`, `aic`, `cross_validation_scores`. (Note: Aligns with Spec FR-005). **Verification**: Ensure this file is syntactically valid YAML and can be loaded by `validate_contracts.py`.
- [X] T005 Implement `src/validation/validate_contracts.py` to load YAML schemas from `specs/contracts/` and validate in-memory pandas DataFrames against them. **(Dependency**: Requires T006 and T007 to exist before this script is written or executed. **NOT Parallel** with schema definition tasks).
- [X] T008a [P] Define the heuristic for estimating subset size in `src/config.py`. **Requirement**: Add constant `SAMPLE_SIZE_ESTIMATE_BYTES_PER_GAME = 2000` to `src/config.py` representing the average PGN header size plus a small amount per game. **Verification**: Constant is defined and documented in `config.py`.
- [X] T008b Implement `src/data/select_subset.py` to execute the subset selection logic. **Requirement**: Use the heuristic defined in T008a (`estimated_size = len(selected_ids) * SAMPLE_SIZE_ESTIMATE_BYTES_PER_GAME`) to select a conservative initial list of game IDs from the **full Lichess index** (accessed via the verified mirror). Use a fixed seed (from `config.py`) to ensure reproducibility. **Verification**: Log the selected game IDs, count, and the *estimated* size metric; ensure reproducibility on re-run. Output a list of selected game IDs to `data/raw/selected_ids.txt` for downstream tasks. **Dependency**: Depends on T008a.
- [X] T008c Implement `src/data/precheck.py` with size validation and reduction logic. **Requirement**: Read `data/raw/selected_ids.txt`, calculate the *estimated* total size using the heuristic from T008a. If estimated size > 6GB, trigger reduction. **Algorithm**: If estimated size > 6GB, halve the sample size (`len(ids) // 2`) and rewrite `data/raw/selected_ids.txt` with the smaller set. Repeat until size < 6GB. **Verification**: Pipeline proceeds only if the final estimated subset size is < 6GB. **Dependency**: Depends on T008b.
- [ ] T008e [US1] Implement `src/data/download.py` using `datasets.load_dataset(..., streaming=True)` to fetch Lichess data for the specific IDs listed in `data/raw/selected_ids.txt`. **Constraint**: Data must be processed in chunks and never loaded entirely into memory. **Requirement**: Implement a function `retry_fetch_with_backoff` with an **exponential backoff retry strategy** (e.g., retry with `delay = base_delay * 2^attempt`) for network errors. **Requirement**: Implement a **graceful exit** mechanism: if the download fails after the maximum number of retries, the script MUST raise a `DataFetchError` exception with a clear error message and exit code 1. **CRITICAL**: NO synthetic data or partial fallback is permitted. The pipeline MUST HALT immediately on failure. **Requirement**: **Explicitly log** the number of retry attempts, the specific error codes encountered, and the final failure reason to stdout/stderr to ensure verifiable graceful exit behavior. **Requirement**: **Specific Exception Handling**: Catch `requests.exceptions.Timeout`, `requests.exceptions.HTTPError`, and `ConnectionError`. **Requirement**: **Rate Limiting**: Check for HTTP 429 status; if detected, raise `DataFetchError` with message: "Rate limit exceeded. Check for rate-limiting or API unavailability."; otherwise raise `DataFetchError` with message: "Download failed after retries: [reason]. Check for rate-limiting or API unavailability.". **Dependency**: This task depends on T008c to obtain the validated list of game IDs to fetch. **Note**: T008e is NOT parallel-safe due to dependency on T008c.

**Checkpoint**: Foundation ready for data fetching - user story implementation (parsing/modeling) begins in Phase 3

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download a subset of Lichess PGN games, parse them to extract features (ECO, move times, material imbalance at move 10), calculate Elo expected probabilities, and produce a clean `GameRecord` dataset.

**Independent Test**: The system can be tested by running the ingestion pipeline on a small sample of games and verifying that the output collection of GameRecord entities contains the expected columns (ECO code, avg_move_time, material_imbalance_move10, elo_expected_prob, outcome_deviation) with no null values in critical fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for `GameRecord` schema validation in `tests/contract/test_game_record.py`.
- [X] T011 [P] [US1] Unit test for PGN parsing logic handling malformed move lists in `tests/unit/test_parsers.py`.
- [X] T012 [P] [US1] **Write-Only TDD Task**: Unit test for Elo probability calculation and deviation math in `tests/unit/test_calculations.py`. **Implementation Detail**: Implement function `test_elo_capping_edge_cases` which asserts that `calculate_elo_probability` clamps results to `[0.01, 0.99]` for extreme rating differences (e.g., >1000) and that `calculate_outcome_deviation` handles the capped values correctly without NaN. **Note**: This task must be written *before* T013/T015 implementation.

### Implementation for User Story 1

- [ ] T013-streaming [US1] Implement function `parse_pgn_stream(iterator)` in `src/data/parse.py` to accept an iterator/generator of PGN games (from T008e). **Constraint**: The parser must yield `GameRecord` objects one by one or in small batches, allowing `process.py` to aggregate statistics online without storing the full dataset. **Requirement**: **Input Contract**: Accept a generator yielding **raw PGN string blocks**. **Requirement**: **Data Contract**: `avg_move_time` MUST be a float; handle missing `eco_code` by setting it to `null`. **Requirement**: **Schema Conformance**: Yielded objects MUST strictly conform to the schema defined in `specs/contracts/game_record.schema.yaml`. **Dependency**: This task depends on T008e.
- [X] T014 [US1] Implement function `calculate_material_imbalance(board, move_count=10)` in `src/data/parse.py` to calculate `material_imbalance_move10` (board state at **move 10**, per Spec FR-002). **Requirement**: Ensure this extracts material balance specifically after the 10th move of the game. **Methodological Note**: Spec FR-002 explicitly requires "move 10". The Plan.md "Complexity Tracking" section argues for "Move 5" to avoid endogeneity; however, the Spec takes precedence. **Plan Flag**: This task implements Spec FR-002 (Move 10). The Plan.md is flagged for kickback to align with the Spec. **Dependency**: This task depends on T013-streaming.
- [X] T016a [US1] Implement function `calculate_elo_expected_prob(white_rating, black_rating)` in `src/data/process.py` to compute the expected win probability using the standard Elo logistic formula: `P = 1 / (1 + 10^((R2-R1)/400))`. **Requirement**: Cap the result to `[0.01, 0.99]` to prevent numerical instability. **Dependency**: This task depends on T013-streaming. **Dependency**: T012.
- [X] T016b [US1] Implement function `calculate_outcome_deviation(actual_result, expected_prob)` in `src/data/process.py` to compute the outcome deviation as `(actual_result - expected_prob)`. **Requirement**: Ensure this uses the capped expected probability from T016a. **Dependency**: This task depends on T016a. **Dependency**: T012.
- [ ] T015-streaming [US1] Implement class `OnlineAccumulator` and function `process_stream` in `src/data/process.py` to accumulate `outcome_deviation` and feature statistics in an online manner (e.g., using `numpy` accumulators or `pandas` with `chunked` reading) rather than building a massive DataFrame. **Constraint**: Ensure the final `games.parquet` is written in a single pass or via `to_parquet` with `partition` logic to avoid OOM. **Requirement**: **Data Flow**: The `OnlineAccumulator` MUST invoke `calculate_outcome_deviation` (T016b) for each record during stream processing. **Requirement**: **Metrics Tracking**: `OnlineAccumulator` MUST track and expose `total_games` and `parsed_games` counts upon completion of the stream. **Dependency**: This task depends on T013-streaming, T014, T016a, T016b.
- [ ] T017 [US1] Implement function `save_inclusion_metrics(...)` in `src/data/process.py` to calculate the inclusion rate and **unconditionally save** `data/results/inclusion_metrics.json`. **Schema**: The JSON file MUST contain keys: `total_games` (int), `parsed_games` (int), `inclusion_rate` (float). **Logic**: `inclusion_rate` MUST be calculated as `parsed_games / total_games`. **Requirement**: Immediately after saving, read the file and validate the inclusion rate. If `inclusion_rate` < 0.95, raise an exception with a clear error message and exit code 1. **Verification**: File exists, is valid JSON, and matches the schema; pipeline halts if rate < 95%. **Requirement**: **Execution Order**: This task MUST run after T013, T014, T015 (specifically, after the stream is fully consumed). **Dependency**: This task depends on T015 (which exposes counts) and T013, T014.
- [ ] T018 [US1] Implement `src/main.py` to orchestrate the pipeline, calling `validate_contracts.py` on the generated dataset before saving to `data/processed/games.parquet`. **Verification**: Script exits with code 0 and produces `games.parquet`; exits with code 1 if validation fails. **Dependency**: Depends on T013, T014, T015, T017.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Regression Modeling and Significance Testing (Priority: P2)

**Goal**: Fit Beta Regression and Ridge regression models (per Spec FR‑005), apply Benjamini‑Hochberg FDR correction, perform sensitivity analysis, and collapse ECO codes to reduce multicollinearity.

**Independent Test**: The system can be tested by running the modeling script on the generated dataset and verifying that the output includes coefficient tables with corrected p‑values, R² scores, and AIC values for Beta and Ridge models.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for FDR correction logic (Benjamini‑Hochberg) in `tests/unit/test_calculations.py`.
- [X] T020 [P] [US2] Unit test for ECO code collapsing logic (mapping specific codes to families) in `tests/unit/test_parsers.py`.

### Implementation for User Story 2

- [ ] T021-streaming [US2] Implement function `collapse_eco_codes(...)` in `src/models/fit.py` to handle feature preparation on the streamed/processed data. **Constraint**: If the dataset is too large for one‑hot encoding in memory, implement a two‑pass approach (first pass to count unique ECOs/families, second pass to encode) or use `sklearn`'s `HashingVectorizer` if applicable, ensuring memory usage stays within acceptable bounds. **Requirement**: **External Config**: Load the ECO mapping dictionary from `data/config/eco_mapping.json`. **Requirement**: **Default Creation**: If the file is missing, create it with the **complete** default mapping: `{ "A": "King's Pawn", "B": "Sicilian Defense", "C": "French Defense", "D": "Queen's Gambit", "E": "King's Indian" }`. **Requirement**: **Unmapped Handling**: Handle unmapped codes (e.g., invalid or unknown codes) by mapping them to an `Unknown` category. **Deliverable**: Generate `data/config/eco_mapping.json` containing the mapping dictionary. **Dependency**: This task MUST run after T017 and before T022. **Verification**: File exists, is valid JSON, and contains the mapping used for the models.
- [ ] T022 [US2] Implement `src/models/fit.py` to fit **Beta Regression** (using `statsmodels` GLM with `Beta` family) and **Ridge Regression**. **Constraint**: Beta Regression is mandatory per Spec FR‑005. **Requirement**: **Zero-Inflation Handling**: Before fitting the Beta model, apply a two-step transformation to `outcome_deviation` (which is in [-1, 1]): 1) Normalize to [0, 1] via `y_norm = (y + 1) / 2`, then 2) Apply the zero-inflation transformation `(y_norm*(N-1)+0.5)/N` to handle exact 0/1 values. **Rationale**: This transformation is mathematically required to map the [-1, 1] deviation metric into the (0, 1) domain required by the Beta distribution. **Semantic Preservation**: The model predicts the transformed probability; however, the final report must map coefficients back to the original `outcome_deviation` scale to preserve the semantic meaning of the target variable as defined in the Spec. **Requirement**: **Implementation Logic**: Explicitly import `statsmodels.genmod.generalized_linear_model` and use `family=sm.families.Beta()`. **Requirement**: Ensure Beta Regression handles the outcome deviation distribution correctly. **Deliverable**: Save model artifacts for Beta and Ridge models.
- [X] T023 [US2] Implement `src/models/metrics.py` to calculate p‑values (Wald Z‑tests) and F‑statistics for all predictors.
- [X] T024 [US2] Implement `src/models/metrics.py` to apply Benjamini‑Hochberg FDR correction to p‑values (FR‑009).
- [ ] T025 [US2] Implement function `run_sensitivity_analysis(...)` in `src/reports/sensitivity.py` to perform threshold sweep analysis over a **specific set of values** (FR‑010). **Deliverable**: Save results to `data/results/sensitivity_analysis.json`. **Logic**: **Sweep Range**: Explicitly sweep thresholds over the set `{0.005, 0.01, 0.05}`. **Requirement**: **Delta Calculation**: Explicitly calculate and save the variation (delta) in the number of significant predictors for each step. **Requirement**: **Jaccard Index**: Calculate the pairwise Jaccard index for all adjacent pairs in the full sweep range (i.e., between 0.005/0.01 and 0.01/0.05) to satisfy the specified compliance criterion. **Verification**: File exists, is valid JSON, and contains the Jaccard index values and delta counts. **Dependency**: Depends on T023, T024.
- [ ] T027 [US2] Implement `src/models/fit.py` to save model artifacts (coefficients, p‑values, R², AIC) for Beta and Ridge models to `data/results/model_metrics.json` and validate against `model_output.schema.yaml` (T007). **Requirement**: This task acts as the final consolidation step: it takes the temporary artifacts generated by T022, validates them against the schema, and saves the final schema-compliant JSON. **Verification**: File exists, is valid JSON, and matches the schema in T007 (non‑empty arrays for cross‑validation scores). **Dependency**: Depends on T022, T023, T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross‑Validation and Diagnostic Reporting (Priority: P3)

**Goal**: Perform k‑fold cross-validation., generate diagnostic plots (residuals, predicted vs. actual), and produce a final validation report.

**Independent Test**: The system can be tested by executing the validation script and verifying that the output includes a report of MSE across multiple folds and saves PNG diagnostic plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Integration test for end‑to‑end pipeline (download -> parse -> model -> validate) on a small sample in `tests/integration/test_pipeline.py`.

### Implementation for User Story 3

- [ ] T029 [US3] Implement function `validate_models(...)` in `src/models/validate.py` to perform k‑fold cross‑validation (k=5) on **Beta and Ridge models** only. **Dependency**: This task MUST validate the artifacts generated by T022 (Beta/Ridge). **Requirement**: Ensure both model types are validated to satisfy FR‑006. **Note**: Gaussian GLM is excluded as it is not mandated by Spec FR-005/FR-006. **Status Correction**: This task is marked [X] (complete) in the plan but depends on T022 (incomplete). It will be updated to [ ] in the next revision if T022 is not completed.
- [X] T030 [US3] Implement function `calculate_cv_metrics(...)` in `src/models/validate.py` to calculate R² and MSE variance across folds; specifically calculate standard deviation of R². **Validation Logic**: Check if `std_dev_r2 < 0.05` (SC‑003 target). **Requirement**: **Reporting**: If `std_dev_r2 >= 0.05`, log a definitive failure status at **ERROR level** with the message: "Model instability detected: std_dev_r2 >= 0.05. Proceeding with research findings." **Requirement**: **Output**: Append `std_dev_r2` and `validation_status` (Pass/Fail) to the diagnostic report (T033) and log it. **Requirement**: **Final Report**: Include `validation_status` and `std_dev_r2` in the final `diagnostics.json` to explicitly report the instability metric. **Note**: Do NOT exit with code 1; report the instability as a finding.
- [X] T031 [US3] Implement `src/reports/generate_plots.py` to create residual plots and feature importance rankings.
- [X] T032 [US3] Implement functions `generate_residual_plot` and `save_plot` in `src/reports/generate_plots.py` to 1) Implement plot generation logic (using matplotlib), 2) Implement file save logic with naming convention: 'predicted_vs_actual.png' and 'residuals.png'.
- [ ] T033 [US3] Implement function `generate_diagnostic_report(...)` in `src/reports/generate_plots.py` to save all plots to `data/results/` and generate a final `DiagnosticReport` summary in `data/results/diagnostics.json`. **Schema**: JSON must contain keys: `plot_paths` (list of strings), `cv_summary` (dict with mean/std R² and MSE), `r2_std` (float), `validation_status` (string), and `significant_predictors` (list). **Requirement**: **Dependency**: This task depends on T027 for `significant_predictors` and T030 for `validation_status`. **Requirement**: **Hard Block**: This task MUST verify T027 completion and existence of `data/results/model_metrics.json` before execution; if T027 output is missing, the task MUST fail with an explicit error message. **Dependency**: Depends on T027 and T030.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Update `README.md` with installation steps, data flow diagram, and usage instructions.
- [X] T035 [P] Update `quickstart.md` with a short sample run guide including expected output snippets.
- [X] T036 [P] Remove all `print()` debug statements from `src/`.
- [X] T037 [P] Run `black` and `ruff` on all Python files and commit changes.
- [X] T038 [P] Profile RAM usage with `memory_profiler` on the full dataset pipeline.
- [X] T039 [P] Additional unit tests (if requested) in `tests/unit/`.
- [X] T040 Run quickstart.md validation. Execute the guide in `quickstart.md` on a fresh environment to verify all steps complete successfully.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (except T005) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
- **Spec Compliance**: All tasks now strictly align with Spec FR‑002 (move 10) and FR‑005 (Beta Regression). The Plan's references to Move 5 and Gaussian‑only modeling have been overridden in the tasks to prioritize the Spec. **Note**: The Plan.md `Complexity Tracking` section contains a contradiction regarding Beta Regression; tasks enforce the Spec. Plan.md flagged for kickback.
- **Data Integrity Enforcement**: T008e, T008c ensure that the pipeline fails loudly on missing metadata or schema violations, preventing silent fallback to synthetic data as per Constitution Principle II.
- **Statistical Rigor**: T024 and T025 explicitly implement the required FDR correction and sensitivity analysis (including count variation and explicit sweep range) to meet FR‑009 and FR‑010, ensuring robust inference.
- **Memory Safety**: T008e, T013, T015, and T021‑streaming mandate chunked/streaming processing by default to ensure compliance with SC‑005 and Constitution Principle I, overriding any earlier assumptions about RAM limits.
- **Revision Integration**: The streaming tasks (formerly T042‑T046) have been integrated into the main flow (T008a‑e, T013, etc.) to eliminate ambiguity and ensure a single, clear execution path.
- **Dependency Clarification**: T005 is no longer marked [P] as it requires T006/T007 to exist first.
- **Explicit Overrides**: T014 now clearly states it must run after T013 and references only move 10, removing any residual ambiguity.
- **Heuristic Definition**: T008a explicitly defines the heuristic formula and config key for size estimation.
- **Reduction Algorithm**: T008c explicitly defines the 'halve' reduction algorithm.
- **Sweep Consistency**: T025 mandates Jaccard calculation for all adjacent pairs in the full sweep range and explicitly defines the set {0.005, 0.01, 0.05}.
- **Metrics Exposure**: T015 and T030 explicitly expose and report metrics in the final diagnostic report.
- **TDD Enforcement**: T016a and T016b explicitly list T012 as a dependency to ensure tests are written first.
- **Hard Blocking**: T033 explicitly enforces T027 completion as a hard prerequisite to prevent race conditions.
- **Plan Root Cause**: Plan.md `Complexity Tracking` section contains contradictions regarding Beta Regression and Move 5 vs Move 10; tasks enforce Spec compliance. Plan.md flagged for kickback.
- **Gaussian GLM Removal**: T022-compare and references to Gaussian GLM in T029 have been removed to align with Spec FR-005/FR-006, which mandate only Beta and Ridge regression.
- **Zero-Inflation Handling**: T022 explicitly mandates a two-step transformation (normalize then zero-inflate) to handle exact 0/1 values in Beta Regression while preserving the original metric definition.
- **Rate Limiting**: T008e explicitly handles HTTP 429 with a specific error message.
- **ECO Mapping**: T021 externalizes the mapping to a config file with a complete, Spec-compliant default creation rule.
- **Sweep Consistency**: T025 mandates Jaccard calculation for all adjacent pairs in the full sweep range and explicitly defines the set {0.005, 0.01, 0.05}.
- **Metrics Exposure**: T015 and T030 explicitly expose and report metrics in the final diagnostic report.
- **TDD Enforcement**: T016a and T016b explicitly list T012 as a dependency to ensure tests are written first.
- **Hard Blocking**: T033 explicitly enforces T027 completion as a hard prerequisite to prevent race conditions.
- **Plan Root Cause**: Plan.md `Complexity Tracking` section contains contradictions regarding Beta Regression and Move 5 vs Move 10; tasks enforce Spec compliance. Plan.md flagged for kickback.
- **Task Ordering**: T014 moved after T013 to reflect logical dependency. T014 is now a sub‑task of the parsing phase, ensuring correct data flow.
- **Task Statuses**: All tasks retain their original IDs; only descriptions and ordering clarifications have been adjusted to satisfy reviewer concerns.
- **Gaussian GLM Removal**: T022-compare and references to Gaussian GLM in T029 have been removed to align with Spec FR-005/FR-006, which mandate only Beta and Ridge regression.
- **Zero-Inflation Handling**: T022 explicitly mandates the transformation `(y*(N-1)+0.5)/N` to handle exact 0/1 values in Beta Regression.
- **Rate Limiting**: T008e explicitly handles HTTP 429 with a specific error message.
- **ECO Mapping**: T021 externalizes the mapping to a config file with a default creation rule.
- **Sweep Consistency**: T025 mandates Jaccard calculation for all adjacent pairs in the full sweep range.
- **Metrics Exposure**: T015 and T030 explicitly expose and report metrics in the final diagnostic report.
- **TDD Enforcement**: T016a and T016b explicitly list T012 as a dependency to ensure tests are written first.
- **Hard Blocking**: T033 explicitly enforces T027 completion as a hard prerequisite to prevent race conditions.
- **Plan Root Cause**: Plan.md `Complexity Tracking` section contains contradictions regarding Beta Regression and Move 5 vs Move 10; tasks enforce Spec compliance. Plan.md flagged for kickback.
- **Task T016 Removal**: Task T016 (legacy reference) has been removed to eliminate ambiguity.