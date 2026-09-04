# Tasks: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

**Input**: Design documents from `/specs/001-cold-work-recrystallization/`
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

## Phase 1: Setup & Foundational

**Purpose**: Project initialization, basic structure, and core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T001 Create project root directories: `code`, `tests`, `data`, `artifacts` in `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/`. <!-- FAILED: unspecified -->
- [ ] T002 Create data subdirectories: `data/raw`, `data/processed`, `data/split`.
- [ ] T003 Create artifacts subdirectories: `artifacts/models`, `artifacts/reports`, `artifacts/figures`.
- [X] T004 Configure `pyproject.toml` with initial configuration for ruff and black (line-length 88, rules E, W, F).
- [X] T005 [P] Create `code/__init__.py` and basic project scaffolding.
- [X] T006 [P] Implement `code/utils.py` with constants, VIF calculation logic, and unit normalization helpers.
- [ ] T007 Implement deterministic synthetic data generator in `code/generate_synthetic.py` that outputs `data/raw/synthetic_baseline.csv` with seed=42 (uses a deterministic physical kinetics model + noise).
- [ ] T008 Configure `pytest` framework in `tests/` with `conftest.py` for fixtures.
- [ ] T009 Setup environment configuration management (`.env` handling or constants file) including `N_PERMUTATIONS=1000` for statistical tests.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Feature Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest raw experimental data (synthetic primary) and transform into a structured dataset with engineered interaction features.

**Independent Test**: The system can be tested by running the data pipeline on the synthetic generator (seed=42) and verifying the output DataFrame contains the required columns, calculated interaction features (`cold_work * Mn_content`, etc.), and no null values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Write TDD unit test for physical bound validation in `tests/unit/test_validation.py` (test fails initially).
- [X] T011 [P] [US1] Write TDD unit test for interaction feature engineering in `tests/unit/test_engineering.py` (test fails initially).

### Implementation for User Story 1

- [ ] T012 [US1] Implement orchestration in `code/ingest.py`: Load `data/raw/synthetic_baseline.csv` (from T007) as the PRIMARY and mandatory source. Do NOT attempt to fetch external data in this step. Output `data/processed/validated.csv` and `artifacts/reports/validation_log.json`. <!-- FAILED: unspecified -->
- [X] T013 [US1] Implement row filtering for missing "time-to-peak softening" in `code/ingest.py` (exclude rows, do not impute target).
- [X] T014 [US1] Implement physical bound validation (0 ≤ cold work ≤ 100%, positive time) in `code/ingest.py`.
- [X] T015 [US1] Implement missing composition value handling in `code/ingest.py`: Impute using the mean of the specific alloy series (group by alloy type or concentration range) or flag for exclusion as per spec Edge Cases. Do NOT use a global mean for all rows.
- [X] T016 [US1] Implement unit normalization for time-to-peak (minutes) in `code/ingest.py`.
- [X] T017 [US1] Implement outlier clipping on target variable at 99th percentile in `code/ingest.py` (FR-007) before any statistical analysis. Log clipped values.
- [ ] T018 [US1] Implement interaction feature engineering in `code/engineer.py`: Calculate `cold_work * Mn_content`, `cold_work * Mg_content`, `cold_work * Si_content`, and `cold_work * Cu_content`. Include annealing temperature as a direct feature. Output `data/processed/engineered_features.csv`. <!-- FAILED: unspecified -->
- [X] T019 [US1] Implement dataset size validation in `code/engineer.py`: Raise `ValueError` if rows < 50 (FR-008).
- [X] T020 [US1] Generate final dataset artifact `data/processed/final_dataset.csv` ready for modeling. Enforce a hard cap on the number of rows here if the generator produced more, ensuring the training set does not exceed the limit.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train a Random Forest Regressor using CPU-only execution, validate with 5-fold CV, and evaluate on a held-out test set.

**Independent Test**: The system can be tested by running the training script on `data/processed/final_dataset.csv`; it must output a trained model artifact and report mean CV R² score and held-out MAE, completing within 6 hours on 4GB RAM.

**⚠️ DEPENDENCY**: This phase MUST wait for T020 (final_dataset.csv) completion.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for VIF calculation in `tests/unit/test_vif.py`.
- [X] T022 [P] [US2] Unit test for model training with small subset in `tests/unit/test_train.py`.

### Implementation for User Story 2

- [X] T023 [US2] Implement data splitting logic in `code/train.py`: /20 stratified split, random seed=42.
- [X] T024 [US2] Implement Random Forest Regressor training (CPU-only) in `code/train.py`. Ensure dataset size ≤ 10,000 rows (FR-003). If larger, use synthetic generator to create a valid subset (do not truncate real data arbitrarily).
- [X] T025 [US2] Implement k-fold cross-validation in `code/train.py` and calculate mean R² and std dev.
- [X] T026 [US2] Implement held-out test set evaluation in `code/train.py`: Calculate MAE and R² on the test set.
- [ ] T027 [US2] Save trained model to `artifacts/models/kinetic_model.pkl`.
- [ ] T028 [US2] Generate `artifacts/reports/training_metrics.json` containing CV scores and test set MAE/R².
- [ ] T029 [US2] Implement fallback logic: If dataset is pure aluminum (zero variance in composition), log warning and skip interaction feature importance (handle gracefully).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Statistical Significance and Interaction Analysis (Priority: P3)

**Goal**: Statistically verify that interaction terms improve prediction accuracy and identify key drivers via SHAP.

**Independent Test**: The system can be tested by running the analysis script; it must output a p-value from a Permutation Test (p < 0.05) and a SHAP interaction value report.

**⚠️ DEPENDENCY**: This phase MUST wait for T027 (kinetic_model.pkl) completion.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for Permutation Test logic in `tests/unit/test_permutation.py`.
- [ ] T031 [P] [US3] Unit test for SHAP interaction calculation in `tests/unit/test_shap.py`.

### Implementation for User Story 3

- [ ] T032 [US3] Implement Baseline Model (Additive: cold work + composition) training in `code/evaluate.py` for comparison.
- [ ] T033 [US3] Implement Interaction Model (cold work + composition + interactions) training in `code/evaluate.py` (re-use logic from T024 but with full feature set).
- [ ] T034 [US3] Implement Permutation Test in `code/evaluate.py`:
 1. Train Additive Model (T032) and Interaction Model (T033).
 2. Shuffle interaction terms `N_PERMUTATIONS` times in the Interaction Model while holding main effects constant.
 3. Compare error distributions of the Additive Model and the shuffled Interaction Model.
 4. Calculate p-value (FR-005). Output to `artifacts/reports/statistical_significance.json`.
- [ ] T035 [US3] Implement Permutation Importance calculation in `code/evaluate.py`: Calculate permutation importance (drop in R² score) for interaction terms and verify > 0.01 threshold (SC-003). Update `artifacts/reports/statistical_significance.json` with key `permutation_importance`.
- [ ] T036 [US3] Implement SHAP Interaction Value analysis in `code/evaluate.py` to rank features by unique contribution (FR-006). **Prerequisites: T018, T027**.
- [ ] T037 [US3] Generate `artifacts/reports/statistical_significance.json` containing p-value, test statistic, and conclusion.
- [ ] T038 [US3] Generate `artifacts/reports/shap_interaction_report.json` with top features and interaction terms.
- [ ] T039 [US3] Verify Success Criteria:
 1. Check p-value < 0.05 (from T034/T037).
 2. Check Permutation Importance > 0.01 (from T035).
 3. Check R² < 0.6 (SC-001).
 Flag in report if any criteria fail (do not crash, but document failure).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates: Update `README.md` installation steps and `quickstart.md` with a 5-step execution guide.
- [ ] T041a [P] Refactor `code/utils.py` for clarity and performance.
- [ ] T041b [P] Refactor `code/ingest.py` to ensure strict error handling on data fetch (no silent synthetic fallback for real data, but synthetic is primary).
- [ ] T042a [P] Optimize model training loop in `code/train.py` to ensure <60 min runtime.
- [ ] T042b [P] Optimize data loading in `code/engineer.py` and `code/evaluate.py`.
- [ ] T043a [P] Write unit tests for `code/utils.py` in `tests/unit/test_utils.py`.
- [ ] T043b [P] Write unit tests for `code/engineer.py` in `tests/unit/test_engineer.py`.
- [ ] T043c [P] Write unit tests for `code/evaluate.py` in `tests/unit/test_evaluate.py`.
- [ ] T044 Security hardening (input sanitization).
- [ ] T045 [P] [Optional] Implement external data fetching logic in `code/ingest_external.py` to attempt fetching from NIST/HuggingFace. If fetch fails, log a warning and do NOT fall back to synthetic; synthetic is already the primary source. Merge external data only if explicitly configured and validated. This task is non-blocking and separate from the primary ingestion flow.
- [ ] T046 Run `quickstart.md` validation to ensure end-to-end execution of the full pipeline (US1 + US2 + US3).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup & Foundational (Phase 1)**: No dependencies - can start immediately
- **User Stories (Phase 2+)**: All depend on Phase 1 completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 1 - Depends on final_dataset.csv from US1
- **User Story 3 (P3)**: Can start after Phase 1 - Depends on trained model from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Once Phase 1 completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Write TDD unit test for physical bound validation in tests/unit/test_validation.py"
Task: "Write TDD unit test for interaction feature engineering in tests/unit/test_engineering.py"

# Launch all models for User Story 1 together:
Task: "Implement orchestration in code/ingest.py to load synthetic data"
Task: "Implement interaction feature engineering in code/engineer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup & Foundational
2. Complete Phase 2: User Story 1
3. **STOP and VALIDATE**: Test User Story 1 independently
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 1 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 together
2. Once Phase 1 is done:
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
- **Critical Constraint**: All tasks must run on free CPU-only CI (limited cores, constrained RAM, no GPU). No 8-bit/4-bit quantization, no CUDA, no large LLMs.
- **Data Integrity**: Use `code/generate_synthetic.py` for baseline data if real data is unavailable; **NEVER** implement a silent fallback to synthetic data if a real fetch fails (must raise error). *Correction*: Per spec FR-001, synthetic is PRIMARY; external is optional. If external fails, proceed with synthetic only.
- **Data Flow**: Ensure data ingestion (US1) completes before model training (US2), and model training completes before validation (US3).
- **Statistical Rigor**: Permutation Test (shuffling interaction terms) and SHAP Interaction Values are mandatory for US3 to validate the "pinning effect" hypothesis.
- **Imputation Logic**: Missing composition values must be imputed using the mean of the specific alloy series, not a global mean.
- **Interaction Terms**: Explicitly calculate `cold_work * Mn_content`, `cold_work * Mg_content`, `cold_work * Si_content`, and `cold_work * Cu_content`.