# Tasks: llmXive follow-up: extending "Wan-Streamer v0.1"

**Input**: Design documents from `/specs/001-llmxive-streamer-optimization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

 Tasks MUST be organized by user story so each story can:
 - Be implemented independently
 - Be tested independently
 - Be delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project root directory structure: `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/`
- [ ] T002 Create `code/` subdirectories: `code/`, `code/data/`, `code/models/`, `code/inference/`, `code/evaluation/`, `code/utils/`, `code/tasks/`, `code/tests/`
- [ ] T003 Create `data/` subdirectories: `data/raw/`, `data/processed/`, `data/models/`
- [ ] T004 Create `state/` and `docs/` directories
- [ ] T005 [P] Create `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/` directory structure
- [X] T005a [P] Create `code/requirements.txt` with CPU-only dependencies (`torch`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `scipy`, `pyyaml`, `videomae`)
- [X] T005b [P] Implement `code/config.py` to pin the exact HuggingFace dataset revision for VoxCeleb2 (FR-019, Constitution Principle I)
- [ ] T005c [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Implement `code/utils/config.py` for seed pinning and path configuration
- [X] T008 [P] Implement `code/utils/update_state_yaml.py` to update `state.yaml` with artifact hashes (Constitution Principle V, FR-020)
- [X] T009 [P] Implement `code/data/validate_logs.py` to check for Wan-Streamer v0.1 logs; if missing, fetch the canonical VoxCeleb2 dataset using `datasets.load_dataset('voxceleb2', revision='...')`, compute and register the checksum in `state.yaml` (Constitution Principle III), and update configuration to use the fetched data (FR-019, FR-022, Assumption about dataset availability)
- [X] T010 [P] Implement `code/utils/validators.py` for schema validation
- [X] T016 [P] Implement `code/tasks/reduce_sample_size.py` module to reduce dataset sample size by [deferred] amount on power limit exceedance, or fail with "Power Limitation" error if minimum sample size is reached (FR-014, FR-023)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Extract time-series latent vectors and turn-taking labels from real Wan-Streamer v0.1 logs (or VoxCeleb2 fallback) to create a CPU-tractable dataset.

**Independent Test**: Verify that `extract_latents.py` and `preprocess.py` produce a Parquet file ≤ 1 GB with valid columns (timestamp, semantic_feature, prosodic_feature, latent_delta_magnitude, turn_label) and at least 10,000 sampled frames including interruption/pause events.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for dataset schema in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/contract/test_dataset_schema.py`
- [X] T012 [P] [US1] Integration test for data extraction pipeline in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/integration/test_data_extraction.py` (US-1, FR-001)

### Implementation for User Story 1

- [X] T013 [P] [US1] [FR-001] Implement `code/data/extract_latents.py` to parse Wan-Streamer v0.1 logs (or fetched VoxCeleb2) and output raw Parquet; define and implement the detection algorithm and thresholds for classifying 'interruption' and 'pause' events as a distinct, configurable component (e.g., audio energy > X dB defined in `code/config.py` or a dedicated config file) to ensure verifiability (FR-018, FR-001, US-1)
- [X] T014 [US1] Implement `code/data/preprocess.py` to: 1) filter for interruption/pause events using the configured thresholds, 2) compute latent deltas, 3) apply stratified sampling by turn_label (interruption/pause/normal) to reduce dataset to ≤ 1 GB while preserving distribution, 4) label events as "high-priority" or "low-priority" with counts logged, 5) validate all required columns are non-null and correctly typed, and 6) explicitly reference T015b for validation of sampling distribution preservation (FR-001, US-1, FR-015)
- [X] T014b [US1] Implement `code/data/validate_sampling.py` to explicitly validate that the stratified sampling process preserves the distribution of turn-taking events (FR-015) and log the distribution comparison results (US-1)
- [X] T015 [US1] Implement logic in `code/data/preprocess.py` to enforce graceful degradation: if memory limits are approached, call the `code/tasks/reduce_sample_size.py` module (T016) to reduce the dataset sample size and retry the sampling process; only fail gracefully with a "Power Limitation" error if the minimum valid sample size cannot be maintained after reduction attempts (Constitution Principle I, Assumption about power limitations, FR-014)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight Estimator Training (Priority: P2)

**Goal**: Train a lightweight GRU model on CPU to predict latent delta magnitude and uncertainty scores.

**Independent Test**: Verify that `gru_estimator.py` and `trainer.py` complete training within 6 hours, use ≤ 7 GB RAM, and achieve MSE [deferred] lower than a zero-delta baseline on a held-out validation set, AND verify uncertainty calibration (SC-006).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for model output schema in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/contract/test_model_output_schema.py`
- [X] T022 [P] [US2] Integration test for training loop and memory constraints in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/integration/test_training_constraints.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement `code/models/gru_estimator.py` defining the lightweight GRU architecture with CPU-compatible operations; ensure the model outputs a tensor of shape `[batch, 2]` where column 0 is the predicted delta magnitude and column 1 is the `UncertaintyScore` (0.0-1.0); save checkpoint to `data/models/estimator_checkpoint.pt` (FR-002, US-2); **depends on T024b**
- [X] T019 [US2] Implement `code/models/trainer.py` with a CPU-optimized training loop, ensuring memory usage stays ≤ 7 GB (FR-002)
- [X] T020 [US2] Implement baseline comparison logic (zero-delta predictor) to validate MSE improvement on the prediction task; output `data/metrics/baseline_comparison.json` with MSE values and p-values; explicitly defer the correlation with FID stability (r ≥ 0.7) to T042 in Phase 5 where the simulation data exists (SC-003, FR-010)
- [ ] T021 [US2] Add logic to compute and output an `UncertaintyScore` alongside predictions (FR-002); explicitly reference T031 for MOS validation logic (FR-012, FR-013, SC-007)
- [ ] T023 [US2] Implement job-level timeout monitoring logic in `code/models/trainer.py` to monitor wall-clock time (FR-014)
- [ ] T023b [US2] Implement sample size reduction logic in `code/models/trainer.py` that calls the `code/tasks/reduce_sample_size.py` module (T016) if the 6-hour limit is approached; fail gracefully with "Power Limitation" error if the minimum sample size is reached (US-2, FR-014)
- [ ] T023c [US2] Implement error logging for "Power Limitation" scenarios in `code/models/trainer.py` (FR-014, FR-023)
- [ ] T024 [US2] Implement `code/metrics/uncertainty_calibration.py` to compute and validate the correlation (r ≥ 0.7) between the model's `UncertaintyScore` and actual prediction error (SC-006) on the validation set; log results and ensure the model is not saved if calibration fails (FR-002, SC-006)
- [ ] T024b [US2] **Critical Validation**: Implement logic to compute the correlation (r ≥ 0.7) between `UncertaintyScore` and actual prediction error (SC-006) **before** the model checkpoint is saved in T018; if correlation < 0.7, raise an error and prevent saving (FR-002, SC-006, Constitution Principle VI)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Hybrid Inference Simulation and Quality-Latency Trade-off (Priority: P3)

**Goal**: Simulate hybrid inference, compute FID/proxy MOS, and validate latency reduction via statistical tests.

**Independent Test**: Verify that `hybrid_engine.py` and `simulator.py` reduce latency by ≥ 20% while keeping FID degradation ≤ 5% and passing TOST equivalence tests (Δ=0.05).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for hybrid output schema in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/contract/test_hybrid_output_schema.py`
- [ ] T029b [P] [US3] Integration test for end-to-end simulation and metrics in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/integration/test_hybrid_simulation.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement `code/inference/counterfactual_generator.py` to generate and log the 'forced skip' ground truth artifact (`data/processed/counterfactual_ground_truth.parquet`) containing frame indices for the randomized subset (≥ 5% of total) forced to be skipped, using a fixed seed for reproducibility (FR-008, FR-017, US-3)
- [ ] T025b [US3] **Critical Data Generation**: Generate and log the specific 'forced skip' ground truth dataset artifact `data/processed/counterfactual_indices.parquet` containing frame indices for the randomized subset (≥ 5% of total) forced to be skipped, using a fixed seed for reproducibility; this artifact is required input for T027 and T030 (FR-008, FR-017, US-3)
- [ ] T026 [US3] Implement `code/inference/hybrid_engine.py` to conditionally skip flow-matching steps based on estimator predictions AND implement the randomized counterfactual intervention (FR-008) where a random subset of frames (≥ 5%) is forced to be skipped regardless of prediction; log forced skip indices to `data/processed/counterfactual_indices.parquet` matching T025b's artifact; use fixed seed for reproducibility (US-3, FR-003, FR-008)
- [ ] T027 [US3] Implement `code/inference/fallback_handler.py` to trigger full solver when uncertainty > 0.8 or delta magnitude is high, explicitly enforcing the precedence rule (FR-017) where the randomized counterfactual intervention (T025b) overrides the deterministic fallback for frames in the randomized subset (FR-006, FR-009, FR-017); depends on T025b
- [ ] T028 [US3] Implement `code/evaluation/metrics.py` to compute FID against the Wan-Streamer v0.1 baseline or VoxCeleb2 ground truth (as per spec) and proxy MOS using VideoMAE (FR-004, US-3)
- [ ] T029 [US3] Implement `code/metrics/power_analysis.py` to perform the a priori power analysis, specifying expected variance and minimum detectable effect size for the TOST test, and log parameters to `data/metrics/power_analysis.json` (FR-016, US-3)
- [ ] T029b [US3] **Critical Statistical Prep**: Perform 'a priori' power analysis to specify expected variance and minimum detectable effect size for the TOST test; log calculated parameters (variance, effect size) to `data/metrics/power_analysis.json` to justify sample size (FR-016, US-3); **must run before T030**
- [ ] T030 [US3] Implement stratified bootstrap with propensity-score matching using *independent covariates* (not the estimator's prediction) for latency reduction validation AND Two One-Sided Tests (TOST) equivalence tests (Δ=0.05) for quality metrics; output `data/metrics/tost_results.csv` and verify p-value < 0.05 (FR-005, US-3, Constitution Principle VI); depends on T029b and T025b
- [ ] T031 [US3] Add logic to calculate Pearson correlation between proxy MOS and human ratings (if available) to validate proxy; if human ratings are missing, explicitly log the string "Assumption Validated (No Human Data Available)" and skip this specific correlation test without failing the pipeline (US-3, SC-007, FR-012, FR-013)
- [ ] T032 [US3] Implement fallback logic for ambiguous turn-taking signals to default to full solver, and explicitly handle the 'Power Limitation' error scenario (FR-014, FR-023) by logging the error and exiting gracefully if the minimum sample size is reached during fallback checks (Edge Case, FR-014, FR-023)
- [ ] T042 [US3] Implement `code/metrics/fid_stability_corr.py` to calculate the correlation (r ≥ 0.7) between predicted delta magnitude and FID stability (relative change in FID between skipped and full-solver frames) as a specific metric, using data generated by the hybrid simulation (FR-010, FR-011, SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `docs/` including `quickstart.md` and `research.md`
- [ ] T034 Code cleanup and refactoring for memory efficiency
- [ ] T035 Performance optimization for CPU inference speed
- [ ] T036 [P] Additional unit tests for edge cases (uncertainty thresholds, missing data) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T038 [P] Verify `state/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer.yaml` is updated with final artifact hashes AND link the `contracts/` directory schema definitions to the `data-model.md` and `quickstart.md` documents specifically in the 'Data Flow' section (FR-021)

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 model

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
- Different user stories can be worked on in parallel by different team members
- **Note**: Implementation tasks within a story (e.g., T013 -> T014) are sequential, not parallel.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Integration test for data extraction pipeline in tests/integration/test_data_extraction.py"

# Launch all foundational setup tasks in parallel:
Task: "Implement code/utils/config.py"
Task: "Implement code/utils/update_state_yaml.py"
Task: "Implement code/data/validate_logs.py"
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
- **Critical**: All data must be real; no synthetic generation of input data or metrics.
- **Critical**: All models must be CPU-tractable; no CUDA/8-bit quantization.
- **Critical**: Data flow must be respected; verification tasks must follow data generation tasks.
- **Critical**: Dataset download tasks must specify real, reachable URLs or package-based fetch methods.