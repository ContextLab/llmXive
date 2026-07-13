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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/` by running `mkdir -p projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/{data/raw,data/processed,data/split,artifacts/models,artifacts/reports,artifacts/figures,code,tests/unit,tests/integration}`.
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` containing: `pandas==2.0.0`, `scikit-learn==1.3.0`, `numpy==1.24.0`, `pyyaml==6.0`, `requests==2.31.0`, `pytest==7.4.0`.
- [ ] T003a [P] Create `pyproject.toml` with initial configuration for ruff and black.
- [ ] T003b [P] Configure specific ruff rules (E, W, F) and black line-length (88) in `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create directories: `data/raw`, `data/processed`, `data/split`, `artifacts/models`, `artifacts/reports`, `artifacts/figures`.
- [ ] T005 [P] Implement `code/utils.py` with constants, VIF calculation logic, and unit normalization helpers
- [ ] T006 [P] Create `code/__init__.py` and basic project scaffolding
- [ ] T007 Implement deterministic synthetic data generator in `code/generate_synthetic.py` that outputs `data/raw/synthetic_baseline.csv` with seed=42 (avoids fabricating real data, uses Avrami kinetics + noise)
- [ ] T008 Configure `pytest` framework in `tests/` with `conftest.py` for fixtures
- [ ] T009 Setup environment configuration management (`.env` handling or constants file)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Variable Validation (Priority: P1) 🎯 MVP

**Goal**: Ingest experimental data (synthetic fallback) and validate variables against physical bounds

**Independent Test**: The system can be tested by feeding a raw CSV file containing the required columns; it must output a cleaned dataset and a validation report listing any missing variables or out-of-bounds values without requiring any model training.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Write TDD unit test for physical bound validation in `tests/unit/test_validation.py` (test fails initially)
- [ ] T011 [P] [US1] Write TDD unit test for alloy series derivation logic in `tests/unit/test_alloy_derivation.py` (test fails initially)

### Implementation for User Story 1

- [ ] T012a [US1] Implement non-blocking API fetch logic in `code/ingest.py` to attempt fetch from NIST/HuggingFace with a 30s timeout; treat as best-effort/optional. If fetch fails or times out, immediately proceed to synthetic fallback.
- [ ] T012b [US1] Implement orchestration in `code/ingest.py` to load `data/raw/synthetic_baseline.csv` (from T007) as the PRIMARY source. Attempt optional fetch (T012a); if successful, merge/append data; otherwise, proceed with synthetic data only. Output `data/processed/validated.csv` and `artifacts/reports/validation_log.json`.
- [ ] T013 [US1] Implement row filtering for missing "time-to-peak softening" in `code/ingest.py`
- [ ] T014 [US1] Implement physical bound validation (0 ≤ cold work ≤ 100%, positive time) in `code/ingest.py`
- [ ] T015 [US1] Implement alloy series derivation logic in `code/ingest.py`: derive series from composition (e.g., Mg > 2.5% for 5xxx), flag ambiguous records as 'Unresolved Series' in a new column `series_status`, and EXCLUDE these rows from the final output.
- [ ] T015b [US1] (Refined from T015) Explicitly implement row filtering in `code/ingest.py` to EXCLUDE all rows where `series_status` is 'Unresolved Series' before final output generation.
- [ ] T016 [US1] Implement unit detection/heuristic (seconds vs minutes) for time-to-peak in `code/ingest.py`
- [ ] T017 [US1] Generate `data/processed/validated.csv` and `artifacts/reports/validation_log.json`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Kinetic Model Training and Feature Importance (Priority: P2)

**Goal**: Train CPU-tractable Random Forest Regressor and rank feature importances

**Independent Test**: The system can be tested by running the training script on a pre-processed dataset; it must output a trained model artifact and a JSON report of feature importances, with execution completing within 60 minutes on a 2-CPU runner.

**⚠️ DEPENDENCY**: This phase MUST wait for T017 (validated.csv) completion.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for VIF calculation in `tests/unit/test_vif.py`
- [ ] T019 [P] [US2] Unit test for model training with small subset in `tests/unit/test_train.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement collinearity diagnostic (VIF) logging in `code/train.py`
- [ ] T021 [US2] Implement Random Forest Regressor training (CPU-only). Explicit logic: If input dataset > 5,000 rows, perform random sampling to reduce to [deferred] rows. Fallback to `data/raw/synthetic_baseline.csv` (T007) if `data/processed/validated.csv` (T017) is missing. Output `artifacts/models/kinetic_model.pkl`.
- [ ] T022 [US2] Implement feature importance calculation: If feature count > 5, calculate PERMUTATION-BASED importance with 95% confidence intervals using 1000 permutations; otherwise use standard importance. Output `artifacts/reports/feature_importance.json`.
- [ ] T023 [US2] Implement fallback to Ridge Regression if RF fails due to multicollinearity in `code/train.py`
- [ ] T024 [US2] Save trained model to `artifacts/models/kinetic_model.pkl`
- [ ] T025 [US2] Generate `artifacts/reports/feature_importance.json` with ranked list and confidence intervals

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Evaluate model on held-out test set and perform sensitivity analysis on prediction confidence intervals

**Independent Test**: The system can be tested by running the validation script on a separate test set; it must output R² and MAE metrics, plus a sensitivity report showing how error rates change when the prediction confidence interval is varied.

**⚠️ DEPENDENCY**: This phase MUST wait for T024 (kinetic_model.pkl) completion.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`
- [ ] T027 [P] [US3] Integration test for full validation pipeline in `tests/integration/test_validate.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement train/test split logic (held-out set) in `code/validate.py`
- [ ] T029 [US3] Calculate R² and MAE metrics on test set in `code/validate.py`
- [ ] T029b [US3] Implement result flagging: If R² < 0.6, HALT stage execution immediately (Hard Gate per Constitution Principle VII). Do not proceed to subsequent tasks.
- [ ] T030 [US3] Implement sensitivity analysis sweeping confidence intervals using a range of plausible values.. Output `artifacts/reports/sensitivity_analysis.json` containing list of {interval, MAE, R2} pairs.
- [ ] T031 [US3] Append "associational, not causal" disclaimer to output if data source has no randomization in `code/validate.py`
- [ ] T032 [US3] Generate `artifacts/reports/validation_metrics.json` and `artifacts/reports/sensitivity_analysis.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates: Update `README.md` with installation steps and `quickstart.md` with a 5-step execution guide.
- [ ] T034a [P] Refactor `code/utils.py` for clarity and performance.
- [ ] T034b [P] Refactor `code/ingest.py` for clarity and performance.
- [ ] T035a [P] Optimize model training loop in `code/train.py` to ensure <60 min runtime.
- [ ] T035b [P] Optimize data loading in `code/ingest.py` and `code/validate.py`.
- [ ] T036a [P] Write unit tests for `code/utils.py` in `tests/unit/test_utils.py`.
- [ ] T036b [P] Write unit tests for `code/ingest.py` in `tests/unit/test_ingest.py`.
- [ ] T036c [P] Write unit tests for `code/train.py` in `tests/unit/test_train.py`.
- [ ] T037 Security hardening (input sanitization)
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end execution of the full pipeline (US1 + US2 + US3)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on validated data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained model from US2

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
Task: "Write TDD unit test for physical bound validation in tests/unit/test_validation.py"
Task: "Write TDD unit test for alloy series derivation logic in tests/unit/test_alloy_derivation.py"

# Launch all models for User Story 1 together:
Task: "Implement row filtering for missing time-to-peak in code/ingest.py"
Task: "Implement physical bound validation in code/ingest.py"
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
- **Critical Constraint**: All tasks must run on free CPU-only CI (limited cores, constrained RAM, no GPU). No 8-bit/4-bit quantization, no CUDA, no large LLMs.
- **Data Integrity**: Use `code/generate_synthetic.py` for baseline data if real data is unavailable; never fabricate real measurements.
- **Data Flow**: Ensure data ingestion (US1) completes before model training (US2), and model training completes before validation (US3).