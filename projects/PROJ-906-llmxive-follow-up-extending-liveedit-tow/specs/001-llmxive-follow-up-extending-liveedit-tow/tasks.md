# Tasks: llmXive follow-up: extending "LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing"

**Input**: Design documents from `/specs/001-optical-flow-temporal-coherence/`
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

- [X] T001a Create project directory structure: `projects/PROJ-<ID>-llmxive-follow-up-extending-liveedit-tow/` with subdirectories `data/raw`, `data/flow`, `data/metrics`, `code`, `code/data`, `code/models`, `code/metrics`, `code/analysis`, `tests/contract`, `tests/unit`, `results`. **Deliverable**: Create directories. **Verify**: Run `ls projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/` and confirm directories exist.
- [X] T001b Create `scripts/init_structure.sh` that generates the directory structure defined in T001a. **Verify**: Run `bash scripts/init_structure.sh` and confirm directories exist.
- [X] T001c Create initial file scaffolding: `code/__init__.py`, `code/config.py`, `tests/__init__.py`, `results/.gitkeep`. **Verify**: Run `ls code/__init__.py code/config.py tests/__init__.py results/.gitkeep` and confirm files exist.
- [X] T002a [P] Create `code/requirements.txt` containing the following pinned dependencies: torch>=2.0.0 (cpu), diffusers, opencv-python, scikit-learn, pandas, numpy, datasets, ruptures. **Verify**: Run `ls code/requirements.txt` and confirm file exists.
- [X] T002b [P] Verify dependencies in `code/requirements.txt` are pinned. **Verify**: Run `pytest tests/unit/test_requirements.py::test_dependencies_pinned`.
- [X] T003a [P] Configure linting (ruff) tool: Create `pyproject.toml` with `[tool.ruff]` section. **Verify**: Run `ls pyproject.toml` and confirm section exists.
- [X] T003b [P] Verify ruff configuration. **Verify**: Run `pytest tests/unit/test_linting.py::test_ruff_config_valid`.
- [X] T003c [P] Configure formatting (black) tool: Create `pyproject.toml` with `[tool.black]` section. **Verify**: Run `ls pyproject.toml` and confirm section exists.
- [X] T003d [P] Verify black configuration. **Verify**: Run `pytest tests/unit/test_linting.py::test_black_config_valid`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Note**: T009a must complete before T009 due to resource contention.

- [X] T004 Create base data models (VideoClip, MetricRecord, AnalysisResult) in `code/data/models.py`. **Details**: Define classes `VideoClip`, `MetricRecord`, `AnalysisResult` with attributes: `VideoClip` (id, path, motion_category, flow_field, mask), `MetricRecord` (clip_id, model_variant, peak_memory, fps, ssim, gradient_variance, flow_magnitude, invalid_flow), `AnalysisResult` (pvalue, regression_coeff, threshold, sensitivity_table). **Verify**: Run `pytest tests/unit/test_models.py`.
- [X] T005 [P] Setup experiment configuration manager in `code/config.py` with explicit `SENSITIVITY_CUTOFFS` constant initialized to {0.01, 0.05, 0.1} (for FR-007 sensitivity analysis) and `STRATIFICATION_THRESHOLDS` constant initialized to {0.5, 5.0} (Plan.md "Critical Methodological Updates") plus random seeds. **Verify**: Run `pytest tests/unit/test_config.py`.
- [X] T006a [P] Implement robust logging infrastructure in `code/utils/logger.py`. **Details**: Implement `get_logger()` function and log rotation. **Verify**: Run `pytest tests/unit/test_logger.py::test_logger_init`.
- [X] T006b [P] Implement checkpointing infrastructure in `code/utils/checkpoint.py` (handles CI limit, resume capability). **Details**: Implement `save_state()` and `load_state()` functions in `checkpoint.py` that serialize state to `data/checkpoints/{run_id}.json`. **Verify**: Run `pytest tests/unit/test_checkpoint.py::test_save_load_cycle`.
- [X] T007a [P] Create dataset schema validator in `specs/001-optical-flow-temporal-coherence/contracts/dataset_schema.py` using `pydantic`. **Verify**: Run `pytest tests/contract/test_dataset_schema.py::test_dataset_schema_load`.
- [X] T007b [P] Create metric schema validator in `specs/001-optical-flow-temporal-coherence/contracts/metric_schema.py` using `pydantic`. **Verify**: Run `pytest tests/contract/test_metric_schema.py::test_metric_schema_load`.
- [X] T007c [P] Create analysis schema validator in `specs/001-optical-flow-temporal-coherence/contracts/analysis_schema.py` using `pydantic`. **Verify**: Run `pytest tests/contract/test_analysis_schema.py::test_analysis_schema_load`.
- [X] T008 [P] Implement memory profiling wrapper in `code/metrics/resource.py` to track peak RAM usage per clip. **Verify**: Run `pytest tests/unit/test_metrics_resource.py::test_memory_tracking`.
- [X] T012 [P] [Foundational] Implement dataset downloader in `code/data/downloader.py` to fetch DAVIS/YouTube-VOS clips via `datasets.load_dataset` with streaming; ensure it fails loudly on missing sources (no synthetic fallback). **Details**: Raise `ValueError` with message "Dataset source missing" if HuggingFace dataset not found. **Verify**: Run `pytest tests/unit/test_downloader.py::test_download_fails_loudly`.
- [ ] T009a [P] [Foundational] Implement lightweight flow magnitude extraction in `code/data/flow.py` (or separate `code/data/flow_mag.py`) to compute mean flow magnitude for stratification; output to `data/flow/magnitudes.json`. **Note**: Must complete before T009 and T013 to avoid resource contention; NOT [P] due to heavy compute overlap with T009. **Depends on T012**. **Verify**: Run `pytest tests/unit/test_flow.py::test_flow_magnitude_extraction`.
- [X] T009 [P] [Foundational] Implement full optical flow computation in `code/data/flow.py` using RAFT-small or Farneback (CPU-optimized) for the Flow-Coherence model; output fields to `data/flow/`. **Note**: This task is for model warping (US2). It must complete after T009a to avoid CPU/RAM contention on the runner with constrained memory resources. **Depends on T009a**. **Verify**: Run `pytest tests/unit/test_flow.py::test_flow_field_computation`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Replication and Metric Collection (Priority: P1) 🎯 MVP

**Goal**: Execute the CPU-optimized LiveEdit baseline model on a stratified dataset to establish ground-truth metrics (memory, latency, temporal consistency) before introducing modifications.

**Independent Test**: Running the baseline pipeline on a subset of clips generates a JSON report containing peak memory, inference time, and background SSIM scores without manual intervention.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for MetricRecord schema in `tests/contract/test_metric_schema.py`
- [X] T011 [P] [US1] Integration test for baseline inference pipeline in `tests/integration/test_baseline_pipeline.py`

### Implementation for User Story 1

- [ ] T013a [US1] Implement video processor in `code/data/processor.py` to generate synthetic masks for each clip. **Details**: Generate synthetic masks and save to `data/raw/masks/`. **Verify**: Run `pytest tests/unit/test_processor.py::test_mask_generation`. **Depends on T012**.
- [ ] T013b [US1] Implement video processor in `code/data/processor.py` to stratify clips by motion complexity as defined in Plan.md Dataset Strategy. **Details**: Read `STRATIFICATION_THRESHOLDS` from `code/config.py` and assign categories (Static, Slow Rigid, Fast Non-Rigid). **Depends on T012, T009a** (reads `data/flow/magnitudes.json` for stratification logic). **Verify**: Run `pytest tests/unit/test_processor.py::test_stratification_logic`.
- [X] T014 [US1] Implement baseline LiveEdit model wrapper in `code/models/baseline.py` with temporal attention layers ENABLED. **Details**: Subclass `diffusers.StableDiffusionPipeline` in `code/models/baseline.py` and override `__call__` to enable `temporal_attention` flag. Class name: `LiveEditBaselinePipeline`. **Verify**: Run `pytest tests/unit/test_baseline.py::test_baseline_pipeline_instantiation`.
- [X] T015 [US1] Implement baseline inference runner in `code/main.py` (baseline mode) that processes clips one-by-one to manage RAM. **Verify**: Run `pytest tests/unit/test_main.py::test_baseline_inference_loop`.
- [X] T016a-bss [US1] Implement Background Stability Score (BSS) calculator for **Baseline** in `code/metrics/ssim.py`. **Details**: Compute BSS by comparing consecutive edited frames (t and t-1) within the edited output video to quantify background stability, strictly avoiding comparison to original ground-truth video as per FR-005. **Output**: `data/metrics/baseline_bss.json`. **Verify**: Run `pytest tests/unit/test_metrics_ssim.py::test_baseline_bss_calculation`.
- [X] T016a-ssim [US1] Implement Consecutive Frame SSIM calculator for **Baseline** in `code/metrics/ssim.py`. **Details**: Compute SSIM between consecutive frames within the edited output video. **Output**: `data/metrics/baseline_ssim.json`. **Verify**: Run `pytest tests/unit/test_metrics_ssim.py::test_baseline_consecutive_ssim_calculation`.
- [X] T016a-grad [US1] Implement Temporal Gradient Variance calculator for **Baseline** in `code/metrics/ssim.py`. **Details**: Compute temporal gradient variance between consecutive frames within the edited output video. **Output**: `data/metrics/baseline_grad.json`. **Verify**: Run `pytest tests/unit/test_metrics_ssim.py::test_baseline_temporal_gradient_variance_calculation`.
- [ ] T017 [US1] Implement report generator for baseline metrics in `code/analysis/reporter.py` (outputs JSON to `data/metrics/baseline_results.json`). **Details**: Aggregate metrics from T016a and resource usage from T008. **Output**: `data/metrics/baseline_results.json` with keys `clip_id`, `peak_memory`, `inference_time`, `consecutive_ssim`, `temporal_gradient_variance`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_baseline_report_generation`.
- [X] T018 [P] [US2] Contract test for invalid_flow flag handling in `tests/contract/test_flow_coherence.py`
- [X] T019 [P] [US2] Integration test for flow-warping logic in `tests/integration/test_flow_warp.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Flow-Coherence Module Implementation and Execution (Priority: P2)

**Goal**: Replace region-tracking logic with a "Flow-Coherence" module using pre-computed optical flow, execute on the dataset, and measure memory reduction vs. artifact generation.

**Independent Test**: Running the modified pipeline on the same dataset subset generates a comparative metrics report showing memory reduction and SSIM scores, including handling of invalid flow vectors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [US2] Implement Flow-Coherence module in `code/models/flow_coherence.py`: replaces Mask Cache, warps latents using pre-computed flow (T009), removes attention layers. **Details**: Use `cv2.remap` with bilinear interpolation on 512x512 latent tensors. **Verify**: Run `pytest tests/unit/test_flow_coherence.py::test_flow_warp_logic`.
- [X] T021a [US2] Implement invalid flow handling in `code/models/flow_coherence.py`: fallback to identity warp for NaN/infinity vectors and set `invalid_flow` flag. **Verify**: Run `pytest tests/unit/test_flow_coherence_invalid.py::test_identity_warp_invalid_vectors`.
- [X] T021b [US2] Implement invalid flow handling verification. **Verify**: Run `pytest tests/unit/test_flow_coherence_invalid.py::test_identity_warp_invalid_vectors`.
- [X] T022 [US2] Implement flow-coherence inference runner in `code/main.py` (flow mode) with checkpointing support. **Verify**: Run `pytest tests/unit/test_main.py::test_flow_inference_loop`.
- [X] T016b-bss [US2] Implement Background Stability Score (BSS) calculator for **Flow-Coherence** in `code/metrics/ssim.py`. **Details**: Compute BSS by comparing consecutive edited frames (t and t-1) within the edited output video to quantify background stability, strictly avoiding comparison to original ground-truth video as per FR-005. **Output**: `data/metrics/flow_bss.json`. **Verify**: Run `pytest tests/unit/test_metrics_ssim.py::test_flow_bss_calculation`.
- [X] T016b-ssim [US2] Implement Consecutive Frame SSIM calculator for **Flow-Coherence** in `code/metrics/ssim.py`. **Details**: Compute SSIM between consecutive frames (t and t) within the edited output video. **Output**: `data/metrics/flow_ssim.json`. **Verify**: Run `pytest tests/unit/test_metrics_ssim.py::test_flow_consecutive_ssim_calculation`.
- [X] T016b-grad [US2] Implement Temporal Gradient Variance calculator for **Flow-Coherence** in `code/metrics/ssim.py`. **Details**: Compute temporal gradient variance between consecutive frames within the edited output video. **Output**: `data/metrics/flow_grad.json`. **Verify**: Run `pytest tests/unit/test_metrics_ssim.py::test_flow_temporal_gradient_variance_calculation`.
- [X] T023 [US2] (Merged into T016b) Implement data collector to record flow magnitude statistics and `invalid_flow` markers per frame. **Details**: Integrate logic directly into metric calculation. **Verify**: Run `pytest tests/unit/test_metrics_ssim.py::test_flow_stats_collection`.
- [ ] T024a [US2] Implement report generator for baseline metrics in `code/analysis/reporter.py`. **Details**: Aggregate metrics from T016a and resource usage from T008. **Output**: `data/metrics/baseline_results.json`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_baseline_report_generation`.
- [ ] T024b [US2] Implement report generator for flow metrics in `code/analysis/reporter.py`. **Details**: Aggregate metrics from T016b and resource usage from T008. **Output**: `data/metrics/flow_results.json`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_flow_report_generation`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Boundary Analysis and Threshold Identification (Priority: P3)

**Goal**: Perform statistical analysis (K-S test, Piecewise Regression) to identify the specific optical flow magnitude threshold where artifact generation becomes significant.

**Independent Test**: Running the post-processing script on metric reports outputs a statistical summary identifying the correlation between flow magnitude and SSIM drop, and the significance of the memory reduction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for AnalysisResult schema in `tests/contract/test_analysis_schema.py`
- [X] T026 [P] [US3] Unit test for Piecewise Regression logic in `tests/unit/test_change_point_detection.py`

### Implementation for User Story 3

- [~] T027a [US3] Implement data loader in `code/analysis/stats.py` to load baseline and flow metrics. **Details**: Load `data/metrics/baseline_results.json` and `data/metrics/flow_results.json`. **Output**: In-memory data structures. **Verify**: Run `pytest tests/unit/test_stats_loader.py::test_load_baseline_flow_metrics`.
- [X] T027a-test [US3] Verify data loader implementation. **Verify**: Run `pytest tests/unit/test_stats_loader.py::test_load_baseline_flow_metrics`.
- [ ] T027b [US3] Implement data aggregator in `code/analysis/stats.py` to merge baseline and flow metrics into paired datasets. **Details**: Merge `data/metrics/baseline_results.json` and `data/metrics/flow_results.json` by `clip_id`. **Output**: `data/metrics/paired_metrics.json`. **Verify**: Run `pytest tests/unit/test_stats_aggregator.py::test_merge_metrics`.
- [ ] T028 [US3] Implement **Kolmogorov-Smirnov (K-S) test** in `code/analysis/stats.py` to compare error distributions between baseline and flow methods; **Note**: Per Plan.md "Critical Methodological Updates", this is the **SECONDARY** check for distribution differences, providing supportive evidence alongside Piecewise Regression. **Depends on T027b**. **Output**: `data/metrics/ks_test.json` with keys `statistic` and `pvalue`. **Verify**: Run `pytest tests/unit/test_stats_kstest.py::test_ks_test_execution`.
- [X] T029 [US3] Implement **Piecewise Regression (Change-Point Detection)** in `code/analysis/stats.py` using `ruptures` to identify flow-magnitude thresholds where SSIM degradation exceeds significance; **Note**: Per Plan.md "Critical Methodological Updates", this is the **PRIMARY** method for threshold identification, superseding K-S test. **Depends on T027b**. **Output**: `data/metrics/pc_regression.json` with keys `threshold`, `regression_coeff`, `pvalue`. **Verify**: Run `pytest tests/unit/test_stats_piecewise.py::test_piecewise_regression_execution`.
- [ ] T030 [US3] Implement sensitivity analysis script in `code/analysis/stats.py` sweeping a **set of cutoff values** {0.01, 0.05, 0.1} and reporting how the *rate of frames where SSIM drop relative to baseline exceeds each specific cutoff* varies across these values; **Depends on T029**. **Output**: `data/metrics/sensitivity_analysis.json`. **Verify**: Run `pytest tests/unit/test_stats_sensitivity.py::test_sensitivity_analysis_sweep`.
- [ ] T031a [US3] Generate statistical summary report (JSON) in `code/analysis/reporter.py`. **Details**: `data/metrics/analysis_results.json` must contain keys `ks_test`, `pc_regression`, `sensitivity_analysis`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_json_summary_generation`.
- [X] T031b [US3] Generate statistical summary report (Markdown) in `code/analysis/reporter.py`. **Details**: `results/summary.md` must contain sections: Executive Summary, Methodology, Results, Statistical Boundary Analysis, Conclusion. **Verify**: Run `pytest tests/unit/test_reporter.py::test_markdown_summary_generation`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032a [P] Generate Executive Summary section in `results/summary.md`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_executive_summary_content`.
- [X] T032b [P] Generate Methodology section in `results/summary.md`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_methodology_content`.
- [X] T032c [P] Generate Results section in `results/summary.md`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_results_content`.
- [X] T032d [P] Generate Statistical Boundary Analysis section in `results/summary.md`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_boundary_analysis_content`.
- [X] T032e [P] Generate Conclusion section in `results/summary.md`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_conclusion_content`.
- [X] T032b-readme [P] Update `README.md` with execution instructions. **Verify**: Run `pytest tests/unit/test_docs.py::test_readme_updated`.
- [X] T032b-quickstart [P] Update `docs/quickstart.md` with execution instructions. **Verify**: Run `pytest tests/unit/test_docs.py::test_quickstart_updated`.
- [X] T032b-diagrams [P] Generate data flow diagrams. **Verify**: Run `pytest tests/unit/test_docs.py::test_diagrams_generated`.
- [X] T033a [P] Remove unused imports. **Verify**: Run `pytest tests/unit/test_linting.py::test_unused_imports_removed`.
- [X] T033b [P] Enforce line length < 88. **Verify**: Run `pytest tests/unit/test_linting.py::test_line_length_enforced`.
- [X] T033c [P] Run ruff check. **Verify**: Run `pytest tests/unit/test_linting.py::test_ruff_check_passed`.
- [X] T034a [P] Profile peak RAM usage. **Verify**: Run `pytest tests/unit/test_metrics_resource.py::test_peak_ram_profiled`.
- [X] T034b [P] Optimize code to reduce RAM. **Verify**: Run `pytest tests/unit/test_metrics_resource.py::test_ram_optimization`.
- [X] T034c [P] Verify peak RAM < 6GB. **Verify**: Run `pytest tests/unit/test_metrics_resource.py::test_peak_ram_under_limit`.
- [X] T035a [P] Execute `docs/quickstart.sh`. **Verify**: Run `pytest tests/integration/test_quickstart.py::test_quickstart_execution`.
- [X] T035b [P] Verify `docs/quickstart.sh` completes without error. **Verify**: Run `pytest tests/integration/test_quickstart.py::test_quickstart_success`.
- [X] T036a [P] Run full pipeline on small subset. **Verify**: Run `pytest tests/integration/test_full_pipeline.py::test_full_pipeline_execution`.
- [X] T036b [P] Verify end-to-end data flow. **Verify**: Run `pytest tests/integration/test_full_pipeline.py::test_end_to_end_data_flow`.

---

## Phase N+1: Research Validation & Data Integrity (Revision Concerns)

**Goal**: Ensure data sourcing is robust, stratification is scientifically valid, and the pilot phase accurately predicts CI feasibility.

### Implementation for Research Validation

- [ ] T037a [US1] Implement dataset stratification logic in `code/data/processor.py`: Add a post-download check that verifies the selected clip subset contains a representative distribution of motion categories (Static, Slow Rigid, Fast Non-Rigid) based on the quantitative flow thresholds defined in **Plan.md** (low, high). **Source**: Plan.md Dataset Strategy. **Logic**: Read `STRATIFICATION_THRESHOLDS` from `code/config.py`. **Verify**: Run `pytest tests/unit/test_processor_stratification.py::test_stratification_logic`.
- [X] T037a-test [US1] Verify stratification logic. **Verify**: Run `pytest tests/unit/test_processor_stratification.py::test_stratification_logic`.
- [ ] T037b [US1] Implement retry mechanism in `code/data/processor.py`: If the initial 50 clips do not meet a minimum threshold (derived from `STRATIFICATION_THRESHOLDS` in `code/config.py`), fetch additional clips to improve representation. **Note**: Thresholds are dynamic based on flow magnitude distribution, not a hard-coded count. **Verify**: Run `pytest tests/unit/test_processor_stratification.py::test_retry_mechanism`.
- [X] T037b-test [US1] Verify retry mechanism. **Verify**: Run `pytest tests/unit/test_processor_stratification.py::test_retry_mechanism`.
- [ ] T037c [US1] Implement logging for imbalance in `code/data/processor.py`: Log a WARNING if the dataset is exhausted and the distribution is still skewed, recording the imbalance in `data/metrics/stratification_report.json`. **Verify**: Run `pytest tests/unit/test_processor_stratification.py::test_imbalance_logging`.
- [X] T037c-test [US1] Verify imbalance logging. **Verify**: Run `pytest tests/unit/test_processor_stratification.py::test_imbalance_logging`.
- [ ] T038a [US1] Implement pilot execution in `code/main.py` (pilot mode): Execute a subset of the full pipeline (Download -> Flow -> Inference -> Metrics) to measure `time_per_clip` and `peak_memory` empirically. **Verify**: Run `pytest tests/unit/test_main_pilot.py::test_pilot_execution`.
- [X] T038a-test [US1] Verify pilot execution. **Verify**: Run `pytest tests/unit/test_main_pilot.py::test_pilot_execution`.
- [ ] T038b [US1] Implement time/memory measurement in `code/main.py`: Write results to `data/metrics/pilot_report.json`. **Schema**: JSON must contain keys `time_per_clip` (float) and `peak_memory` (float). **Verify**: Run `pytest tests/unit/test_main_pilot.py::test_time_measurement`.
- [X] T038b-test [US1] Verify time measurement. **Verify**: Run `pytest tests/unit/test_main_pilot.py::test_time_measurement`.
- [ ] T038c [US1] Implement dynamic sample size adjustment in `code/main.py`: Calculate `adjusted_n = floor(time_budget / time_per_clip)` and write `adjusted_n` to `data/metrics/adjusted_n.json`. **Verify**: Run `pytest tests/unit/test_main_pilot.py::test_sample_size_adjustment`.
- [X] T038c-test [US1] Verify sample size adjustment. **Verify**: Run `pytest tests/unit/test_main_pilot.py::test_sample_size_adjustment`.
- [X] T038d [US1] Implement post-hoc statistical power analysis in `code/analysis/stats.py`: Calculate the statistical power for the reduced sample size (N=50) given the observed effect sizes, acknowledging the Spec's original N=500 assumption is invalid. **Source**: Plan.md "Critical Methodological Updates" (N=50 reduction). **Output**: `data/metrics/power_analysis.json`. **Verify**: Run `pytest tests/unit/test_stats_power.py::test_power_analysis`.
- [X] T038d-test [US1] Verify power analysis. **Verify**: Run `pytest tests/unit/test_stats_power.py::test_power_analysis`.
- [X] T039a [US3] Implement N calculation logic in `code/analysis/stats.py` to consume `data/metrics/adjusted_n.json` and dynamically calculate the maximum feasible `N`. **Verify**: Run `pytest tests/unit/test_stats_adjustment.py::test_n_calculation`.
- [X] T039a-test [US3] Verify N calculation. **Verify**: Run `pytest tests/unit/test_stats_adjustment.py::test_n_calculation`.
- [ ] T039b [US3] Update CLI arguments in `code/main.py` to read `data/metrics/adjusted_n.json`. **Verify**: Run `pytest tests/unit/test_stats_adjustment.py::test_cli_update`.
- [X] T039b-test [US3] Verify CLI update. **Verify**: Run `pytest tests/unit/test_stats_adjustment.py::test_cli_update`.
- [ ] T039c [US3] Implement pipeline abort/adjust logic in `code/main.py` if the pilot suggests the full 50 clips will exceed the time budget. **Verify**: Run `pytest tests/unit/test_stats_adjustment.py::test_abort_logic`.
- [X] T039c-test [US3] Verify abort logic. **Verify**: Run `pytest tests/unit/test_stats_adjustment.py::test_abort_logic`.
- [X] T040a [US3] Implement histogram generation in `code/analysis/reporter.py` to visually confirm the stratification covers the required range (0.5 to >5.0) before analysis begins. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_flow_magnitude_histogram`.
- [X] T040a-test [US3] Verify histogram generation. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_flow_magnitude_histogram`.
- [X] T040b [US3] Verify plot covers required range. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_plot_range_verification`.

---

## Phase N+2: Final Review & Documentation (Revision Concerns)

**Goal**: Address final reviewer concerns regarding data integrity, reproducibility, and the specific handling of invalid flow vectors in the final report.

- [X] T041a [US1] [P] Implement directory scanning in `code/utils/audit.py` that scans `data/raw/` and `data/flow/` for checksums. **Verify**: Run `pytest tests/unit/test_audit.py::test_directory_scanning`.
- [X] T041a-test [US1] Verify directory scanning. **Verify**: Run `pytest tests/unit/test_audit.py::test_directory_scanning`.
- [X] T041b [US1] [P] Implement checksum verification in `code/utils/audit.py`. **Verify**: Run `pytest tests/unit/test_audit.py::test_checksum_verification`.
- [X] T041b-test [US1] Verify checksum verification. **Verify**: Run `pytest tests/unit/test_audit.py::test_checksum_verification`.
- [X] T041c [US1] [P] Implement source logging in `code/utils/audit.py` to log the source URL and timestamp. **Verify**: Run `pytest tests/unit/test_audit.py::test_source_logging`.
- [X] T041c-test [US1] Verify source logging. **Verify**: Run `pytest tests/unit/test_audit.py::test_source_logging`.
- [X] T042a [US2] [P] Implement invalid flow handling section generation in `code/analysis/reporter.py` for the final `results/summary.md` report, explicitly listing the number of frames flagged with `invalid_flow` and the impact of the identity warp fallback on the overall BSS score. **Verify**: Run `pytest tests/unit/test_reporter.py::test_invalid_flow_section_generation`.
- [X] T042a-test [US2] Verify invalid flow section generation. **Verify**: Run `pytest tests/unit/test_reporter.py::test_invalid_flow_section_generation`.
- [X] T043a [US3] [P] Implement sensitivity plot generation in `code/analysis/reporter.py` visualizing the inconsistency rates across a range of swept cutoff values to provide a visual confirmation of the threshold robustness. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_sensitivity_plot_generation`.
- [X] T043a-test [US3] Verify sensitivity plot generation. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_sensitivity_plot_generation`.
- [X] T043b [US3] [P] Verify plot exists and is valid. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_plot_validity`.
- [X] T044a [P] Implement reproducibility checklist content in `README.md`. **Verify**: Run `pytest tests/unit/test_docs.py::test_reproducibility_checklist_content`.
- [X] T044a-test [P] Verify reproducibility checklist content. **Verify**: Run `pytest tests/unit/test_docs.py::test_reproducibility_checklist_content`.
- [X] T044b [P] Verify checklist exists in `README.md`. **Verify**: Run `pytest tests/unit/test_docs.py::test_reproducibility_checklist_exists`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Research Validation (Phase N+1)**: Depends on Foundational and US1/US2 implementation to ensure data pipelines are ready for validation
- **Final Review (Phase N+2)**: Depends on completion of all previous phases and the generation of the final metrics reports

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T009 (Flow computation) which is foundational for this story, but can run in parallel with US1 inference if flow is pre-computed
- **User Story 3 (P3)**: Depends on completion of US1 (T017) and US2 (T024) to have data to analyze

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) *except T009a which must precede T009 due to resource contention*
- Once Foundational phase completes, US1 and US2 can proceed in parallel (data download/flow prep can be parallelized)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Implementation Strategy

#### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

#### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

#### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Baseline)
 - Developer B: User Story 2 (Flow-Coherence) - can start flow computation early
 - Developer C: User Story 3 (Analysis) - waits for data
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
- **Data Integrity**: All dataset downloads MUST fail loudly; no synthetic fallbacks allowed.
- **Compute Constraints**: All inference must be CPU-optimized; ensure N=50 clips fits within 6h limit.
- **Metric Validity**: Use Background Stability Score (BSS) and Flow-Normalized SSIM as defined in plan.md. BSS isolates background and compares to GT; Consecutive Frame SSIM measures flickering.
- **Threshold Identification**: Piecewise Regression is the PRIMARY method for threshold identification (Plan); K-S test is SECONDARY (Spec).
- **Stratification Thresholds**: Numeric thresholds (0.5, 5.0) are derived from Plan.md Dataset Strategy (overrides Spec); T037 defers to Plan definition and reads from config.
- **Sensitivity Analysis Cutoffs**: Must use {0.01, 0.05, 0.1} as per Spec FR-007.
- **Flow Computation**: T009a is for stratification (US1); T009 is for model warping (US2). T009a must complete before T009 to avoid resource contention.
- **Pilot Validation**: T038/T039 are critical to prevent CI timeout failures and resolve Spec/Plan sample size conflict; the pipeline must dynamically adjust N based on pilot results.
- **Stratification Verification**: T037 ensures the dataset is not biased towards "easy" clips; failure to stratify triggers a retry mechanism, not a hard crash.
- **Data Audit**: T041 ensures all data sources are verified and logged for reproducibility.
- **Invalid Flow Reporting**: T042 ensures the fallback mechanism is explicitly reported in the final summary.
- **Visual Confirmation**: T043 and T044 provide visual and textual confirmation of the sensitivity analysis and reproducibility.
- **Statistical Power**: T038d addresses the Spec/Plan conflict on sample size by calculating and documenting the power for N=50.
