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
- [ ] T005 Initialize Python 3.11 project with CPU-only dependencies (`torch`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `scipy`, `pyyaml`, `videomae`) in `code/requirements.txt`
- [ ] T006 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 [P] Implement `code/utils/config.py` for seed pinning and path configuration
- [ ] T008 [P] Implement `code/utils/versioning.py` to update `state/` YAML with artifact hashes (Constitution Principle V)
- [ ] T009 [P] Implement `code/data/validate_logs.py` to check for real Wan-Streamer v0.1 logs; IF missing, fetch from canonical source (VoxCeleb2 as per FR-019 for proxy data ONLY); IF Wan-Streamer latent logs are missing, the system MUST fail gracefully with "Data Unavailable" error (FR-022) and NOT attempt to substitute VoxCeleb2 for latent trajectories (Plan: Critical Data Constraint)
- [ ] T010 [P] Implement `code/utils/validators.py` for schema validation
- [ ] T018 [P] Implement `code/tasks/reduce_sample_size.py` module to reduce dataset sample size by [deferred] amount on power limit exceedance, or fail with "Power Limitation" error if minimum sample size is reached (FR-014, FR-023)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Extract time-series latent vectors and turn-taking labels from real Wan-Streamer v0.1 logs (or VoxCeleb2 fallback) to create a CPU-tractable dataset.

**Independent Test**: Verify that `extract_latents.py` and `preprocess.py` produce a Parquet file ≤ 1 GB with valid columns (timestamp, semantic_feature, prosodic_feature, latent_delta_magnitude, turn_label) and at least 10,000 sampled frames including interruption/pause events.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for dataset schema in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/contract/test_dataset_schema.py`
- [ ] T012 [P] [US1] Integration test for data extraction pipeline in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/integration/test_data_extraction.py` (US-1, FR-001)

### Implementation for User Story 1

- [ ] T013 [P] [US1] [US-1] [FR-001] Implement `code/data/extract_latents.py` to parse Wan-Streamer v0.1 logs (or canonical fallback from T009) and output raw Parquet (FR-001, US-1)
- [ ] T014 [US1] [FR-018] Implement `code/tasks/detect_events.py` to define the detection algorithm and thresholds for classifying 'interruption' and 'pause' events (e.g., audio energy > X dB overlapping with agent speech) to ensure a sufficient minimum event count is verifiable (FR-018)
- [ ] T016 [US1] [FR-015] Implement `code/tasks/validate_sampling_distribution.py` to measure and confirm that stratified sampling preserves the distribution of turn-taking events (FR-015)
- [ ] T019 [US1] Implement `code/data/compute_deltas.py` to compute latent deltas between timesteps for the extracted dataset (FR-001)
- [ ] T020 [US1] Implement `code/data/sample_and_filter.py` to apply stratified sampling by turn_label to reduce dataset to ≤ 1 GB while preserving distribution, label events as "high-priority" or "low-priority" with counts logged, and validate all required columns are non-null and correctly typed (FR-001, FR-018, US-1)
- [ ] T015 [US1] Implement logic in `code/data/sample_and_filter.py` to enforce distribution preservation; if memory limits are approached, invoke `code/tasks/reduce_sample_size.py` (T018) to reduce sample size by [deferred] amount; ONLY fail with "Power Limitation" error if minimum valid sample size is reached (Constitution Principle I, FR-014, Edge Cases)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight Estimator Training (Priority: P2)

**Goal**: Train a lightweight GRU model on CPU to predict latent delta magnitude and uncertainty scores.

**Independent Test**: Verify that `gru_estimator.py` and `trainer.py` complete training within 6 hours, use ≤ 7 GB RAM, and achieve MSE [deferred] lower than a zero-delta baseline on a held-out validation set.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for model output schema in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/contract/test_model_output_schema.py`
- [ ] T022 [P] [US2] Integration test for training loop and memory constraints in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/integration/test_training_constraints.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/models/gru_estimator.py` defining the lightweight GRU architecture with CPU-compatible operations (FR-002)
- [ ] T024 [US2] Implement `code/models/trainer.py` with a CPU-optimized training loop, ensuring memory usage stays ≤ 7 GB (FR-002)
- [ ] T025 [US2] Implement baseline comparison logic (zero-delta predictor) to validate MSE improvement
- [ ] T026 [US2] Implement `code/models/uncertainty_score.py` module to calculate and output an `UncertaintyScore` alongside predictions as a distinct artifact required by the data model (FR-002, SC-006)
- [ ] T027 [US2] Remove `pytest-timeout` from training script; enforce 6-hour runtime limit via system-level runner configuration instead (FR-002, US-2)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Hybrid Inference Simulation and Quality-Latency Trade-off (Priority: P3)

**Goal**: Simulate hybrid inference, compute FID/proxy MOS, and validate latency reduction via statistical tests.

**Independent Test**: Verify that `hybrid_engine.py` and `simulator.py` reduce latency by ≥ 20% while keeping FID degradation ≤ 5% and passing TOST equivalence tests (Δ=0.05).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for hybrid output schema in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/contract/test_hybrid_output_schema.py`
- [ ] T029 [P] [US3] Integration test for end-to-end simulation and metrics in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/integration/test_hybrid_simulation.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/inference/hybrid_engine.py` to conditionally skip flow-matching steps based on estimator predictions (FR-003)
- [ ] T031 [US3] [FR-009] Implement `code/tasks/execute_fallback.py` to handle the conditional fallback logic, ensuring precedence for randomized counterfactuals over deterministic thresholds (FR-006, FR-009, FR-017)
- [ ] T032 [US3] Implement `code/evaluation/metrics.py` to compute FID (using a frozen Inception-v3 model) against the *project's own baseline generation* (full flow-matching) and proxy MOS (using VideoMAE); ensure validation independence (FR-004, Constitution Principle VII)
- [ ] T033 [US3] Implement `code/evaluation/simulator.py` to run the hybrid pipeline on a test set of video segments, including the randomized counterfactual subset; CRITICAL: MUST generate the *paired* "Full Solver" ground truth for the randomized subset frames before simulation to enable FID stability calculation (US-3, FR-008, FR-010)
- [ ] T034 [US3] Implement logic to call the `analyze_latency_bias` module (T041) and `calculate_fid_stability_corr` module (T040) for statistical validation (FR-005, US-3, Constitution Principle VI)
- [ ] T035 [US3] Implement fallback logic for ambiguous turn-taking signals to default to full solver, ensuring the randomized counterfactual intervention (FR-008) OVERRIDES the deterministic fallback (FR-006) for frames in the randomized subset (Edge Case, FR-017)
- [ ] T040 [US3] [FR-010, FR-011] Implement `code/tasks/calculate_fid_stability_corr.py` to calculate the correlation (r ≥ 0.7) between predicted delta magnitude and FID stability (relative change in FID between skipped and full-solver frames) (FR-010, FR-011)
- [ ] T041 [US3] [FR-005, FR-007] Implement `code/tasks/analyze_latency_bias.py` to execute stratified bootstrap with propensity-score matching for latency reduction validation AND Two One-Sided Tests (TOST) equivalence tests (Δ=0.05) for quality metrics (FR-005, FR-007)
- [ ] T042 [US3] [FR-012, FR-013] Implement `code/tasks/validate_proxy_mos.py` to calculate Pearson correlation between proxy MOS and human ratings (if available); if human ratings are missing, log the EXACT string "Assumption Validated (No Human Data Available)" and continue without failing (US-3, SC-007, FR-012, FR-024)
- [ ] T043 [US3] [FR-016] Implement `code/tasks/power_analysis.py` to calculate and log the power analysis parameters (expected variance, minimum detectable effect size) to justify the sample size for the TOST test (FR-016)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` including `quickstart.md` and `research.md`
- [ ] T037 Code cleanup and refactoring for memory efficiency
- [ ] T038 Performance optimization for CPU inference speed
- [ ] T039 [P] Additional unit tests for edge cases (uncertainty thresholds, missing data) in `tests/unit/`
- [ ] T040 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T041 [P] Verify `state/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer.yaml` is updated with final artifact hashes
- [ ] T044 [P] [FR-021] Update `data-model.md` and `quickstart.md` to link the `contracts/` directory schema definitions as required (FR-021)
- [ ] T045 [P] [FR-020] Implement `code/tasks/update_state_yaml.py` to update the `state.yaml` file with artifact hashes (FR-020)

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
Task: "Implement code/utils/versioning.py"
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