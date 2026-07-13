# Tasks: llmXive follow-up: extending "Moebius: 0.2B Lightweight Image Inpainting Framework with 10B-Level Pe"

**Input**: Design documents from `/specs/001-llmxive-moebius-dynamic/`
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

- [ ] T001 Create project structure per `plan.md` and `projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/` directory layout
- [ ] T002 Initialize a Python project with PyTorch (CPU-only), scikit-learn, pillow, numpy, pandas, scipy, datasets, lpips, torchmetrics, torchvision dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan):

- [ ] T004 Implement `code/config.py` with seeds, paths, hyperparameters, and mode flags (CI vs Research)
- [X] T005 [P] Implement `code/utils/seed.py` for deterministic seeding across all libraries
- [ ] T006 [P] Implement `code/utils/cpu_profiler.py` for CPU-specific timing utilities (`time.perf_counter`)
- [ ] T007 Create base data model classes (`MaskedRegion`, `InferenceResult`, `GatingState`) in `code/models/data_models.py`
- [ ] T008 Configure error handling and logging infrastructure in `code/utils/logger.py`
- [ ] T009 Setup environment configuration management for dataset paths and artifact hashes

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Preparation and Human Complexity Annotation (Priority: P1) 🎯 MVP

**Goal**: Ingest Places2/CelebA-HQ, generate synthetic masks, and establish ground truth (Human or Decoupled Synthetic Proxy) without circularity.

**Independent Test**: Verify existence of masked dataset and CSV of scores with no model inference used to generate labels.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for mask generation metrics (gradient variance, entropy) in `tests/unit/test_mask_generator.py`
- [~] T011 [P] [US1] Integration test for data pipeline independence (no model inference in label gen) in `tests/integration/test_data_independence.py`

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement `code/data/loader.py` to fetch Places365 subset from HuggingFace (`mit-places/Places365`) with checksum verification
- [~] T013 [P] [US1] Implement `code/data/mask_generator.py` to create synthetic masks with varying complexity; record `gradient_variance` and `texture_entropy`
- [~] T014 [US1] Implement `code/data/annotator.py` to provide CLI/JSON interface for crowdsourcing structure
 - [ ] T014a [US1] **CI Mode**: Generate `data/annotations/decoupled_scores.csv` with columns `[image_id, score, mode]`. Logic: Generate scores using **random independent values** (uniform distribution 1-5) strictly decoupled from synthetic mask metrics (gradient/entropy) to satisfy FR-007 and avoid circularity. {{claim:c_9f11c331}} (Wikidata Q47604, https://www.wikidata.org/wiki/Q47604).
 - [ ] T014b [US1] **Research Mode**: Implement logic to load external human-annotated CSV. Validate schema and integrity.
 - [ ] T014c [US1] **Research Mode Ingestion**: Implement the specific mechanism to ingest, manage, and validate real human participant data for 'Research Mode' as required by FR-002.
 - [ ] T014d [US1] Implement **Participant Disagreement Logic**: Calculate standard deviation of scores per image. If std dev > 1.0, apply majority vote or flag for exclusion as per spec edge cases.
 - [ ] T014e [US1] **Flow Control**: If CI Mode, skip T015 (IR) and **explicitly log** "CI Mode: Single-Rater Simulation" to `data/results/validation_log.txt` to satisfy Constitution Principle VI auditability. If Research Mode, proceed to T015.
- [ ] T015 [US1] Implement Inter-Rater Reliability calculation (Krippendorff's alpha) in `code/data/annotator.py` (Research Mode only)
- [ ] T016 [US1] Add validation logic in `code/data/annotator.py` that raises an error if sample size < 50 or if label independence check fails. Log result to `data/results/validation_log.txt`.
- [ ] T017 [US1] Persist masked images to `data/processed/masked_images/` and scores to `data/annotations/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 4 - Synthetic Proxy Validation (Priority: P2) ⚠️ GATES US2

**Goal**: Validate that synthetic mask metrics correlate with ground truth BEFORE training the gating mechanism.

**Independent Test**: Compute Pearson correlation; flag if r < 0.7 (for human data) or log expected behavior (CI mode).

### Implementation for User Story 4

- [ ] T035 [P] [US4] Implement correlation analysis in `code/eval/stats.py` (Pearson between synthetic metrics and ground truth)
- [ ] T036a [US4] **Research Mode Gate**: Check if correlation r ≥ 0.7. If not, update `data/results/proxy_validation.json` with `gate_status: BLOCKED` and raise `SystemExit` with code 1.
- [ ] T036b [US4] **CI Mode Log**: If CI Mode, log expected low correlation behavior to `data/results/proxy_validation.json` with `gate_status: EXPECTED_LOW_CORRELATION` and **continue execution** (do not exit).
- [ ] T037 [US4] Save validation results to `data/results/proxy_validation.json`

**Checkpoint**: Proxy validation complete; gating mechanism training can proceed with confidence

---

## Phase 5: User Story 2 - Dynamic Rank Adjustment Mechanism Implementation (Priority: P2)

**Goal**: Implement "Moebius-Dynamic" architecture with lightweight gating head and dynamic rank modulation.

**Independent Test**: Run on single CPU core with low-complexity mask; verify reduced rank output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for gating head output scalar range (1-5) in `tests/unit/test_gating_head.py`
- [ ] T019 [P] [US2] Integration test for dynamic rank modulation logic in `tests/integration/test_dynamic_rank.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/models/moebius_tiny.py` (Simplified CPU version, ≤15M params total)
- [ ] T021 [US2] Implement `code/models/gating_head.py` (Lightweight conv head, **≤5M parameters**) to output scalar complexity. **Verification**: Count parameters and fail if > 5M.
- [ ] T022 [US2] Implement `code/models/moebius_dynamic.py` (Deliverable: `code/models/moebius_dynamic.py`) integrating gating head with $L\lambda MI$ linear matrices rank modulation logic.
 - [ ] T022a [US2] Handle edge case: interpolation for score=3
 - [ ] T022b [US2] Handle edge case: fallback to static high-rank if mask > 50%
- [ ] T023 [US2] Implement `code/training/train_gating.py` with multi-task loss (reconstruction + regression + rank classification)
- [ ] T024 [US2] Implement `code/training/train_end_to_end.py` for fine-tuning
- [ ] T025 [US2] Implement permutation test logic in `code/eval/stats.py` to verify no overfitting (FR-008)
- [ ] T025a [US2] **Pre-Deployment Gate**: Implement a validation step that checks the permutation test p-value. If p ≤ 0.05, block deployment and raise an error. This explicitly satisfies FR-008's requirement for a pre-deployment check.
- [ ] T026 [US2] Save model weights to `code/models/moebius_dynamic.pt` and gating weights to `data/results/`

**Checkpoint**: At this point, User Stories 1, 4, AND 2 should all work independently

---

## Phase 6: User Story 3 - Efficiency and Fidelity Evaluation (Priority: P3)

**Goal**: Benchmark dynamic vs. static models on CPU for latency and quality.

**Independent Test**: Run evaluation script on held-out set; generate report comparing latency/FID.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for FID/LPIPS calculation on CPU in `tests/unit/test_metrics.py`
- [ ] T028 [P] [US3] Integration test for statistical significance (t-test) in `tests/integration/test_stats_eval.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/eval/metrics.py` for FID, LPIPS, and wall-clock latency measurement (CPU only)
- [ ] T030a [US3] Implement `code/eval/stats.py` power analysis calculation (SC-005). Output power value to `data/results/power_analysis.json`.
- [ ] T030b [US3] **Decision Gate**: If power < 0.8, update `data/results/power_analysis.json` with `status: UNDERPOWERED` and **continue execution** to allow report generation. If power ≥ 0.8, proceed.
- [ ] T031 [US3] Implement `code/eval/report.py` to generate `data/results/evaluation_report.json`
- [ ] T032 [US3] Implement ablation logic in `code/eval/report.py` for counterfactual runs (Static Low Rank vs Dynamic)
- [ ] T033a [US3] **Run Inference**: Execute inference on test set across complexity bins; save raw latency metrics to `data/results/latency_raw.csv`.
- [ ] T033b [US3] **Verify Target**: Calculate latency reduction from `latency_raw.csv`. Verify ≥30% reduction for low-complexity regions. Update `data/results/evaluation_report.json`.
- [ ] T034 [US3] Verify FID difference ≤0.5 vs static baseline and statistical significance (p > 0.05)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` and `paper/draft.md` with mode labeling (CI vs Research)
- [ ] T039 Code cleanup and refactoring
- [ ] T040 Performance optimization (chunked processing for FID/LPIPS to stay within 7GB RAM)
- [ ] T041 [P] Additional unit tests in `tests/unit/`
- [ ] T042 Run `quickstart.md` validation and ensure all artifacts are checksummed
- [ ] T043 Generate final `paper/draft.md` with embedded metrics and mode distinctions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (Phase 3)**: Can start after Foundational.
 - **US4 (Phase 4)**: **GATES** US2. Depends on US1.
 - **US2 (Phase 5)**: Depends on US1 and US4.
 - **US3 (Phase 6)**: Depends on US2.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data; **GATES US2**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 and US4 for ground truth and validation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for trained model

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start
- Once US1 completes, US4 can start (US4 gates US2)
- Once US4 completes, US2 can start
- US3 depends on US2 completion
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for mask generation metrics in tests/unit/test_mask_generator.py"
Task: "Integration test for data pipeline independence in tests/integration/test_data_independence.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/loader.py"
Task: "Implement code/data/mask_generator.py"
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
3. Add User Story 4 (Proxy Validation) → Validate data quality (Gates US2)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Prep)
3. Once US1 complete:
 - Developer B: User Story 4 (Proxy Validation)
4. Once US4 complete (Gate Passed):
 - Developer C: User Story 2 (Model)
 - Developer D: User Story 3 (Evaluation) - can start partial setup
5. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All training and evaluation MUST run on CPU-only CI (cores, limited RAM). No CUDA, no 8-bit quantization.
- **CRITICAL**: Ground truth must be decoupled from model metrics in CI mode to prevent circularity.
- **CRITICAL**: US4 (Proxy Validation) MUST pass (r ≥ 0.7 for human data) before US2 (Training) begins.