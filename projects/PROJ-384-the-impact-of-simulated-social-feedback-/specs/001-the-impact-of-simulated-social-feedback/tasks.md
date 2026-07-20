# Tasks: The Impact of Simulated Social Feedback on Self-Esteem Fluctuations

**Input**: Design documents from `/specs/001-the-impact-of-simulated-social-feedback-on-self-esteem-fluctuations/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are REQUIRED based on the spec's "Independent Test" and "Acceptance Scenarios" sections.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project - adjusted based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (create `code/`, `code/utils/`, `tests/`, `data/raw/`, `data/processed/` directories)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scikit-learn, statsmodels, transformers, torch, datasets, requests, tqdm, pydantic)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `code/utils/config.py` to define paths, random seeds, and thresholds (VIF limit, sentiment range [negative, positive])
- [X] T005 [P] Create `code/utils/logger.py` to set up logging with file and console handlers, ensuring logs are written to `logs/pipeline.log`
- [ ] T006 Create `contracts/interaction_schema.schema.yaml` defining the JSON schema for raw interaction data (post_text, reply_text, timestamp, user_id) with strict type enforcement
- [X] T007 Create `code/utils/data_validation.py` to load the schema and provide a `validate_dataframe(df)` function that raises on schema mismatch
- [ ] T008 Create `code/utils/model_loader.py` to initialize the RoBERTa sentiment model (CPU-optimized) and load the Rosenberg self-esteem lexicon from `data/raw/lexicons/rosenberg_words.txt`, caching them in memory
- [X] T009 [P] Create `tests/test_config.py` to verify config loading and seed reproducibility
- [X] T010 [P] Create `tests/test_validation.py` to verify schema validation logic raises on malformed data

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Valence Sequencing (Priority: P1) 🎯 MVP

**Goal**: Download the LOST dataset, parse raw text, validate against schema, and compute a time-series of feedback valence for each user session.

**Independent Test**: Run `code/01_ingest.py` on a small subset (or full dataset if fast enough) and verify `data/processed/valence_sequence.csv` is generated with `user_id`, `timestamp`, `post_text`, `reply_text`, and `calculated_valence` columns, with no nulls in `calculated_valence` except for the sentinel - a specific placeholder value indicating missing or undefined data.

### Tests for User Story 1 ⚠️

- [X] T011 [P] [US1] Unit test `tests/test_ingest.py` verifying that `validate_dataframe` correctly rejects a DataFrame with missing `timestamp`
- [X] T012 [P] [US1] Unit test `tests/test_ingest.py` verifying that `calculate_sentiment` returns -999.0 for empty reply text and a float in [-1.0, 1.0] for valid text
- [X] T013 [P] [US1] Integration test `tests/test_ingest.py` verifying that a mock dataset of a representative number of rows produces a valid CSV with no crashes

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/01_ingest.py` to download the `pushshift_reddit` dataset (LOST) using `datasets.load_dataset('pushshift_reddit', split='train', streaming=True)` if necessary, parsing raw text fields
- [ ] T015 [US1] Implement `code/01_ingest.py` to validate raw data against `contracts/interaction_schema.schema.yaml` using `code/utils/data_validation.py` (hard gate: raise if invalid)
- [ ] T016 [US1] Implement `code/01_ingest.py` to apply the RoBERTa model (via `code/utils/model_loader.py`) to `post_text` and `reply_text`, normalizing scores to [-1.0, 1.0]
- [ ] T017 [US1] Implement `code/01_ingest.py` to handle missing replies by assigning -999.0 to `calculated_valence` and logging a warning
- [ ] T018 [US1] Implement `code/01_ingest.py` to group interactions by `user_id` and `timestamp`, sorting chronologically, and output `data/processed/valence_sequence.csv`
- [ ] T019 [US1] Add error handling in `code/01_ingest.py` to skip rows with malformed timestamps or missing critical fields, logging the count of skipped rows

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Volatility Metric Calculation (Priority: P2)

**Goal**: Calculate specific metrics representing feedback volatility (rolling window std dev, sign change frequency) and the Self-Esteem Indicator for each user.

**Independent Test**: Feed a synthetic time-series `[1.0, -1.0, 1.0, -1.0]` into the calculation module and verify the volatility score is high compared to `[0.1, 0.1, 0.1]`. Verify the Self-Esteem Indicator is derived correctly from a test string containing Rosenberg words.

### Tests for User Story 2 ⚠️

- [ ] T020 [P] [US2] Unit test `tests/test_metrics.py` verifying rolling window std dev calculation for a known sequence (e.g., alternating 1/-1)
- [ ] T021 [P] [US2] Unit test `tests/test_metrics.py` verifying sign change frequency calculation (count of 1->-1 or -1->1 transitions)
- [ ] T022 [P] [US2] Unit test `tests/test_metrics.py` verifying that sequences with < 2 interactions return -999.0 and log a warning
- [ ] T023 [P] [US2] Unit test `tests/test_metrics.py` verifying the Rosenberg lexicon score calculation against a known input string

### Implementation for User Story 2

- [ ] T024 [US2] Implement `code/02_metrics.py` to load `data/processed/valence_sequence.csv` and group by `user_id`
- [ ] T025 [US2] Implement `code/02_metrics.py` to calculate `mean_reply_valence` for each user from their `calculated_valence` sequence (excluding sentinels)
- [ ] T026 [US2] Implement `code/02_metrics.py` to calculate the Self-Esteem Indicator (Rosenberg lexicon score) for each user's `post_text` using the lexicon from `data/raw/lexicons/rosenberg_words.txt`
- [ ] T027 [US2] Implement `code/02_metrics.py` to calculate `post_valence` (mean sentiment of the user's own `post_text`) as a distinct covariate. **Verification**: Assert that the source of `post_valence` is strictly the raw `post_text` column and not conflated with the Self-Esteem Indicator lexicon score.
- [ ] T028 [US2] Implement `code/02_metrics.py` to calculate `post_length` (character or word count of `post_text`) as a covariate
- [ ] T029 [US2] Implement `code/02_metrics.py` to calculate `user_activity_level` (total number of interactions per user) as a covariate
- [ ] T030 [US2] Implement `code/02_metrics.py` to calculate the primary volatility metric: Standard Deviation of a rolling window (size=5) of `calculated_valence`; if 2 <= interactions < 5, use all available data for the window; if < 2, return -999.0
- [ ] T031 [US2] Implement `code/02_metrics.py` to calculate the secondary volatility metric: Frequency of sign changes in `calculated_valence`; if 2 <= interactions < 5, use all available data; if < 2, return -999.0
- [ ] T032 [US2] Implement `code/02_metrics.py` to handle edge cases: use available data (min 2) if window size < 5, return -999.0 if < 2 interactions
- [ ] T033 [US2] Implement `code/02_metrics.py` to output `data/processed/user_metrics.csv` containing `user_id`, `self_esteem_indicator`, `volatility_std`, `volatility_sign_changes`, `mean_reply_valence`, `post_valence`, `post_length`, and `user_activity_level`
- [ ] T034 [US2] Add logging in `code/02_metrics.py` to calculate the exclusion percentage (users with < 2 interactions), log it, and report it as a success criterion metric (SC-002) without asserting a threshold

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4.5: Sensitivity Analysis Producer (Parallel to Phase 5)

**Goal**: Generate intermediate volatility datasets for alternate window sizes required by FR-006.

- [ ] T035 [US2] Implement `code/02_metrics.py` to calculate volatility metrics for window sizes 3 and 7 based on `valence_sequence.csv` and save them to separate CSV files (`data/processed/volatility_window_3.csv`, `data/processed/volatility_window_7.csv`) containing `user_id` and the specific volatility metric, to be used by T045 (Sensitivity Analysis).

---

## Phase 5: User Story 3 - Regression Analysis and Significance Testing (Priority: P3)

**Goal**: Run multiple linear regression controlling for overall valence and post_valence to determine if volatility predicts self-esteem, including VIF checks and sensitivity analysis.

**Independent Test**: Run `code/03_analysis.py` on a synthetic dataset with known coefficients and verify the output includes correct p-values and R² within 1% margin of error.

### Tests for User Story 3 ⚠️

- [ ] T036 [P] [US3] Unit test `tests/test_analysis.py` verifying VIF calculation returns correct values for a known matrix
- [ ] T037 [P] [US3] Unit test `tests/test_analysis.py` verifying regression model halts with an error if VIF >= 5.0
- [ ] T038 [P] [US3] Integration test `tests/test_analysis.py` verifying the full regression pipeline on a small synthetic dataset produces expected coefficients

### Implementation for User Story 3

- [ ] T039 [US3] Implement `code/03_analysis.py` to load `data/processed/user_metrics.csv` and prepare the regression DataFrame with columns: `self_esteem_indicator`, `mean_reply_valence`, `volatility_std`, `volatility_sign_changes`, `post_valence`, `post_length`, `user_activity_level`
- [ ] T040 [US3] Implement `code/03_analysis.py` to calculate VIF for all independent variables (`mean_reply_valence`, `volatility_std`, `volatility_sign_changes`, `post_valence`, `post_length`, `user_activity_level`)
- [ ] T041 [US3] Implement `code/03_analysis.py` to log and save the specific VIF values for each variable to `data/results/diagnostics/vif_report.csv` and console output
- [ ] T042 [US3] Implement `code/03_analysis.py` to halt execution and log a diagnostic error if any VIF >= 5.0 (SC-005)
- [ ] T043 [US3] Implement `code/03_analysis.py` to fit a multiple linear regression model with `self_esteem_indicator` as dependent variable and volatility/valence metrics (including `post_valence` and covariates) as predictors
- [ ] T044 [US3] Implement `code/03_analysis.py` to extract and format results: p-values, coefficients, R², and adjusted R²
- [ ] T045 [US3] Implement `code/03_analysis.py` to perform the sensitivity analysis (FR-006): load `data/processed/volatility_window_3.csv` and `data/processed/volatility_window_7.csv` (generated in T035), merge with other covariates, re-run regression for window sizes {3, 5, 7}, and generate `data/results/sensitivity_summary.csv` containing the variance in p-values and magnitudes for the volatility coefficient across window sizes
- [ ] T046 [US3] Implement `code/03_analysis.py` to generate `data/results/regression_report.md` containing the primary results and sensitivity analysis findings
- [ ] T047 [US3] Implement `code/03_analysis.py` to generate diagnostic plots (residuals vs fitted, Q-Q plot) and save to `data/results/diagnostics/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting and Polish (Priority: P4)

**Goal**: Generate the final report and ensure all success criteria are met.

- [ ] T048 [US3] Implement `code/04_report.py` to aggregate results from `data/results/regression_report.md` and `data/processed/user_metrics.csv` into a final summary. **Requirement**: Explicitly format and verify the presence of the p-value for the volatility coefficient as `p=0.XX` in the final `data/results/final_report.md` to satisfy SC-004.
- [ ] T049 [P] [Polish] Run the full pipeline end-to-end on a sample to verify execution time < 60 mins (SC-003)
- [ ] T050 [P] [Polish] Verify `data/processed/valence_sequence.csv` contains ≥ 95% of records from source (SC-001)
- [ ] T051 [P] [Polish] Verify `data/processed/user_metrics.csv` contains valid metrics for ≥ 90% of eligible users (SC-002)
- [ ] T052 [P] [Polish] Add a `README.md` in `code/` with instructions to run `01_ingest.py`, `02_metrics.py`, `03_analysis.py` in order
- [ ] T053 [P] [Polish] Create `code/run_pipeline.sh` to execute the full sequence with error handling

**Checkpoint**: Final report generated and all success criteria verified.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (Data Ingest)**: Must complete before US2 (Metrics) because US2 requires `valence_sequence.csv`
 - **US2 (Metrics)**: Must complete before US3 (Analysis) because US3 requires `user_metrics.csv`
 - **Sensitivity Analysis (T035)**: Can run in parallel with US3 (T039-T047) after US1 completes, but T045 depends on T035.
 - **US3 (Analysis)**: Must complete before Reporting
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **DEPENDS ON US1**. Cannot calculate volatility without the valence sequence generated in US1.
- **User Story 3 (P3)**: **DEPENDS ON US2**. Cannot run regression without the metrics calculated in US2.
- **Sensitivity Analysis (T035)**: **DEPENDS ON US1 ONLY**. T035 recalculates volatility from `valence_sequence.csv` and can run in parallel with US2 (Phase 4) or immediately after US1. T045 depends on T035.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before Services/Scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **US1, US2, US3 cannot run in parallel** due to strict data flow dependencies (Ingest -> Metrics -> Analysis), EXCEPT T035 (Sensitivity Analysis Producer) which can run in parallel with US2 after US1 completes.
- All tests for a user story marked [P] can run in parallel
- Different parts of the sensitivity analysis (window sizes 3, 5, 7) can run in parallel once US1 is complete (specifically T035 for windows 3/7 can run parallel to T030/T031 for window 5).

---

## Parallel Example: Sensitivity Analysis

Once `code/01_ingest.py` is complete (US1), the sensitivity analysis for window sizes can be parallelized with US2:

```bash
# Launch regression for different window sizes in parallel (if using a runner that supports it):
Task: "Run regression for window_size=3"
Task: "Run regression for window_size=5"
Task: "Run regression for window_size=7"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ingest & Valence)
4. **STOP and VALIDATE**: Verify `data/processed/valence_sequence.csv` exists and matches schema.
5. Proceed to US2 only after US1 is verified.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Validate CSV output
3. Add User Story 2 → Test independently → Validate Metrics CSV
4. Add User Story 3 → Test independently → Validate Regression Report
5. Add Reporting → Finalize output

### Sequential Execution (Recommended for this Pipeline)

Given the strict data flow (Ingest -> Metrics -> Analysis), this project is best executed sequentially:
1. **T001-T010**: Setup & Foundational
2. **T011-T019**: US1 (Ingest) - Generates `valence_sequence.csv`
3. **T020-T034**: US2 (Metrics) - Reads `valence_sequence.csv`, generates `user_metrics.csv`
4. **T035**: Sensitivity Producer - Generates alternate window metrics
5. **T036-T047**: US3 (Analysis) - Reads `user_metrics.csv` and T035 outputs, generates `regression_report.md`
6. **T048-T053**: Reporting & Polish
*Note: T035 (Sensitivity Analysis) can run in parallel with T020-T034 after T018 completes.*

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- **Data Flow is Critical**: Do not attempt US2 before US1 is complete. Do not attempt US3 before US2 is complete.
- **Sentiment Model**: Use CPU-optimized RoBERTa as per plan. Ensure `transformers` and `torch` are configured for CPU.
- **Data Integrity**: `code/01_ingest.py` MUST raise on schema violation. No silent fallbacks.
- **Sentinel Values**: Strictly use -999.0 for missing data as defined in spec.
- **Verify tests fail before implementing**.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.