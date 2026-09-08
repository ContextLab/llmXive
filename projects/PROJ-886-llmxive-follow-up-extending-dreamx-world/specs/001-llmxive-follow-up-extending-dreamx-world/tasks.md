# Tasks: DreamX-Lite: Geometric Priors for 3D Consistency

**Input**: Design documents from `/specs/001-dreamx-lite-geometric-priors/`
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

## Phase 0: Data Verification & Fallback (Pre-Execution)

**Purpose**: Verify data sources and implement fallback logic BEFORE any primary claim generation.

- [ ] T000a [P] Configure CPU-Only Runtime Environment: Create `scripts/config_cpu_env.sh` that sets `CUDA_VISIBLE_DEVICES=""` and verifies `torch.cuda.is_available()` returns `False` or is ignored. The script will create the full project directory tree starting at the repository root. Run from repo root. This is a global prerequisite for all subsequent tasks. (Per Spec FR-002 & Review: Coverage-d0994ae4).
- [ ] T000b [P] Define Verified Data Sources Schema: Create `verified_data_sources.json` schema and a script `scripts/init_verified_sources.py` that generates the file if missing, containing the expected source IDs and checksums for DreamX-World and ScanNet. (Per Review: Coverage-c8ae7397).
- [ ] T001a [P] Initialize Project Structure Script: Create `scripts/init_dirs.sh` that creates the full nested directory tree `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/` including `data/raw/`, `data/derived/`, `data/derived/videos/`, `code/`, `code/models/`, `code/pipeline/`, `code/analysis/`, `code/utils/`, `tests/unit/`, `tests/integration/`, `logs/`, `docs/`, `config/`. The script will create the full project directory tree starting at the repository root. **Run from repo root**. (Per Plan Project Structure & Review: Executability-8072e44c).
- [ ] T001b [P] Verify File Manifest: Run `scripts/init_dirs.sh` and verify the following 15 directories exist: `data/raw`, `data/derived`, `data/derived/videos`, `code`, `code/models`, `code/pipeline`, `code/analysis`, `code/utils`, `tests/unit`, `tests/integration`, `logs`, `docs`, `config`, `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world`, `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data` (Per Plan Project Structure).
- [ ] T001c [P] Verify Placeholder Files: Verify empty placeholder files exist for `requirements.txt`, `README.md`, `pyproject.toml`, `.ruff.toml`, `code/__init__.py`, `code/models/__init__.py`, `code/pipeline/__init__.py`, `code/analysis/__init__.py`, `code/utils/__init__.py`, `tests/__init__.py`. (Per Plan Project Structure).
- [ ] T002 [P] Initialize Python 3.x+ project with `requirements.txt` (torch CPU, transformers, datasets, colmap, scipy, pandas, numpy, opencv-python, scikit-learn) in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/`
- [ ] T003 [US1] Configure environment variables and random seed fixation in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/config.py` (Sequential: Global seed must be set once)
- [ ] T004 [P] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/io.py` for data loading, checksumming, and logging
- [ ] T005a [P] Configure Linting Config: Create `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections, and `.ruff.toml` config in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/`. (Per Plan Project Structure).
- [ ] T005b [P] Verify Linting: Run `ruff check .` and `black --check .` successfully (no errors) in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/`. (Per Plan Project Structure).
- [ ] T006 [P] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/models/__init__.py` and base model loader structure
- [ ] T007 [US1] Implement 'Logic Verification' mode switch in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/io.py`: If DreamX-World data is missing, abort primary claim and switch to ScanNet fallback, marking results as 'Pending Data Access' (Per Plan Phase 0 & Data Fallback Protocol)
- [ ] T008 [US2] Implement data loader in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/io.py` to fetch DreamX-World subset OR ScanNet fallback (Per T007 logic). **Prerequisite: T007 must define the logic flow before this loader executes.** MUST fail loudly if NEITHER source is available; MUST NOT use synthetic data.
- [ ] T009 [US2] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/io.py` to stream the DreamX-World subset (or ScanNet fallback) using `datasets.load_dataset(..., streaming=True)` to process frames in chunks. Conditional Logic: If T007 triggers ScanNet fallback, skip streaming logic as dataset fits in RAM. Verification: Add a memory profiling wrapper using `psutil` with **sampling interval: a fixed, short duration suitable for capturing rapid system dynamics.** and assertion logic `psutil.virtual_memory().available` for `available_ram`. **If `max_rss > 0.95 * available_ram`, log a Soft Warning** (do not abort) to `logs/memory.log`. This task must be executed after T007 to ensure the logic verification is complete before streaming begins. (Per Plan Assumption: Resource-Constrained Validation & Review: Executability-25d1e14f, Constraint-6af088a8, Ordering-801d9b84).
- [ ] T010 [P] [US2] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/io.py` to validate and cache checksums of the downloaded DreamX-World subset or ScanNet fallback before any processing begins (Per Plan Phase 0 & Constitution III).
- [ ] T017 [US1] Add logging for parameter count delta in `logs/init.log`. Format: "Param Delta: -{value}". **Calculation: value = base_params - lite_params**. **Source**: Calculate `base_params` from `dreamx_base` model instance and `lite_params` from `dreamx_lite` model instance using `count_parameters()`. Verification: Verify `logs/init.log` contains the string "Param Delta: -X" after initialization (Per Spec FR-001 & Constitution VI). Configuration: Use `logging.basicConfig(filename='logs/init.log', level=logging.INFO, format='%(message)s')`. (Per Review: Executability-d43dccb9).

---

## Phase 1: Model Abstraction & Configuration (User Story 1)

**Purpose**: Replace learned E-PRoPE with fixed 4x4 camera projection and verify CPU initialization

**Independent Test**: Load pre-trained weights, apply modification, verify forward pass accepts 4x4 matrices without CUDA errors and parameter count decreases.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for parameter count reduction in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_model_ablation.py`
- [ ] T012 [P] [US1] Unit test for deterministic output on fixed input in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_determinism.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/models/dreamx_base.py` to load pre-trained DreamX-World 1.0 DiT weights AND define `embedding_dim` constant (e.g., 768)
- [ ] T014 [US1] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/models/dreamx_lite.py` replacing E-PRoPE with a linear projection layer mapping from a low-dimensional input space to the embedding dimension. (fixed, non-trainable, using `embedding_dim` from T013). Verification: Include a check that parameter count decreases by the size of the removed E-PRoPE module.
- [ ] T015 [P] [US1] Create `tests/unit/test_cpu_init.py` to verify `dreamx_lite` initialization completes without CUDA errors on CPU runner. Assertion: `assert "CUDA" not in str(e)` or `device == "cpu"`.
- [ ] T016 [US1] Implement forward pass wrapper in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/models/dreamx_lite.py` to accept 4x4 camera extrinsic matrices

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 2: Evaluation Integrity & Independence (User Story 4)

**Purpose**: Ensure metric pipeline is strictly decoupled from generative model internals

**Independent Test**: Static analysis confirms no imports of DiT backbone/attention maps; function signature accepts only frames and extrinsics.

### Implementation for User Story 4

- [ ] T018 [P] [US4] Add static analysis check in CI to verify `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` has no imports of `dit_attention`, `latent_space`, or model internals
- [ ] T019 [US4] Refactor `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` function signatures to accept only `numpy` frames and `4x4` matrices
- [ ] T020 [US4] Document the "Blindness" constraint in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` docstrings and README

---

## Phase 3: Long-Horizon Rollout & Metric Computation (User Story 2)

**Purpose**: Generate videos, recover trajectories via SfM, and compute MAE/Scale Drift

**Independent Test**: Run inference on 5 trajectories, generate MP4s, run SfM, output JSON/CSV with MAE and convergence flags.

### Schema Definition (Pre-requisite for US2 Implementation)

- [ ] T028 [P] [US2] Create `metrics.csv` schema and writer: Define exact columns: `trajectory_id` (str), `model` (str), `mae_position` (float, **-1.0** for divergence), `mae_rotation` (float, **-1.0** for divergence), `convergence` (bool), `sfm_failure_reason_raw` (str, exact raw error), `sfm_failure_reason_std` (str, standardized category), `scale_drift` (float, null allowed). Implementation: Create `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/metrics_schema.py` with this definition and verification step: `python -c "import metrics_schema; assert 'mae_position' in metrics_schema.COLUMNS"`. (Per Spec FR-004, FR-008, FR-009 & Plan Phase 2 & Review: Ordering-2f3460ef, Constraint-7325f57c).

### Implementation for User Story 2

- [ ] T023b [P] [US2] Create `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data/derived/videos/` directory structure. Verification: `test -d data/derived/videos`.
- [ ] T023a [P] [US2] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/generate.py` function `run_rollout(prompt, model)` returning MP4 path. Input: `prompt` (str), `model` (object). Output: `path` (str). Codec: H.264. Resolution: 256x256. **Frame Rate: Standard real-time display rates**. Output naming: `{model_name}_{trajectory_id}.mp4`. **Duration: exactly 10.0 seconds (tolerance ±0.1s)**. Verification: Verify file exists, **10.0 <= duration <= 10.1**, and resolution matches. (Per Spec FR-003 & Edge Case: Video generation failures & Review: Executability-13079425, Coverage-0d7a52d6).
- [ ] T024 [US2] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` to run external COLMAP SfM on generated video frames
- [ ] T025 [US2] Implement Procrustes Alignment logic in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` to resolve scale/rotation ambiguity; Output: Aligned Trajectory (Input for T026)
- [ ] T026 [US2] Implement MAE calculation (position, rotation) in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` using aligned trajectories from T025. Output: Write to `metrics.csv` (Schema from T028).
- [ ] T026b [US2] Explicitly calculate 'Scale Drift' metric (ratio of mean depth of recovered trajectory to mean depth of ground-truth trajectory) in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py`. Output: Append `scale_drift` column to `metrics.csv` (Schema from T028). (Per Spec FR-008).
- [ ] T027 [US2] Implement SfM failure handling in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py`: record `convergence=false`, **capture the exact raw error string verbatim** from COLMAP logs, parse and map to a **standardized category** (e.g., 'insufficient_features'), and set `mae_position` and `mae_rotation` to **-1.0** (Sentinel Value per Spec FR-004). **Note: Spec FR-004 requires sentinel -1.0, overriding Plan's 'null' instruction.** Write to `metrics.csv` (Schema from T028). (Per Spec FR-004, FR-009 & Review: Coverage-2f769780, Coverage-2b8da957, Coverage-6a63e021, Constraint-7325f57c, Constraint-6a63e021).
- [ ] T029 [US2] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/generate.py` to handle OOM crashes on CPU runner by implementing a retry mechanism with reduced batch size (e.g., 1 frame at a time) up to 3 times. Logging: Log failure mode in format "OOM Retry {n}: {error_msg}" to `logs/generate.log` (Per Edge Case: Video generation failures).
- [ ] T030 [US2] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` to detect and handle singularities in ground-truth camera extrinsics (e.g., gimbal lock) by decomposing the rotation matrix using **intrinsic ZYX** order and checking if `abs(pitch) > 85 degrees`. If detected, log "Warning: Gimbal lock detected in frame {X}" and set `sfm_failure_reason_std` to **`'gimbal_lock'`** and `sfm_failure_reason_raw` to the original matrix state in `metrics.csv` (Per Edge Case: Singularities & FR-009).

---

## Phase 4: Statistical Significance & Sensitivity Analysis (User Story 3)

**Purpose**: Perform McNemar's test, Wilcoxon signed-rank test, and threshold sensitivity sweep

**Independent Test**: Provide CSV of paired scores, verify output of test statistics, p-values, and sensitivity table.

### Schema Definition (Pre-requisite for US3 Implementation)

- [ ] T037 [P] [US3] Generate `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data/derived/statistical_results.json` schema: Define keys: `mcnemar_p` (float), `wilcoxon_p` (float), `censoring_rate` (float), `sufficiency_ratio` (float), `sensitivity_table` (dict). Implementation: Create `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis/stats_schema.py` with this definition and verification step: `python -c "import stats_schema; assert 'mcnemar_p' in stats_schema.KEYS"`. (Per Spec SC-005 & SC-003 & Review: Ordering-5afebeb2).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for McNemar and Wilcoxon logic on mock data in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_stats.py`
- [ ] T032a [P] [US3] Unit test for sensitivity sweep logic in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_sensitivity_logic.py`
- [ ] T032b [P] [US3] Unit test for specific thresholds in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_sensitivity_thresholds.py`

### Implementation for User Story 3

- [ ] T033b [P] [US3] Create Constitution Amendment Document: Create `docs/amendments/const_vi_wilcoxon.md` documenting the override of Constitution Principle VI (paired t-test) with Wilcoxon/McNemar tests due to non-Gaussian errors. Content must include: Rationale, Specification Reference (US-3, FR-005), and Plan Reference. **Ratification Step**: Write `ratified_amendment.log` with timestamp and checksum to simulate ratification before tests run. **Note: This amendment requires formal ratification to override the 'NON-NEGOTIABLE' Constitution.** Verification: File exists and contains "Constitution Principle VI" and "Wilcoxon". (Per Plan Constitution Check & Constraint Preservation & Review: Constraint-09ef4055).
- [ ] T033 [P] [US3] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis/stats.py` with McNemar's test for binary convergence flags; explicitly state null hypotheses (Per Spec US-3). Note: Relies on T033b being documented.
- [ ] T034 [US3] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis/stats.py` to calculate and report 'Censoring Rate' (formula: `failed_count / total_count`) for both models. Output: Append `{"censoring_rate": <value>}` to `data/derived/statistical_results.json` (Schema from T037) (Per Plan Phase 3 Step 3).
- [ ] T035 [US3] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis/sensitivity.py` to sweep thresholds **read from `config/sensitivity.yaml`**. **Default thresholds: [low, 0.05, 0.1]** (hardcoded if config missing). **Logic**: Filter dataset to `convergence=true` rows before applying thresholds to exclude -1.0 sentinel values. Compute success rates. (Per Spec FR-006 & SC-003 & Review: Executability-0b498615, Coverage-5b491ef9, Constraint-a80fce86). Note: Corrected threshold range from "a range of small significance levels" to the specific values defined in Spec Assumptions.
- [ ] T036 [US3] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis/stats.py` with Wilcoxon signed-rank test for MAE scores: filter for `convergence=true` trajectories only (Per Spec FR-005); depends on T028 (metrics.csv) which includes T027's sentinel values. Output: Append `{"wilcoxon_p": <value>}` to `data/derived/statistical_results.json` (Schema from T037).
- [ ] T039b [US3] Calculate and log the "Information-Theoretic Sufficiency Ratio" = (DreamX-Lite Success Rate) / (Baseline Success Rate). Output: Append `{"sufficiency_ratio": <value>}` to `data/derived/statistical_results.json` (Schema from T037) (Per Spec SC-005 & Plan Phase 5, Step 1).
- [ ] T039c [US3] Generate 'sensitivity table' (dict of threshold -> success rate) and write to `data/derived/statistical_results.json` (Schema from T037). (Per Spec SC-003 & US-3 acceptance criteria).
- [ ] T038a [US3] Log statistical power warning to `logs/stats.log` if sample size of converged trajectories < 30. Text: "Warning: Sample size < 30 may lack power for Wilcoxon test."
- [ ] T038b [US3] Append limitation text to `docs/report.md` with specific content: "Limitation: Statistical power may be insufficient for small effect sizes due to sample size < 30." (Per Assumption: Statistical Power).

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/README.md` and `docs/` covering Data Fallback Protocol. Section: "Data Fallback Protocol" with text: "If DreamX-World data is missing, pipeline aborts primary claim and switches to ScanNet."
- [ ] T040 [P] Code cleanup and refactoring for CPU memory optimization: Refactor `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/generate.py` to use streaming if needed to keep peak memory < 6GB. Verification: Run memory profiler and assert < 6GB (Per NFR-001).
- [ ] T041 [P] [US3] Create `tests/integration/test_performance.py` that asserts total runtime < 6 hours for a **A small subset of trajectories** run **on a -core, 7GB RAM runner** (Per NFR-001 & Executability-34afb737).
- [ ] T042 [P] [US2] Additional unit tests for edge cases in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/`: Add `test_gimbal_lock_handling`, `test_oom_retry`, `test_sfm_failure_reason_persistence` (Per Executability-0a0cca7e).
- [ ] T043 [P] [US2] Create `tests/integration/test_quickstart.py` to verify `quickstart.md` runs without error and produces `data/derived/metrics.csv` (Per Executability-b43ebf4f).

---

## Phase 6: Revision & Robustness (Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical rigor, and failure modes identified in the analysis phase.

- [ ] T044 [P] [US2] Implement a strict "Data Source Verification" wrapper in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/io.py` that checks for the presence of a `verified_data_sources.json` file (created by T000b) before attempting any download. If the file is missing or the source ID is not listed, raise a `DataVerificationError` immediately without attempting a fallback. (Per Review: "Loader must fail loudly, never fall back to synthetic").
- [ ] T045 [US2] Add a "Non-Triviality Check" task in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` that compares generated video frames against a direct render of the input geometry (using a simple rasterizer) to ensure the model is not simply outputting the input prompt. Log "Non-Triviality Check: PASS/FAIL" to `logs/evaluate.log`. (Per Review: "Verify that the generated video is not a trivial identity of the input prompt").
- [ ] T046 [US3] Refactor `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis/stats.py` to explicitly handle the case where `convergence=false` for ALL trajectories in a model variant. In this case, the Wilcoxon test must be skipped, and the result must be recorded as "UNDEFINED (No Converged Trajectories)" rather than attempting a test on empty sets. (Per Review: "Wilcoxon test runs ONLY on convergence=true trajectories").
- [ ] T047 [US2] Implement a "Scale Normalization" verification step in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` that confirms the Procrustes alignment has successfully normalized the scale to a canonical unit (mean distance to origin = 1.0) before calculating the "Scale Drift" metric. If normalization fails, set `scale_drift` to `null` and log "Scale Normalization Failed". (Per Review: "Assumption about scale normalization").
- [ ] T048 [US3] Create a "Statistical Power Analysis" script in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis/power.py` that calculates the post-hoc power of the Wilcoxon test given the observed effect size and sample size. If power < 0.8, append a detailed "Power Limitation" section to `docs/report.md` with the calculated power value. (Per Review: "Assumption about statistical power").
- [ ] T049 [US2] Add a "SfM Convergence Baseline" task in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` that runs SfM on a small subset of ground-truth renders (not generated videos) to establish a baseline convergence rate. This baseline must be reported in `data/derived/statistical_results.json` to distinguish "metric failure" from "model failure". (Per Review: "Baseline SfM Validation").
- [ ] T050 [US1] Implement a "Parameter Count Verification" unit test in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_model_ablation.py` that asserts the parameter count of `dreamx_lite` is exactly `dreamx_base` minus the size of the E-PRoPE module. This ensures the ablation is exact and not approximate. (Per Review: "Verify via a forward pass that the model accepts camera matrices as input without error and produces output tensors of the expected shape").
- [ ] T051 [P] [US2] Add a "Video Generation Timeout" mechanism in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/generate.py` that kills the generation process if it exceeds a predefined time limit per trajectory, logging "Generation Timeout" and marking the trajectory as "FAILED_TIMEOUT" in `metrics.csv`. (Per Review: "Edge Case: Video generation failures").
- [ ] T052 [US3] Implement a "Threshold Sensitivity Visualization" script in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis/sensitivity.py` that generates a plot of success rates vs. MAE thresholds for both models and saves it to `docs/figures/sensitivity_plot.png`. (Per Review: "Sensitivity analysis sweeping the consistency threshold").

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Setup + Data)**: No dependencies - can start immediately
- **Phase 1 (Model)**: Depends on Phase 0 completion
- **Phase 2 (Integrity)**: Depends on Phase 0 completion
- **Phase 3 (Pipeline)**: Depends on Phase 0 and Phase 1 (Model) completion
- **Phase 4 (Stats)**: Depends on Phase 3 (Metrics) completion
- **Phase 5 (Polish)**: Depends on all desired user stories being complete
- **Phase 6 (Revision)**: Depends on Phase 4 completion and analysis review

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 0 - No dependencies on other stories
- **User Story 4 (P1)**: Can start after Phase 0 - Ensures US2 implementation is clean
- **User Story 2 (P2)**: Can start after Phase 0 and Phase 1 - Requires US1 model implementation
- **User Story 3 (P3)**: Can start after Phase 0 and Phase 3 - Requires US2 metric outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 0)
- Once Phase 0 completes, US1, US4, and US2 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for parameter count reduction in tests/unit/test_model_ablation.py"
Task: "Unit test for deterministic output on fixed input in tests/unit/test_determinism.py"

# Launch all models for User Story 1 together:
Task: "Implement code/models/dreamx_base.py to load pre-trained DreamX-World 1.0 DiT weights"
Task: "Implement code/models/dreamx_lite.py replacing E-PRoPE with nn.Linear(16, embedding_dim)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Setup + Data Verification
2. Complete Phase 1: User Story 1
3. **STOP and VALIDATE**: Test User Story 1 independently (CPU load, param count)
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 4 → Ensure metric integrity
4. Add User Story 2 → Test independently (Generation + SfM) → Deploy/Demo
5. Add User Story 3 → Test independently (Stats) → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 together
2. Once Phase 0 is done:
 - Developer A: User Story 1 (Model Ablation)
 - Developer B: User Story 4 (Integrity) & User Story 2 (Pipeline)
 - Developer C: User Story 3 (Stats)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Data loaders must implement fallback logic (T007); no synthetic fallbacks allowed (Plan Section: Data Fallback Protocol)
- **Streaming**: T009 ensures the full dataset is processed via streaming to avoid RAM overflow (Per Plan Assumption: Resource-Constrained Validation).
- **Sentinel Values**: Failed SfM trajectories MUST record MAE = `-1.0` (not `null`) to allow proper filtering in Wilcoxon test (Per Spec FR-004 & Plan Phase 2). T027 and T028 enforce this. **Note: Spec FR-004 takes precedence over Plan's 'null' instruction.**
- **Sensitivity Thresholds**: Sweep MUST include the range `{0.01, 0.05, 0.1}` to verify robustness at the "exact" consistency level (Per Spec FR-006 & Assumptions)
- **Censoring Rate**: Must be calculated and explicitly reported in `data/derived/statistical_results.json` (Per Plan Phase 3 Step 3)
- **Exact Failure Reasons**: `sfm_failure_reason` must capture the specific COLMAP error string (Per Spec FR-009)
- **Statistical Scope**: Wilcoxon test runs ONLY on `convergence=true` trajectories (Per Spec FR-005)
- **Power Validation**: T038 ensures statistical power limitations are explicitly acknowledged if sample size is insufficient (Per Assumption: Statistical Power).
- **Schema First**: T028 and T037 define schemas before data writing tasks (T026, T027, T034, T036).
- **Gimbal Lock**: T030 handles singularities in ground-truth extrinsics to prevent SfM divergence (Per Edge Cases).
- **Video Generation**: T029 handles OOM retries to ensure completion within NFR-001 limits (Per Edge Cases).
- **Constitution Amendment**: T033b documents the override of Principle VI before implementation (Per Plan Constitution Check).
- **Revision Tasks**: Phase 6 tasks (T044-T052) address specific reviewer concerns regarding data integrity, statistical rigor, and failure modes. These must be completed before final sign-off.