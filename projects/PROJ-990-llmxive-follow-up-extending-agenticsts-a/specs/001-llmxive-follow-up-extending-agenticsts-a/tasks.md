# Tasks: llmXive follow-up: extending "AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents"

**Input**: Design documents from `/specs/001-llmxive-agenticsts-followup/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-990-llmxive-follow-up-extending-agenticsts-a/`)
- [X] T002 Initialize Python 3.11 project with dependencies (`requirements.txt`: pandas, numpy, scikit-learn, pytest, pyyaml)
- [X] T003 [P] Configure linting and formatting tools (ruff/black) in `code/` and `tests/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data processing, model training, and validation gates.
**⚠️ CRITICAL**: No user story work (Phase 3+) can begin until this phase is complete.

**Data Flow**: T005/T006 (Parse) -> T008 (Ablation) -> T008b (Extract) -> T008c (Check) -> T014a (Split) -> T014 (Validate) -> T009 (Train)

- [X] T004 Implement `code/config.py` for paths, seeds, and hyperparameters. Define `TOKEN_BUDGET=4096`, `MIN_CONTEXT=256` as explicit constants loaded from config or env vars.
- [X] T005 [P] Implement `code/entropy.py` to calculate Shannon entropy of legal move distributions. **Edge Case Handling**: If calculation returns NaN or Inf, the function MUST default to returning a sentinel value that triggers retrieval of the **full "all-layers" set** for that turn and MUST log a warning event with the specific error details. **Input**: `data/raw/trajectories.csv`. **Depends on**: T006. <!-- FAILED: unspecified -->
- [X] T006 [P] Implement `code/parser.py` to extract per-turn metrics (health, threat, deck size) from raw trajectory logs in `data/raw/`.
- [ ] T007 Create `data/processed/` directory structure and schema validation for derived metrics.
- [~] T008 Implement `code/ablation.py` to perform a **full ablation study on the training set** (re-run engine with layers removed) to generate ground-truth utility labels. **Input**: `data/raw/trajectories.csv`. **Output**: `data/processed/ablation_labels_full.json` (schema: `{layer_id, utility_score}`). **Depends on**: T006 (Parser) and T005 (Entropy).
- [~] T008b Implement `code/extractor.py` to convert ablation results into structured training labels. **Input**: `data/processed/ablation_labels_full.json`. **Output**: `data/processed/utility_labels.csv`. **Depends on**: T008.
- [~] T008c Implement `code/validator.py` to check sample count (n < 300). If n < 300, log warning and trigger fallback to heuristic (fixed k=2). **Depends on**: T008b.
- [~] T014a [P] Implement `code/splitter.py` to perform stratified data split of the trajectories into training set and hold-out set (specifically a subset for hold-out). **Output**: `data/processed/train_set.csv`, `data/processed/holdout_set.csv`.
- [~] T014 [US1] Implement proxy validation logic in `code/classifier.py`. **Logic**: Check Pearson correlation (≥ 0.7) between static logs (proxy) and ablation utility (ground truth) on the hold-out set (from T014a). **Output**: `data/processed/proxy_validation_report.json`. **Action**: Raise exception if r < 0.7. **Depends on**: T008b, T014a.
- [~] T009 [US1] Implement `code/classifier.py` to train lightweight CPU-tractable models (Decision Tree/Logistic Regression). **Input**: `data/processed/utility_labels.csv` (ablation-derived ground-truth utility from T008b). **Target**: `utility_score`. **Split**: 80/20. **Output**: `models/layer_utility_classifier.pkl`. **Note**: Trains exclusively on ablation-derived ground truth. **Depends on**: T008b, T008c, T014 (must pass).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 & 2 - Dynamic Policy & Baselines (Priority: P1, P2) 🎯 MVP

**Goal**: Implement dynamic retrieval agent and baseline simulations.

**Independent Test**: Run held-out trajectories through Dynamic, Static, and Random agents; verify variable layer selection, token budget compliance, and outcome logging.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T012 [P] [US1] Unit test for entropy calculation edge cases (NaN, Inf, zero moves) in `tests/unit/test_entropy.py`.
- [~] T013 [P] [US1] Unit test for token budget enforcement and minimum context floor in `tests/unit/test_simulator.py`.

### Implementation for User Story 1 (Dynamic Policy)

- [~] T015 [US1] Implement dynamic layer selection logic in `code/simulator.py`. **Logic**: Use trained model (T009) to predict top-k layers based on current turn entropy, **integrating** this prediction with the token budget constraint logic (4096 tokens). **Depends on**: T009.
- [~] T016 [US1] Add logic to enforce a hard token budget and a minimum context floor in `code/simulator.py`. **Error Condition**: If predicted token count > 4096, the system MUST **truncate or prune the least useful layers** until the prompt size is ≤ 4096. It MUST NOT fallback to full layers if that exceeds the budget. **Depends on**: T015.
- [~] T017 [US1] Add logging for layer selection decisions and entropy values in `code/simulator.py`.

### Implementation for User Story 2 (Baselines & Aggregation)

**Note**: Baselines (T019, T020) are moved here to ensure they run after Dynamic Policy (T015) logic is established, enabling T021 aggregation.

- [~] T019 [US2] Implement "Static All-Layers" baseline execution in `code/simulator.py`. **Depends on**: T015 (for shared engine logic).
- [~] T020 [US2] Implement "No-Store Random" baseline execution in `code/simulator.py`. **Depends on**: T015 (for shared engine logic).
- [~] T021 [US2] Create aggregation script `code/stats.py` to compute average win rate and token usage per condition. **Input**: Outputs from T015, T019, T020.
- [~] T022 [US2] Generate summary CSV output in `data/processed/baseline_comparison.csv`. **Schema**: `condition, win_rate, avg_tokens`. **Aggregation Logic**: Mean of win_rate and token columns grouped by condition.
- [~] T022a [US2] Implement verification logic to calculate percentage reduction in token usage. **Output**: Generate `data/processed/token_reduction_verification.json` containing a boolean field `passed` (true if reduction ≥ 30%). **Build Logic**: The build pipeline MUST fail if `passed` is false. **Input**: `data/processed/baseline_comparison.csv`. **Output**: `data/processed/token_reduction_verification.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Statistical Significance Reporting (Priority: P3)

**Goal**: Perform paired statistical tests to validate the dynamic policy's efficacy.

**Independent Test**: Run analysis on a dataset with known outcomes and verify correct selection of McNemar's test and Bonferroni correction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T023 [P] [US3] Unit test for McNemar's test selection logic (binary data) in `tests/unit/test_stats.py`.
- [~] T024 [P] [US3] Unit test for Bonferroni correction application in `tests/unit/test_stats.py`.

### Implementation for User Story 3

- [~] T024a [US3] Implement trajectory divergence detection in `code/stats.py`. **Logic**: Analyze paired trajectories from Dynamic vs Static runs to detect non-deterministic divergence (e.g., different final states from same start). **Output**: `data/processed/divergence_report.json` (boolean `is_divergent`). **Depends on**: T021.
- [~] T025 [US3] Implement statistical testing logic in `code/stats.py`. **Logic**:
 1. Read `divergence_report.json` (T024a).
 2. If `is_divergent` is true, execute **Permutation Test** (or Z-test) for win/loss outcomes.
 3. If `is_divergent` is false (paired/deterministic), execute **McNemar's test**.
 4. Execute paired t-test for token usage (if normality holds).
 5. Apply **Bonferroni correction** to all p-values.
 **Output**: `data/processed/statistical_results.json`. **Depends on**: T024a, T021.
- [ ] T026 [US3] (Removed: Logic merged into T025)
- [ ] T027 [US3] (Removed: Logic merged into T025)
- [ ] T028 [US3] Generate final statistical report in `data/processed/statistical_results.json`. **Schema**: `{p_value, effect_size, test_type, bonferroni_adjusted, divergence_status}`. **Includes**: SC-001/SC-003 metrics. **Depends on**: T025.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `README.md` and `quickstart.md`.
- [ ] T030 Code cleanup and refactoring.
- [ ] T031 Performance optimization to ensure completion within 6 hours on CPU-only runner.
- [ ] T032 [P] Additional unit tests for edge cases (n < 300 warning logic) in `tests/unit/`.
- [ ] T033 Run `quickstart.md` validation to ensure reproducibility.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup. **Blocks all user stories**.
 - **Critical Flow**: T005/T006 -> T008 -> T008b -> T008c -> T014a -> T014 -> T009.
 - T009 (Training) MUST wait for T014 (Validation) to pass.
- **User Stories (Phase 3)**: Depends on Foundational (Phase 2).
 - T015 (Dynamic) depends on T009 (Model).
 - T019/T020 (Baselines) depend on T015 (Shared logic).
 - T021 (Aggregation) depends on T015, T019, T020.
- **Statistical (Phase 4)**: Depends on Phase 3 (Aggregation results).
 - T024a (Divergence) depends on T021.
 - T025 (Testing) depends on T024a.
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models/Utilities (Entropy, Parser) before services (Simulator, Classifier).
- Services before analysis scripts.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- T005, T006, T014a can run in parallel in Phase 2.
- T019, T020 can run in parallel in Phase 3 (after T015).
- All tests for a user story marked [P] can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - Ensure T014 (Validation) passes before T009 (Training).
3. Complete Phase 3: User Story 1 (Dynamic Policy)
4. **STOP and VALIDATE**: Test Dynamic Policy against Static Baseline on a small subset.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!).
3. Add User Story 2 (Baselines) → Test independently → Deploy/Demo.
4. Add User Story 3 (Statistical) → Test independently → Deploy/Demo.
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Dynamic Policy).
 - Developer B: User Story 2 (Baselines - T019, T020).
 - Developer C: User Story 3 (Statistical Analysis).
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story for traceability.
- Each user story should be independently completable and testable.
- Verify tests fail before implementing.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
- **Critical Constraint**: All tasks must run on CPU-only CI with limited cores and memory. No GPU models or 8-bit quantization.
- **Data Integrity**: All analysis tasks must use real trajectory data from `data/raw/` or `data/processed/`. No synthetic data generation for results.
- **Methodology**: Ablation study (T008) is performed on the **full training set** to generate ground truth. The final classifier (T009) trains exclusively on this ablation-derived ground truth.