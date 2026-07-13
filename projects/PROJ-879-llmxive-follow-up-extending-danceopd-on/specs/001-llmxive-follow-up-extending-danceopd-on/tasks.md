# Tasks: llmXive follow-up: extending "DanceOPD: On-Policy Generative Field Distillation"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-danceopd-on/`
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
  - Delivered as a MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/` including directories: `code/`, `code/utils/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/integration/`, `specs/contracts/` and files: `code/requirements.txt`, `code/main.py`, `code/00_data_generation.py`, `code/01_train_trees.py`, `code/02_evaluate_fidelity.py`, `code/03_versioning.py`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/` including pinned dependencies: `torch`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `pillow`, `scipy`, `torch-fidelity`, `open-clip-torch`
- [ ] T003 [P] Configure linting and formatting tools (ruff/black) in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/config.py` to manage seeds, paths, and hyperparameters (including `TEACHER_WEIGHTS_PATH`)
- [ ] T005 [P] Create `code/utils/metrics.py` with function signatures for CPU-only CLIP Score and FID calculation: `calculate_clip_score(image_path_1: str, image_path_2: str) -> float` and `calculate_fid(image_path_1: str, image_path_2: str) -> float`. These functions MUST raise `NotImplementedError` until implemented, ensuring the pipeline can run without crashing.
- [ ] T005b [P] Implement `code/utils/metrics.py` with actual CPU-only CLIP Score (using `open-clip-torch`) and FID (using `torch-fidelity`) functions
- [ ] T006 Create `code/03_versioning.py` to calculate SHA256 hashes for artifacts and update `state/`
- [ ] T007 Setup data directories: `data/raw/`, `data/processed/`, `data/results/` in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/`
- [ ] T008 Implement pre-flight check script `code/utils/check_weights.py` that verifies existence and SHA256 checksum of user-provided weights against `data/raw/weights_manifest.json`. The manifest MUST contain entries with `filename`, `expected_sha256`, and `expected_size_bytes`. The script MUST exit with code 1 if the manifest is missing, a file is missing, or the checksum/size does not match.
- [ ] T009 Create JSON schemas for `TeacherRoutingDataset`, `InferenceResult`, and `DecisionTreeMetadata` in `specs/contracts/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Teacher Routing Ground Truth (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of `(prompt_embedding, noise_level, routing_label, velocity_vector)` tuples by running the pre-trained DanceOPD teacher model on sampled ImageNet-1K and LAION-400M prompts.

**Independent Test**: The system produces a CSV/Parquet file with ≥1,000 rows, valid expert identifiers, and consistent velocity vector dimensions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for data schema validation in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_data_schema.py`
- [ ] T011 [P] [US1] Integration test for data generation pipeline in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_data_generation.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement data streaming logic in `code/00_data_streaming.py` to perform a stratified random sample of 500 images from ImageNet-1K and 500 from LAION-400M, saving raw batches to `data/raw/`
- [ ] T012b [P] [US1] Implement orchestration logic in `code/00_data_streaming.py` to combine the sampled subsets from both ImageNet-1K and LAION-400M, asserting `len(imageNet_samples) > 0` and `len(laion_samples) > 0` before proceeding, ensuring FR-001 dual-source requirement is met.
- [ ] T013a [US1] Implement teacher model loading in `code/00_teacher_inference.py` using `config.TEACHER_WEIGHTS_PATH` and batch inference loop on the streamed data. The inference MUST run on the CPU runner (using CPU-only weights or streaming) and fail if GPU is required, removing the assumption of external GPU resources.
- [ ] T013b [US1] Implement logic in `code/00_teacher_inference.py` to detect undefined routes, log the count of excluded samples, and EXCLUDE them from the dataset. Do NOT assign fallback labels; only exclude to maintain 'sole source of truth' for ground truth.
- [ ] T014 [US1] Implement logic in `code/00_data_extraction.py` to extract `prompt_embedding`, `noise_level`, `routing_label`, and `velocity_vector` from inference outputs and stream to `data/processed/teacher_routing_dataset.parquet`
- [ ] T015 [US1] Add validation in `code/00_data_extraction.py` to ensure `routing_label` matches known expert field IDs for the remaining valid samples
- [ ] T016 [US1] Implement checksumming and versioning of the generated dataset using `code/03_versioning.py`
- [ ] T016b [US1] Add validation logic in `code/00_data_extraction.py` to assert the final `teacher_routing_dataset.parquet` contains samples from both ImageNet-1K and LAION-400M sources
- [ ] T016c [US1] Verify that the count of excluded undefined routes is recorded in the dataset metadata and reported in `data/results/exclusion_log.json`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Evaluate Static Decision Trees (Priority: P2)

**Goal**: Train Decision Tree classifiers with `max_depth` 2–20 on the generated dataset to approximate routing labels and compute "Routing Consistency".

**Independent Test**: A tree with `max_depth=5` is saved and reports a reproducible validation accuracy on a held-out test split.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for Decision Tree training parameters in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_tree_training.py`
- [ ] T019 [P] [US2] Integration test for training loop and metadata schema validation in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_tree_training.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement data splitting logic (train/test) in `code/01_train_trees.py` consuming `data/processed/teacher_routing_dataset.parquet` (producer: T014)
- [ ] T021 [US2] Implement loop to train `DecisionTreeClassifier` (scikit-learn, CPU) for `max_depth` 2 to 20 in `code/01_train_trees.py`
- [ ] T022 [US2] Implement logic to compute and log "Routing Consistency" (accuracy) for each depth against the test set
- [ ] T023 [US2] Implement saving of trained models to disk and generation of results table (depth vs. accuracy)
- [ ] T024 [US2] Add metadata schema validation for each trained model and update `state/` with model hashes

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Quantify Fidelity Degradation and Statistical Significance (Priority: P3)

**Goal**: Execute CPU-only inference using tree-predicted routing, measure FID/CLIP Score, and perform statistical tests (bootstrap, paired t-test) on the "Matched-Routing" and "Mismatched-Routing" subsets to measure total degradation.

**Independent Test**: The system calculates FID/CLIP for teacher vs. tree (depth=5) on both subsets and outputs valid p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for statistical test functions (bootstrap, t-test) in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/unit/test_statistics.py`
- [ ] T027 [P] [US3] Integration test for full fidelity evaluation pipeline in `projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/tests/integration/test_fidelity_evaluation.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement logic to filter `TeacherRoutingDataset` into "Matched-Routing" subset (tree prediction == teacher label) in `code/02_evaluate_fidelity.py`
- [ ] T028b [P] [US3] Implement logic to filter `TeacherRoutingDataset` into "Mismatched-Routing" subset (tree prediction != teacher label) in `code/02_evaluate_fidelity.py` to ensure total degradation is measurable.
- [ ] T029 [US3] Implement CPU-only Euler integrator in `code/02_integrator.py` to generate images using tree-predicted velocity vectors for the Matched subset. Parameters: `step_size = 0.1`, `num_steps = 20`. The integrator MUST invoke the selected expert field to generate the velocity vector before integration.
- [ ] T029a [US3] Implement CPU-only Euler integrator in `code/02_integrator.py` to generate images using TEACHER velocity vectors for the Matched subset (baseline). Parameters: `step_size = 0.1`, `num_steps = 20`.
- [ ] T029b [US3] Implement CPU-only Euler integrator in `code/02_integrator.py` to generate images for the Mismatched subset using BOTH tree-predicted and TEACHER velocity vectors. Parameters: `step_size = 0.1`, `num_steps = 20`.
- [ ] T030 [US3] Implement FID and CLIP Score calculation in `code/02_metrics.py` for the Matched subset images (N=200 sample)
- [ ] T030a [US3] Implement statistical power validation for the Matched subset metrics in `code/02_statistics.py`. If power < 0.8, ENFORCE a stop condition and trigger a fallback to increase sample size (up to N=500) or abort with error code 2. Do NOT proceed with insufficient power.
- [ ] T030b [US3] Implement FID and CLIP Score calculation in `code/02_metrics.py` for the Mismatched subset images (tree vs teacher)
- [ ] T030c [US3] Implement statistical power validation for the Mismatched subset metrics in `code/02_statistics.py`. If power < 0.8, ENFORCE a stop condition and trigger a fallback to increase sample size (up to N=500) or abort with error code 2. Do NOT proceed with insufficient power.
- [ ] T031 [US3] Implement bootstrap hypothesis test on FID distributions and paired t-test on CLIP scores in `code/02_statistics.py` (only if T030a AND T030c confirm sufficient power)
- [ ] T032 [US3] Generate final results: `data/results/fidelity_metrics.csv` and `data/results/statistical_tests.json` with p-values and conclusions
- [ ] T032b [US3] Aggregate Matched and Mismatched metrics to calculate and report "Total Degradation" (weighted average based on subset proportions)
- [ ] T033 [US3] Implement early-stop condition if the CPU runtime limit is exceeded. Use `signal` module with `SIGALRM` handler to trigger a timeout. On timeout, write partial results to `data/results/partial_results.json` as a list of completed depths and exit with code 3.
- [ ] T033b [US3] Update `code/02_evaluate_fidelity.py` to ensure the 6-hour limit applies to the entire fidelity evaluation loop, not just individual sub-tasks.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `docs/` and `README.md`
- [ ] T035 Code cleanup and refactoring in `code/`
- [ ] T036 Performance optimization for data streaming and batch processing
- [ ] T037 [P] Additional unit tests for edge cases (memory exhaustion, undefined routes) in `tests/unit/`
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T014 (dataset generation)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T023 (trained trees) and T014 (dataset)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data streaming and schema validation before model training
- Training before inference and statistical testing
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Phase 3**: T012, T012b, T013a, T013b, T014, T015, T016, T016b, T016c are now in separate files (`00_data_streaming.py`, `00_teacher_inference.py`, `00_data_extraction.py`) and can run in parallel where file dependencies allow.
- **Phase 5**: T029, T029a, T029b, T030, T030a, T030b, T030c, T031, T032, T032b, T033, T033b are now in separate files (`02_integrator.py`, `02_metrics.py`, `02_statistics.py`) and can run in parallel where file dependencies allow.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for data schema validation in tests/unit/test_data_schema.py"
Task: "Integration test for data generation pipeline in tests/integration/test_data_generation.py"

# Launch all models for User Story 1 together (files are now split):
Task: "Implement data streaming logic in code/00_data_streaming.py"
Task: "Implement teacher model inference loop in code/00_teacher_inference.py"
Task: "Implement data extraction logic in code/00_data_extraction.py"
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
- **Critical Constraint**: All tasks must run on CPU-only CI with minimal computational resources (limited CPU cores and RAM). No CUDA, no 8-bit quantization, no large model training.
- **Data Integrity**: No synthetic/fake input data allowed. All data must come from real sources (ImageNet/LAION via HF) or real teacher model inference.
- **File Separation**: Phase 3 tasks are split into `00_data_streaming.py`, `00_teacher_inference.py`, `00_data_extraction.py` to prevent merge conflicts. Phase 5 tasks are split into `02_integrator.py`, `02_metrics.py`, `02_statistics.py` for the same reason.
- **Statistical Validity**: T030a/T030c enforce hard stop if power < 0.8.
- **Total Degradation**: T028b, T030b, T032b ensure both Matched and Mismatched subsets are measured.