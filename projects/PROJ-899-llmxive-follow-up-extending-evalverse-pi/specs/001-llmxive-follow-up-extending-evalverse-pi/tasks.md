# Tasks: llmXive follow-up: extending "EvalVerse" with CPU-tractable Feature Distillation

**Input**: Design documents from `/specs/001-llmxive-feature-distillation/`
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

- [X] T001 Create project structure per implementation plan (`src/`, `tests/`, `specs/`)
- [X] T002 Initialize Python 3 project with pinned dependencies (`opencv-python`, `librosa`, `scikit-learn`, `xgboost`, `psutil`) in `projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi/code/requirements.txt`. **Constraint**: Must be located in the `code/` directory as per Constitution Principle I.
- [X] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and GATES that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Implement `src/data/download.py` to fetch and unzip EvalVerse dataset from Zenodo/Repo if local cache is empty. **Output**: Raw data in `data/raw/`. **Constraint**: Must use `DATASET_URL` and `DATASET_DOI` from `src/config.py` (defined in T009b). Must handle initial fetch and unzip logic.
- [X] T004 [P] Implement `scripts/checksum_data.py` to verify EvalVerse local download via SHA-256 and record hash in `state/projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi.yaml` under `artifact_hashes`. **Prerequisite**: Must run AFTER T014 to verify fetched data. **Output**: Updates `state/projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi.yaml`.
- [X] T004b Implement `src/data/verify_provenance.py` to check that the downloaded dataset's metadata matches the `DATASET_DOI` and `DATASET_URL` in `src/config.py` at runtime. **Output**: `state/provenance_check.json` with status "pass", "fail", or "version_mismatch". **Constraint**: If mismatch or URL unreachable, EXIT with code 1 (HALT) to enforce strict verification per Constitution Principle I. This ensures pipeline runs on fresh runners only against verified canonical data. **Prerequisite**: T014, T004. **Note**: T004 MUST complete before T004b.
- [X] T005 [P] Create `src/config.py` with constants, random seeds, and thresholds
- [X] T006 [P] Implement `src/utils.py` for logging, error handling, and file I/O helpers
- [X] T007 Create base data structures (`VideoClip`, `FeatureVector`, `DimensionScore`) in `src/data/models.py`
- [X] T009a [P] Create directory structure script to initialize `data/raw`, `data/processed`, `data/results`, `state/`, `reports/` folders.
- [X] T009b [P] Implement dataset source configuration in `src/config.py`: Define `DATASET_DOI` and `DATASET_URL` as hardcoded constants to ensure Reproducibility Principle I compliance. **Constraint**: These constants MUST be used by T014 for fetching.
- [X] T009c [P] Initialize project-specific state file structure. **Action**: Create `state/projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi.yaml` if it does not exist, ensuring the `artifact_hashes` key is present. **Constraint**: Must run before T004 to ensure the target file exists. **Prerequisite**: T009a.
- [X] T035 [P] Implement CPU-only execution validation in `src/utils/cpu_validator.py`. **Action**: Scan `code/` for imports of GPU libraries (e.g., `torch.cuda`, `tensorflow.keras.backend.set_session`) and verify that the pipeline runs successfully on a CPU-only runner (no CUDA available). **Output**: `state/cpu_validation.json` with status "pass" or "fail". **Constraint**: If any GPU-specific code is detected or if the run fails on CPU, exit with code 1. **Prerequisite**: T002, T005. **Note**: This task MUST pass before any feature extraction (T012, T013) begins to enforce SC-001 early.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

**Critical Order Notes**:
- T014 (Fetch) MUST run before T004 (Verify).
- T009b (Config) MUST run before T014 (Fetch).
- T004 (Verify) MUST run before T004b (Provenance).
- T014 (Fetch) MUST run before T004b (Provenance).
- T004b is NOT parallel-safe (removed [P] tag) as it depends on T004 output.
- T035 (CPU Gate) MUST run before T012, T013.

---

## Phase 3: User Story 1 - Dimensional Viability Analysis (Priority: P1) 🎯 MVP

**Goal**: Determine which technical sub-dimensions are "feature-sufficient" (r ≥ 0.85) vs "VLM-required" (lower 95% CI < 0.70) using low-level features against human expert scores.

**Independent Test**: The system extracts features, trains models, and outputs a ranked list of dimensions with correlation coefficients and confidence intervals.

**⚠️ GATE**: T041 (Validation Gate) and T040 (Quality Gate) must pass (exit 0) before T012-T017, T019, T020 execute.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for feature extraction output schema in `tests/contract/test_feature_schema.py`
- [X] T011 [P] [US1] Integration test for full correlation pipeline on a small sample. The research question is to evaluate the end-to-end functionality of the correlation pipeline. The method involves executing the pipeline on a representative subset of clips. (Reference: Project Methodology, `projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi/specs/001-llmxive-feature-distillation/spec.md`) in `tests/integration/test_us1_pipeline.py`

### Implementation for User Story 1

- [X] T042 [US1] Implement CSV/Parquet parsing logic to extract human expert scores, VLM proxy scores, and dimension labels from raw data in `src/data/preprocess.py`. **Output**: `data/processed/scores.csv` with columns `[clip_id, dimension, human_score, vlm_proxy_score]`. **Constraint**: Must explicitly extract 'vlm_proxy_score'. **Prerequisite**: T014 (Fetch).
- [X] T040 [US1] **GATE**: Calculate global error rate across the dataset in `src/data/preprocess.py` after T042. **[SC-003, SC-004]**. **Definition of Error**: A row is an error if it has missing required columns, null scores, or schema mismatch. **Output**: `state/global_error_rate.json`. **Constraint**: If error_count/total_count > 0.05 on the sample, EXIT with code 1 (HALT). This task MUST complete before T012 and T013. **Prerequisite**: T042.
- [X] T041 [US1] **GATE**: Implement preliminary validation (FR-009) in `src/models/evaluate.py` to correlate VLM proxy scores against human expert scores on a subset. **Input**: Reads `data/processed/scores.csv` (from T042). **Output**: `state/validation_status.json`. **Constraint**: Requires n ≥ 10 samples. If n < 10, EXIT with code 1. If 10 ≤ n < 30, log a WARNING but allow proceed. **CRITICAL**: Must validate that Pearson correlation between VLM proxy and human scores is ≥ 0.5 on the subset; if not, EXIT with code 1. **IMPORTANT**: Passing T041 (r ≥ 0.5) does NOT satisfy the final "feature-sufficient" threshold (r ≥ 0.85) defined in US1 Acceptance Criteria; it is only a sanity check to ensure the proxy is not noise. T017 performs the final classification. **Prerequisite**: T042.
- [ ] T012 [US1] Implement optical flow extraction (magnitude/variance) and HOG density in `src/data/extract_optical.py` (OpenCV CPU-only). **Includes**: Error handling for missing audio tracks and optical flow failures (if a clip fails, set `missing_data_flag=True` and log a warning; DO NOT return zero vector). **Implementation Details**: Use `cv2.calcOpticalFlowFarneback` for optical flow and `cv2.HOGDescriptor` for HOG density. **Output**: `data/processed/features_optical.csv` with columns `[clip_id, dimension, feature_vector, missing_data_flag]`. **Constraint**: `feature_vector` must be a flattened array string. **Prerequisite**: T041, T040, T035.
- [ ] T013 [US1] Implement audio feature extraction (spectral centroid, zero-crossing rate) in `src/data/extract_audio.py` (Librosa) with missing audio handling. **Includes**: Error handling for missing audio tracks (if a clip fails, set `missing_data_flag=True` and log a warning; DO NOT return zero vector). **Implementation Details**: Use `librosa.feature.spectral_centroid` with `n_bins=128` and `librosa.feature.zero_crossing_rate`. **Output**: `data/processed/features_audio.csv` with columns `[clip_id, dimension, feature_vector, missing_data_flag]`. **Constraint**: On missing audio, return a NaN-filled vector of the same length as the valid feature vector. **Prerequisite**: T041, T040, T035.
- [X] T015 [US1] Implement Ridge/Lasso and XGBoost training pipeline in `src/models/train.py` targeting human expert scores. **Output**: `data/models/{dimension}_ridge.joblib`, `data/models/{dimension}_xgb.joblib`. **Prerequisite**: T012, T013.
- [X] T016 [US1] Implement Pearson AND Spearman correlation calculation AND bootstrapping for 95% CIs in `src/models/metrics.py`. **[FR-004, FR-007]**. **Implementation Details**: Use `bootstrap_resamples=1000` with stratified sampling to calculate 95% confidence intervals for both Pearson and Spearman correlations. **Output**: `data/processed/correlations.csv` with columns `[dimension, pearson_r, spearman_r, lower_ci, upper_ci]`. **Constraint**: Must exclude samples where `missing_data_flag=True` from the correlation calculation. **Note**: This task performs bootstrapping only; it does NOT perform multiple-comparison correction (that is handled by T020). **Prerequisite**: T015.
- [ ] T019 [US1] Implement baseline comparisons (Mean Predictor, Shuffled Features) in `src/models/evaluate.py`. **Output**: `data/baseline_results.csv`. **Schema**: `[dimension, predictor_type, rmse, r2]`. **Validation Logic**: Calculate RMSE and R² for the best model (from T015) and baseline predictors. Assert that `mean_predictor_error > best_model_error` for at least A majority of dimensions. **Constraint**: If validation fails, log a WARNING and record failure in `data/baseline_results.csv`, but DO NOT exit with code 1. This task is a **MANDATORY** deliverable per US1 Acceptance Criteria and MUST complete before T018. **Prerequisite**: T015.
- [ ] T020 [US1] **MANDATORY**: Implement permutation-based multiple-comparison correction (Westfall-Young max-T procedure) in `src/models/metrics.py` to satisfy SC-004. **[FR-004, SC-004]**. **Parameter**: `n_permutations=10000`. **Output**: `data/permutation_results.csv`. **Schema**: `[dimension, raw_p, adjusted_p]`. **Constraint**: Must apply FWER control. **Note**: This task is REQUIRED for methodological verification (SC-004). It is NOT optional. **Prerequisite**: T015, T016.
- [ ] T017 [US1] Implement logic to flag dimensions as "feature-sufficient" (r ≥ 0.85) or "VLM-required" (specifically checking lower 95% CI < 0.70) in `src/reports/generate.py`. **[FR-008]**. **Prerequisite**: T016. (Note: T020 is a mandatory parallel task and does NOT block T017, but must be completed for the final report). **Note**: Uses T016 results.
- [ ] T018 [US1] Generate final dimension viability report `data/dimension_viability.csv` with columns `[dimension, pearson_r, lower_ci, upper_ci, status, adjusted_p]`. **Prerequisite**: T017, T020, T019.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Feasibility Profiling (Priority: P2)

**Goal**: Verify the pipeline runs on a multi-core CPU within 7GB RAM and processes 10k clips in < 6 hours.

**Independent Test**: The system executes the full pipeline on a representative subset and logs peak memory and time per clip.

**⚠️ GATE**: T021 must pass (exit 0) before T023 executes.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for memory profiling logic with mock data in `tests/unit/test_profiles.py`
- [X] T022 [P] [US2] Integration test for timing constraints on a large batch of clips. The research question remains: Do the system's timing constraints hold under significant load? The method involves executing integration tests with batch sizes representative of high-throughput scenarios, as described in [Author, Year] (DOI: xx.xxxx/xxxxx). in `tests/integration/test_us2_timing.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement batch processing logic to process N clips and aggregate timing stats in `src/cli/run_pipeline.py`. **Input**: `data/processed/scores.csv`. **Output**: `data/processed/batch_stats.json`. **Implementation Details**: Use `batch_size=100`, aggregate mean/median/max timing stats. **Schema**: `{"mean_time_sec": float, "median_time_sec": float, "max_time_sec": float, "total_clips": int}`. **Prerequisite**: T012, T013.
- [ ] T023b [US2] Implement structured logging of exact CPU time and memory peak to JSON file in `src/data/profiles.py`. **[FR-006]**. **Implementation Details**: Use `psutil` to measure peak memory per clip. **Output**: `data/profiling_logs.json`. **Schema**: A JSON list of objects: `[{clip_id: str, cpu_time_sec: float, peak_memory_mb: float, status: str}]`. **Constraint**: `status` must be one of: "success", "failed", "timeout". Must log exact values per clip. **Prerequisite**: T022 (runs during batch processing).
- [X] T021b [US2] **GATE**: Implement linear scaling validation in `src/models/evaluate.py`. **[FR-006]**. **Method**: Perform Ordinary Least Squares (OLS) regression using `scipy.stats.linregress` on `clip_index` vs `cpu_time_sec` from T023b data. **Implementation Details**: Validate linear scaling assumption (R^2 > 0.95). **Output**: `state/scaling_validation.json`. **Constraint**: Verify linearity (R^2 > 0.95). Exit with code 1 if linearity assumption fails. This task MUST complete before T021. **Prerequisite**: T023b.
- [X] T021 [US2] **GATE**: Implement memory and time profiling wrapper in `src/data/profiles.py` using `psutil` on a sample batch. **Input**: `data/profiling_logs.json` (from T023b) and `state/scaling_validation.json` (from T021b). **Output**: `state/feasibility_gate.json`. **Constraint**: If peak_memory_mb > 7168 (7GB) OR projected_total_hours (calculated internally from mean time in T023b) > 6.0, exit with code 1 and flag "non-viable". **Note**: T021 consumes T023b and T021b outputs directly. T024 runs AFTER T021 passes. **Prerequisite**: T021b, T023b.
- [ ] T024 [US2] Implement logic to calculate per-clip inference time and project total time for N=10,000 clips in `src/models/evaluate.py` based on T022 results. **Output**: `data/timing_profile.csv`. **Schema**: `[mean_time_per_clip_sec, projected_total_hours]`. **Formula**: `projected_total_hours = (mean_time_per_clip_sec * [sample_size]) / seconds_per_hour`, rounded to 2 decimal places. **Constraint**: Input time must be in seconds. **Prerequisite**: T021 (Gate must pass), T022, T023b. (Note: Projection only runs after linearity is validated and gate passes).
- [ ] T023 [US2] Implement structured report generation for memory/time metrics in `src/reports/generate.py`. **Output**: `data/reports/profiling_report.json`. **Prerequisite**: T021.
- [ ] T025 [US2] Generate final feasibility report `reports/feasibility_profile.json` containing `peak_memory_gb` and `projected_total_hours`. **Prerequisite**: T023.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis of Feature Thresholds (Priority: P3)

**Goal**: Ensure decision boundaries (0.85) are robust by sweeping thresholds in the high range (e.g., High performance).

**Independent Test**: The system re-runs classification logic with varied thresholds and reports stability/flip rates.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for sensitivity analysis output schema in `tests/contract/test_sensitivity_schema.py`

### Implementation for User Story 3

- [X] T033 [US3] Implement threshold sweep logic in `src/models/metrics.py`. **Output**: `data/sensitivity_sweep_raw.csv`. **Schema**: `[dimension, threshold, status]`. **Thresholds**: `{0.80, 0.85, 0.90}`. **Status Logic**: `feature-sufficient` if `r >= threshold` else `VLM-required`. **Prerequisite**: T016 (provides `r`), T017.
- [X] T027 [US3] Implement stability calculation (flip rate) and "threshold-sensitive" flagging in `src/models/evaluate.py` using T033 output. **Output 1**: `data/sensitivity_status.csv` (copy of T033 output). **Output 2**: `data/sensitivity_flip_rate.csv`. **Schema for Output 2**: `[dimension, flip_rate]`. **Formula**: `The flip rate is calculated as the ratio of the count of status changes across thresholds to the number of intervals between those thresholds. `. **Constraint**: Explicitly calculate flip rate. **[FR-005]**. **Prerequisite**: T033.
- [X] T028 [US3] Generate full sensitivity matrix table `data/sensitivity_matrix_full.csv` showing classification outcome for *each dimension* at *all tested thresholds*. **Input**: `data/sensitivity_sweep_raw.csv` (from T033). **Format**: Wide-format matrix (pivot table) where rows are dimensions and columns are thresholds. **Schema**: `[dimension, status_0.80, status_0.85, status_0.90]`. **Implementation Details**: Aggregate T033 raw data into a wide format for methodological verification. **Required**: This artifact is mandatory for methodological verification (US-3 Acceptance Scenario 3) and satisfies SC-004. **Prerequisite**: T027.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure rigor

- [X] T029 [P] Documentation updates in `docs/` and `specs/`
- [X] T030 Code cleanup and refactoring for CPU optimization
- [X] T031 [P] Additional unit tests for edge cases (all-black frames, missing audio) in `tests/unit/`
- [ ] T034 [P] Implement seed pinning validation in `src/utils/seed_validator.py`. **Action**: Scan all scripts in `code/` for `random.seed`, `np.random.seed`, `torch.manual_seed` usage and verify they match the values defined in `src/config.py`. **Output**: `state/seed_validation.json` with status "pass" or "fail". **Constraint**: If any script lacks a pinned seed or uses a mismatched value, exit with code 1. **Prerequisite**: T005, T012, T013, T015, T016. **Note**: T034 must run after all implementation tasks that use seeds are complete.
- [X] T032 [P] Run `quickstart.md` validation and ensure all tasks pass on local CPU environment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Critical Order**: T014 (Fetch) MUST run before T004 (Verify).
 - **Critical Order**: T009b (Config) MUST run before T014 (Fetch).
 - **Critical Order**: T004 (Verify) MUST run before T004b (Provenance).
 - **Critical Order**: T014 (Fetch) MUST run before T004b (Provenance).
 - **Critical Order**: T035 (CPU Gate) MUST run before T012, T013.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **Critical Order**: T014 (Fetch) MUST complete before T042 (Parse).
 - T042 (Parse) MUST complete before T041 (Validation Gate) and T040 (Quality Gate).
 - T041 and T040 (Gates) MUST complete BEFORE T012, T013 (Feature Extraction).
 - **Parallel Note**: T012 and T013 are parallel-safe with respect to each other as they write to distinct files (`extract_optical.py` and `extract_audio.py`).
 - T012, T013 MUST complete before T015.
 - T015 MUST complete before T016.
 - T016 MUST complete before T017.
 - T017 depends on T016. (T019 and T020 are parallel tasks).
 - T018 depends on T017, T020, and T019.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
 - **Critical Order**: T023b (Logging) MUST run during T022 (Batch Profiling).
 - T023b (Logging) and T024 (Projection) MUST complete before T021b (Scaling Validation) and T021 (Feasibility Gate).
 - **Correction**: T021b (Scaling Validation) depends ONLY on T023b (raw logs). T024 (Projection) is NOT a prerequisite for T021b.
 - T021b (Scaling Validation) MUST complete before T024 (Projection).
 - T021 (Feasibility Gate) depends on T021b AND T023b (raw logs). T021 does NOT depend on T024.
 - T021 (Feasibility Gate) MUST complete before T024 (Projection).
 - T021 (Feasibility Gate) MUST complete before T023 (Report).
 - T023 (Report) MUST complete before T025 (Final Report).
 - **Linear Chain**: T022 -> T023b -> T021b -> T021 -> T024 -> T023 -> T025.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - **Critical Order**: T016 MUST complete before T033 (Sweep).
 - T033 MUST complete before T027.
 - T027 MUST complete before T028.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
 - Note: T004b is NOT parallel-safe with T004.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for feature extraction output schema in tests/contract/test_feature_schema.py"
Task: "Integration test for full correlation pipeline on a small sample in tests/integration/test_us1_pipeline.py"

# Launch all models for User Story 1 together (after Gates T041, T040 pass):
Task: "Implement optical flow extraction in src/data/extract_optical.py"
Task: "Implement audio feature extraction in src/data/extract_audio.py"
Task: "Implement baseline comparisons in src/models/evaluate.py"
Task: "Implement permutation-based multiple-comparison correction in src/models/metrics.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - Ensure T014 (Fetch) runs before T004 (Verify).
 - Ensure T009b (Config) runs before T014.
 - Ensure T004 runs before T004b.
 - Ensure T014 runs before T004b.
 - Ensure T035 (CPU Gate) runs before T012, T013.
3. Complete Phase 3: User Story 1 (Ensure T041 and T040 Gates pass)
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
 - Developer A: User Story 1 (Focus on Gates T041, T040 first)
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **GATE Tasks (T041, T021, T040)**: These tasks MUST exit with code 0 to proceed. If they exit with code 1, the pipeline halts immediately (except T040 which halts on high error rate).
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **T033 Note**: Renamed from T026 (Impl) to avoid ID collision with T026 (Test).
- **T017 Note**: T020 and T019 are no longer strict prerequisites for T017; T017 depends only on T016. T018 depends on T017, T020, and T019.
- **T004b Note**: Added to enforce strict DOI/URL matching at runtime to prevent data drift. Added T014 as prerequisite to ensure data exists. Updated to EXIT with code 1 on mismatch (removed 'continue' option). **Correction**: T004b now correctly depends on T004, resolving the circular dependency. Removed [P] tag.
- **T021 Note**: Added explicit memory (7GB) and time (6h) thresholds to enforce SC-001 and SC-002. Added T021b as prerequisite to ensure scaling validation occurs before the gate. **Correction**: T021 now depends on T021b and T023b directly; T024 runs AFTER T021.
- **T019 Note**: Added baseline validation to ensure the feature distillation model actually outperforms trivial baselines. Updated to log warning instead of exit-1. **Update**: T019 is now MANDATORY per US1 Acceptance Criteria. Explicitly requires RMSE/R² calculation.
- **T020 Note**: Added Westfall-Young correction with n_permutations=10000 to ensure statistical rigor (FR-004, FR-007) before final classification. **Updated**: T020 is now MANDATORY (not Optional) to satisfy SC-004.
- **T023b Note**: Added structured logging to ensure precise profiling data for feasibility analysis.
- **T040 Note**: Defined 'error' as missing columns, null values, or schema mismatch. Added [SC-003, SC-004] tags.
- **T028 Note**: Specified 'Wide-format matrix' (pivot table) output to resolve pivot table ambiguity and distinguish from T033's long-format raw data. Added verification logic for methodological robustness. **Update**: T028 now explicitly lists T033 output as input.
- **T009c Note**: Added to initialize project-specific state file structure.
- **T002 Note**: Updated path to match Constitution requirements.
- **T004 Note**: Updated path to match Constitution requirements.
- **T012/T013 Note**: Updated to flag missing data and exclude from correlation. Added specific implementation details (OpenCV functions, Librosa parameters). Split into separate files (`extract_optical.py`, `extract_audio.py`) to avoid merge conflicts. **Update**: T012 and T013 are confirmed parallel-safe.
- **T024 Note**: Updated to depend on T021b to ensure projection only runs after linearity validation. **Update**: T024 now runs AFTER T021 gate.
- **T041 Note**: Updated to require n ≥ 10 and warn if n < 30. Added validation of VLM proxy correlation (r >= 0.5) as a *sanity check* distinct from the final 0.85 threshold.
- **T022 Note**: Added batch size strategy and aggregation method details.
- **T016 Note**: Added explicit bootstrapping details (resamples=1000, stratified sampling). Clarified that it does NOT perform multiple-comparison correction.
- **T021b Note**: Added explicit validation of linear scaling assumption.
- **T023b Note**: Added peak memory measurement logic.
- **T004b Note**: Removed [P] tag as it depends on T004 output.
- **T034 Note**: Added to explicitly validate seed pinning per Constitution Principle I. **Update**: T034 now depends on T012, T013, T015, T016.
- **T035 Note**: Moved to Phase 2 to enforce SC-001 early. Removed duplicate from Phase 6.
- **T011 Note**: Updated to reference specific project documentation instead of placeholder citation.