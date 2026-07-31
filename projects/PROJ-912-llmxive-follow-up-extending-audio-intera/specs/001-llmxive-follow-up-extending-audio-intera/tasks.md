# Tasks: llmXive follow-up: extending "Audio Interaction Model"

**Input**: Design documents from `/specs/001-audio-compression-robustness/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per plan.md structure)
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `state/`)
- [ ] T002 Initialize Python 3.11 project with dependencies: `torch`, `torchaudio`, `scikit-learn`, `datasets`, `pandas`, `matplotlib`, `numpy` in `code/requirements.txt`
- [ ] T003 [P] Configure linting and formatting tools (ruff/black) in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement global configuration in `code/config.py` (seeds, paths, model aliases, resource limits)
- [ ] T005 [P] Setup error handling and logging infrastructure in `code/utils/logger.py`
- [ ] T006 [P] Implement schema validation utilities in `code/utils/validators.py` (for contracts)
- [ ] T007 Create base model wrapper class in `code/models/student.py` (empty skeleton for StudentModel entity)
- [ ] T008 Setup environment configuration management for CI runner (GitHub Actions YAML)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Train Compressed Student Models (Priority: P1) 🎯 MVP

**Goal**: Instantiate, compress, and train pre-trained Audio-Language Model into student variants with varying precision levels (FP32, INT8, INT4) using Knowledge Distillation, ensuring CPU-only execution.

**Independent Test**: Verify that distinct model checkpoints are saved with correct parameter counts, quantization types, and training loss convergence (KD loss), and that they load without CUDA errors on a 2-core CPU runner.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST (TDD). T009/T010 are written before implementation but must logically follow file creation.

- [ ] T009 [P] [US1] Unit test for quantization logic in `tests/unit/test_compression.py`
- [ ] T010 [P] [US1] Integration test for model loading in `tests/integration/test_student_load.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement teacher model loader in `code/models/teacher_loader.py` (Load `facebook/wav2vec2-base-960h` as substitute for DeSTA2.5-Audio)
- [ ] T012 [US1] Implement compression logic in `code/models/compress.py` using `torch.ao.quantization` for FP32, INT8, INT4 (Dynamic Quantization)
- [ ] T013 [US1] Implement pruning logic in `code/models/compress.py`: Create a config parser to read pruning ratios (even if default/deferred) and apply structural pruning to the model architecture. Do not use placeholders; implement the parser and application logic.
- [ ] T014 [US1] Implement Knowledge Distillation training loop in `code/models/compress.py` (CPU-only, small batch size). **MUST**: 1) Load teacher model from T011 artifact, 2) Compute KD loss as weighted sum of student logits and teacher logits (soft targets) vs ground truth, 3) Save `distillation_loss_curve.csv`. Do NOT use standard supervised loss only.
- [ ] T015 [US1] Implement checkpoint saving in `code/models/compress.py` (save to `data/processed/` with metadata: bit-width, param count)
- [ ] T016 [US1] Add validation to ensure saved models load successfully on CPU without CUDA errors in `code/models/student.py`
- [ ] T017 [US1] Add logging for compression and training metrics in `code/models/compress.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Feature Robustness on Subtle Cue Dataset (Priority: P2)

**Goal**: Run inference on a curated subset of ESC-50/AudioSet containing high-frequency transients and low-amplitude events (Subtle Cue) AND a Control Set of non-subtle classes using all student models to measure AUC.

**Independent Test**: Execute evaluation script on a small sample, confirming AUC score calculation for each model variant against ground-truth labels, with valid True Positive/False Positive discrimination.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for data filtering logic in `tests/unit/test_filter.py`
- [ ] T019 [P] [US2] Unit test for AUC calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement filtered data loader in `code/data/loader.py` using `datasets.load_dataset` with `streaming=True`. **MUST** stream only the defined "Subtle Cue" classes and "Control Set" classes to avoid OOM. Do not load full dataset.
- [ ] T021 [US2] Implement "Subtle Cue" filtering criteria in `code/data/subtle_cue_builder.py`: Define classes with freq > 8kHz OR amplitude < -40dBFS (e.g., "glass breaking," "alarm," "whisper").
- [ ] T021b [US2] Implement "Control Set" generator in `code/data/subtle_cue_builder.py`: Define and filter a set of low-frequency, high-amplitude classes (e.g., "engine hum," "wind") to ensure valid binary discrimination for AUC calculation.
- [ ] T022 [US2] Implement CPU inference runner in `code/inference/runner.py` (Batch processing to fit RAM, handle OOM gracefully)
- [ ] T023 [US2] Implement metrics calculation in `code/inference/metrics.py` (AUC, latency, peak RAM usage)
- [ ] T024 [US2] Integrate inference and metrics to generate `data/processed/robustness_metrics.csv`
- [ ] T025 [US2] Add validation to ensure metrics are independent of internal model weights: **MUST** implement unit tests asserting that no internal gradients, feature maps, or weight tensors are accessed or logged during metric calculation; rely solely on final classification logits and external labels.
- [ ] T026 [US2] Add logging for inference performance and resource usage

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Robustness Curve and Sensitivity Report (Priority: P3)

**Goal**: Perform trend analysis to map compression intensity vs. performance drop, including sensitivity analysis on decision thresholds.

**Independent Test**: Run analysis script, verifying trend plot (AUC vs. compression) and sensitivity report for threshold variations, with explicit "breaking point" value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for step-change detection in `tests/unit/test_analysis.py`
- [ ] T028 [P] [US3] Unit test for sensitivity sweep in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement robustness curve analysis in `code/analysis/robustness_curve.py` (Correlate bits/params with AUC drop)
- [ ] T030 [US3] Implement step-change detection in `code/analysis/robustness_curve.py`: Identify the specific "breaking point" (bit-width) where relative AUC drop exceeds a significant threshold compared to FP32 baseline. **MUST** output `data/processed/breaking_point.json` containing the exact bit-width, relative drop percentage, and a boolean flag `threshold_violated`.
- [ ] T031 [US3] Implement sensitivity analysis in `code/analysis/sensitivity.py` (Sweep thresholds across a range of low significance levels)
- [ ] T032 [US3] Generate plots and reports in `data/processed/` (AUC vs. Compression plot, Sensitivity table)
- [ ] T033 [US3] Add validation to ensure results are descriptive (no causal claims)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Execute Ablation Study on Architectural Components (Priority: P4)

**Goal**: Systematically vary architectural components (freezing attention, pruning FFN) while maintaining constant compression to isolate contributions.

**Independent Test**: Run ablation script, confirming distinct metrics for each configuration with no cross-contamination.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [P] [US4] Unit test for ablation config parsing in `tests/unit/test_ablation.py`
- [ ] T035 [P] [US4] Integration test for ablation execution in `tests/integration/test_ablation_run.py`

### Implementation for User Story 4

- [ ] T036 [P] [US4] Implement ablation configuration parser in `code/analysis/ablation.py` (Config for freeze attention, prune FFN)
- [ ] T037 [US4] Implement component freezing logic in `code/models/student.py`: **MUST** use `requires_grad=False` on specific early attention head parameters to freeze them for inference, ensuring the forward pass structure remains intact (no layer removal).
- [ ] T038 [US4] Implement component pruning logic in `code/models/student.py`: **MUST** use weight masking (zeroing specific FFN weights) to simulate pruning, rather than physically removing layers, to isolate the contribution without altering the model architecture.
- [ ] T039 [US4] Integrate ablation with inference runner in `code/analysis/ablation.py` (Run inference on ablated models)
- [ ] T040 [US4] Generate ablation results in `data/processed/ablation_results.csv`
- [ ] T041 [US4] Add validation to verify gradients are zeroed or weights masked as expected

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042a [P] Update `README.md` with usage examples and installation instructions
- [ ] T042b [P] Generate API documentation for `code/models/compress.py` and `code/analysis/robustness_curve.py`
- [ ] T042c [P] Update `quickstart.md` with the specific "Subtle Cue" + "Control Set" data flow
- [ ] T043a [P] Run `ruff`/`black` to format all code in `code/`
- [ ] T043b [P] Remove unused imports and dead code in `code/`
- [ ] T044a [P] Optimize data loader batch size to minimize RAM usage while maintaining throughput
- [ ] T044b [P] Verify streaming efficiency and chunking logic in `code/data/loader.py`
- [ ] T045 [P] Additional unit tests in `tests/unit/`
- [ ] T046 Run quickstart.md validation
- [ ] T047 Verify all outputs against schemas in `contracts/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 (P1) must complete before US2 (P2) can fully utilize models
  - US2 (P2) must complete before US3 (P3) can analyze metrics
  - US4 (P4) can run in parallel with US3 once models are available, but depends on US1
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for model variants
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for metrics
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US1 for model variants

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
Task: "Unit test for quantization logic in tests/unit/test_compression.py"
Task: "Integration test for model loading in tests/integration/test_student_load.py"

# Launch all models for User Story 1 together:
Task: "Implement teacher model loader in code/models/teacher_loader.py"
Task: "Implement compression logic in code/models/compress.py"
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
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
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
- **Data Hygiene**: All data loading MUST use `streaming=True` and fail loudly if real data is unavailable (no synthetic fallbacks).
- **Resource Constraints**: All inference and training MUST be optimized for a constrained multi-core CPU environment with limited memory and a fixed time budget.
- **Distillation**: T014 MUST use teacher logits for loss; standard supervised loss is insufficient.
- **Ablation**: T037/T038 MUST use freezing/masking, not layer removal, to preserve architecture.
- **Metrics**: T025 MUST ensure no internal weights are accessed during AUC calculation.