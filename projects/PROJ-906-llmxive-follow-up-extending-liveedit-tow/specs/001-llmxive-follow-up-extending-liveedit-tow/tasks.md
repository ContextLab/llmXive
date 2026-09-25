# Tasks: llmXive follow-up: extending "LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing"

**Input**: Design documents from `/specs/001-optical-flow-temporal-coherence/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure & Configuration)

- [X] T001a Create project directory structure: `projects/PROJ-<ID>-llmxive-follow-up-extending-liveedit-tow/` with subdirectories `data/raw`, `data/flow`, `data/metrics`, `code`, `code/data`, `code/models`, `code/metrics`, `code/analysis`, `tests/contract`, `tests/unit`, `results`. **Deliverable**: Create directories. **Verify**: Run `ls projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/` and confirm directories exist.
- [X] T001b Create `scripts/init_structure.sh` that generates the directory structure defined in T001a. **Verify**: Run `bash scripts/init_structure.sh` and confirm directories exist.
- [X] T001c Create initial file scaffolding: `code/__init__.py`, `code/config.py`, `tests/__init__.py`, `results/.gitkeep`. **Verify**: Run `ls code/__init__.py code/config.py tests/__init__.py results/.gitkeep` and confirm files exist.
- [X] T002a [P] Create `code/requirements.txt` containing the following pinned dependencies: torch>=2.0.0 (cpu), diffusers, opencv-python, scikit-learn, pandas, numpy, datasets, ruptures. **Verify**: Run `ls code/requirements.txt` and confirm file exists.
- [X] T002c [P] Create `tests/unit/test_requirements.py` that asserts all dependencies in `code/requirements.txt` are pinned versions. **Verify**: Run `pytest tests/unit/test_requirements.py::test_dependencies_pinned`.
- [X] T003a [P] Configure linting (ruff) tool: Create `pyproject.toml` with `[tool.ruff]` section. **Verify**: Run `ls pyproject.toml` and confirm section exists.
- [X] T003b [P] Create `tests/unit/test_linting.py` with `test_ruff_config_valid` that validates the ruff configuration. **Verify**: Run `pytest tests/unit/test_linting.py::test_ruff_config_valid`.
- [X] T003f [P] Ensure `pyproject.toml` contains both `[tool.ruff]` and `[tool.black]` sections. **Verify**: Run `cat pyproject.toml` and check sections.
- [X] T004a [P] Create base data models (VideoClip, MetricRecord, AnalysisResult) in `code/data/models.py` and create `tests/unit/test_models.py` to validate them. **Verify**: Run `pytest tests/unit/test_models.py`.
- [X] T005a [P] Setup experiment configuration manager in `code/config.py` with explicit `SENSITIVITY_CUTOFFS` constant initialized to {0.01, 0.05, 0.1} and `STRATIFICATION_THRESHOLDS` constant initialized to {0.5, 5.0}, and create `tests/unit/test_config.py` to validate them. **Verify**: Run `pytest tests/unit/test_config.py`.
- [X] T006a [P] Implement robust logging infrastructure in `code/utils/logger.py` and create `tests/unit/test_logger.py` to verify it. **Verify**: Run `pytest tests/unit/test_logger.py::test_logger_init`.
- [X] T006b [P] Implement checkpointing infrastructure in `code/utils/checkpoint.py` (handles CI limit, resume capability) and create `tests/unit/test_checkpoint.py` to verify it. **Verify**: Run `pytest tests/unit/test_checkpoint.py::test_save_load_cycle`.
- [X] T007a [P] Create dataset schema validator in `specs/001-optical-flow-temporal-coherence/contracts/dataset_schema.py` using `pydantic` and create `tests/contract/test_dataset_schema.py`. **Verify**: Run `pytest tests/contract/test_dataset_schema.py::test_dataset_schema_load`.
- [X] T007b [P] Create metric schema validator in `specs/001-optical-flow-temporal-coherence/contracts/metric_schema.py` using `pydantic` and create `tests/contract/test_metric_schema.py`. **Verify**: Run `pytest tests/contract/test_metric_schema.py::test_metric_schema_load`.
- [X] T007c [P] Create analysis schema validator in `specs/001-optical-flow-temporal-coherence/contracts/analysis_schema.py` using `pydantic` and create `tests/contract/test_analysis_schema.py`. **Verify**: Run `pytest tests/contract/test_analysis_schema.py::test_analysis_schema_load`.
- [X] T008a [P] Implement memory profiling wrapper in `code/metrics/resource.py` to track peak RAM usage per clip and create `tests/unit/test_metrics_resource.py`. **Verify**: Run `pytest tests/unit/test_metrics_resource.py::test_memory_tracking`.
- [X] T046a [P] **Sample Size Declaration**: Implement logic in `code/main.py` to declare and enforce the sample size N=50 (or dynamic N) based on pilot results. **Depends on**: T005a. **Verify**: Run `pytest tests/unit/test_reporter.py::test_sample_size_declaration`.

## Phase 2: Data Pipeline & Preprocessing

- [X] T009a [P] Implement optical flow computation in `code/data/flow.py` using a lightweight, CPU-optimized algorithm (RAFT-small/Farneback) and create `tests/unit/test_flow.py`. **Verify**: Run `pytest tests/unit/test_flow.py::test_flow_field_computation`.
- [X] T009b [P] Implement flow magnitude extraction in `code/data/flow_magnitude.py` to compute mean flow magnitude for stratification; output to `data/flow/magnitudes.json`. **Depends on**: T009a. **Verify**: Run `pytest tests/unit/test_flow_magnitude.py::test_flow_magnitude_extraction`.
- [X] T013a [P] Implement video processor in `code/data/processor.py` to generate synthetic masks for each clip and create `tests/unit/test_processor.py`. **Details**: Generate synthetic masks and save to `data/raw/masks/`. **Verify**: Run `pytest tests/unit/test_processor.py::test_mask_generation`.
- [X] T013b [P] Implement video processor in `code/data/processor.py` to stratify clips by motion complexity based on `STRATIFICATION_THRESHOLDS` from `code/config.py` and create `tests/unit/test_processor.py`. **Depends on**: T009b. **Verify**: Run `pytest tests/unit/test_processor.py::test_stratification_logic`.
- [X] T036a [P] **Dataset Loader**: Implement a robust dataset loader in `code/data/downloader.py`. **Logic**: 1. Attempt to fetch from verified HuggingFace URL. 2. If URL is metadata-only, load pre-downloaded subset from `data/raw/`. 3. If real data unavailable, **FAIL LOUDLY** (no synthetic fallback). Create `tests/unit/test_downloader.py`. **Verify**: Run `pytest tests/unit/test_downloader.py::test_loader_logic`.

## Phase 3: Model Implementation

- [X] T014a [P] Implement baseline LiveEdit model wrapper in `code/models/baseline.py` with temporal attention layers ENABLED and create `tests/unit/test_baseline.py`. **Verify**: Run `pytest tests/unit/test_baseline.py::test_baseline_pipeline_instantiation`.
- [X] T018a [P] Implement invalid flow handling in `code/models/flow_coherence.py`: fallback to identity warp for invalid vectors and flag the frame. Create `tests/unit/test_flow_coherence_invalid.py`. **Verify**: Run `pytest tests/unit/test_flow_coherence_invalid.py::test_identity_warp_invalid_vectors`.
- [X] T019a [P] Implement Flow-Coherence module in `code/models/flow_coherence.py` to replace the region-tracking logic and create `tests/unit/test_flow_coherence.py`. **Verify**: Run `pytest tests/unit/test_flow_coherence.py::test_flow_warp_logic`.

## Phase 4: Inference & Metric Collection

- [X] T015a [P] Implement baseline inference runner in `code/main.py` (baseline mode) that processes clips one-by-one to manage RAM. **Depends on**: T046a, T013b. **Verify**: Run `pytest tests/unit/test_main.py::test_baseline_inference_loop`.
- [X] T016a [P] Implement metric calculators for **Baseline** in `code/metrics/ssim.py`. **Details**: Compute SSIM and temporal gradient variance between **consecutive frames ($t$ and $t-1$) within the edited output video** using the edit mask to isolate background regions. **Output**: `data/metrics/baseline_ssim.json`. **Verify**: Run `pytest tests/unit/test_metrics_ssim.py::test_baseline_metrics_calculation`.
- [X] T017a [P] Implement report generator for baseline metrics in `code/analysis/reporter.py` (outputs JSON to `data/metrics/baseline_results.json`) and create `tests/unit/test_reporter.py`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_baseline_report_generation`.
- [X] T020a [P] Implement Flow-Coherence inference runner in `code/main.py`. **Depends on**: T046a, T013b. **Verify**: Run `pytest tests/unit/test_main.py::test_flow_inference_loop`.
- [X] T022a [P] Implement metric calculators for **Flow-Coherence** in `code/metrics/ssim.py`. **Details**: Compute SSIM and temporal gradient variance between **consecutive frames ($t$ and $t-1$) within the edited output video** using the edit mask. **Output**: `data/metrics/flow_ssim.json`. **Verify**: Run `pytest tests/unit/test_metrics_ssim.py::test_flow_metrics_calculation`.
- [X] T024a [P] Implement report generator for flow metrics in `code/analysis/reporter.py`. **Details**: Aggregate metrics from T022a. **Output**: `data/metrics/flow_results.json`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_flow_report_generation`.

## Phase 5: Statistical Analysis

- [X] T027a [P] Implement data loader in `code/analysis/stats.py` to load baseline and flow metrics from `data/metrics/`. **Depends on**: T017a, T024a. **Verify**: Run `pytest tests/unit/test_stats_loader.py::test_load_baseline_flow_metrics`.
- [X] T027b [P] Implement data aggregator in `code/analysis/stats.py` to merge baseline and flow metrics into paired datasets and create `tests/unit/test_stats_aggregator.py`. **Verify**: Run `pytest tests/unit/test_stats_aggregator.py::test_merge_metrics`.
- [X] T028a [P] Implement **Piecewise Regression** (Primary) and **Kolmogorov-Smirnov (K-S) test** (Secondary) in `code/analysis/stats.py` using `ruptures`. **Verify**: Run `pytest tests/unit/test_stats_piecewise.py::test_piecewise_regression_execution`.
- [X] T029a [P] Implement sensitivity analysis in `code/analysis/stats.py` sweeping cutoff values {0.01, 0.05, 0.1} and creating `tests/unit/test_stats_sensitivity.py`. **Verify**: Run `pytest tests/unit/test_stats_sensitivity.py::test_sensitivity_analysis_sweep`.
- [X] T031a [P] Implement power analysis in `code/analysis/stats.py` to validate sample size N=50 and create `tests/unit/test_stats_power.py`. **Verify**: Run `pytest tests/unit/test_stats_power.py::test_power_analysis`.
- [X] T030a [P] Implement statistical summary report in `code/analysis/reporter.py` that outputs the identified flow-magnitude threshold and sensitivity analysis table. **Verify**: Run `pytest tests/unit/test_reporter.py::test_json_summary_generation`.

## Phase 6: Reporting & Documentation

- [X] T032a [P] Generate Executive Summary section in `results/summary.md` and create `tests/unit/test_reporter.py`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_executive_summary`.
- [X] T032b [P] Generate Methodology section in `results/summary.md` and create `tests/unit/test_reporter.py`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_methodology`.
- [X] T032c [P] Generate Results section in `results/summary.md` and create `tests/unit/test_reporter.py`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_results`.
- [X] T032d [P] Generate Statistical Boundary Analysis section in `results/summary.md` and create `tests/unit/test_reporter.py`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_boundary_analysis`.
- [X] T032e [P] Generate Conclusion section in `results/summary.md` and create `tests/unit/test_reporter.py`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_conclusion`.
- [X] T032b-readme [P] Update `README.md` with execution instructions and create `tests/unit/test_docs.py`. **Verify**: Run `pytest tests/unit/test_docs.py::test_readme`.
- [X] T032b-quickstart [P] Update `docs/quickstart.md` with execution instructions and create `tests/unit/test_docs.py`. **Verify**: Run `pytest tests/unit/test_docs.py::test_quickstart`.
- [X] T032b-diagrams [P] Generate data flow diagrams and create `tests/unit/test_docs.py`. **Verify**: Run `pytest tests/unit/test_docs.py::test_diagrams`.
- [X] T040a [P] Generate histogram of flow magnitudes in `code/analysis/reporter.py` and create `tests/unit/test_reporter_plots.py`. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_histogram`.
- [X] T043a [P] Implement sensitivity plot generation in `code/analysis/reporter.py` and create `tests/unit/test_reporter_plots.py`. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_sensitivity_plot`.
- [X] T044a [P] Implement reproducibility checklist content in `README.md` and create `tests/unit/test_docs.py`. **Verify**: Run `pytest tests/unit/test_docs.py::test_checklist`.
- [X] T044b [P] Verify checklist exists in `README.md` and create `tests/unit/test_docs.py`. **Verify**: Run `pytest tests/unit/test_docs.py::test_checklist_exists`.
- [X] T046b [P] Verify no synthetic data generators in main pipeline paths and create `tests/unit/test_fabrication_guard.py`. **Verify**: Run `pytest tests/unit/test_fabrication_guard.py::test_no_synthetic`.

## Phase 7: Validation & Cleanup

- [X] T033a [P] Remove unused imports and create `tests/unit/test_linting.py`. **Verify**: Run `pytest tests/unit/test_linting.py::test_no_unused_imports`.
- [X] T033b [P] Enforce line length < 88 and create `tests/unit/test_linting.py`. **Verify**: Run `pytest tests/unit/test_linting.py::test_line_length`.
- [X] T033c [P] Run ruff check and create `tests/unit/test_linting.py`. **Verify**: Run `pytest tests/unit/test_linting.py::test_ruff_check`.
- [X] T034a [P] Profile peak RAM usage and create `tests/unit/test_metrics_resource.py`. **Verify**: Run `pytest tests/unit/test_metrics_resource.py::test_ram_profile`.
- [X] T034b [P] Optimize code to reduce RAM and create `tests/unit/test_metrics_resource.py`. **Verify**: Run `pytest tests/unit/test_metrics_resource.py::test_ram_optimization`.
- [X] T035a [P] Execute docs/quickstart.sh and create `tests/integration/test_quickstart.py`. **Verify**: Run `pytest tests/integration/test_quickstart.py::test_quickstart`.
- [X] T035b [P] Verify docs/quickstart.sh completes without error and create `tests/integration/test_quickstart.py`. **Verify**: Run `pytest tests/integration/test_quickstart.py::test_quickstart_success`.
- [X] T036b Run full pipeline on small subset and verify end-to-end data flow by creating tests/integration/test_full_pipeline.py. **Depends on**: All previous phases. **Verify**: Run `pytest tests/integration/test_full_pipeline.py::test_full_pipeline`.
- [X] T036b-2 [P] Verify end-to-end data flow and create `tests/integration/test_full_pipeline.py`. **Verify**: Run `pytest tests/integration/test_full_pipeline.py::test_end_to_end`.
- [X] T037a [P] Implement stratification logic in `code/data/processor.py` and create `tests/unit/test_processor_stratification.py`. **Verify**: Run `pytest tests/unit/test_processor_stratification.py::test_stratification_logic`.
- [X] T037b [P] Implement retry mechanism in `code/data/processor.py` and create `tests/unit/test_processor_stratification.py`. **Verify**: Run `pytest tests/unit/test_processor_stratification.py::test_retry_mechanism`.
- [X] T037c [P] Implement logging for imbalance in `code/data/processor.py` and create `tests/unit/test_processor_stratification.py`. **Verify**: Run `pytest tests/unit/test_processor_stratification.py::test_imbalance_logging`.
- [X] T038a [P] Implement pilot execution in `code/main.py` and create `tests/unit/test_main_pilot.py`. **Verify**: Run `pytest tests/unit/test_main_pilot.py::test_pilot_execution`.
- [X] T038b [P] Implement time/memory measurement in `code/main.py` and create `tests/unit/test_main_pilot.py`. **Verify**: Run `pytest tests/unit/test_main_pilot.py::test_measurement`.
- [X] T038c [P] Implement dynamic sample size adjustment in `code/main.py` and create `tests/unit/test_main_pilot.py`. **Verify**: Run `pytest tests/unit/test_main_pilot.py::test_sample_size_adjustment`.
- [X] T039a Implement N calculation logic in code/analysis/stats.py and create tests/unit/test_stats_adjustment.py. **Depends on**: T027a, T027b. **Verify**: Run `pytest tests/unit/test_stats_adjustment.py::test_n_calculation`.
- [X] T039b Update CLI arguments in code/main.py and create tests/unit/test_stats_adjustment.py. **Depends on**: T039a. **Verify**: Run `pytest tests/unit/test_stats_adjustment.py::test_cli_update`.
- [X] T039c [P] Implement pipeline abort/adjust logic in `code/main.py` and create `tests/unit/test_stats_adjustment.py`. **Verify**: Run `pytest tests/unit/test_stats_adjustment.py::test_abort_logic`.
- [X] T040b [P] Verify plot covers required range and create `tests/unit/test_reporter_plots.py`. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_plot_range`.
- [X] T041a [P] Implement directory scanning in `code/utils/audit.py` and create `tests/unit/test_audit.py`. **Verify**: Run `pytest tests/unit/test_audit.py::test_directory_scanning`.
- [X] T041b [P] Implement checksum verification in `code/utils/audit.py` and create `tests/unit/test_audit.py`. **Verify**: Run `pytest tests/unit/test_audit.py::test_checksum_verification`.
- [X] T041c [P] Implement source logging in `code/utils/audit.py` and create `tests/unit/test_audit.py`. **Verify**: Run `pytest tests/unit/test_audit.py::test_source_logging`.
- [X] T042a [P] Implement invalid flow handling section generation in `code/analysis/reporter.py` and create `tests/unit/test_reporter.py`. **Verify**: Run `pytest tests/unit/test_reporter.py::test_invalid_flow_section`.
- [X] T043b [P] Verify plot exists and is valid and create `tests/unit/test_reporter_plots.py`. **Verify**: Run `pytest tests/unit/test_reporter_plots.py::test_plot_valid`.