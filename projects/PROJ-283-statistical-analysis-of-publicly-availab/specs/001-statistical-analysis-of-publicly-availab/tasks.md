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

- [ ] T001 Create project structure: `src/`, `tests/`, `data/`, `specs/`, `data/raw/`, `data/processed/`, `data/results/`, `specs/contracts/`, `tests/contract/`, `tests/unit/`, `tests/integration/`. Create `__init__.py` in all `src/` and `tests/` subdirectories.
- [ ] T002 Initialize Python 3.11 project by creating `requirements.txt` at repository root containing: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `chess`, `matplotlib`, `seaborn`, `requests`, `datasets`, `pytest`.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml` or `.ruff.toml`/`.black.toml`.
- [ ] T004 [P] Setup `src/config.py` with random seeds (e.g., `RANDOM_SEED=42`), file paths constants, and Lichess dataset URL constants.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement `src/validation/validate_contracts.py` to load YAML schemas from `specs/contracts/` and validate in-memory pandas DataFrames against them.
- [ ] T006 Define `specs/contracts/game_record.schema.yaml` with columns: `game_id`, `white_rating`, `black_rating`, `eco_code`, `avg_move_time_white`, `avg_move_time_black`, `material_imbalance_move5`, `outcome`, `elo_expected_prob`, `outcome_deviation`. (Note: Aligns with Plan.md Complexity Tracking override of Spec FR-002).
- [ ] T007 Define `specs/contracts/model_output.schema.yaml` with columns: `model_type`, `coefficients`, `p_values`, `r_squared`, `aic`, `cross_validation_scores`. (Note: Aligns with Plan.md Complexity Tracking override of Spec FR-005).
- [ ] T008 Implement `src/data/download.py` with exponential backoff retry logic for Lichess/HuggingFace API.
- [ ] T009 [US1] Implement `src/data/download.py` logic to: (1) Verify dataset URL reachability; if unreachable, HALT with error. (2) Sample a small subset of games to check for `move_time` metadata presence. (3) If >5% of sampled games lack `move_time`, HALT immediately with error (per Plan.md Dataset Verification). (4) If ≤5% lack `move_time`, exclude those specific games and proceed. This resolves the conflict between Spec Edge Cases (skip) and Plan (halt) by enforcing the Plan's HALT threshold.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download a subset of Lichess PGN games, parse them to extract features (ECO, move times, material imbalance at move 5), calculate Elo expected probabilities, and produce a clean `GameRecord` dataset.

**Independent Test**: The system can be tested by running the ingestion pipeline on a small sample (e.g., 100 games) and verifying that the output collection of GameRecord entities contains the expected columns (ECO code, avg_move_time, material_imbalance_move5, elo_expected_prob, outcome_deviation) with no null values in critical fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for `GameRecord` schema validation in `tests/contract/test_game_record.py`.
- [ ] T011 [P] [US1] Unit test for PGN parsing logic handling malformed move lists in `tests/unit/test_parsers.py`.
- [ ] T012 [P] [US1] Unit test for Elo probability calculation and deviation math in `tests/unit/test_calculations.py`.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `src/data/parse.py` to read PGN files, extract ECO codes, and calculate `avg_move_time` per player.
- [ ] T014 [US1] Implement `src/data/parse.py` logic to calculate `material_imbalance_move5` (board state at move 5). This implements the Plan.md Complexity Tracking override of Spec FR-002 (Move 10). The schema in T006 and downstream tasks reference this Move 5 value.
- [ ] T015 [US1] Implement `src/data/process.py` to calculate `elo_expected_prob` using `P = 1 / (1 + 10^((R2-R1)/400))` with probability capping for numerical stability (e.g., clamp to [0.01, 0.99]).
- [ ] T016 [US1] Implement `src/data/process.py` to compute `outcome_deviation` as `(actual_result - expected_probability)`.
- [ ] T017 [US1] Implement error handling in `src/data/process.py` to skip malformed games, log errors, and ensure final dataset inclusion rate meets SC-001 (≥95% of valid PGNs). Remove any ±1% target constraint as it conflicts with the exclusion rule and T009 HALT logic.
- [ ] T018 [US1] Integrate schema validation in `src/main.py` to run `validate_contracts.py` on the generated dataset before saving to `data/processed/games.parquet`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Regression Modeling and Significance Testing (Priority: P2)

**Goal**: Fit Gaussian GLM and Ridge regression models (per Plan.md override), apply Benjamini-Hochberg FDR correction, perform sensitivity analysis, and collapse ECO codes to reduce multicollinearity.

**Independent Test**: The system can be tested by running the modeling script on the generated dataset and verifying that the output includes coefficient tables with corrected p-values, R² scores, and AIC values for Gaussian GLM and Ridge models.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for FDR correction logic (Benjamini-Hochberg) in `tests/unit/test_calculations.py`.
- [ ] T020 [P] [US2] Unit test for ECO code collapsing logic (mapping specific codes to families) in `tests/unit/test_parsers.py`.

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `src/models/fit.py` to prepare features: one-hot encode ECO codes and collapse them into opening families (e.g., King's Pawn, Queen's Gambit) as per FR-011. This task prepares features specifically for the Plan-authorized models (Gaussian GLM/Ridge).
- [ ] T022 [US2] Implement `src/models/fit.py` to fit Gaussian GLM (Gaussian family) and Ridge Regression. This implements the Plan.md Complexity Tracking override of Spec FR-005 (Beta Regression). The implementation uses `statsmodels` for GLM and `sklearn.linear_model.Ridge`.
- [ ] T023 [US2] Implement `src/models/fit.py` to fit Ridge Regression as a linear baseline (if not covered in T022).
- [ ] T024 [US2] Implement `src/models/metrics.py` to calculate p-values (Wald Z-tests) and F-statistics for all predictors.
- [ ] T025 [US2] Implement `src/models/metrics.py` to apply Benjamini-Hochberg FDR correction to p-values (FR-009).
- [ ] T026 [US2] Implement `src/reports/sensitivity.py` to perform threshold sweep analysis over a range of small thresholds and report Jaccard index of significant predictors (FR-010).
- [ ] T027 [US2] Save model artifacts (coefficients, p-values, R², AIC) to `data/results/model_metrics.json` and validate against `model_output.schema.yaml` (T007).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Validation and Diagnostic Reporting (Priority: P3)

**Goal**: Perform 5-fold cross-validation, generate diagnostic plots (residuals, predicted vs. actual), and produce a final validation report.

**Independent Test**: The system can be tested by executing the validation script and verifying that the output includes a report of MSE across 5 folds and saves PNG diagnostic plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Integration test for end-to-end pipeline (download -> parse -> model -> validate) on a small sample in `tests/integration/test_pipeline.py`.

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `src/models/validate.py` to perform k-fold cross-validation on both Gaussian GLM and Ridge models (FR-006).
- [ ] T030 [US3] Implement `src/models/validate.py` to calculate R² and MSE variance across folds; specifically calculate standard deviation of R². If `std_dev_r2 >= 0.05`, raise a `RuntimeError` with message "SC-003 Threshold Exceeded: Model instability detected". This enforces SC-003 as a hard pass/fail gate.
- [ ] T031 [US3] Implement `src/reports/generate_plots.py` to create residual plots and feature importance rankings.
- [ ] T032 [US3] Implement `src/reports/generate_plots.py` to create predicted vs. actual deviation scatterplots.
- [ ] T033 [US3] Save all plots to `data/results/` and generate a final `DiagnosticReport` summary in `data/results/diagnostics.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `README.md` and `quickstart.md`.
- [ ] T035 Code cleanup and refactoring.
- [ ] T036 Performance optimization (ensure RAM usage < 7GB, sample data if necessary).
- [ ] T037 [P] Additional unit tests (if requested) in `tests/unit/`.
- [ ] T038 Run quickstart.md validation.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for GameRecord schema validation in tests/contract/test_game_record.py"
Task: "Unit test for PGN parsing logic handling malformed move lists in tests/unit/test_parsers.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/parse.py to read PGN files..."
Task: "Implement src/data/process.py to calculate elo_expected_prob..."
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
- **Spec/Plan Override Note**: Where tasks deviate from Spec text (e.g., Move 5 vs 10, Gaussian vs Beta), the Plan.md Complexity Tracking section is the ratified authority for implementation.