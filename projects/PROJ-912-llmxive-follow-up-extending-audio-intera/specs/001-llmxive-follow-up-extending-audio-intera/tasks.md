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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create `code/__init__.py`
- [X] T001b Create `data/__init__.py`
- [X] T001c Create `tests/__init__.py`
- [ ] T001d Create `state/__init__.py`
- [X] T002 Initialize Python 3.11 project with dependencies: `torch`, `torchaudio`, `scikit-learn`, `datasets`, `pandas`, `matplotlib`, `numpy` in `code/requirements.txt`
- [X] T003a Configure linting in `code/.ruff.toml`
- [X] T003b Configure formatting in `code/.black.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement global configuration in `code/config.py` (seeds, paths, model aliases, resource limits, pruning ratios schema)
- [X] T005 [P] Setup error handling and logging infrastructure in `code/utils/logger.py`
- [X] T006 [P] Implement schema validation utilities in `code/utils/validators.py` (for contracts)
- [X] T007 Create base model wrapper class in `code/models/student.py` (empty skeleton for StudentModel entity)
- [ ] T008a Setup GitHub Actions workflow file `.github/workflows/ci.yml`
- [ ] T008b Configure CI runner environment variables for resource limits

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Train Compressed Student Models (Priority: P1) 🎯 MVP

**Goal**: Instantiate, compress, and train **facebook/wav2vec2-base-960h** (verified substitute for non-existent DeSTA2.5-Audio) into student variants with varying precision levels (FP32, INT8, INT4) and structural pruning using Knowledge Distillation, ensuring CPU-only execution.

**Independent Test**: Verify that distinct model checkpoints are saved with correct parameter counts, quantization types, pruning ratios, and training loss convergence (KD loss), and that they load without CUDA errors on a 2-core CPU runner.

### Tests for User Story 1 (Post-Implementation Execution) ⚠️

> **NOTE**: These tests are written TDD-style but execute AFTER the implementation tasks (T011-T014) are complete.

- [X] T009 [US1] Unit test for quantization logic in `tests/unit/test_compression.py` (Executes after T012)
- [X] T010 [US1] Integration test for model loading in `tests/integration/test_student_load.py` (Executes after T011)

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement teacher model loader in `code/models/teacher_loader.py`. **FR-001 Override**: Load `facebook/wav2vec2-base-960h` as verified substitute for non-existent `DeSTA2.5-Audio`. Justification: Plan.md Summary.
- [X] T012 [US1] Implement compression logic in `code/models/compress.py` using `torch.ao.quantization` for FP32, INT8, INT4 (Dynamic Quantization).
- [X] T013 [US1] Implement **structural pruning logic** in `code/models/compress.py`: Read pruning ratios from `code/config.py` (schema key: `pruning_ratios`) as **deferred variables** and apply **magnitude-based pruning** to remove X% of weights. **Output**: Save `pruned_model.pt` to `data/processed/`. **Dependency**: This artifact is required input for T014b training loop.
- [X] T014a [US1] Implement Knowledge Distillation training loop for **quantized** models in `code/models/compress.py` (CPU-only, small batch size). **MUST**: 1) Load teacher model from T011 artifact, 2) Load student model (quantized from T012), 3) Compute KD loss as weighted sum of student logits and teacher logits (soft targets) vs ground truth, 4) Save `distillation_loss_curve_quant.csv`. Do NOT use standard supervised loss only.
- [X] T014b [US1] Implement Knowledge Distillation training loop for **pruned** models in `code/models/compress.py` (CPU-only, small batch size). **MUST**: 1) Load teacher model from T011 artifact, 2) Load student model (pruned from T013), 3) Compute KD loss as weighted sum of student logits and teacher logits (soft targets) vs ground truth, 4) Save `distillation_loss_curve_pruned.csv`. Do NOT use standard supervised loss only.
- [X] T015 [US1] Implement checkpoint saving in `code/models/compress.py` (save to `data/processed/` with metadata: bit-width, param count, pruning ratio). **Depends on T014a/T014b**.
- [X] T016 [US1] Add validation to ensure saved models load successfully on CPU without CUDA errors in `code/models/student.py`. **Note**: Validates base structure; ablation modifications (T037/T038) are runtime-only and do not affect this saved artifact.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Feature Robustness on Subtle Cue Dataset (Priority: P2)

**Goal**: Run inference on a curated subset of ESC-50/AudioSet containing high-frequency transients and low-amplitude events (Subtle Cue) AND a Control Set of non-subtle classes using all student models to measure AUC.

**Independent Test**: Execute evaluation script on a small sample, confirming AUC score calculation for each model variant against ground-truth labels, with valid True Positive/False Negative discrimination.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for data filtering logic in `tests/unit/test_filter.py`
- [X] T019 [P] [US2] Unit test for AUC calculation and independence in `tests/unit/test_metrics.py`. **MUST**: Assert that no internal gradients, feature maps, or weight tensors are accessed during metric calculation; rely solely on final classification logits and external labels.

### Implementation for User Story 2

- [X] T021 [US2] Implement "Subtle Cue" filtering criteria in `code/data/subtle_cue_builder.py`: Define classes with freq > 8kHz OR amplitude < -40dBFS (e.g., "glass breaking," "alarm," "whisper").
- [X] T021b [US2] [FR-002 Scope Extension] Implement "Control Set" generator in `code/data/subtle_cue_builder.py`: Use UrbanSound (Plan Complexity Tracking) to define low-frequency, high-amplitude classes (e.g., "engine hum" -> class IDs X, Y). **MUST**: 1) Explicitly reference Plan.md justification for scope extension, 2) Map class names to dataset IDs, 3) **Verify**: Record UrbanSound8K subset checksum in `state/` YAML for lineage.
- [ ] T020 [US2] Implement filtered data loader in `code/data/loader.py` using `datasets.load_dataset` with `streaming=True`. **MUST**: 1) Consume class definitions from T021/T021b artifacts to determine which classes to stream, 2) Stream only the defined "Subtle Cue" classes and "Control Set" classes to avoid OOM, 3) **Output**: Generate `data/processed/subtle_cue_subset.parquet` with checksum, 4) **Verify**: Assert file exists and checksum matches `state/` YAML. Do not load full dataset.
- [X] T022 [US2] Implement CPU inference runner in `code/inference/runner.py` (Batch processing to fit RAM, handle OOM gracefully)
- [X] T023 [US2] Implement metrics calculation in `code/inference/metrics.py` (AUC, latency, peak RAM usage). **MUST**: Calculate values and immediately compare against GitHub Actions constraints (≤6h, ≤7GB) [UNRESOLVED-CLAIM: c_8cd7219d — status=not_enough_info], logging a pass/fail status per FR-004 and SC-002.
- [X] T024 [US2] Integrate inference and metrics to generate `data/processed/robustness_metrics.csv`. **MUST**: 1) Ensure schema: `model_id`, `auc`, `latency_ms`, `ram_gb`, 2) **Verify**: Assert CSV has correct columns and row count > 0.
- [ ] T026 [US2] Add logging for inference performance and resource usage

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Robustness Curve and Sensitivity Report (Priority: P3)

**Goal**: Perform trend analysis to map compression intensity vs. performance drop, including sensitivity analysis on decision thresholds.

**Independent Test**: Run analysis script, verifying trend plot (AUC vs. compression) and sensitivity report for threshold variations, with explicit "breaking point" value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for step-change detection in `tests/unit/test_analysis.py`
- [X] T028 [P] [US3] Unit test for sensitivity sweep in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement robustness curve analysis in `code/analysis/robustness_curve.py`. **MUST**: Output raw correlation data (bits/params vs AUC) to `data/processed/correlation_data.json` for consumption by T030.
- [ ] T030 [US3] Implement step-change detection in `code/analysis/robustness_curve.py`. **MUST**: 1) Consume `correlation_data.json` from T029, 2) Identify the "breaking point" where relative AUC drop exceeds **>10%** (per FR-005), 3) **Verify**: Assert and output `threshold_violated` flag (true if drop > 10%) in `data/processed/breaking_point.json` containing bit-width, drop %, and `threshold_violated` flag.
- [X] T031 [US3] Implement sensitivity analysis in `code/analysis/sensitivity.py` (Sweep thresholds {0.01, 0.05, 0.1} and report FPR/FNR [UNRESOLVED-CLAIM: c_13aafb32 — status=not_enough_info]).
- [ ] T032 [US3] Generate plots and reports in `data/processed/` (AUC vs. Compression plot, Sensitivity table). **MUST**: Output `data/processed/robustness_curve.png` and `data/processed/sensitivity_report.csv`.
- [ ] T033 [US3] Add validation to ensure results are descriptive (no causal claims).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Execute Ablation Study on Architectural Components (Priority: P4)

**Goal**: Systematically vary architectural components (freezing attention, pruning FFN) while maintaining constant compression to isolate contributions.

**Independent Test**: Run ablation script, confirming distinct metrics for each configuration with no cross-contamination.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US4] Unit test for ablation config parsing in `tests/unit/test_ablation.py`
- [X] T035 [P] [US4] Integration test for ablation execution in `tests/integration/test_ablation_run.py`

### Implementation for User Story 4

- [X] T036 [P] [US4] Implement ablation configuration parser in `code/analysis/ablation.py` (Config for freeze attention, prune FFN).
- [X] T036b [P] [US4] Implement model cloning utility in `code/models/student.py`: Create a function `clone_model(model)` that returns a deep copy of the model weights to ensure state isolation.
- [ ] T037 [US4] Implement component freezing logic in `code/models/student.py`: **True Freezing**: **MUST** call T036b utility to instantiate a fresh model copy, then set `requires_grad=False` on specific early attention head parameters AND **remove** those parameters from the computation graph to ensure no gradients flow, isolating their contribution.
- [ ] T038 [US4] Implement component pruning logic in `code/models/student.py`: **True Pruning**: **MUST** call T036b utility to instantiate a fresh model copy, then **remove** specific late feed-forward layers from the model architecture (not just mask weights) to simulate pruning and isolate contribution.
- [ ] T039 [US4] Integrate ablation with inference runner in `code/analysis/ablation.py` (Run inference on ablated models).
- [ ] T040 [US4] Generate ablation results in `data/processed/ablation_results.csv`. **MUST**: Verify file exists and contains columns [config_id, auc, latency].
- [ ] T041 [US4] Add validation to verify gradients are zeroed or layers removed as expected.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042a1 [P] Add installation section to `README.md`
- [ ] T042a2 [P] Add usage example section to `README.md`
- [ ] T042b [P] Generate API documentation for `code/models/compress.py` and `code/analysis/robustness_curve.py`
- [ ] T042c [P] Update `quickstart.md` with the specific "Subtle Cue" + "Control Set" data flow
- [ ] T043a1 [P] Format `code/models/compress.py`
- [ ] T043a2 [P] Format `code/analysis/robustness_curve.py`
- [ ] T043a3 [P] Format `code/data/loader.py`
- [ ] T043a4 [P] Format `code/analysis/ablation.py`
- [ ] T043b [P] Remove unused imports and dead code in `code/`
- [ ] T044a [P] Optimize data loader batch size: **Metric**: Maximize throughput while keeping peak RAM < 6GB. **Method**: Binary search on batch size.
- [ ] T044b [P] Verify streaming efficiency and chunking logic in `code/data/loader.py`
- [ ] T045 [P] Additional unit tests: Add tests for `code/data/loader.py` edge cases and `code/analysis/ablation.py`.
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
# Launch all models for User Story 1 together:
Task: "Implement teacher model loader in code/models/teacher_loader.py"
Task: "Implement compression logic in code/models/compress.py"

# Launch tests AFTER implementation:
Task: "Unit test for quantization logic in tests/unit/test_compression.py"
Task: "Integration test for model loading in tests/integration/test_student_load.py"
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
- **Distillation**: T014a/T014b MUST use teacher logits for loss; standard supervised loss is insufficient.
- **Ablation**: T037/T038 MUST use true structural modifications (removal) on **fresh model copies** (via T036b) to preserve architecture and ensure state isolation.
- **Metrics**: T019 MUST ensure no internal weights are accessed during AUC calculation.
- **Overrides**: T011 (FR-001) and T021b (FR-002) explicitly acknowledge plan-driven scope extensions/substitutions.
- **Revision Concerns (Data Flow)**: T020 (Data Loader) MUST execute AFTER T021/T021b (Definitions) and BEFORE T022 (Inference Runner) and T024 (Metric Integration) to ensure data availability.
- **Revision Concerns (Ablation Isolation)**: T037 and T038 must be executed with a fresh model instance per configuration (via T036b) to prevent state leakage between "freeze" and "mask" runs.
- **Revision Concerns (Artifact Clarity)**: T020, T024, T029, T030, T032, T040 now explicitly name output artifacts and verification steps.
- **Revision Concerns (Task Granularity)**: T001, T042a, T043a split into atomic tasks for better executability.