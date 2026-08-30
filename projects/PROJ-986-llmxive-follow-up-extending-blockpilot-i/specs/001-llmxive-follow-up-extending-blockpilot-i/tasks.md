# Tasks: llmXive follow-up: extending "BlockPilot: Instance-Adaptive Policy Learning for Diffusion-based Spec"

**Input**: Design documents from `/specs/001-llmxive-blockpilot-extension/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` dependencies (`transformers`, `datasets`, `scikit-learn`, `xgboost`, `torch`, `pandas`, `numpy`, `pyyaml`, `pytest`, `statsmodels`)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/data_loader.py` with streaming support for GSM8K and HumanEval using `datasets.load_dataset(..., streaming=True)`
- [ ] T005 [P] Implement `code/utils/metrics.py` for latency calculation, accuracy, and correlation coefficient functions
- [ ] T006 [P] Implement `code/utils/collinearity.py` for VIF calculation and residualization/PCA logic
- [ ] T007 Create base schemas in `contracts/` for `FeatureVector`, `GroundTruth`, `Prediction`, and `ModelArtifact`
- [ ] T008 Configure error handling and logging infrastructure in `code/main.py`
- [ ] T009 Setup environment configuration management for dataset paths and model weights

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ground Truth Generation via Exhaustive Sweep (Priority: P1) 🎯 MVP

**Goal**: Execute a complete inference sweep across block sizes $\{1, 2, 4, 8, 16, 32\}$ for every input sample to establish ground-truth optimal block size ($B^*$).

**Independent Test**: The system can be tested by running the sweep on a single sample from the GSM8K dataset and verifying that the output includes a mapped block size for every tested value and a clear winner ($B^*$).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Contract test for sweep output schema in `tests/contract/test_sweep_output.py`
- [ ] T011 [P] [US1] Integration test for sweep logic on a single GSM8K sample in `tests/integration/test_sweep_logic.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/sweep.py` to execute exhaustive block-size sweep on CPU with explicit graceful fallback and OOM handling logic for HumanEval (US-1 Acceptance Scenario 2)
- [ ] T013 [US1] Implement deterministic tie-breaking rule (select smallest block size) in `code/sweep.py`
- [ ] T014 [US1] Implement checkpoint/resume mechanism in `code/sweep.py` to handle 6-hour CI limit
- [ ] T015 [US1] Add validation to ensure sweep results are written to `data/processed/ground_truth.jsonl`
- [ ] T016 [US1] Add error handling for OOM errors on larger block sizes (e.g., 32) with graceful fallback to skip or reduce batch size
- [ ] T017 [US1] Perform feasibility mini-sweep on a small subset to validate the 6-hour CI time limit assumption before full execution

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Static Feature Extraction (Priority: P2)

**Goal**: Extract static prefilling features (prompt length, mean attention entropy, hidden state norms) from the model's initial forward pass for every sample.

**Independent Test**: The system can be tested by processing a single prompt and verifying that the output vector contains exactly three numeric values corresponding to the defined features, with no latency exceeding a minimal threshold.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for feature vector schema in `tests/contract/test_feature_vector.py`
- [ ] T019 [P] [US2] Integration test for feature extraction latency in `tests/integration/test_feature_latency.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/features.py` to extract prompt length, mean attention entropy **across all layers**, and hidden state norms
- [ ] T021 [US2] Implement NaN/Inf detection and handling in `code/features.py` (log warning, impute with median or exclude)
- [ ] T022 [US2] Implement latency measurement logic to ensure extraction ≤ 1ms per sample on 2-core CPU
- [ ] T023 [US2] Integrate feature extraction with `code/utils/data_loader.py` to process streamed data (Sequential, not [P])
- [ ] T024 [US2] Write extracted features to `data/processed/features.jsonl` linked to sample IDs

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Lightweight Policy Training and Validation (Priority: P3)

**Goal**: Train non-neural regression models (XGBoost, Random Forest, Decision Trees) on (Feature, $B^*$) pairs and evaluate alignment with ground truth across domains.

**Independent Test**: The system can be tested by training a Random Forest on an 80/20 split of the GSM8K data and evaluating on the held-out test set, reporting the prediction accuracy against the exhaustive sweep results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Contract test for model artifact schema in `tests/contract/test_model_artifact.py`
- [ ] T026 [P] [US3] Integration test for cross-domain generalization in `tests/integration/test_generalization.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/train.py` to train XGBoost, Random Forest, and Decision Tree models. **Note**: Per Spec FR-003/US-3, these must be **regression models** predicting continuous/ordinal $B^*$ using MAE/RMSE metrics, despite the Plan's classification framing. Explicitly reconcile this in code comments or amend Plan if classification is required.
- [ ] T028 [US3] Implement VIF handling in `code/train.py` to decorrelate features if VIF > 5
- [ ] T029 [US3] Implement `code/evaluate.py` to calculate regression metrics (MAE, RMSE) on held-out data
- [ ] T030 [US3] Implement cross-architecture validation in `code/evaluate.py` with **explicit bidirectional tests**: Train Qwen->Test Llama AND Train Llama->Test Qwen
- [ ] T031 [US3] Implement correlation calculation between predicted $B^*$ and **perplexity OR output entropy** (FR-006) in `code/evaluate.py`
- [ ] T032 [US3] Generate feature importance scores and correlation coefficients for reporting
- [ ] T033 [US3] Write model artifacts to `data/models/` and evaluation results to `data/processed/results.json`
- [ ] T034 [US3] **New**: Join Ground Truth (`ground_truth.jsonl`) and Features (`features.jsonl`) into a unified training dataset `data/processed/training_set.jsonl` before training
- [ ] T035 [US3] **New**: Generate feature importance ranking specifically for 'attention entropy' to satisfy SC-004, outputting to `data/processed/feature_importance.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` and `README.md`
- [ ] T037 Code cleanup and refactoring
- [ ] T038 Performance optimization across all stories (ensure CPU latency targets)
- [ ] T039 [P] Additional unit tests in `tests/unit/`
- [ ] T040 [P] Run `quickstart.md` validation and final contract checks
- [ ] T041 Verify all metrics are labeled as "preliminary" or "exploratory" in the report

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
Task: "Contract test for sweep output schema in tests/contract/test_sweep_output.py"
Task: "Integration test for sweep logic on a single GSM8K sample in tests/integration/test_sweep_logic.py"

# Launch all models for User Story 1 together:
Task: "Implement code/sweep.py to execute exhaustive block-size sweep on CPU"
Task: "Implement deterministic tie-breaking rule in code/sweep.py"
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