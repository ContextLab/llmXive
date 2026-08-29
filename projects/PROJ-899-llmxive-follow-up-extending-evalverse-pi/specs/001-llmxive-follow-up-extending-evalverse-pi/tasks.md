---
description: "Task list template for feature implementation"
---

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
- [X] T004 Implement `scripts/checksum_data.py` to verify EvalVerse local download via SHA-256 and record hash in `state/projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi.yaml` under `artifact_hashes`. **Prerequisite**: Must run AFTER T014 to verify fetched data. **Output**: Updates `state/projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi.yaml`. **Note**: Removed [P] tag to enforce serial dependency with T004b.
- [X] T004b Implement `src/data/verify_provenance.py` to check that the downloaded dataset's metadata matches the `DATASET_DOI` and `DATASET_URL` in `src/config.py` at runtime. **Output**: `state/provenance_check.json` with status "pass", "fail", or "version_mismatch". **Constraint**: If mismatch or URL unreachable, EXIT with code 1 (HALT) to enforce strict verification per Constitution Principle I. This ensures pipeline runs on fresh runners only against verified canonical data. **Prerequisite**: T014, T004. **Note**: T004 MUST complete before T004b.
- [X] T005 [P] Create `src/config.py` with constants, random seeds, and thresholds
- [X] T006 [P] Implement `src/utils.py` for logging, error handling, and file I/O helpers
- [X] T007 Create base data structures (`VideoClip`, `FeatureVector`, `DimensionScore`) in `src/data/models.py`
- [X] T009a [P] Create directory structure script to initialize `data/raw`, `data/processed`, `data/results`, `state/`, `reports/` folders.
- [X] T009b [P] Implement dataset source configuration in `src/config.py`: Define `DATASET_DOI` and `DATASET_URL` as hardcoded constants to ensure Reproducibility Principle I compliance. **Constraint**: These constants MUST be used by T014 for fetching.
- [X] T009c [P] Initialize project-specific state file structure. **Action**: Create `state/projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi.yaml` if it does not exist, ensuring the `artifact_hashes` key is present. **Constraint**: Must run before T004 to ensure the target file exists. **Prerequisite**: T009a.
- [X] T035 [P] **GATE**: Implement comprehensive CPU-only execution validation in `src/utils/cpu_validator.py`. **Action**: (1) Static scan: Scan `code/` for imports of GPU libraries (e.g., `torch.cuda`, `tensorflow.keras.backend.set_session`) and exit 1 if found. (2) Runtime test: Execute a dry-run of the feature extraction pipeline on a small sample on a CPU-only runner. **Output**: `state/cpu_validation.json` with status "pass" or "fail". **Constraint**: If any GPU-specific code is detected or if the runtime dry-run fails, exit with code 1. **Prerequisite**: T002, T005. **Note**: This task MUST pass before any feature extraction (T012a, T013a) begins to enforce SC-001 early.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

**Critical Order Notes**:
- T014 (Fetch) MUST run before T004 (Verify).
- T009b (Config) MUST run before T014 (Fetch).
- T004 (Verify) MUST run before T004b (Provenance).
- T014 (Fetch) MUST run before T004b (Provenance).
- T035 (CPU Gate) MUST run before T012a, T013a.

---

## Phase 3: User Story 1 - Dimensional Viability Analysis (Priority: P1) 🎯 MVP

**Goal**: Determine which technical sub-dimensions are "feature-sufficient" (r ≥ 0.85) vs "VLM-required" (lower 95% CI < 0.70) using low-level features against human expert scores.

**Independent Test**: The system extracts features, trains models, and outputs a ranked list of dimensions with correlation coefficients and confidence intervals.

**⚠️ GATE**: T041 (Validation Gate) and T040 (Quality Gate) must pass (exit 0) before T012a, T013a, T015a-T015b, T016a-T016c, T019a-T019c, T020a-T020c, T017, T018 execute.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for feature extraction output schema in `tests/contract/test_feature_schema.py`
- [X] T011 [P] [US1] Integration test for full correlation pipeline on a small sample in `tests/integration/test_us1_pipeline.py`. **Assertion**: `assert pearson_corr > 0.5` on the test subset. **Constraint**: Must use the same seed as T005.

### Implementation for User Story 1

- [X] T042 [US1] Implement CSV/Parquet parsing logic to extract human expert scores, VLM proxy scores, and dimension labels from raw data in `src/data/preprocess.py`. **Output**: `data/processed/scores.csv` with columns `[clip_id, dimension, human_score, vlm_proxy_score]`. **Constraint**: Must explicitly extract 'vlm_proxy_score'. **Prerequisite**: T014 (Fetch).
- [X] T040 [US1] **GATE**: Calculate global error rate across the dataset in `src/data/preprocess.py` after T042. **Definition of Error**: A row is an error if it has missing required columns, null scores, or schema mismatch. **Output**: `state/global_error_rate.json`. **Constraint**: If error_count/total_count > 0.05 on the sample, EXIT with code 1 (HALT). This task MUST complete before T012a and T013a. **Prerequisite**: T042.
- [X] T041 [US1] **GATE**: Implement preliminary validation (FR-009) in `src/models/evaluate.py` to correlate VLM proxy scores against human expert scores on a subset. **Input**: Reads `data/processed/scores.csv` (from T042). **Output**: `state/validation_status.json`. **Constraint**: The validation gate requires a minimum of 10 samples. If n < 10, EXIT with code 1. If 10 ≤ n < 30, log a WARNING but allow proceed. **CRITICAL**: Must validate that Pearson correlation between VLM proxy and human scores is ≥ `CONFIG.VLM_PROXY_THRESHOLD` (default moderate from `src/config.py`); if not, EXIT with code 1. **Rationale**: This 0.5 threshold is a "Sanity Check" derived from FR-009's requirement to validate the proxy's signal before investing in feature extraction. It ensures the proxy is not random noise. This is distinct from the final "feature-sufficient" threshold (0.85) defined in T017. T041 passing does NOT guarantee the final research criteria; T017 performs the final classification. **Prerequisite**: T042.
- [ ] T012a [US1] Implement optical flow extraction (magnitude/variance) and HOG density calculation in `src/data/extract_optical.py` (OpenCV CPU-only). **Includes**: Error handling for missing frames (if a clip fails, set `missing_data_flag=True` and log a warning; DO NOT return zero vector). **Implementation Details**: Use `cv2.calcOpticalFlowFarneback` and `cv2.HOGDescriptor`. **Output**: `data/processed/features_optical.json` with entries `[{"clip_id": str, "dimension": str, "feature_vector": [float], "missing_data_flag": bool}]`. **Constraint**: `feature_vector` must be a JSON list of floats. **Prerequisite**: T041, T040.
- [ ] T013a [US1] Implement audio feature extraction (spectral centroid, zero-crossing rate) in `src/data/extract_audio.py` (Librosa). **Includes**: Error handling for missing audio tracks (if a clip fails, set `missing_data_flag=True` and log a warning; DO NOT return zero vector). **Implementation Details**: Use `librosa.feature.spectral_centroid` with `n_bins=128` and `librosa.feature.zero_crossing_rate`. **Output**: `data/processed/features_audio.json` with entries `[{"clip_id": str, "dimension": str, "feature_vector": [float], "missing_data_flag": bool}]`. **Constraint**: `feature_vector` must be a JSON list of floats. **Prerequisite**: T041, T040.
- [X] T012d [US1] **GATE**: Verify Feature Extraction Artifacts. **Action**: Check existence and schema validity of `data/processed/features_optical.json` and `data/processed/features_audio.json`. **Constraint**: If files are missing or schema invalid, EXIT with code 1. **Prerequisite**: T012a, T013a.
- [X] T015a [US1] Implement Ridge/Lasso training pipeline in `src/models/train.py` targeting human expert scores. **Output**: `data/models/{dimension}_ridge.joblib`, `data/models/{dimension}_lasso.joblib`. **Prerequisite**: T012d.
- [X] T015b [US1] Implement XGBoost training pipeline in `src/models/train.py` targeting human expert scores. **Output**: `data/models/{dimension}_xgb.joblib`. **Prerequisite**: T012d.
- [ ] T016a [US1] Implement data preparation for correlation analysis in `src/models/metrics.py`. **Action**: Load `features_optical.json` and `features_audio.json`, parse to numpy, exclude `missing_data_flag=True`, and prepare arrays for each dimension. **Output**: `data/processed/correlation_data.pkl`. **Prerequisite**: T015a, T015b.
- [ ] T016b [US1] Implement Pearson AND Spearman correlation calculation in `src/models/metrics.py`. **[FR-004]**. **Implementation Details**: Load `correlation_data.pkl`, calculate point estimates. **Output**: `data/processed/correlations_point.csv` with columns `[dimension, pearson_r, spearman_r]`. **Prerequisite**: T016a.
- [ ] T016c [US1] Implement bootstrapping for 95% CIs in `src/models/metrics.py`. **[FR-007]**. **Implementation Details**: Use `scipy.stats.bootstrap` with `method="basic"`, `n_resamples=1000`, and **stratified sampling** on the `dimension` column of the raw data from T016a. **Output**: `data/processed/correlations.csv` with columns `[dimension, pearson_r, spearman_r, lower_ci, upper_ci]`. **Prerequisite**: T016a.
- [ ] T019a [US1] Implement baseline predictors (Mean, Shuffled) in `src/models/evaluate.py`. **Output**: `data/processed/baseline_predictions.csv`. **Prerequisite**: T015a, T015b.
- [ ] T019b [US1] Calculate RMSE/R² for baselines and best model in `src/models/evaluate.py`. **Output**: `data/baseline_results.csv`. **Schema**: `[dimension, predictor_type, rmse, r2]`. **Prerequisite**: T019a.
- [ ] T019c [US1] **GATE**: Implement baseline quality check in `src/models/evaluate.py`. **Action**: Assert that `best_model_rmse < mean_predictor_rmse`. **Constraint**: If validation fails (reduction < 10%), log failure and EXIT with code 1. **Rationale**: This is a Quality Gate to ensure model efficacy, not a research scope limiter. **Prerequisite**: T019b.
- [ ] T020a [US1] Implement permutation engine (shuffling labels, recalculating stats) in `src/models/metrics.py`. **Parameter**: `n_permutations=10000`. **Output**: `data/processed/permutation_raw.csv`. **Prerequisite**: T015a, T015b.
- [ ] T020b [US1] Implement Max-T aggregation logic in `src/models/metrics.py`. **Action**: Aggregate max-T statistics from T020a. **Output**: `data/processed/max_t_stats.csv`. **Prerequisite**: T020a.
- [ ] T020c [US1] Implement FWER adjustment calculation in `src/models/metrics.py`. **Action**: Apply Westfall-Young max-T procedure. **Output**: `data/permutation_results.csv`. **Schema**: `[dimension, raw_p, adjusted_p]`. **Constraint**: Must apply FWER control. **Prerequisite**: T020b.
- [ ] T017 [US1] Implement logic to flag dimensions as "feature-sufficient" (lower_95ci >= 0.85), "VLM-required" (lower_95ci < 0.70), or "gray_zone" (in between) in `src/reports/generate.py`. **[FR-008]**. **Prerequisite**: T016c, T019c, T020c.
- [ ] T018 [US1] Generate final dimension viability report `data/dimension_viability.csv` with columns `[dimension, pearson_r, lower_ci, upper_ci, status, adjusted_p]`. **Prerequisite**: T017.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

**Critical Order Notes (Phase 3)**:
- **Pipeline Unblocked**: The chain T014 -> T042 -> T041 -> T012a/T013a -> T012d -> T015a/b -> T016a -> T016b/T016c, T019a/b/c, T020a/b/c -> T017 -> T018 is now executable.
- T012a and T013a are atomic and correctly ordered.
- T017 now depends on T016c, T019c, and T020c. All are mandatory.
- T016b and T016c are parallel tasks dependent on T016a.
- T019c and T020c are mandatory gates before T017.

---

## Phase 4: User Story 2 - Compute Feasibility Profiling (Priority: P2)

**Goal**: Verify the pipeline runs on a multi-core CPU within 7GB RAM and processes 10k clips in < 6 hours.

**Independent Test**: The system executes the full pipeline on a representative subset and logs peak memory and time per clip.

**⚠️ GATE**: T021 must pass (exit 0) before T024 executes.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for memory profiling logic with mock data in `tests/unit/test_profiles.py`
- [X] T022 [P] [US2] Integration test for timing constraints on a large batch of clips in `tests/integration/test_us2_timing.py`. **Assertion**: `assert projected_hours < 6.0`. **Constraint**: Must use the same seed as T005.

### Implementation for User Story 2

- [ ] T022a [US2] Implement batch processing loop to process N clips and log per-clip timing in `src/cli/run_pipeline.py`. **Input**: `data/processed/scores.csv`. **Output**: `data/processed/batch_raw_logs.json`. **Implementation Details**: Use `batch_size=100`. **Schema**: `[{clip_id: str, cpu_time_sec: float, status: str}]`. **Prerequisite**: T012a, T013a.
- [X] T022b [US2] Implement aggregation logic in `src/cli/run_pipeline.py`. **Action**: Calculate mean/median/max from `batch_raw_logs.json`. **Output**: `data/processed/batch_stats.json`. **Prerequisite**: T022a.
- [ ] T023b [US2] Implement structured logging of exact CPU time and memory peak to JSON file in `src/data/profiles.py`. **[FR-006]**. **Implementation Details**: Use `psutil` to measure peak memory per clip. **Output**: `data/profiling_logs.json`. **Schema**: A JSON list of objects: `[{clip_id: str, cpu_time_sec: float, peak_memory_mb: float, status: str, artifact_hash: str, git_commit: str, seed: int}]`. **Constraint**: `status` must be one of: "success", "failed", "timeout". Must log exact values per clip. **Reproducibility**: Must record `artifact_hash` of input data and `git_commit`/`seed` of the run. **Prerequisite**: T022a (runs during batch processing).
- [X] T021b [US2] **GATE**: Implement linear scaling validation in `src/models/evaluate.py`. **[FR-006]**. **Method**: Perform Ordinary Least Squares (OLS) regression using `scipy.stats.linregress` on `clip_index` vs `cpu_time_sec` from T023b data. **Implementation Details**: Validate linear scaling assumption (R^2 > 0.95). **Output**: `state/scaling_validation.json`. **Constraint**: Verify linearity (R^2 > 0.95). Exit with code 1 if linearity assumption fails. This task MUST complete before T021. **Prerequisite**: T023b.
- [X] T021 [US2] **GATE**: Implement memory and time profiling wrapper in `src/data/profiles.py` using `psutil` on a sample batch. **Input**: `data/profiling_logs.json` (from T023b) and `state/scaling_validation.json` (from T021b). **Output**: `state/feasibility_gate.json`. **Constraint**: If peak_memory_mb > 7168 (7GB) OR projected_total_hours (calculated internally from mean time in T023b: `mean_time * 10000 / 3600`) > 6.0, log failure and generate a "non-viable" report. Do NOT exit 1 immediately; allow T023 to generate the report. **Note**: T021 consumes T023b and T021b outputs directly. T024 runs AFTER T021 passes. **Prerequisite**: T021b, T023b.
- [ ] T024a [US2] Implement logic to calculate per-clip inference time and project total time for N=10,000 clips in `src/models/evaluate.py` based on T023b results. **Output**: `data/timing_profile.csv`. **Schema**: `[mean_time_per_clip_sec, projected_total_hours]`. **Formula**: `projected_total_hours = (mean_time_per_clip_sec * [sample_size]) / seconds_per_hour`, rounded to 2 decimal places. **Constraint**: Input time must be in seconds. **Prerequisite**: T021 (Gate must pass), T023b.
- [ ] T024b [US2] Generate final feasibility report `reports/feasibility_profile.json` containing `peak_memory_gb` and `projected_total_hours`. **Prerequisite**: T024a.
- [ ] T023 [US2] Implement structured report generation for memory/time metrics in `src/reports/generate.py`. **Output**: `data/reports/profiling_report.json`. **Prerequisite**: T021.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

**Critical Order Notes (Phase 4)**:
- **Linear Chain**: T022a -> T022b -> T023b -> T021b -> T021 -> T024a -> T024b -> T023 -> T025.
- **No Circular Dependencies**: T024a runs AFTER T021. T023b produces data for T021.
- **Schema Fixed**: T023b includes `artifact_hash`, `git_commit`, `seed` for reproducibility.

---

## Phase 5: User Story 3 - Sensitivity Analysis of Feature Thresholds (Priority: P3)

**Goal**: Ensure decision boundaries (0.85) are robust by sweeping thresholds in the high range (e.g., High performance).

**Independent Test**: The system re-runs classification logic with varied thresholds and reports stability/flip rates.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for sensitivity analysis output schema in `tests/contract/test_sensitivity_schema.py`

### Implementation for User Story 3

- [X] T033 [US3] Implement threshold sweep logic in `src/models/metrics.py`. **Output**: `data/sensitivity_sweep_raw.csv`. **Schema**: `[dimension, threshold, status]`. **Thresholds**: `{0.80, 0.85, 0.90}`. **Status Logic**: `feature-sufficient` if `r >= threshold` else `VLM-required`. **Prerequisite**: T016c (provides `r`), T017, T019c, T020c.
- [ ] T027a [US3] Implement flip rate calculation in `src/models/evaluate.py` using T033 output. **Output**: `data/sensitivity_flip_rate.csv`. **Schema**: `[dimension, flip_rate]`. **Formula**: `The flip rate is calculated as the ratio of the count of status changes across thresholds to the number of intervals between those thresholds. `. **Constraint**: Explicitly calculate flip rate. **[FR-005]**. **Prerequisite**: T033.
- [ ] T027b [US3] Implement stability flagging logic in `src/models/evaluate.py`. **Action**: Flag dimensions as "threshold-sensitive" if `flip_rate > 0.1`. **Output**: `data/sensitivity_status.csv` (updated with flag). **Prerequisite**: T027a.
- [X] T028 [US3] Generate full sensitivity matrix table `data/sensitivity_matrix_full.csv` showing classification outcome for *each dimension* at *all tested thresholds*. **Input**: `data/sensitivity_sweep_raw.csv` (from T033). **Format**: Wide-format matrix (pivot table) where rows are dimensions and columns are thresholds. **Schema**: `[dimension, status_0.80, status_0.85, status_0.90]`. **Implementation Details**: Aggregate T033 raw data into a wide format for methodological verification. **Required**: This artifact is mandatory for methodological verification (US-3 Acceptance Scenario 3) and satisfies SC-004. **Prerequisite**: T027b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure rigor

- [X] T029 [P] Documentation updates in `docs/` and `specs/`
- [X] T030 Code cleanup and refactoring for CPU optimization
- [X] T031 [P] Additional unit tests for edge cases (all-black frames, missing audio) in `tests/unit/`
- [ ] T034a [P] Implement seed scanning logic in `src/utils/seed_validator.py`. **Action**: Scan all scripts in `code/` for `random.seed`, `np.random.seed`, `torch.manual_seed` usage. **Prerequisite**: T005, T012a, T013a, T015a. (Removed T016a dependency).
- [ ] T034b [P] Implement seed validation report generation in `src/utils/seed_validator.py`. **Action**: Verify seeds match values in `src/config.py`. **Output**: `state/seed_validation.json` with status "pass" or "fail". **Constraint**: If any script lacks a pinned seed or uses a mismatched value, exit with code 1. **Prerequisite**: T034a.
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
 - **Critical Order**: T035 (CPU Gate) MUST run before T012a, T013a.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **Critical Order**: T014 (Fetch) MUST complete before T042 (Parse).
 - T042 (Parse) MUST complete before T041 (Validation Gate) and T040 (Quality Gate).
 - T041 and T040 (Gates) MUST complete BEFORE T012a, T013a (Feature Extraction).
 - **Parallel Note**: T012a and T013a are parallel-safe with respect to each other as they write to distinct files (`features_optical.json` and `features_audio.json`).
 - T015a/b MUST complete before T016a, T016b, T016c, T019a, T020a.
 - T016a MUST complete before T016b and T016c.
 - T016b and T016c are parallel tasks.
 - T019c and T020c are mandatory prerequisites for T017.
 - T017 depends on T016c, T019c, T020c.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
 - **Critical Order**: T022a (Batch Loop) MUST run before T023b (Logging).
 - T023b (Logging) and T022b (Aggregation) MUST complete before T021b (Scaling Validation) and T021 (Feasibility Gate).
 - **Correction**: T021b (Scaling Validation) depends ONLY on T023b (raw logs). T024a (Projection) is NOT a prerequisite for T021b.
 - T021b (Scaling Validation) MUST complete before T024a (Projection).
 - T021 (Feasibility Gate) depends on T021b AND T023b (raw logs). T021 does NOT depend on T024a.
 - T021 (Feasibility Gate) MUST complete before T024a (Projection).
 - T021 (Feasibility Gate) MUST complete before T023 (Report).
 - T023 (Report) MUST complete before T024b (Final Report).
 - **Linear Chain**: T022a -> T022b -> T023b -> T021b -> T021 -> T024a -> T024b -> T023 -> T025.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - **Critical Order**: T016c MUST complete before T033 (Sweep).
 - T019c and T020c MUST complete before T033 (Sweep).
 - T033 MUST complete before T027a.
 - T027a MUST complete before T027b.
 - T027b MUST complete before T028.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
 - Note: T004 is NOT parallel-safe with T004b.
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
 - Ensure T035 (CPU Gate) runs before T012a, T013a.
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
- **GATE Tasks (T041, T021, T040)**: These tasks MUST exit with code 0 to proceed. If they exit with code 1, the pipeline halts immediately (except T040 which halts on high error rate, T021 which logs failure).
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **T012a/T013a Note**: Merged error handling tasks into extraction tasks. Removed T012c/T013c. Added T012d (Gate) to verify artifacts.
- **T016b Note**: Explicitly mandated 'stratified' sampling and `scipy.stats.bootstrap`. Split into T016a, T016b, T016c.
- **T019 Note**: Added explicit 10% reduction threshold. Made it a hard gate (EXIT 1 on failure). Split into T019a, T019b, T019c.
- **T020 Note**: Marked as MANDATORY. Blocks T017. Split into T020a, T020b, T020c.
- **T021 Note**: Added explicit memory (7GB) and time (6h) thresholds. T021 calculates projection internally; T024a runs after. Modified to report failure instead of halting.
- **T024 Note**: Updated to depend on T021 (Gate must pass). Split into T024a, T024b.
- **T041 Note**: Updated to require n ≥ 10 and warn if n < 30. Added validation of VLM proxy correlation (r >= 0.5) as a *sanity check* distinct from the final 0.85 threshold. Explicitly linked to FR-009.
- **T004 Note**: Removed [P] tag to enforce serial dependency with T004b.
- **T034 Note**: Added to explicitly validate seed pinning per Constitution Principle I. **Update**: T034 now depends on T012a, T013a, T015a. Split into T034a/T034b. Removed T016a dependency.
- **T035 Note**: Added to explicitly validate CPU-only execution per SC-001. Merged T035a/T035b into single T035 task in Phase 2.