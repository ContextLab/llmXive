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
- **Paths shown below assume single project - adjust based on plan.md structure

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  
  The /speckit-tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/
  
  Do NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

- [X] T001a Create project directory structure: `projects/PROJ-<ID>-llmxive-follow-up-extending-liveedit-tow/` with subdirectories `data/raw`, `data/flow`, `data/metrics`, `code`, `code/data`, `code/models`, `code/metrics`, `code/analysis`, `tests/contract`, `tests/unit`, `results`. **Deliverable**: Create directories. **Verify**: Run `ls projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/` and confirm directories exist.
- [X] T001b Create `scripts/init_structure.sh` that generates the directory structure defined in T001a. **Verify**: Run `bash scripts/init_structure.sh` and confirm directories exist.
- [X] T001c Create initial file scaffolding: `code/__init__.py`, `code/config.py`, `tests/__init__.py`, `results/.gitkeep`. **Verify**: Run `ls code/__init__.py code/config.py tests/__init__.py results/.gitkeep` and confirm files exist.
- [X] T002a [P] Create `code/requirements.txt` containing the following pinned dependencies: torch>=2.0.0 (cpu), diffusers, opencv-python, scikit-learn, pandas, numpy, datasets, ruptures. **Verify**: Run `ls code/requirements.txt` and confirm file exists.
- [X] T002c [P] Create `tests/unit/test_requirements.py` that asserts all dependencies in `code/requirements.txt` are pinned versions. **Verify**: Run `pytest tests/unit/test_requirements.py::test_dependencies_pinned`.
- [X] T003a [P] Configure linting (ruff) tool: Create `pyproject.toml` with `[tool.ruff]` section. **Verify**: Run `ls pyproject.toml` and confirm section exists.
- [X] T003b [P] Create `tests/unit/test_linting.py` with `test_ruff_config_valid` that validates the ruff configuration. **Verify**: Run `pytest tests/unit/test_linting.py::test_ruff_config_valid`.
- [X] T003d [P] Add `test_black_config_valid` to `tests/unit/test_linting.py` that validates the black configuration. **Verify**: Run `pytest tests/unit/test_linting.py::test_black_config_valid`.
- [X] T003e [P] Create `tests/unit/test_linting.py` entries for ruff and black validation if not already present. **Verify**: Same as above.
- [X] T003f [P] Ensure `pyproject.toml` contains both `[tool.ruff]` and `[tool.black]` sections. **Verify**: Run `cat pyproject.toml` and check sections.
- [X] T004 [P] Create base data models (VideoClip, MetricRecord, AnalysisResult) in `code/data/models.py`. **Verify**: Run `pytest tests/unit/test_models.py`.
- [X] T004c [P] Create `tests/unit/test_models.py` to validate the data model classes. **Verify**: Run `pytest tests/unit/test_models.py`.
- [X] T005 [P] Setup experiment configuration manager in `code/config.py` with explicit `SENSITIVITY_CUTOFFS` constant initialized to {0.01, 0.05, 0.1} and `STRATIFICATION_THRESHOLDS` constant initialized to {0.5, 5.0}. **Verify**: Run `pytest tests/unit/test_config.py`.
- [X] T005c [P] Create `tests/unit/test_config.py` to validate configuration constants. **Verify**: Run `pytest tests/unit/test_config.py`.
- [X] T006a [P] Implement robust logging infrastructure in `code/utils/logger.py`. **Verify**: Run `pytest tests/unit/test_logger.py::test_logger_init`.
- [X] T006c [P] Create `tests/unit/test_logger.py` to verify logger initialization. **Verify**: Run `pytest tests/unit/test_logger.py::test_logger_init`.
- [X] T006b [P] Implement checkpointing infrastructure in `code/utils/checkpoint.py` (handles CI limit, resume capability). **Verify**: Run `pytest tests/unit/test_checkpoint.py::test_save_load_cycle`.
- [X] T006d [P] Create `tests/unit/test_checkpoint.py` to verify checkpoint save/load cycle. **Verify**: Run `pytest tests/unit/test_checkpoint.py::test_save_load_cycle`.
- [X] T007a [P] Create dataset schema validator in `specs/001-optical-flow-temporal-coherence/contracts/dataset_schema.py` using `pydantic`. **Verify**: Run `pytest tests/contract/test_dataset_schema.py::test_dataset_schema_load`.
- [X] T007d [P] Create `tests/contract/test_dataset_schema.py` for dataset schema validation. **Verify**: Run `pytest tests/contract/test_dataset_schema.py::test_dataset_schema_load`.
- [X] T007b [P] Create metric schema validator in `specs/001-optical-flow-temporal-coherence/contracts/metric_schema.py` using `pydantic`. **Verify**: Run `pytest tests/contract/test_metric_schema.py::test_metric_schema_load`.
- [X] T007e [P] Create `tests/contract/test_metric_schema.py` for metric schema validation. **Verify**: Run `pytest tests/contract/test_metric_schema.py::test_metric_schema_load`.
- [X] T007c [P] Create analysis schema validator in `specs/001-optical-flow-temporal-coherence/contracts/analysis_schema.py` using `pydantic`. **Verify**: Run `pytest tests/contract/test_analysis_schema.py::test_analysis_schema_load`.
- [X] T007f [P] Create `tests/contract/test_analysis_schema.py` for analysis schema validation. **Verify**: Run `pytest tests/contract/test_analysis_schema.py::test_analysis_schema_load`.
- [X] T008 [P] Implement memory profiling wrapper in `code/metrics/resource.py` to track peak RAM usage per clip. **Verify**: Run `pytest tests/unit/test_metrics_resource.py::test_memory_tracking`.
- [X] T008c [P] Create `tests/unit/test_metrics_resource.py` to verify memory profiling wrapper. **Verify**: Run `pytest tests/unit/test_metrics_resource.py::test_memory_tracking`.
- [X] T009 [P] Implement full optical flow computation in `code/data/flow.py` using RAFT-small or Farneback (CPU-optimized) for the Flow-Coherence model; output fields to `data/flow/`. **Verify**: Run `pytest tests/unit/test_flow.py::test_flow_field_computation`.
- [X] T009-test [P] Create `tests/unit/test_flow.py` for optical flow computation verification. **Verify**: Run `pytest tests/unit/test_flow.py::test_flow_field_computation`.
- [X] T009a [P] Implement flow magnitude extraction in `code/data/flow_magnitude.py` to compute mean flow magnitude for stratification; output to `data/flow/magnitudes.json`. **Depends on T009**. **Verify**: Run `pytest tests/unit/test_flow_magnitude.py::test_flow_magnitude_extraction`.
- [X] T009a-test [P] Create `tests/unit/test_flow_magnitude.py` for flow magnitude extraction verification. **Verify**: Run `pytest tests/unit/test_flow_magnitude.py::test_flow_magnitude_extraction`.
- [X] T010 [P] [US1] Contract test for MetricRecord schema in `tests/contract/test_metric_schema.py`
- [X] T011 [P] [US1] Integration test for baseline inference pipeline in `tests/integration/test_baseline_pipeline.py`
- [X] T012 (Removed) Placeholder task removed; dependencies updated accordingly.
- [X] T013a [US1] Implement video processor in `code/data/processor.py` to generate synthetic masks for each clip. **Details**: Generate synthetic masks and save to `data/raw/masks/`. **Verify**: Run `pytest tests/unit/test_processor.py::test_mask_generation`.
- [X] T013a-test [P] Create `tests/unit/test_processor.py` for mask generation verification. **Verify**: Run `pytest tests/unit/test_processor.py::test_mask_generation`.
- [X] T013b [US1] Implement video processor in `code/data/processor.py` to stratify clips by motion complexity as defined in Plan.md Dataset Strategy. **Details**: Read `STRATIFICATION_THRESHOLDS` from `code/config.py` and assign categories (Static, Slow Rigid, Fast Non-Rigid) based on flow magnitude from `data/flow/magnitudes.json`. **Edge Cases**: Handle values exactly at 0.5 and 5.0 by assigning to the higher category. **Depends on T009a**. **Verify**: Run `pytest tests/unit/test_processor.py::test_stratification_logic`.
- [X] T013b-test [P] Create `tests/unit/test_processor.py` for stratification logic verification. **Verify**: Run `pytest tests/unit/test_processor.py::test_stratification_logic`.
- [X] T014 [US1] Implement baseline LiveEdit model wrapper in `code/models/baseline.py` with temporal attention layers ENABLED. **Details**: Subclass `diffusers.StableDiffusionPipeline` in `code/models/baseline.py` and override `__call__` to enable `temporal_attention` flag. Class name: `LiveEditBaselinePipeline`. **Verify**: Run `pytest tests/unit/test_baseline.py::test_baseline_pipeline_instantiation`.
- [X] T014-test [P] Create `tests/unit/test_baseline.py` for baseline model instantiation verification. **Verify**: `pytest tests/unit/test_baseline.py::test_baseline_pipeline_instantiation`.
- [X] T015 [US1] Implement baseline inference runner in `code/main.py` (baseline mode) that processes clips one-by-one to manage RAM. **Verify**: Run `pytest tests/unit/test_main.py::test_baseline_inference_loop`.
- [X] T015-test [P] Create `tests/unit/test_main.py` for baseline inference loop verification. **Verify**: `pytest tests/unit/test_main.py::test_baseline_inference_loop`.
- [X] T016a [US1] Implement metric calculators for **Baseline** in `code/metrics/ssim.py`. **Details**: 
  1. **Consecutive Frame SSIM** (FR-005): Compute SSIM between consecutive frames (t, t-1) within the edited output video, **using the edit mask to isolate background regions** to quantify flickering. **Output**: `data/metrics/baseline_ssim.json`.
  2. **Temporal Gradient Variance** (FR-005): Compute temporal gradient variance between consecutive edited frames, **using the edit mask to isolate background regions**. **Output**: `data/metrics/baseline_grad.json`.
  **[FR-005]**. **Verify**: Run `pytest tests/unit/test_metrics_ssim.py::test_baseline_metrics_calculation`.
- [X] T016a-test [P] Create `tests/unit/test_metrics_ssim.py` for baseline metric calculation verification. **Verify**: `pytest tests/unit/test_metrics_ssim.py::test_baseline_metrics_calculation`.
- [X] T016c [Plan-override] Compute Background Stability Score (BSS) by comparing edited background regions to original ground‑truth video. **Output**: `data/metrics/baseline_bss.json`. **Verify**: Run appropriate test (to be added). 
- [X] T017 [US1] Implement report generator for baseline metrics in `code/analysis/reporter.py` (outputs JSON to `data/metrics/baseline_results.json`). **Details**: Aggregate metrics from T016a and resource usage from T008. **Merge Schema**: `baseline_results.json` must contain keys `clip_id`, `peak_memory`, `inference_time`, `consecutive_ssim`, `temporal_gradient_variance`. **Merge Logic**: Load all JSON files from T016a and T008, merge by `clip_id`, and write to `data/metrics/baseline_results.json`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_baseline_report_generation`.
- [X] T017-test [P] Create `tests/unit/test_reporter.py` for baseline report generation verification. **Verify**: `pytest tests/unit/test_reporter.py::test_baseline_report_generation`.
- [X] T018 [P] [US2] Contract test for invalid_flow flag handling in `tests/contract/test_flow_coherence.py`
- [X] T018-test [P] Create `tests/contract/test_flow_coherence.py` for invalid flow flag contract test. **Verify**: `pytest tests/contract/test_flow_coherence.py::test_invalid_flow_flag`.
- [X] T019 [P] [US2] Integration test for flow-warping logic in `tests/integration/test_flow_warp.py`
- [X] T019-test [P] Create `tests/integration/test_flow_warp.py` for flow warp integration test. **Verify**: `pytest tests/integration/test_flow_warp.py::test_flow_warp_logic`.
- [X] T020 [US2] Implement Flow-Coherence module in `code/models/flow_coherence.py`: replaces Mask Cache, warps latents using pre-computed flow (T009), removes attention layers. **Details**: Use `cv2.remap` with bilinear interpolation on 512x512 latent tensors. **Verify**: Run `pytest tests/unit/test_flow_coherence.py::test_flow_warp_logic`.
- [X] T020-test [P] Create `tests/unit/test_flow_coherence.py` for flow-coherence module verification. **Verify**: `pytest tests/unit/test_flow_coherence.py::test_flow_warp_logic`.
- [X] T021a [US2] Implement invalid flow handling in `code/models/flow_coherence.py`: fallback to identity warp for NaN/infinity vectors and set `invalid_flow` flag. **Verify**: Run `pytest tests/unit/test_flow_coherence_invalid.py::test_identity_warp_invalid_vectors`.
- [X] T021a-test [P] Create `tests/unit/test_flow_coherence_invalid.py` for invalid flow handling verification. **Verify**: `pytest tests/unit/test_flow_coherence_invalid.py::test_identity_warp_invalid_vectors`.
- [X] T022 [US2] Implement flow-coherence inference runner in `code/main.py` (flow mode) with checkpointing support. **Verify**: Run `pytest tests/unit/test_main.py::test_flow_inference_loop`.
- [X] T022-test [P] Create `tests/unit/test_main.py` for flow inference loop verification. **Verify**: `pytest tests/unit/test_main.py::test_flow_inference_loop`.
- [X] T016b [US2] Implement metric calculators for **Flow-Coherence** in `code/metrics/ssim.py`. **Details**: 
  1. **Consecutive Frame SSIM** (FR-005): Compute SSIM between consecutive frames (t, t-1) within the edited output video, **using the edit mask to isolate background regions** to quantify flickering. **Output**: `data/metrics/flow_ssim.json`.
  2. **Temporal Gradient Variance** (FR-005): Compute temporal gradient variance between consecutive edited frames, **using the edit mask to isolate background regions**. **Output**: `data/metrics/flow_grad.json`.
  **[FR-005]**. **Verify**: Run `pytest tests/unit/test_metrics_ssim.py::test_flow_metrics_calculation`.
- [X] T016b-test [P] Create `tests/unit/test_metrics_ssim.py` for flow metric calculation verification. **Verify**: `pytest tests/unit/test_metrics_ssim.py::test_flow_metrics_calculation`.
- [X] T023 [US2] (Merged into T016b) Implement data collector to record flow magnitude statistics and `invalid_flow` markers per frame. **Details**: Integrate logic directly into metric calculation. **Verify**: Run `pytest tests/unit/test_metrics_ssim.py::test_flow_stats_collection`.
- [X] T023-test [P] Create `tests/unit/test_metrics_ssim.py` for flow stats collection verification. **Verify**: `pytest tests/unit/test_metrics_ssim.py::test_flow_stats_collection`.
- [X] T024b [US2] Implement report generator for flow metrics in `code/analysis/reporter.py`. **Details**: Aggregate metrics from T016b and resource usage from T008. **Output**: `data/metrics/flow_results.json`. **Merge Logic**: Load all three JSON files from T016b and T008, merge by `clip_id`, and write to `data/metrics/flow_results.json`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_flow_report_generation`.
- [X] T024b-test [P] Create `tests/unit/test_reporter.py` for flow report generation verification. **Verify**: `pytest tests/unit/test_reporter.py::test_flow_report_generation`.
- [X] T025 [P] [US3] Contract test for AnalysisResult schema in `tests/contract/test_analysis_schema.py`
- [X] T025-test [P] Create `tests/contract/test_analysis_schema.py` for analysis schema contract test. **Verify**: `pytest tests/contract/test_analysis_schema.py::test_analysis_schema_load`.
- [X] T026 [P] [US3] Unit test for Piecewise Regression logic in `tests/unit/test_change_point_detection.py`
- [X] T026-test [P] Create `tests/unit/test_change_point_detection.py` for piecewise regression unit test. **Verify**: `pytest tests/unit/test_change_point_detection.py::test_piecewise_regression_execution`.
- [X] T027a [US3] Implement data loader in `code/analysis/stats.py` to load baseline and flow metrics. **Details**: Load `data/metrics/baseline_results.json` and `data/metrics/flow_results.json`. **Output**: In-memory data structures. **Verify**: Run `pytest tests/unit/test_stats_loader.py::test_load_baseline_flow_metrics`.
- [X] T027a-test [P] Create `tests/unit/test_stats_loader.py` for data loader verification. **Verify**: `pytest tests/unit/test_stats_loader.py::test_load_baseline_flow_metrics`.
- [X] T027a-verify-test [P] Duplicate verification for data loader (same as above). **Verify**: Same as above.
- [X] T027b [US3] Implement data aggregator in `code/analysis/stats.py` to merge baseline and flow metrics into paired datasets. **Details**: Merge `data/metrics/baseline_results.json` and `data/metrics/flow_results.json` by `clip_id`. **Output**: `data/metrics/paired_metrics.json`. **Merge Logic**: Inner join on `clip_id`. **Verify**: Run `pytest tests/unit/test_stats_aggregator.py::test_merge_metrics`.
- [X] T027b-test [P] Create `tests/unit/test_stats_aggregator.py` for data aggregator verification. **Verify**: `pytest tests/unit/test_stats_aggregator.py::test_merge_metrics`.
- [X] T028 [FR-006][P] Implement **Kolmogorov-Smirnov (K‑S) test** in `code/analysis/stats.py` to compare error distributions between baseline and flow methods. **Output**: `data/metrics/ks_test.json` with keys `statistic` and `pvalue`. **Verify**: Run `pytest tests/unit/test_stats_kstest.py::test_ks_test_execution`.
- [X] T028-test [P] Create `tests/unit/test_stats_kstest.py` for K‑S test execution verification. **Verify**: `pytest tests/unit/test_stats_kstest.py::test_ks_test_execution`.
- [X] T029 [P] Implement **Piecewise Regression (Change‑Point Detection)** in `code/analysis/stats.py` using `ruptures` to identify flow‑magnitude thresholds where SSIM degradation exceeds significance; **Note**: This is the primary method for threshold identification per Plan. **Output**: `data/metrics/pc_regression.json` with keys `threshold`, `regression_coeff`, `pvalue`. **Verify**: Run `pytest tests/unit/test_stats_piecewise.py::test_piecewise_regression_execution`.
- [X] T029-test [P] Create `tests/unit/test_stats_piecewise.py` for piecewise regression verification. **Verify**: `pytest tests/unit/test_stats_piecewise.py::test_piecewise_regression_execution`.
- [X] T030 [FR-007][P] Implement sensitivity analysis script in `code/analysis/stats.py` sweeping a **set of cutoff values** {0.01, 0.05, 0.1} and reporting how the *rate of frames where SSIM drop relative to baseline exceeds each specific cutoff* varies across these values; **Depends on T029**. **Output**: `data/metrics/sensitivity_analysis.json`. **Verify**: Run `pytest tests/unit/test_stats_sensitivity.py::test_sensitivity_analysis_sweep`.
- [X] T030-test [P] Create `tests/unit/test_stats_sensitivity.py` for sensitivity analysis verification. **Verify**: `pytest tests/unit/test_stats_sensitivity.py::test_sensitivity_analysis_sweep`.
- [X] T031a [P] Generate statistical summary report (JSON) in `code/analysis/reporter.py`. **Details**: `data/metrics/analysis_results.json` must contain keys `ks_test`, `pc_regression`, `sensitivity_analysis`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_json_summary_generation`.
- [X] T031a-test [P] Create `tests/unit/test_reporter.py` for JSON summary generation verification. **Verify**: `pytest tests/unit/test_reporter.py::test_json_summary_generation`.
- [X] T031b [P] Generate statistical summary report (Markdown) in `code/analysis/reporter.py`. **Details**: `results/summary.md` must contain sections: Executive Summary, Methodology, Results, Statistical Boundary Analysis, Conclusion. **Verify**: Run `pytest tests/unit/test_reporter.py::test_markdown_summary_generation`.
- [X] T031b-test [P] Create `tests/unit/test_reporter.py` for Markdown summary generation verification. **Verify**: `pytest tests/unit/test_reporter.py::test_markdown_summary_generation`.
- [X] T032a [P] Generate Executive Summary section in `results/summary.md`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_executive_summary_content`.
- [X] T032a-test [P] Create `tests/unit/test_reporter.py` for executive summary content verification. **Verify**: `pytest tests/unit/test_reporter.py::test_executive_summary_content`.
- [X] T032b [P] Generate Methodology section in `results/summary.md`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_methodology_content`.
- [X] T032b-test [P] Create `tests/unit/test_reporter.py` for methodology content verification. **Verify**: `pytest tests/unit/test_reporter.py::test_methodology_content`.
- [X] T032c [P] Generate Results section in `results/summary.md`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_results_content`.
- [X] T032c-test [P] Create `tests/unit/test_reporter.py` for results content verification. **Verify**: `pytest tests/unit/test_reporter.py::test_results_content`.
- [X] T032d [P] Generate Statistical Boundary Analysis section in `results/summary.md`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_boundary_analysis_content`.
- [X] T032d-test [P] Create `tests/unit/test_reporter.py` for boundary analysis content verification. **Verify**: `pytest tests/unit/test_reporter.py::test_boundary_analysis_content`.
- [X] T032e [P] Generate Conclusion section in `results/summary.md`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_conclusion_content`.
- [X] T032e-test [P] Create `tests/unit/test_reporter.py` for conclusion content verification. **Verify**: `pytest tests/unit/test_reporter.py::test_conclusion_content`.
- [X] T032b-readme [P] Update `README.md` with execution instructions. **Verify**: Run `pytest tests/unit/test_docs.py::test_readme_updated`.
- [X] T032b-readme-test [P] Create `tests/unit/test_docs.py` for README update verification. **Verify**: `pytest tests/unit/test_docs.py::test_readme_updated`.
- [X] T032b-quickstart [P] Update `docs/quickstart.md` with execution instructions. **Verify**: Run `pytest tests/unit/test_docs.py::test_quickstart_updated`.
- [X] T032b-quickstart-test [P] Create `tests/unit/test_docs.py` for quickstart update verification. **Verify**: `pytest tests/unit/test_docs.py::test_quickstart_updated`.
- [X] T032b-diagrams [P] Generate data flow diagrams. **Verify**: Run `pytest tests/unit/test_docs.py::test_diagrams_generated`.
- [X] T032b-diagrams-test [P] Create `tests/unit/test_docs.py` for diagram generation verification. **Verify**: `pytest tests/unit/test_docs.py::test_diagrams_generated`.
- [X] T033a [P] Remove unused imports. **Verify**: Run `pytest tests/unit/test_linting.py::test_unused_imports_removed`.
- [X] T033a-test [P] Create `tests/unit/test_linting.py` for unused imports verification. **Verify**: `pytest tests/unit/test_linting.py::test_unused_imports_removed`.
- [X] T033b [P] Enforce line length < 88. **Verify**: Run `pytest tests/unit/test_linting.py::test_line_length_enforced`.
- [X] T033b-test [P] Create `tests/unit/test_linting.py` for line length verification. **Verify**: `pytest tests/unit/test_linting.py::test_line_length_enforced`.
- [X] T033c [P] Run ruff check. **Verify**: Run `pytest tests/unit/test_linting.py::test_ruff_check_passed`.
- [X] T033c-test [P] Create `tests/unit/test_linting.py` for ruff check verification. **Verify**: `pytest tests/unit/test_linting.py::test_ruff_check_passed`.
- [X] T034a [P] Profile peak RAM usage. **Verify**: Run `pytest tests/unit/test_metrics_resource.py::test_peak_ram_profiled`.
- [X] T034a-test [P] Create `tests/unit/test_metrics_resource.py` for peak RAM profiling verification. **Verify**: `pytest tests/unit/test_metrics_resource.py::test_peak_ram_profiled`.
- [X] T034b [P] Optimize code to reduce RAM. **Verify**: Run `pytest tests/unit/test_metrics_resource.py::test_ram_optimization`.
- [X] T034b-test [P] Create `tests/unit/test_metrics_resource.py` for RAM optimization verification. **Verify**: `pytest tests/unit/test_metrics_resource.py::test_ram_optimization`.
- [X] T034c [P] Verify peak RAM < 6GB. **Verify**: Run `pytest tests/unit/test_metrics_resource.py::test_peak_ram_under_limit`.
- [X] T034c-test [P] Create `tests/unit/test_metrics_resource.py` for RAM limit verification. **Verify**: `pytest tests/unit/test_metrics_resource.py::test_peak_ram_under_limit`.
- [X] T035a [P] Execute `docs/quickstart.sh`. **Verify**: Run `pytest tests/integration/test_quickstart.py::test_quickstart_execution`.
- [X] T035a-test [P] Create `tests/integration/test_quickstart.py` for quickstart execution verification. **Verify**: `pytest tests/integration/test_quickstart.py::test_quickstart_execution`.
- [X] T035b [P] Verify `docs/quickstart.sh` completes without error. **Verify**: Run `pytest tests/integration/test_quickstart.py::test_quickstart_success`.
- [X] T035b-test [P] Create `tests/integration/test_quickstart.py` for quickstart success verification. **Verify**: `pytest tests/integration/test_quickstart.py::test_quickstart_success`.
- [X] T036a [P] Run full pipeline on small subset. **Verify**: Run `pytest tests/integration/test_full_pipeline.py::test_full_pipeline_execution`.
- [X] T036a-test [P] Create `tests/integration/test_full_pipeline.py` for full pipeline execution verification. **Verify**: `pytest tests/integration/test_full_pipeline.py::test_full_pipeline_execution`.
- [X] T036b [P] Verify end-to-end data flow. **Verify**: Run `pytest tests/integration/test_full_pipeline.py::test_end_to_end_data_flow`.
- [X] T036b-test [P] Create `tests/integration/test_full_pipeline.py` for end-to-end data flow verification. **Verify**: `pytest tests/integration/test_full_pipeline.py::test_end_to_end_data_flow`.
- [X] T037a [P] Implement stratification logic in `code/data/processor.py`: Add a post-download check that verifies the selected clip subset contains a representative distribution of motion categories (Static, Slow Rigid, Fast Non-Rigid) based on the quantitative flow thresholds defined in **Plan.md** (low, high). **Source**: Plan.md Dataset Strategy. **Logic**: Read `STRATIFICATION_THRESHOLDS` from `code/config.py`. **Verify**: Run `pytest tests/unit/test_processor_stratification.py::test_stratification_logic`.
- [X] T037a-test [P] Create `tests/unit/test_processor_stratification.py` for stratification logic verification. **Verify**: `pytest tests/unit/test_processor_stratification.py::test_stratification_logic`.
- [X] T037b [P] Implement retry mechanism in `code/data/processor.py`: If the initial 50 clips do not meet a minimum threshold (derived from `STRATIFICATION_THRESHOLDS` in `code/config.py`), fetch additional clips to improve representation. **Note**: Thresholds are dynamic based on flow magnitude distribution, not a hard-coded count. **Logic**: If any category has < 10% of total clips, fetch more until all categories have >= 10%. **Verify**: Run `pytest tests/unit/test_processor_stratification.py::test_retry_mechanism`.
- [X] T037b-test [P] Create `tests/unit/test_processor_stratification.py` for retry mechanism verification. **Verify**: `pytest tests/unit/test_processor_stratification.py::test_retry_mechanism`.
- [X] T037c [P] Implement logging for imbalance in `code/data/processor.py`: Log a WARNING if the dataset is exhausted and the distribution is still skewed, recording the imbalance in `data/metrics/stratification_report.json`. **Verify**: Run `pytest tests/unit/test_processor_stratification.py::test_imbalance_logging`.
- [X] T037c-test [P] Create `tests/unit/test_processor_stratification.py` for imbalance logging verification. **Verify**: `pytest tests/unit/test_processor_stratification.py::test_imbalance_logging`.
- [X] T038a [P] Implement pilot execution in `code/main.py` (pilot mode): Execute a subset of the full pipeline (Download -> Flow -> Inference -> Metrics) to measure `time_per_clip` and `peak_memory` empirically. **Verify**: Run `pytest tests/unit/test_main_pilot.py::test_pilot_execution`.
- [X] T038a-test [P] Create `tests/unit/test_main_pilot.py` for pilot execution verification. **Verify**: `pytest tests/unit/test_main_pilot.py::test_pilot_execution`.
- [X] T038b [P] Implement time/memory measurement in `code/main.py`: Write results to `data/metrics/pilot_report.json`. **Schema**: JSON must contain keys `time_per_clip` (float) and `peak_memory` (float). **Verify**: Run `pytest tests/unit/test_main_pilot.py::test_time_measurement`.
- [X] T038b-test [P] Create `tests/unit/test_main_pilot.py` for time measurement verification. **Verify**: `pytest tests/unit/test_main_pilot.py::test_time_measurement`.
- [X] T038c [P] Implement dynamic sample size adjustment in `code/main.py`: Calculate `adjusted_n = floor(time_budget / time_per_clip)` and write `adjusted_n` to `data/metrics/adjusted_n.json`. **Logic**: `time_budget` = 5.5 hours. **Verify**: Run `pytest tests/unit/test_main_pilot.py::test_sample_size_adjustment`.
- [X] T038c-test [P] Create `tests/unit/test_main_pilot.py` for sample size adjustment verification. **Verify**: `pytest tests/unit/test_main_pilot.py::test_sample_size_adjustment`.
- [X] T038d [P] Implement post-hoc statistical power analysis in `code/analysis/stats.py`: Calculate the statistical power for the reduced sample size (N=50) given the observed effect sizes, acknowledging the Spec's original N=500 assumption is invalid. **Output**: `data/metrics/power_analysis.json`. **Verify**: Run `pytest tests/unit/test_stats_power.py::test_power_analysis`.
- [X] T038d-test [P] Create `tests/unit/test_stats_power.py` for power analysis verification. **Verify**: `pytest tests/unit/test_stats_power.py::test_power_analysis`.
- [X] T039a [P] Implement N calculation logic in `code/analysis/stats.py` to consume the `data/metrics/adjusted_n.json` and dynamically calculate the maximum feasible `N`. **Verify**: Run `pytest tests/unit/test_stats_adjustment.py::test_n_calculation`.
- [X] T039a-test [P] Create `tests/unit/test_stats_adjustment.py` for N calculation verification. **Verify**: `pytest tests/unit/test_stats_adjustment.py::test_n_calculation`.
- [X] T039b [P] Update CLI arguments in `code/main.py` to read `data/metrics/adjusted_n.json`. **Verify**: Run `pytest tests/unit/test_stats_adjustment.py::test_cli_update`.
- [X] T039b-test [P] Create `tests/unit/test_stats_adjustment.py` for CLI update verification. **Verify**: `pytest tests/unit/test_stats_adjustment.py::test_cli_update`.
- [X] T039c [P] Implement pipeline abort/adjust logic in `code/main.py` if the pilot suggests the full 50 clips will exceed the time budget. **Logic**: If `adjusted_n < 50`, reduce sample size to `adjusted_n`. **Verify**: Run `pytest tests/unit/test_stats_adjustment.py::test_abort_logic`.
- [X] T039c-test [P] Create `tests/unit/test_stats_adjustment.py` for abort logic verification. **Verify**: `pytest tests/unit/test_stats_adjustment.py::test_abort_logic`.
- [X] T040a [P] Generate histogram of flow magnitudes in `code/analysis/reporter.py` to visually confirm the stratification covers the required range (0.5 to >5.0) before analysis begins. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_flow_magnitude_histogram`.
- [X] T040a-test [P] Create `tests/unit/test_reporter_plots.py` for histogram generation verification. **Verify**: `pytest tests/unit/test_reporter_plots.py::test_flow_magnitude_histogram`.
- [X] T040b [P] Verify plot covers required range. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_plot_range_verification`.
- [X] T040b-test [P] Create `tests/unit/test_reporter_plots.py` for plot range verification. **Verify**: `pytest tests/unit/test_reporter_plots.py::test_plot_range_verification`.
- [X] T041a [P] Implement directory scanning in `code/utils/audit.py` that scans `data/raw/` and `data/flow/` for checksums. **Verify**: Run `pytest tests/unit/test_audit.py::test_directory_scanning`.
- [X] T041a-test [P] Create `tests/unit/test_audit.py` for directory scanning verification. **Verify**: `pytest tests/unit/test_audit.py::test_directory_scanning`.
- [X] T041b [P] Implement checksum verification in `code/utils/audit.py`. **Verify**: Run `pytest tests/unit/test_audit.py::test_checksum_verification`.
- [X] T041b-test [P] Create `tests/unit/test_audit.py` for checksum verification. **Verify**: `pytest tests/unit/test_audit.py::test_checksum_verification`.
- [X] T041c [P] Implement source logging in `code/utils/audit.py` to log the source URL and timestamp. **Verify**: Run `pytest tests/unit/test_audit.py::test_source_logging`.
- [X] T041c-test [P] Create `tests/unit/test_audit.py` for source logging verification. **Verify**: `pytest tests/unit/test_audit.py::test_source_logging`.
- [X] T042a [P] Implement invalid flow handling section generation in `code/analysis/reporter.py` for the final `results/summary.md` report, explicitly listing the number of frames flagged with `invalid_flow` and the impact of the identity warp fallback on the overall BSS score. **Verify**: Run `pytest tests/unit/test_reporter.py::test_invalid_flow_section_generation`.
- [X] T042a-test [P] Create `tests/unit/test_reporter.py` for invalid flow section generation verification. **Verify**: `pytest tests/unit/test_reporter.py::test_invalid_flow_section_generation`.
- [X] T043a [P] Implement sensitivity plot generation in `code/analysis/reporter.py` visualizing the inconsistency rates across a range of swept cutoff values to provide a visual confirmation of the threshold robustness. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_sensitivity_plot_generation`.
- [X] T043a-test [P] Create `tests/unit/test_reporter_plots.py` for sensitivity plot generation verification. **Verify**: `pytest tests/unit/test_reporter_plots.py::test_sensitivity_plot_generation`.
- [X] T043b [P] Verify plot exists and is valid. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_plot_validity`.
- [X] T043b-test [P] Create `tests/unit/test_reporter_plots.py` for plot validity verification. **Verify**: `pytest tests/unit/test_reporter_plots.py::test_plot_validity`.
- [X] T044a [P] Implement reproducibility checklist content in `README.md`. **Verify**: Run `pytest tests/unit/test_docs.py::test_reproducibility_checklist_content`.
- [X] T044a-test [P] Create `tests/unit/test_docs.py` for reproducibility checklist content verification. **Verify**: `pytest tests/unit/test_docs.py::test_reproducibility_checklist_content`.
- [X] T044b [P] Verify checklist exists in `README.md`. **Verify**: Run `pytest tests/unit/test_docs.py::test_reproducibility_checklist_exists`.
- [X] T044b-test [P] Create `tests/unit/test_docs.py` for checklist existence verification. **Verify**: `pytest tests/unit/test_docs.py::test_reproducibility_checklist_exists`.
- [X] T045a [P] Implement strict dataset loader in `code/data/downloader.py` that fetches DAVIS/YouTube-VOS clips using `datasets.load_dataset` with `streaming=True`. **Details**: Use `datasets.load_dataset("j-hartmann/davis", split="validation", streaming=True)` or equivalent verified source. **Constraint**: MUST NOT contain `try/except` blocks that catch download failures and switch to `generate_synthetic_*()`. If the real source fails, the script MUST raise an exception and halt execution. **Fallback**: If the source is metadata‑only, fall back to a pre‑downloaded subset of video files hosted in the repo. **Verify**: Run `pytest tests/unit/test_downloader.py::test_strict_real_data_fetch`.
- [X] T045a-test [P] Create `tests/unit/test_downloader.py` for strict real data fetch verification. **Verify**: `pytest tests/unit/test_downloader.py::test_strict_real_data_fetch`.
- [X] T045b [P] Implement chunked processing logic in `code/data/downloader.py` to handle large video files within the 7GB RAM limit. **Details**: Use `itertools.islice` to process the streaming dataset in chunks of 5 clips, accumulating statistics online without loading the full dataset into memory. **Output**: `data/raw/processed_clips/` with individual clip files. **Verify**: Run `pytest tests/unit/test_downloader.py::test_chunked_streaming_logic`.
- [X] T045b-test [P] Create `tests/unit/test_downloader.py` for chunked streaming verification. **Verify**: `pytest tests/unit/test_downloader.py::test_chunked_streaming_logic`.
- [X] T045c [P] Add explicit logging of the "Real Data Source" in `code/data/downloader.py` that records the exact HuggingFace dataset ID, split, and revision hash used for the current run. **Output**: `data/metrics/data_source_log.json`. **Verify**: Run `pytest tests/unit/test_downloader.py::test_source_logging`.
- [X] T045c-test [P] Create `tests/unit/test_downloader.py` for source logging verification. **Verify**: `pytest tests/unit/test_downloader.py::test_source_logging`.
- [X] T046a [P] Implement a "Sample Size Declaration" task in `code/main.py` that reads the pilot results (T038c) and explicitly logs the final `N` (e.g., 50 or adjusted) and the specific streaming/sampling rule (e.g., "First 50 clips from DAVIS validation stream") in the final report. **Output**: `results/summary.md` section "Data Sampling Strategy". **Verify**: Run `pytest tests/unit/test_reporter.py::test_sample_declaration`.
- [X] T046a-test [P] Create `tests/unit/test_reporter.py` for sample declaration verification. **Verify**: `pytest tests/unit/test_reporter.py::test_sample_declaration`.
- [X] T046b [P] Verify that no synthetic data generators (e.g., `generate_synthetic_masks`, `mock_flow`) are imported or called in the main pipeline paths (`code/main.py`, `code/data/processor.py`). **Details**: Static analysis check to ensure no `import mock` or `generate_synthetic` calls exist in the critical path. **Verify**: Run `pytest tests/unit/test_fabrication_guard.py::test_no_synthetic_calls`.
- [X] T046b-test [P] Create `tests/unit/test_fabrication_guard.py` for synthetic call detection verification. **Verify**: `pytest tests/unit/test_fabrication_guard.py::test_no_synthetic_calls`.
