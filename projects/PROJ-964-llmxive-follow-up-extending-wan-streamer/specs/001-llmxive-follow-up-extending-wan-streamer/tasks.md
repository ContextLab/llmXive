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

- [X] T002a [P] Create `code/` directory. **Verification**: Run `os.path.isdir('code')` and assert True.
- [X] T002b [P] Create `code/data/` directory. **Verification**: Run `os.path.isdir('code/data')` and assert True.
- [X] T002c [P] Create `code/models/` directory. **Verification**: Run `os.path.isdir('code/models')` and assert True.
- [X] T002d [P] Create `code/inference/` directory. **Verification**: Run `os.path.isdir('code/inference')` and assert True.
- [X] T002e [P] Create `code/metrics/` directory. **Verification**: Run `os.path.isdir('code/metrics')` and assert True.
- [X] T002f [P] Create `code/utils/` directory. **Verification**: Run `os.path.isdir('code/utils')` and assert True.
- [X] T002g [P] Create `code/tasks/` directory. **Verification**: Run `os.path.isdir('code/tasks')` and assert True.
- [X] T002h [P] Create `code/tests/` directory. **Verification**: Run `os.path.isdir('code/tests')` and assert True.
- [X] T003a [P] Create `data/` directory. **Verification**: Run `os.path.isdir('data')` and assert True.
- [X] T003b [P] Create `data/raw/` directory. **Verification**: Run `os.path.isdir('data/raw')` and assert True.
- [X] T003c [P] Create `data/processed/` directory. **Verification**: Run `os.path.isdir('data/processed')` and assert True.
- [X] T003d [P] Create `data/models/` directory. **Verification**: Run `os.path.isdir('data/models')` and assert True.
- [X] T004a [P] Create `state/` directory. **Verification**: Run `os.path.isdir('state')` and assert True.
- [X] T004b [P] Create `docs/` directory. **Verification**: Run `os.path.isdir('docs')` and assert True.
- [X] T005a [P] Create `code/requirements.txt` with CPU-only dependencies (`torch`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `scipy`, `pyyaml`, `videomae`). **Verification**: Run `os.path.exists('code/requirements.txt')` and assert True.
- [X] T005b [P] Implement `code/config.py` to pin the exact HuggingFace dataset revision for VoxCeleb2 (FR-019, Constitution Principle I). **Verification**: Run `os.path.exists('code/config.py')` and assert True.
- [X] T005d [P] Create `pyproject.toml` with black formatting configuration. **Verification**: Run `os.path.exists('pyproject.toml')` and assert True.
- [X] T005e [P] Create `tests/unit/test_setup_verification.py` with automated assertions using `os.path.exists` and `os.path.isdir` to verify directory structure creation (FR-001, FR-002, FR-003, FR-004, FR-005). **Verification**: Run `pytest tests/unit/test_setup_verification.py` and assert pass.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Implement `code/utils/config.py` for seed pinning and path configuration.
- [X] T008 [P] Implement `code/utils/update_state_yaml.py` to update `state.yaml` with artifact hashes (Constitution Principle V, FR-020).
- [X] T009 [P] **Implement Data Source Check**: Implement `code/data/validate_logs.py` to check for Wan-Streamer v0.1 logs first; if missing, fetch the canonical VoxCeleb2 dataset. **Logic**: 1. Check `os.path.exists('data/raw/wan-streamer-logs')`. If True, register checksum and set `data_source='wan-streamer'` in `code/config.py`. 2. If False, check `os.path.exists('data/raw/voxceleb2')`. If True, register checksum and set `data_source='voxceleb2'`. 3. If both missing, fetch `voxceleb2` via `datasets.load_dataset`, register checksum, set `data_source='voxceleb2'`. **Must assert checksum registration in `state.yaml` before returning.** (FR-019, FR-022, Assumption about dataset availability).
- [X] T010 Implement `code/utils/validators.py` for schema validation. **Dependency**: T009 MUST complete successfully before T010 runs (Sequential). T010 reads the `data_source` flag set by T009.
- [ ] T016 [US1] **Implement Sample Size Reduction Module**: Implement `code/tasks/reduce_sample_size.py` module to reduce dataset sample size by [deferred] amount on power limit exceedance, or fail with "Power Limitation" error if minimum sample size is reached (FR-014, FR-023). **Note**: This module must be importable by Phase 4 tasks; define `MIN_SAMPLE_SIZE` constant explicitly. **Dependency**: T014.
- [ ] T029b [US1] **Critical Statistical Prep (Power Analysis)**: Perform 'a priori' power analysis per **FR-016** and **SC-008** using **real empirical variance** calculated from the `data/processed/raw_extract.parquet` produced by T013. **Logic**: 1. Load `data/processed/raw_extract.parquet`. 2. If file is empty or missing, **FAIL** and log "POWER ANALYSIS FAILED: NO DATA" to `data/logs/power_analysis_fail.log` and update `state.yaml` with `power_analysis_status: 'failed'`. Do not proceed. 3. If data exists, compute variance of `latent_delta_magnitude` and effect size from the sample. 4. Output `data/metrics/power_analysis.json` with `min_sample_size`, `expected_variance`, `effect_size`. **Dependency**: T013 (to provide raw data). **Verification**: Validate `data/metrics/power_analysis.json` exists and contains non-null numeric values. (FR-016, SC-008).

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

- [ ] T012a [P] [US1] [FR-018] **Define Thresholds**: Create `code/config/detection_thresholds.yaml` to explicitly define the detection algorithm and thresholds for classifying 'interruption' and 'pause' events. **Logic**: 1. Set default `audio_energy_threshold: 20` (dB). 2. Perform a **dry-run** on the first rows of the raw dataset (if available) or a synthetic sample to count events. 3. If event count < 500, adjust threshold via **binary search** (e.g., lower by 2dB increments) until count ≥ 500 or minimum threshold reached. 4. Log the final threshold and estimated event count. **Output**: `code/config/detection_thresholds.yaml` with validated threshold. **Dependency**: None (Independent of T013). **Verification**: Assert `os.path.exists('code/config/detection_thresholds.yaml')` and that the file contains `audio_energy_threshold` and a log entry confirming the count ≥ 500. (FR-018, US-1).
- [ ] T013 [US1] [FR-001] Implement `code/data/extract_latents.py` to parse Wan-Streamer v0.1 logs (or fetched VoxCeleb2) and output raw Parquet. **Logic**: Load thresholds from `code/config/detection_thresholds.yaml` (created by T012a). **Dependency**: T012a. **Output**: `data/processed/raw_extract.parquet`. **Verification**: Assert `os.path.exists('data/processed/raw_extract.parquet')` and schema validation. (FR-001, US-1).
- [ ] T014 [US1] Implement `code/data/preprocess.py` with logic to: (1) filter for interruption/pause events using configured thresholds (FR-001, US-1), (2) perform stratified sampling to reduce dataset to ≤ 1 GB while preserving distribution using parameters from `data/metrics/power_analysis.json` (FR-015, US-1), (3) label events as "high-priority" or "low-priority" with counts logged (FR-001, US-1), and (4) validate all required columns are non-null and correctly typed (FR-001, US-1). **Dependency**: T013, T029b. **Output**: `data/processed/sampled_dataset.parquet`.
- [ ] T015 [US1] Implement `code/data/validate_sampling.py` to explicitly validate that the stratified sampling process preserves the distribution of turn-taking events (FR-015) and log the distribution comparison results (US-1). **Dependency**: T014.
- [ ] T029c_search [P] [US1] **Literature Search**: Search arXiv, Google Scholar, and IEEE Xplore for "audio-visual latent delta variance" and "turn-taking effect size". **Output**: `data/metrics/literature_search_results.txt` with at least 3 relevant citations and extracted numeric estimates. **Note**: Non-blocking, can run in parallel with T013. (FR-016, SC-008).
- [ ] T029c_parse [P] [US1] **Parse Literature Estimates**: Parse `data/metrics/literature_search_results.txt` to extract numeric variance/effect size estimates. **Output**: `data/metrics/literature_estimates.json`. **Dependency**: T029c_search. (FR-016, SC-008).
- [ ] T029c_update [P] [US1] **Update Power Analysis with Literature**: Update `data/metrics/power_analysis.json` with refined values from `data/metrics/literature_estimates.json` if available. **Dependency**: T029c_parse, T029b. (FR-016, SC-008).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight Estimator Training (Priority: P2)

**Goal**: Train a lightweight GRU model on CPU to predict latent delta magnitude and uncertainty scores.

**Independent Test**: Verify that `gru_estimator.py` and `trainer.py` complete training within 6 hours, use ≤ 7 GB RAM, and achieve MSE [deferred] lower than a zero-delta baseline on a held-out validation set, AND verify uncertainty calibration (SC-006).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for model output schema in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/contract/test_model_output_schema.py`
- [X] T022 [P] [US2] Integration test for training loop and memory constraints in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/integration/test_training_constraints.py`

### Implementation for User Story 2

- [X] T025 [US2] **Implement GRU Architecture**: Implement `code/models/gru_estimator.py` defining the lightweight GRU architecture with CPU-compatible operations; ensure the The model outputs a tensor of shape `[batch, N]`, where N represents the number of target classes, with the first column representing the predicted delta magnitude and the second column representing the `UncertaintyScore` (0.0-1.0).; **Verification**: Run a schema check to ensure the class is defined and compatible with `torch`. **Note**: This task defines the architecture only; it does NOT produce a checkpoint file. **Dependency**: None.
- [ ] T019 [US2] **Implement Trainer & Produce Pending Checkpoint**: Implement `code/models/trainer.py` with a CPU-optimized training loop, ensuring memory usage stays ≤ 7 GB (FR-002). **Action**: Train the model defined in T025. **Output**: Save the checkpoint to `data/models/estimator_checkpoint_pending.pt` with `checkpoint['pending_validation'] = True` explicitly set in the dictionary. **Verification**: Assert `os.path.exists('data/models/estimator_checkpoint_pending.pt')` and `checkpoint['pending_validation'] == True` before completing. **Dependency**: T025, T016.
- [X] T020 [US2] Implement baseline comparison logic (zero-delta predictor) to validate MSE improvement on the prediction task; output `data/metrics/baseline_comparison.json` with MSE values and p-values; explicitly defer the correlation with FID stability (r ≥ 0.7) to T043 in Phase 5 where the simulation data exists (SC-003, FR-010).
- [X] T023 [US2] Implement job-level timeout monitoring logic in `code/models/trainer.py` to monitor wall-clock time (FR-014).
- [X] T023b [US2] Implement sample size reduction logic in `code/models/trainer.py` that calls the `code/tasks/reduce_sample_size.py` module (T016) if the 6-hour limit is approached; fail gracefully with "Power Limitation" error if the minimum sample size is reached (US-2, FR-014). **Dependency**: T016.
- [X] T023c [US2] Implement error logging for "Power Limitation" scenarios in `code/models/trainer.py` (FR-014, FR-023).
- [ ] T024 [US2] **Implement Uncertainty Calibration & Finalize Checkpoint**: Implement `code/metrics/uncertainty_calibration.py` to compute and validate the correlation (r ≥ 0.7) between the model's `UncertaintyScore` and actual prediction error (SC-006) on the validation set. **Action**: Load `data/models/estimator_checkpoint_pending.pt` (produced by T019). If correlation < 0.7, write `data/logs/uncertainty_calibration_failed.log` with the error details and update `state.yaml` with `calibration_status: 'failed'`. If >= 0.7, copy/rename the file to `data/models/estimator_checkpoint_final.pt` and update `state.yaml` with `calibration_status: 'passed'` (FR-002, SC-006, Constitution Principle VI). **Dependency**: T019.
- [X] T018a [US2] **Finalize Checkpoint**: **Verify** that `data/models/estimator_checkpoint_final.pt` exists (created by T024 if T024 passed). If T024 failed, this task fails. **Dependency**: T024. (Note: T024 handles the actual move/copy; this task ensures the final state is consistent).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Hybrid Inference Simulation and Quality-Latency Trade-off (Priority: P3)

**Goal**: Simulate hybrid inference, compute FID/proxy MOS, and validate latency reduction via statistical tests.

**Independent Test**: Verify that `hybrid_engine.py` and `simulator.py` reduce latency by ≥ 20% while keeping FID degradation ≤ 5% and passing TOST equivalence tests (Δ=0.05).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for hybrid output schema in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/contract/test_hybrid_output_schema.py`
- [ ] T029 [P] [US3] Integration test for end-to-end simulation and metrics in `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/tests/integration/test_hybrid_simulation.py`

### Implementation for User Story 3

- [ ] T047 [US3] **Critical Data Generation**: Generate and log the specific 'forced skip' ground truth artifact `data/processed/counterfactual_indices.parquet` containing frame indices for the randomized subset (≥ 5% of total) forced to be skipped, using a fixed seed `SEED=42`. **Logic**: 1. Verify `data/processed/sampled_dataset.parquet` exists (from T014). 2. Read total frame count. 3. Calculate 5% threshold. 4. Generate indices using `numpy.random.default_rng(42)`. 5. Write to parquet with schema `frame_id` (int64). **Verification**: Assert `len(counterfactual_indices) >= 0.05 * total_frames` and schema validation. **Dependency**: T014. (FR-008, US-3).
- [X] T045 [US3] **Implement execute_fallback module**: Implement `code/inference/fallback_handler.py` to trigger full solver when uncertainty > 0.8 or delta magnitude is high, explicitly enforcing the precedence rule (FR-017) where the randomized counterfactual intervention (T047) overrides the deterministic fallback for frames in the randomized subset (FR-006, FR-009, FR-017); depends on T047.
- [ ] T050 [US3] **Implement and Execute Hybrid Simulation**: Implement `code/inference/hybrid_sim.py` to execute the full hybrid inference pipeline; explicitly apply the randomized intervention logic from FR-008 using indices from T047; consume the estimator (T018a) and fallback handler (T045); generate the `HybridOutput` artifact `data/processed/hybrid_output.parquet` required for FID/MOS calculation (FR-003, US-3, FR-008). **Output Schema**: `frame_id` (int64), `latency` (float64), `fid_score` (float64), `skip_flag` (bool). **Verification**: Assert `os.path.exists('data/processed/hybrid_output.parquet')` and schema validation. **Dependency**: T047, T045, T018a.
- [X] T028 [US3] Implement `code/evaluation/metrics.py` to compute FID and proxy MOS. **Logic**: Import `code.config` and read `data_source`. If `data_source == 'wan-streamer'`, use Wan-Streamer baseline. If `data_source == 'voxceleb2'`, use **linear interpolation baseline** for FID degradation metrics (Plan Scope Limitation). (FR-004, US-3).
- [ ] T048 [US3] **Implement analyze_latency_bias module**: Implement stratified bootstrap with propensity-score matching for latency reduction validation using *independent covariates* (frame timestamp and audio energy, excluding estimator prediction) via `sklearn.linear_model.LogisticRegression` and `statsmodels.stats.weightstats.ttest_ind`; output `data/metrics/latency_bootstrap_results.csv` (FR-005, FR-007, US-3, Constitution Principle VI); depends on T050. **Fallback**: If T050 fails, log "CAUSAL VALIDATION SKIPPED" and update `state.yaml` with `causal_validation: 'skipped'`. **Logic**: Read `data_source` from `code/config` and switch baseline calculation method if necessary.
- [ ] T049 [US3] Implement Two One-Sided Tests (TOST) equivalence tests (Δ=0.05) for quality metrics; output `data/metrics/tost_results.csv` and verify p-value < 0.05 (FR-005, US-3, Constitution Principle VI); depends on T050. **Logic**: Use `statsmodels.stats.weightstats.ttost_ind`. **Fallback**: If T050 fails, log "TOST VALIDATION SKIPPED". **Logic**: Read `data_source` from `code/config` and switch baseline calculation method if necessary.
- [ ] T046 [US3] **Check Human Rating Data**: Implement logic to check for the existence of `data/raw/human_ratings.json`. **Action**: Write `data/metrics/human_data_status.json` with keys `status` ('present' or 'missing') and `reason`. **Dependency**: None. (FR-012, FR-013, SC-007).
- [ ] T044 [US3] **Implement validate_proxy_mos module**: Add logic to calculate Pearson correlation between proxy MOS and human ratings (if available) to validate proxy (FR-012, FR-013, SC-007). **Logic**: Read `data/metrics/human_data_status.json`. If `status == 'missing'`, log "Assumption Validated (No Human Data Available)" to `data/logs/mos_assumption_validated.log` and update `state.yaml` with `mos_validation: 'assumption_validated'`. If `status == 'present'`, compute correlation and update `state.yaml` with `mos_validation: 'passed'` or `failed` based on r ≥ 0.8. **Dependency**: T046.
- [ ] T032 [US3] Implement fallback logic for ambiguous turn-taking signals to default to full solver, and explicitly handle the 'Power Limitation' error scenario (FR-014, FR-023) by logging the error and exiting gracefully if the minimum sample size is reached during fallback checks (Edge Case, FR-014, FR-023).
- [ ] T043 [US3] **Implement calculate_fid_stability_corr module**: Implement `code/metrics/fid_stability_corr.py` to calculate the correlation (r ≥ 0.7) between predicted delta magnitude and FID stability (relative change in FID between skipped and full-solver frames) as a specific metric, using data generated by the hybrid simulation (FR-010, FR-011, SC-003); **If correlation >= 0.7, update `state.yaml` to `validation_status: 'validated'`; if < 0.7, update `state.yaml` to `validation_status: 'invalidated'` and log "FID STABILITY CORRELATION FAILED: r < 0.7". **Dependency**: T050. **Fallback**: If T050 fails, log "FID STABILITY UNVERIFIABLE" and update `state.yaml` with `validation_status: 'skipped'`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] **Create Documentation**: Create `docs/quickstart.md` and `docs/research.md` with initial content. **Verification**: Assert `os.path.exists('docs/quickstart.md')` and `os.path.exists('docs/research.md')`.
- [ ] T034 Code cleanup and refactoring for memory efficiency
- [ ] T035 Performance optimization for CPU inference speed
- [ ] T036 [P] Additional unit tests for edge cases (uncertainty thresholds, missing data) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T038 [P] Verify `state/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer.yaml` is updated with final artifact hashes AND link the `contracts/` directory schema definitions to the `data-model.md` and `quickstart.md` documents specifically in the 'Data Flow' section (FR-021). **Dependency**: T033.

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