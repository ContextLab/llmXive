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

- [ ] T001 [P] Initialize Project Structure: Create the full nested directory tree `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/` including `data/raw/`, `data/derived/`, `data/derived/videos/`, `code/`, `code/models/`, `code/pipeline/`, `code/analysis/`, `code/utils/`, `tests/unit/`, `tests/integration/`, `logs/`, `docs/`, `config/`. Verification: Run `ls -R projects/PROJ-llmxive-follow-up-extending-dreamx-world/` and confirm the following 15 directories exist: `data/raw`, `data/derived`, `data/derived/videos`, `code`, `code/models`, `code/pipeline`, `code/analysis`, `code/utils`, `tests/unit`, `tests/integration`, `logs`, `docs`, `config`, `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world`, `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data` (Per Plan Project Structure).
- [ ] T001b [P] Verify File Manifest: Create empty placeholder files for `requirements.txt`, `README.md`, `pyproject.toml`, `.ruff.toml`, `code/__init__.py`, `code/models/__init__.py`, `code/pipeline/__init__.py`, `code/analysis/__init__.py`, `code/utils/__init__.py`, `tests/__init__.py`. Verification: Run `test -f projects/PROJ-llmxive-follow-up-extending-dreamx-world/requirements.txt && test -f projects/PROJ-llmxive-follow-up-extending-dreamx-world/README.md &&...` (check all required project files exist) (Per Plan Project Structure).
- [X] T002 [P] Initialize Python 3.x+ project with `requirements.txt` (torch CPU, transformers, datasets, colmap, scipy, pandas, numpy, opencv-python, scikit-learn) in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/`
- [X] T003 [US1] Configure environment variables and random seed fixation in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/config.py` (Sequential: Global seed must be set once)
- [X] T004 [P] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/io.py` for data loading, checksumming, and logging
- [ ] T005 [P] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections, and `.ruff.toml` config. Verification: Run `ruff check.` and `black --check.` successfully (no errors) (Per Plan Project Structure).
- [X] T006 [P] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/models/__init__.py` and base model loader structure
- [X] T007 [US1] Implement 'Logic Verification' mode switch in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/io.py`: If DreamX-World data is missing, abort primary claim and switch to ScanNet fallback, marking results as 'Pending Data Access' (Per Plan Phase 0 & Data Fallback Protocol)
- [X] T008 [US2] Implement data loader in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/io.py` to fetch DreamX-World subset OR ScanNet fallback (Per T007 logic): MUST fail loudly if NEITHER source is available; MUST NOT use synthetic data
- [X] T009 [US2] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/io.py` to stream the DreamX-World subset (or ScanNet fallback) using `datasets.load_dataset(..., streaming=True)` to process frames in chunks. Conditional Logic: If T007 triggers ScanNet fallback, skip streaming logic as dataset fits in RAM. Verification: Add a memory profiling wrapper using `psutil` (sampling interval at a fine-grained temporal resolution) that asserts `max_rss < 0.9 * available_ram` and fails the test if exceeded (Per Plan Assumption: Resource-Constrained Validation).
- [X] T010 [P] [US2] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils/io.py` to validate and cache checksums of the downloaded DreamX-World subset or ScanNet fallback before any processing begins (Per Plan Phase 0 & Constitution III).

---

## Phase 1: Model Abstraction & Configuration (User Story 1)

**Purpose**: Replace learned E-PRoPE with fixed 4x4 camera projection and verify CPU initialization

**Independent Test**: Load pre-trained weights, apply modification, verify forward pass accepts 4x4 matrices without CUDA errors and parameter count decreases.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Unit test for parameter count reduction in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_model_ablation.py`
- [X] T012 [P] [US1] Unit test for deterministic output on fixed input in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_determinism.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/models/dreamx_base.py` to load pre-trained DreamX-World 1.0 DiT weights AND define `embedding_dim` constant (e.g., 768)
- [X] T014 [US1] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/models/dreamx_lite.py` replacing E-PRoPE with a linear projection layer mapping from a low-dimensional input space to the embedding dimension. (fixed, non-trainable, using `embedding_dim` from T013). Verification: Include a check that parameter count decreases by the size of the removed E-PRoPE module.
- [X] T015 [P] [US1] Create `tests/unit/test_cpu_init.py` to verify `dreamx_lite` initialization completes without CUDA errors on CPU runner. Assertion: `assert "CUDA" not in str(e)` or `device == "cpu"`.
- [X] T016 [US1] Implement forward pass wrapper in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/models/dreamx_lite.py` to accept 4x4 camera extrinsic matrices
- [ ] T017 [US1] Add logging for parameter count delta in `logs/init.log`. Format: "Param Delta: -{value}". Verification: Verify `logs/init.log` contains the string "Param Delta: -X" after initialization (Per Spec FR-001 & Constitution VI). Configuration: Use `logging.basicConfig(filename='logs/init.log', level=logging.INFO, format='%(message)s')`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 2: Evaluation Integrity & Independence (User Story 4)

**Purpose**: Ensure metric pipeline is strictly decoupled from generative model internals

**Independent Test**: Static analysis confirms no imports of DiT backbone/attention maps; function signature accepts only frames and extrinsics.

### Implementation for User Story 4

- [X] T018 [P] [US4] Add static analysis check in CI to verify `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` has no imports of `dit_attention`, `latent_space`, or model internals
- [X] T019 [US4] Refactor `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` function signatures to accept only `numpy` frames and `4x4` matrices
- [X] T020 [US4] Document the "Blindness" constraint in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` docstrings and README

---

## Phase 3: Long-Horizon Rollout & Metric Computation (User Story 2)

**Purpose**: Generate videos, recover trajectories via SfM, and compute MAE/Scale Drift

**Independent Test**: Run inference on 5 trajectories, generate MP4s, run SfM, output JSON/CSV with MAE and convergence flags.

### Schema Definition (Pre-requisite for US2 Implementation)

- [ ] T028 [P] [US2] Create `metrics.csv` schema and writer: Define exact columns: `trajectory_id` (str), `model` (str), `mae_position` (float, null allowed), `mae_rotation` (float, null allowed), `convergence` (bool), `sfm_failure_reason` (str, empty if success). Implementation: Create `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data/derived/metrics.csv` with this header row. (Per Spec FR-004 & Plan Phase 2).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for metric independence (no internal model imports) in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_metrics.py`
- [X] T022a [P] [US2] Unit test for video generation in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_video_gen.py`
- [X] T022b [P] [US2] Unit test for SfM recovery in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_sfm_recovery.py`
- [X] T022c [P] [US2] Unit test for metric calculation in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_metric_calc.py`

### Implementation for User Story 2

- [X] T023a [P] [US2] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/generate.py` function `run_rollout(prompt, model)` returning MP4 path. Input: `prompt` (str), `model` (object). Output: `path` (str). Codec: H.264. <!-- FAILED: unspecified -->
- [ ] T023b [P] [US2] Create `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data/derived/videos/` directory structure.
- [X] T024 [US2] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` to run external COLMAP SfM on generated video frames
- [X] T025 [US2] Implement Procrustes Alignment logic in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` to resolve scale/rotation ambiguity; Output: Aligned Trajectory (Input for T026)
- [X] T026 [US2] Implement MAE calculation (position, rotation) in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` using aligned trajectories from T025. Output: Write to `metrics.csv` (Schema from T028).
- [X] T026b [US2] Explicitly calculate 'Scale Drift' metric (ratio of mean depth of recovered trajectory to mean depth of ground-truth trajectory) in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py`. Output: Append `scale_drift` column to `metrics.csv` (Schema from T028). (Per Spec FR-008).
- [X] T027 [US2] Implement SfM failure handling in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py`: record `convergence=false`, parse COLMAP logs to extract the **exact failure reason** (e.g., 'insufficient_features', 'optimization_divergence') using regex `r"(ERROR|WARNING).*?(insufficient_features|optimization_divergence|sparse_reconstruction)"` and mapping to standardized strings, and set `mae_position` and `mae_rotation` to **`null`** (Per Spec FR-004 & Plan Phase 2). Write to `metrics.csv` (Schema from T028).
- [ ] T027b [US2] Reconcile Spec FR-004 'sentinel value' requirement with Plan 'null' convention: Update `metrics.csv` schema and documentation to explicitly state that `null` is the accepted value for divergence to ensure statistical validity, and log this exception. (Per Plan Phase 2 & Spec FR-004).
- [X] T029 [US2] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/generate.py` to handle OOM crashes on CPU runner by implementing a retry mechanism with reduced batch size (e.g., 1 frame at a time) up to 3 times. Logging: Log failure mode in format "OOM Retry {n}: {error_msg}" to `logs/generate.log` (Per Edge Case: Video generation failures).
- [ ] T030 [US2] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/evaluate.py` to detect and handle singularities in ground-truth camera extrinsics (e.g., gimbal lock) by decomposing the rotation matrix using **intrinsic ZYX** order and checking if `abs(pitch) > 85 degrees`. If detected, log "Warning: Gimbal lock detected in frame {X}" and set `sfm_failure_reason` to "gimbal_lock" in `metrics.csv` (Per Edge Case: Singularities & FR-009).

---

## Phase 4: Statistical Significance & Sensitivity Analysis (User Story 3)

**Purpose**: Perform McNemar's test, Wilcoxon signed-rank test, and threshold sensitivity sweep

**Independent Test**: Provide CSV of paired scores, verify output of test statistics, p-values, and sensitivity table.

### Schema Definition (Pre-requisite for US3 Implementation)

- [ ] T037 [P] [US3] Generate `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data/derived/statistical_results.json` schema: Define keys: `mcnemar_p` (float), `wilcoxon_p` (float), `censoring_rate` (float), `sufficiency_ratio` (float), `sensitivity_table` (dict). (Per Spec SC-005 & SC-003).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for McNemar and Wilcoxon logic on mock data in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_stats.py`
- [ ] T032a [P] [US3] Unit test for sensitivity sweep logic in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_sensitivity_logic.py`
- [ ] T032b [P] [US3] Unit test for specific thresholds in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/test_sensitivity_thresholds.py`

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis/stats.py` with McNemar's test for binary convergence flags; explicitly state null hypotheses (Per Spec US-3)
- [ ] T033b [P] [US3] Submit Constitution Amendment Request: Document the override of Constitution Principle VI (paired t-test) with Wilcoxon/McNemar tests due to non-Gaussian errors, and propose the amendment to the Constitution. (Per Plan Constitution Check & Constraint Preservation).
- [ ] T034 [US3] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis/stats.py` to calculate and report 'Censoring Rate' (formula: `failed_count / total_count`) for both models. Output: Append `{"censoring_rate": <value>}` to `data/derived/statistical_results.json` (Schema from T037) (Per Plan Phase 3 Step 3).
- [ ] T035 [US3] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis/sensitivity.py` to sweep thresholds **read from `config/sensitivity.yaml`** (default {a range of small significance levels}) and compute success rates (Per Spec FR-006 & SC-003)
- [ ] T036 [US3] Implement `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis/stats.py` with Wilcoxon signed-rank test for MAE scores: filter for `convergence=true` trajectories only (Per Spec FR-005); depends on T028 (metrics.csv) which includes T027's null values. Output: Append `{"wilcoxon_p": <value>}` to `data/derived/statistical_results.json` (Schema from T037).
- [ ] T039b [US3] Calculate and log the "Information-Theoretic Sufficiency Ratio" = (DreamX-Lite Success Rate) / (Baseline Success Rate). Output: Append `{"sufficiency_ratio": <value>}` to `data/derived/statistical_results.json` (Schema from T037) (Per Spec SC-005 & Plan Phase 5, Step 1).
- [ ] T039c [US3] Generate 'sensitivity table' (dict of threshold -> success rate) and write to `data/derived/statistical_results.json` (Schema from T037). (Per Spec SC-003 & US-3 acceptance criteria).
- [ ] T038a [US3] Log statistical power warning to `logs/stats.log` if sample size of converged trajectories < 30. Text: "Warning: Sample size < 30 may lack power for Wilcoxon test."
- [ ] T038b [US3] Append limitation text to `docs/report.md` with specific content: "Limitation: Statistical power may be insufficient for small effect sizes due to sample size < 30." (Per Assumption: Statistical Power).

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/README.md` and `docs/` covering Data Fallback Protocol. Section: "Data Fallback Protocol" with text: "If DreamX-World data is missing, pipeline aborts primary claim and switches to ScanNet."
- [ ] T040 [P] Code cleanup and refactoring for CPU memory optimization: Refactor `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline/generate.py` to use streaming if needed to keep peak memory < 6GB. Verification: Run memory profiler and assert < 6GB (Per NFR-001).
- [ ] T041 [P] [US3] Create `tests/integration/test_performance.py` that asserts total runtime < 6 hours for a **-trajectory subset** run (Per NFR-001 & Executability-12d00d3a).
- [ ] T042 [P] [US2] Additional unit tests for edge cases in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit/`: Add `test_gimbal_lock_handling`, `test_oom_retry`, `test_sfm_failure_reason_persistence` (Per Executability-0a0cca7e).
- [ ] T043 [P] [US2] Create `tests/integration/test_quickstart.py` to verify `quickstart.md` runs without error and produces `data/derived/metrics.csv` (Per Executability-b43ebf4f).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Setup + Data)**: No dependencies - can start immediately
- **Phase 1 (Model)**: Depends on Phase 0 completion
- **Phase 2 (Integrity)**: Depends on Phase 0 completion
- **Phase 3 (Pipeline)**: Depends on Phase 0 and Phase 1 (Model) completion
- **Phase 4 (Stats)**: Depends on Phase 3 (Metrics) completion
- **Phase 5 (Polish)**: Depends on all desired user stories being complete

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
- **Null Values**: Failed SfM trajectories MUST record MAE = `null` (not -1.0) to allow proper filtering in Wilcoxon test (Per Spec FR-004 & Plan Phase 2)
- **Sensitivity Thresholds**: Sweep MUST include a range of small learning rates. to verify robustness at the "exact" consistency level (Per Spec FR-006)
- **Censoring Rate**: Must be calculated and explicitly reported in `data/derived/statistical_results.json` (Per Plan Phase 3 Step 3)
- **Exact Failure Reasons**: `sfm_failure_reason` must capture the specific COLMAP error string (Per Spec FR-009)
- **Statistical Scope**: Wilcoxon test runs ONLY on `convergence=true` trajectories (Per Spec FR-005)
- **Power Validation**: T038 ensures statistical power limitations are explicitly acknowledged if sample size is insufficient (Per Assumption: Statistical Power).
- **Schema First**: T028 and T037 define schemas before data writing tasks (T026, T027, T034, T036).