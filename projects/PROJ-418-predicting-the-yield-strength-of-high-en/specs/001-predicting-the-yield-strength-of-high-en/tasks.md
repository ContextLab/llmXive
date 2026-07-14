# Tasks: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

**Input**: Design documents from `/specs/001-predict-hea-yield-strength/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create directory structure: `code/`, `data/raw`, `data/processed`, `output/`, `tests/`, `output/plots`
- [ ] T001b Create `__init__.py` files in all `code/` and `tests/` subdirectories
- [ ] T001c Create `requirements.txt` and `README.md` scaffolding

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup deterministic logging and random seed management in `code/utils/logging.py`
- [X] T005 [P] Create base data schemas and validation logic in `code/data/__init__.py`
- [X] T006 Implement unit normalization utility (MPa conversion) in `code/utils/unit_utils.py`
- [X] T007 Setup environment configuration management for verified dataset URLs in `code/utils/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Descriptor Engineering (Priority: P1) 🎯 MVP

**Goal**: Download HEA data from verified repositories, calculate compositional descriptors (δ, Δχ, VEC, entropy, melting var), and filter to single-phase room-temperature alloys.

**Independent Test**: Execute data pipeline; verify output CSV exists with count of single-phase HEA compositions and complete descriptor values.

### Implementation for User Story 1

- [ ] T014 [US1] Implement pipeline orchestrator in `code/data/pipeline.py` to define the sequence: download -> preprocess (filter) -> normalize -> descriptors -> filter_missing. **Depends on T005, T006, T007**.
- [ ] T008 [P] [US1] Implement data downloader in `code/data/download.py` to fetch from `research.verified_datasets['hea_compositions']` in `research.md`. If no verified URL exists, the system MUST terminate immediately with error code `DATA_SOURCE_MISSING` and log the specific missing requirement. **DO NOT** attempt fallback public search or local file loading. **Depends on T005, T007**.
- [ ] T009 [P] [US1] Implement data preprocessor in `code/data/preprocess.py` to filter single-phase, room-temp (20-25°C), and handle missing yield strength values. **Depends on T005, T008**.
- [~] T010 [US1] Implement unit normalizer in `code/data/preprocess.py` to convert all yield strength to MPa. **Depends on T009**.
- [~] T011 [P] [US1] Implement elemental property loader in `code/data/descriptors.py` (atomic radii, electronegativity, valence counts) with fallback to standard databases. **Depends on T005**.
- [~] T012 [US1] Implement descriptor calculator in `code/data/descriptors.py` for δ, Δχ, VEC, mixing entropy, and melting temperature variance. **Depends on T010, T011**.
- [~] T013 [US1] Implement composition filter in `code/data/descriptors.py` to exclude entries with missing elemental properties. **Depends on T012**.
- [~] T015 [US1] Generate `data/processed/hea_descriptors.csv` and write `output/data_status.json` with `count_warning` if N < 500 (data limitation) AND `power_status` flag if N < 50 (insufficient power). **Depends on T014**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Predictive Performance Evaluation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models (5-fold CV, hyperparameter tuning ≤50 trees, depth ≤10), evaluate on hold-out test set, and compare against Linear Regression baseline.

**Independent Test**: Execute training script; verify `output/metrics.json` contains R², MAE, RMSE for all models; confirm runtime ≤ 3 hours on CPU.

### Implementation for User Story 2

- [~] T016 [P] [US2] Implement data splitter in `code/models/train.py` to create stratified train/test splits with fixed seed. **Depends on T015**.
- [~] T017 [P] [US2] Implement Linear Regression baseline trainer in `code/models/train.py`. **Depends on T016**.
- [~] T018 [P] [US2] Implement Random Forest trainer with 5-fold CV and grid search (trees ≤ 50, depth ≤ 10) in `code/models/train.py`. **Depends on T016**.
- [~] T019 [P] [US2] Implement Gradient Boosting trainer with 5-fold CV and grid search (trees ≤ 50, depth ≤ 10) in `code/models/train.py`. **Depends on T016**.
- [~] T020 [US2] Implement evaluation runner in `code/models/evaluate.py` to compute R², MAE, RMSE on held-out test set. **Depends on T017, T018, T019**.
- [~] T021 [US2] Create `output/metrics.json` writer to record metrics for all models (RF, GB, Linear). **Depends on T020**.
- [~] T022 [US2] Add runtime tracker in `code/models/train.py` to enforce ≤ 3 hour limit and log warnings if exceeded. **Depends on T018, T019**.
- [~] T029a [P] [US2] Implement plot disclaimer injector in `code/utils/plot_utils.py` to append "Associational analysis only; no causal inference" to all generated matplotlib/seaborn figures. **Depends on T004**.
- [~] T029b [P] [US2] Implement report disclaimer injector in `code/utils/report_utils.py` to append the mandatory disclaimer to report markdown text. **Depends on T004**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Significance Reporting (Priority: P3)

**Goal**: Perform permutation testing (1000 perms), bootstrap resampling (1000 resamples), multiple-comparison correction, sensitivity analysis on α, and VIF diagnostics.

**Independent Test**: Execute validation script; verify report contains p-values, confidence intervals, corrected significance levels, and VIF flags.

### Implementation for User Story 3

- [~] T023 [US3] Implement VIF calculator in `code/models/evaluate.py` for the **Linear Regression baseline ONLY**. Calculate VIF for all descriptors in the linear model and flag any VIF > 10. **DO NOT** calculate VIF for RF or GB models. **Depends on T017**.
- [~] T024 [US3] Implement permutation importance tester in `code/models/evaluate.py` (1000 permutations) to calculate p-values for all descriptors. **If N < 50, SKIP this test entirely** and write `output/power_analysis.json` with `status: 'insufficient_power'`. **Depends on T018, T019**.
- [~] T025 [US3] Implement multiple-comparison correction (Bonferroni/Benjamini-Hochberg) in `code/models/evaluate.py`. **Depends on T024**.
- [~] T026 [US3] Implement bootstrap resampling in `code/models/evaluate.py` (1000 resamples) for the full model (RF/GB) to calculate 95% CI for R². **If N < 50, SKIP this test entirely** and ensure `output/power_analysis.json` reflects `status: 'insufficient_power'`. **Depends on T018, T019**.
- [~] T027 [US3] Implement sensitivity analysis runner in `code/models/evaluate.py` to sweep α over the discrete set **{0.01, 0.05, 0.1}** and report how the count of significant descriptors and R² values vary. **Depends on T024, T025**.
- [~] T030 [US3] Handle edge case: if N < 50, ensure `output/power_analysis.json` is written with `status: 'insufficient_power'` and log message `'INSUFFICIENT_POWER: N={n} < 50'` at WARNING level. **Depends on T024, T026**.
- [~] T028 [US3] Create statistical report generator in `output/report.md` including all p-values, CIs, VIF flags, and integrating disclaimers from T029a/T029b. **Depends on T023, T024, T025, T026, T027, T029a, T029b**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T031 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T032a Run `ruff check` and fix all linting errors in `code/`
- [ ] T032b Run `black` and format all Python files in `code/`
- [ ] T033a Profile execution with `cProfile`, generate `output/profile.log` identifying top 3 bottlenecks
- [ ] T033b Refactor code based on `output/profile.log` to reduce runtime by at least 10%
- [ ] T034 [P] Unit tests for descriptor math in `tests/unit/test_descriptors.py`
- [ ] T035 [P] Integration tests for full pipeline in `tests/integration/test_pipeline.py`
- [ ] T036 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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