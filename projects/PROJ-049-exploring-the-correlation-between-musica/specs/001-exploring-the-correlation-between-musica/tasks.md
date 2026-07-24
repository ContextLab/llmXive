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

- [X] T001a [P] Create directory structure: `data/raw/`, `data/processed/`, `code/`, `tests/`, `results/`, `logs/`. **Note**: The `contracts/` directory is created in Phase 2 (T007a) as it is a foundational artifact, not a generic setup directory.
- [X] T001b [P] Create empty `__init__.py` files in `code/` and `tests/`
- [X] T001c [P] Initialize `requirements.txt` with placeholder dependencies
- [X] T002 [P] Initialize Python project with dependencies in `requirements.txt`. **Content**: Pin exact versions for `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `numpy`, `datasets`, `requests`, `pytest`, `statsmodels`. **Verification**: Run `pip install -r requirements.txt` successfully; ensure all versions are pinned (e.g., `pandas==2.0.0`).
- [X] T003a [P] Create `.ruff.toml` configuration file for linting. **Content**: Set `line-length = 88`, `target-version = "py311"`, and enable specific rules (E, F, W).
- [X] T003b [P] Create `pyproject.toml` with `[tool.black]` configuration for formatting. **Content**: Set `line-length = 88`, `target-version = ['py311']`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005a [P] Implement `setup_logging()` function in `code/utils.py` returning a logger configured with file rotation to `logs/app.log`.
- [X] T006b [P] Create `.env.example` file listing expected environment variable names (e.g., `RANDOM_SEED`, `DATA_PATH`) with placeholder values.
- [X] T006c [P] **Populate `.env`**: Create a `.env` file with default values for `RANDOM_SEED=42` and `DATA_PATH="data"`. **Verification**: Verify file exists and contains these keys.
- [X] T006a Implement `load_config()` function in `code/utils.py` returning a dict of environment variables (Depends on T006c to ensure variables are defined).
- [X] T007a [P] Create `contracts/` directory if it does not exist. **Verification**: `ls contracts/` must succeed.
- [X] T007b [P] Define schema fields in `contracts/dataset.schema.yaml` (fields: `user_id`, `openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism`, `age`, `gender`, `country`) and `contracts/analysis_output.schema.yaml` (fields: `trait`, `genre`, `rho`, `p_value`, `adjusted_p_value`, `is_significant`, `beta`, `std_error`, `effect_size_r`, `effect_size_fisher_z`, `significance_status`). **Verification**: Use `pandera` to validate a sample CSV against the schema. Sample CSV content: `user_id,openness,age...` (provide several rows of dummy data).
- [X] T009 [P] Setup error handling wrappers in `code/utils.py` for HTTP timeouts and 404s.
- [X] T013b [P] **Create Genre Lookup Table**: Create `contracts/genre_lookup.yaml` defining the mapping from raw genre tags (e.g., 'alt', 'rock', 'classical') to the standardized categories (Rock, Pop, Hip-Hop, Classical, Electronic, Jazz, Folk, Country, Metal, Other). **Verification**: Verify file exists and contains all 10 categories.
- [X] T040 [P] **Constitution Update (Gate)**: Implement a task to open a formal PR to amend the Constitution (Principle VI) to align with FR-005 (Benjamini-Hochberg FDR) and FR-006 (Pearson's r/Fisher's z). **Action**: The task must describe the procedure: (1) Draft PR description, (2) Update `CONSTITUTION.md` version line to `1.0.1`, (3) Record the change in `state/projects/...yaml` as a Sync Impact Report. **Verification**: Verify the PR template exists and the version line is updated in the draft.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest OpenML BFI-2 and Last.fm 1k, clean, map genres, and prepare a unified dataframe.

**Independent Test**: The pipeline can be tested by executing the data loading script and verifying the output dataframe contains non-null values for all personality traits and at least 10 standardized genre categories (plus 'Other') for a sample of at least 100 users, with no missing demographic covariates.

### Implementation for User Story 1

- [X] T012a [US1] **Load OpenML BFI-2**: Implement `code/ingest.py` to load the BFI-2 dataset from OpenML using `openml.datasets.get_dataset` with the appropriate dataset identifier. **Logic**:
 1. Attempt download with `timeout=300` and `retry_count=3`.
 2. If HTTP 404/Timeout or dataset not found occurs, raise `DataUnavailableError` with message "Real data fetch failed (OpenML 42473); verified source unavailable. Aborting analysis." **NO SYNTHETIC FALLBACK**.
 3. If successful, save raw data to `data/raw/bfi2_raw.csv`.
 **Verification**: Log file must show "Download successful" or raise a clear `DataUnavailableError`. No synthetic data generation code is present.
- [X] T012b [US1] **Load Last.fm 1k**: Implement `code/ingest.py` to load the Last.fm dataset from HuggingFace (`lastfm/lastfm_k`, split="train") using `datasets.load_dataset("lastfm/lastfm_1k", split="train", streaming=True)`. **Logic**:
 1. Use `streaming=True` to handle potential size issues.
 2. If HTTP 404/Timeout or dataset not found occurs, raise `DataUnavailableError` with message "Real data fetch failed (lastfm/lastfm_1k); verified source unavailable. Aborting analysis." **NO SYNTHETIC FALLBACK**.
 3. If successful, save raw data to `data/raw/lastfm_raw.csv`.
 **Verification**: Log file must show "Download successful" or raise a clear `DataUnavailableError`. No synthetic data generation code is present.
- [X] T013 [US1] **Merge Datasets**: Implement `code/ingest.py` to merge `data/raw/bfi2_raw.csv` and `data/raw/lastfm_raw.csv` on `user_id`. **Logic**:
 1. Perform an inner join.
 2. If the join results in 0 rows, raise `DataUnavailableError` with message "No common users found between BFI-2 and Last.fm datasets. Aborting analysis."
 3. Save merged result to `data/processed/merged_data.csv`.
 **Verification**: Verify output file exists and has >0 rows.
- [X] T014 [US1] **Map Genres**: Implement `code/mapping.py`: Load lookup table from `contracts/genre_lookup.yaml` (T013b) and map raw genre tags from `data/processed/merged_data.csv` to standard categories + 'Other'. **Verification**: Test with inputs `['alt', 'rock']` expecting `['Rock', 'Rock']`. **Dependency**: Depends on T013 completion to ensure source data exists.
- [X] T015 [US1] **Prepare Unified Data**: Implement `code/ingest.py`: Select relevant columns from the merged dataset (traits, genres, demographics). Exclude users with zero listening minutes. **Dependency**: Depends on T014 completion.
- [X] T016 [US1] **Handle Missing Data**: Implement `code/ingest.py`: Handle missing demographic data (impute numeric with median, categorical with mode) or exclude; log counts. **Verification**: Log must contain exact string "INFO: Imputed X rows using {strategy} | Excluded Y rows" at INFO level. **Dependency**: Depends on T015 completion.
- [X] T017 [US1] Verify `data/processed/merged_data.csv` schema integrity (non-empty, correct columns) and log checksum.

### Tests for User Story 1 (TDD - Write before implementation)

- [X] T010 [US1] Define test cases in `tests/test_mapping.py`: `test_map_raw_tags_to_standard` using inputs `['alt', 'rock']` and expected output from `contracts/genre_lookup.yaml`. (Write this test *before* T014 implementation).
- [X] T011 [US1] Define test cases in `tests/test_ingest.py`: `test_missing_data_imputation` verifying strategy and logging. (Write this test *before* T016 implementation).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation and Regression Analysis (Priority: P2)

**Goal**: Compute Spearman correlations and multiple linear regressions with demographic controls, applying FDR correction.

**Independent Test**: The analysis can be tested by running the script on a known synthetic dataset with pre-calculated correlation values and verifying the output matches the expected coefficients within an acceptable tolerance.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/analysis.py`:
 1. Log-transform `listening_minutes`.
 2. Compute Spearman rho and p-values for all trait-genre pairs.
 3. Write intermediate results to `data/processed/correlation_results.csv` with columns: `trait`, `genre`, `rho`, `p_value`.
 4. Calculate boolean flag for `r > 0.3` (SC-001).
 **Verification**: Verify file exists, contains correct columns, and numerical values match synthetic ground truth (from T010/T011 - *if a synthetic test file is manually provided for CI*) within 0.001 tolerance.
- [X] T021 [US2] Implement `code/analysis.py`: Run multiple linear regression for each trait with age, gender, and country as covariates. **Formula**: `trait ~ age + gender + C(country)`. **API**: Use `statsmodels.formula.api.ols`. **Verification**: Verify output contains beta coefficients and standard errors.
- [X] T022 [FR-004] [US2] Implement `code/analysis.py`: Detect collinear predictors using VIF (statsmodels) with a threshold of **VIF > 5** (as defined in Plan). If VIF > 5, drop the predictor, log the specific predictor name, update the regression model, and output a `model_definition` column in results as a JSON string listing the *actual* covariates used. **Verification**: Verify JSON column exists and contains valid JSON.
- [X] T023 [US2] Implement `code/analysis.py`: Apply Benjamini-Hochberg FDR correction (q < 0.05) to all p-values. **Logic**: Calculate dynamic test count N = (N_traits × N_genres). Use `statsmodels.stats.multitest.multipletests(p_values, method='fdr_bh')`. **Verification**: Verify adjusted p-values are in output and flag `is_significant` correctly. (Depends on T040 completion).
- [X] T034 [US2] **Measure Validity of Demographic Controls**: Implement `code/analysis.py` to calculate the delta in regression coefficients for personality traits between models with covariates and models without covariates (SC-003). **Logic**: `delta = abs(beta_with_covariates - beta_without_covariates)`. Calculate `percent_change = delta / abs(beta_without_covariates)`. Set `validity_status` to "Significant Change" if `percent_change > 0.10` (10% threshold), else "Stable". **Output**: Save to `data/processed/coefficient_deltas.csv` with columns `trait`, `genre`, `delta`, `percent_change`, `validity_status`. **Verification**: Verify file exists, contains non-zero deltas, and logs the threshold used.
- [X] T024 [US2] Save final analysis results (rho, p-value, adjusted p-value, is_significant, beta coefficients, model_definition) to `data/processed/analysis_results.csv`. (Depends on T020, T021, T022, T023, T034).

**Checkpoint**: At this point, All user stories should now be independently functional

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate correlation heatmap, regression coefficient plots, and a summary report with effect sizes.

**Independent Test**: The reporting module can be tested by executing the script and verifying the existence of a `results_report.csv` and a `correlation_heatmap.png` file, ensuring the heatmap correctly displays the sign and magnitude of correlations.

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis.py`: Read `data/processed/analysis_results.csv` (T024 output). Generate `results/correlation_heatmap.png` (800x600, 150dpi) using `sns.heatmap` with a **diverging colormap** ('coolwarm'). **Axis Labels**: "Personality Trait" (y), "Genre" (x). **Title**: "Spearman Correlation: Personality vs. Music Genre". **Verification**: Verify output file exists and color intensity maps to signed rho values (positive=red, negative=blue).
- [X] T027 [US3] **Calculate Effect Sizes**: Implement `code/analysis.py`: Read `data/processed/merged_data.csv` (raw data, T017) and `data/processed/analysis_results.csv` (Spearman results, T024). Calculate **Pearson's r** effect sizes and **Fisher's z** confidence intervals for significant results as mandated by FR-006/US-3. **Clarification**: Treat the calculated Spearman rho as the basis for the effect size magnitude (i.e., `effect_size_r = abs(rho)`), and apply Fisher's z-transformation to derive the confidence interval. **Verification**: Verify output contains `effect_size_r` and `effect_size_fisher_z` columns.
- [X] T028 [US3] Implement `code/analysis.py`: Generate `results/results_report.csv` containing effect sizes, CIs, and explicit "Non-significant (adjusted p ≥ 0.05)" labels for null results. **Logic**: For rows where `is_significant` is False, set `effect_size_r` and `effect_size_fisher_z` to `NaN` (empty string in CSV) and set a new column `significance_status` to "Non-significant (adjusted p ≥ 0.05)". For significant rows, set `significance_status` to "Significant". **Verification**: Verify schema matches FR-006 (numeric columns remain numeric) and nulls are handled correctly.
- [X] T029 [P] [US3] Add `tests/test_report.py::test_report_completeness` to verify `results_report.csv` includes all relevant traits across a diverse set of genres.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [P] Documentation updates in `README.md` with execution instructions and real data source explanation.
- [X] T031 Code cleanup and refactoring in `code/` (Only after T020, T026, T028 are verified complete).
- [X] T032a [P] Add `tests/test_edge_cases.py::test_empty_dataset` for empty dataset handling.
- [X] T032b [P] Add `tests/test_edge_cases.py::test_all_missing_demographics` for missing demographic handling.
- [X] T033 [P] [US1-US3] Implement `code/pipeline.py` end-to-end orchestration script that sequentially executes ingestion, analysis, and reporting; add timing logic to record execution time in `logs/timing.log`. **Timeout Logic**: Implement a wrapper that raises `TimeoutError` and fails the run if total time exceeds **6 hours** (as defined by SC-004). **Verification**: Verify `logs/timing.log` exists and contains the total execution time in seconds, and that the script fails if the limit is exceeded.
- [X] T042 [P] **Documentation**: Update `README.md` and `data/README.md` to explicitly document the "Real-First" strategy (OpenML + Last.fm) and confirm the exclusive use of real data. Remove all references to "Validation Mode" or "Synthetic Data". **Verification**: Verify the text "Real-First", "OpenML 42473", and "lastfm/lastfm_1k" appear in the README.

---

## Phase O: Review Resolution & Robustness (Revision Pass)

**Purpose**: Improvements that address specific reviewer concerns regarding data sourcing, streaming capability, and error handling to ensure execution on free-tier CI. (Note: T050/T051 logic has been integrated into T012a/T012b).

### Implementation for Review Resolution

- [ ] T053 [US2] **Add Sensitivity Analysis (Optional)**: Implement a new function in `code/analysis.py` to perform a sensitivity analysis on the FDR threshold (sweeping alpha ranging from a stringent threshold to a more permissive threshold) and log how the count of significant results changes. **Output**: Save to `data/processed/sensitivity_analysis.csv`. **Verification**: Verify the output file contains the alpha level and the count of significant findings for each level. **Note**: This task is linked to the "Assumption: Sensitivity Analysis" in the spec and is marked as optional.
- [ ] T054 [US3] **Enhance Report Validation**: Add a check in `code/visualization.py` to ensure that the `correlation_heatmap.png` includes a colorbar with a labeled scale and that the `results_report.csv` includes a header row with exact column names matching `contracts/analysis_output.schema.yaml`. **Verification**: Run the script and visually inspect the heatmap for the colorbar; parse the CSV header to confirm schema compliance.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review Resolution (Phase O)**: Can run in parallel with Polish, but must be completed before final deployment to ensure robustness.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires merged data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires analysis results from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T006a which depends on T006c)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase O tasks can be implemented in parallel with Phase N tasks.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for genre mapping logic in tests/test_mapping.py"
Task: "Unit test for missing data imputation in tests/test_ingest.py"

# Launch all implementation tasks for User Story 1 together:
Task: "Implement code/ingest.py: Load OpenML BFI-2..."
Task: "Implement code/ingest.py: Load Last.fm 1k..."
Task: "Implement code/ingest.py: Merge datasets..."
```

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
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Ensure all statistical tests run on CPU only (no GPU dependencies).
- **Critical**: T020, T026, T028 are now marked complete and include verification steps for numerical accuracy and schema compliance.
- **Critical**: Phase O has been streamlined; T050/T051 logic is integrated into T012a/T012b.
- **Critical**: `contracts/` directory creation is now exclusively handled in Phase 2 (T007a) to avoid confusion.
- **Critical**: T040 addresses the Constitution conflict by performing a formal amendment procedure instead of creating ad-hoc files.
- **Critical**: T042 ensures ethical documentation of the real data usage.
- **Critical**: T012a and T012b must complete before T013 to ensure data availability.
- **Critical**: **All tasks are now aligned with the "Real-First" strategy defined in `plan.md`.**
- **Critical**: T013b (Genre Lookup) is now in Phase 2 to ensure it is available for T014.
- **Critical**: T016 specifies log level (INFO) and format.
- **Critical**: T027 explicitly treats Spearman rho as the basis for effect size calculation.
- **Critical**: T028 uses a separate column for status text to preserve numeric schema.
- **Critical**: T034 defines the validity threshold logic (10% change).