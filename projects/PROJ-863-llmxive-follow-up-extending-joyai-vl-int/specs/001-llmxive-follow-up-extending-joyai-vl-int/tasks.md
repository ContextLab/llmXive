# Tasks: llmXive Follow-up: Extending "JoyAI-VL-Interaction"

**Input**: Design documents from `/specs/001-llmxive-vl-intuition/`
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

- [ ] T001 Create project structure per implementation plan (`src/data_synthesis`, `src/feature_extraction`, `src/baseline`, `src/scheduler`, `tests/`)
- [ ] T002 Initialize Python project with `requirements.txt` (CPU-only `torch`, `transformers`, `scikit-learn`, `opencv-python`, `datasets`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Setup `pytest` configuration with CPU resource limit markers

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement `src/utils/logging.py` for execution logging (FR-001.1)
- [ ] T006 Implement `src/utils/validation.py` for schema validation (FR-002, Edge Cases)
- [X] T007 [P] Create base data models: `SyntheticVideoFrame`, `InternalStateVector`, `SchedulerDecision` in `src/data_synthesis/models.py` (aligned with plan.md structure)
- [X] T008 Setup streaming/batching utilities in `src/feature_extraction/streaming.py` to enforce <6GB RAM limit
- [~] T009 Configure environment variables for `JOYAI_VL_MODEL_PATH` and `DATA_SEED`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Data Generation and Ground-Truth Labeling (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of video streams with ground-truth labels derived strictly from visual content (e.g., falls) independent of any model output.

**Independent Test**: The data pipeline can be executed in isolation to produce a JSONL file containing video frames and labels. The test verifies that the labeling logic relies solely on the video content and that an execution log confirms zero VLM API calls.

### Tests for User Story 1 (Mandatory per Spec) ⚠️

> **NOTE**: Write these tests FIRST (TDD). These tasks are to WRITE the test code. The tests will FAIL until implementation (T013-T017) is complete.
> **[P] Clarification**: T010-T012 are "Test Code Writing" tasks. They can be written in parallel with T013-T017 "Implementation" tasks because they depend on the interface definition, not the implementation completion.

- [X] T010 [P] [US1] Write contract test code: Verify labeling logic uses only visual events in `tests/unit/test_visual_labeler.py`
- [ ] T011 [P] [US1] Write integration test code: Verify execution log contains zero VLM calls in `tests/integration/test_data_pipeline.py`
- [X] T012 [P] [US1] Write test code: Verify deterministic rule application for ambiguous events (sitting vs. falling) in `tests/unit/test_visual_labeler.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `src/data_synthesis/generator.py` to produce video content. **CI Mode**: Generate a subset (e.g., hours) to fit 6h runtime. **Non-CI Mode**: Generate full hours. Use chunked streaming to write directly to disk (FR-001). <!-- FAILED: unspecified -->
- [ ] T013a [US1] **NEW**: Implement verification logic in `src/data_synthesis/verify_volume.py` to confirm `manifest.jsonl` reports >= 180,000 seconds (50 hours) of video for Non-CI runs, or the defined subset for CI runs.
- [ ] T013b [US1] **NEW**: Implement "Streaming Handoff" logic in `src/data_synthesis/handoff.py` to allow US2/US3 to begin processing chunks as T013 writes them, avoiding false serialization.
- [ ] T014 [US1] Implement `src/data_synthesis/visual_labeler.py` using object detection (e.g., YOLO/COCO classes) to label "critical" vs "silence"
- [ ] T015 [US1] Implement logic to handle ambiguous events with deterministic rules (velocity thresholds) as per Edge Cases
- [ ] T016 [US1] Integrate `src/utils/logging.py` to record data sources and verify zero VLM API calls during labeling
- [ ] T017 [US1] Implement data export to `data/raw/` and `data/manifest.jsonl`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Extraction from Internal States (Priority: P2)

**Goal**: Extract feature vectors from the internal hidden states and attention maps of the JoyAI-VL-Interaction model for every time step, ensuring final token logits are excluded.

**Independent Test**: The extraction module can be run on a subset of the dataset. The test verifies that the output feature matrix dimensions match the internal state dimensions and that the feature set contains no data from the final output layer.

### Tests for User Story 2 (Mandatory per Spec) ⚠️

- [ ] T018 [P] [US2] Write contract test: Verify feature keys exclude final token logits in `tests/unit/test_feature_extractor.py`
- [ ] T019 [P] [US2] Write integration test: Verify 1:1 temporal alignment between input frames and output features in `tests/integration/test_feature_pipeline.py`
- [ ] T020 [P] [US2] Write test code: Verify graceful failure on dimension mismatch (Edge Case) in `tests/unit/test_feature_extractor.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `src/feature_extraction/extractor.py` to load JoyAI-VL-Interaction (CPU mode) and extract hidden states/attention maps
- [ ] T022 [US2] Integrate `src/feature_extraction/streaming.py` (from T008) to process video in fixed-size chunks (e.g., a predefined number of frames) ensuring RAM < 6GB
- [ ] T023 [US2] Implement dimension validation against a hardcoded schema; **must raise a `ValueError` with a clear, formatted message containing "Expected: X, Actual: Y" if a mismatch occurs** (Edge Case)
- [ ] T024 [US2] Implement logic to explicitly exclude final token logits and generated text from output vectors
- [ ] T025 [US2] Export extracted features to `data/features/*.jsonl` with temporal alignment metadata

**Checkpoint**: Feature extraction ready for training phase

---

## Phase 5: Visual Baseline Implementation (Priority: P2 - Prerequisite for US3)

**Goal**: Implement the Noisy Rule-Based Visual Detector required for baseline comparison and Nested Model Comparison (SC-005, FR-005).

**Independent Test**: The baseline detector can be run on the synthetic dataset to generate predictions for comparison.

### Implementation for User Story 3 (Baseline Component)

- [ ] T026a [US3] **NEW**: Implement `src/baseline/deterministic_detector.py` (Deterministic Rule-Based Visual Detector) for SC-005 compliance. **Rules**: Apply strict visual thresholds without noise. Output `data/baseline/deterministic_predictions.jsonl`.
- [ ] T026b [US3] Implement `src/baseline/visual_detector.py` (Noisy Rule-Based Visual Detector) for memorization prevention. **Parameters**: Apply a moderate level of label flip noise and temporal jitter. Output `data/baseline/noisy_predictions.jsonl`.
- [ ] T027 [US3] Run deterministic detector on `data/raw/` to generate `data/baseline/deterministic_predictions.jsonl`
- [ ] T028 [US3] Calculate baseline F1, AUC, and Interruption Reduction metrics for both detectors; save to `data/baseline/metrics.json`
- [ ] T029 [US3] Run noisy detector on `data/raw/` to generate `data/baseline/noisy_predictions.jsonl` (if not covered by T027)

**Checkpoint**: Baseline detectors ready for comparison in Phase 6

---

## Phase 6: User Story 3 - CPU-Optimized Scheduler Training and Evaluation (Priority: P3)

**Goal**: Train a Transformer classifier on the extracted features to predict intervention labels and evaluate its ability to reduce interruptions while maintaining safety recall.

**Independent Test**: The training and evaluation script can be run end-to-end on a hardware profile equivalent to an AWS c6i.large instance with enforced resource limits.

### Tests for User Story 3 (Mandatory per Spec) ⚠️

- [ ] T030 [P] [US3] Integration test: Verify training completes within 6h, <7GB RAM, **and measures/records inference latency** in `tests/integration/test_training_pipeline.py`
- [ ] T031 [P] [US3] Contract test: Verify "Interruption Reduction Rate" and "Safety Recall" are calculated separately in `tests/unit/test_eval_metrics.py`
- [ ] T032 [P] [US3] Test Mutual Information calculation and partial correlation analysis in `tests/unit/test_statistical_analysis.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `src/scheduler/model.py` with a Transformer architecture optimized for CPU
- [ ] T034 [US3] Implement `src/scheduler/train.py` with CPU-optimized training loop (no CUDA/GPU ops, no bitsandbytes)
- [ ] T035 [US3] Implement `src/scheduler/eval.py` to calculate AUC-ROC, Cohen's Kappa, Interruption Reduction Rate, Safety Recall, **and inference latency**. **Input**: Must read `data/baseline/predictions.jsonl` (from T027/T029) and `data/features/*.jsonl`.
- [ ] T036 [US3] Implement Nested Model Comparison (Likelihood Ratio Test) between visual-only (T026a) and visual+internal states models. **Implement Mutual Information and partial correlation analysis** between internal state features and **final output logits**, conditioned on ground truth, to verify unique predictive signal distinct from the visual proxy. **Output**: `data/evaluation/mi_matrix.json`. **Verify**: MI > 0.05.
- [ ] T037 [US3] **NEW**: Implement Spearman rank correlation (p < 0.05) between **scheduler predictions** and **video-derived ground truth** against a random baseline (Generate a set of random baselines.). **Output**: `data/evaluation/spearman_results.json` with p-value check.
- [ ] T038 [US3] **NEW**: Implement comparison of scheduler F1-score against **Deterministic Baseline F1** (from T028/T026a) to satisfy SC-005. **Input**: `data/baseline/metrics.json`.
- [ ] T039 [US3] Export `models/scheduler_checkpoint.pth` and `data/evaluation/results.jsonl`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Versioning & Validation (Polish)

**Purpose**: Ensure reproducibility and traceability

- [ ] T040 [P] Implement SHA-256 hash computation for all `data/` and `code/` artifacts in `src/main.py`
- [ ] T041 [P] Run `Reference-Validator Agent` on citations in `specs/` and `docs/`. **Output**: `validation_report.json` with status `NO_CITATIONS` if no external citations are found, or `VALID`/`INVALID` otherwise.
- [ ] T042 [P] Run `quickstart.md` validation to ensure pipeline reproducibility
- [ ] T043 [P] Final documentation update in `specs/001-llmxive-vl-intuition/research.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Must complete first as it generates the data required for US2 and US3.
- **User Story 2 (Phase 4)**: Depends on US1 (data generation).
- **Visual Baseline (Phase 5)**: Depends on US1 data availability. Must complete before Phase 6 Analysis tasks.
- **User Story 3 (Phase 6)**: Depends on US1 (labels), US2 (features), and Phase 5 (Baseline).
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational. No dependencies on other stories.
- **User Story 2 (P2)**: Depends on US1 (data generation).
- **User Story 3 (P3)**: Depends on US1 (labels), US2 (features), and Phase 5 (Baseline).

### Within Each User Story

- Tests (Mandatory per Spec) MUST be written (code created) before implementation
- Models/Utilities before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Test Code Writing tasks (T010-T012, T018-T020, T030-T032) marked [P] can run in parallel with Implementation tasks for the same story.
- Different modules within a story (e.g., generator vs labeler in US1) marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all test code writing for User Story 1 together:
Task: "Write contract test code: Verify labeling logic uses only visual events in tests/unit/test_visual_labeler.py"
Task: "Write integration test code: Verify execution log contains zero VLM calls in tests/integration/test_data_pipeline.py"

# Launch implementation components in parallel:
Task: "Implement src/data_synthesis/generator.py (CI/Non-CI subset logic)"
Task: "Implement src/data_synthesis/visual_labeler.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test US1 independently (ensure zero VLM calls in logs)
5. Deploy/demo data pipeline if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently
4. Add Visual Baseline (Phase 5) → Test independently
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Features) - *Can start once US1 data is available*
 - Developer C: Visual Baseline (Phase 5) - *Can start once US1 data is available*
 - Developer D: User Story 3 (Scheduler) - *Can start once US1/US2/Baseline are available*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Ensure no CUDA/GPU operations are used in US3 (CPU-only constraint)
- **Critical**: Ensure US1 labeling logic is strictly visual (no VLM involvement)
- **Critical**: Ensure T013 generates 50h data via streaming (FR-001) or subset for CI
- **Critical**: Ensure T026a (Deterministic Baseline) is completed before T035/T036 (Analysis)
- **Critical**: Ensure T036 includes conditioning on ground truth and comparison to logits (FR-005)
- **Critical**: Ensure T037 implements Spearman correlation against random baseline (SC-001)
- **Critical**: Ensure T038 implements F1 comparison against Deterministic Baseline (SC-005)
- **Critical**: Ensure T023 raises ValueError with clear message on dimension mismatch