---
description: "Task list template for feature implementation"
---

# Tasks: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

**Input**: Design documents from `/specs/001-the-impact-of-visual-complexity-on-cogni/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US0, US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`

## Phase 0: Specification Alignment (Critical Prerequisite)

- [X] T000 [P] Perform a spec‑task alignment review: compare `spec.md` against the drafted `tasks.md`, flag any contradictions, and produce `docs/spec_alignment_report.md`.
- [X] T000a [P] Generate `docs/spec_alignment_report.md` summarizing alignment findings.  
  **Verification**: Add `tests/test_spec_alignment.py::test_report_exists` to assert the report file exists.
- [X] T000b [P] Verify `docs/spec_alignment_report.md` exists and is non-empty.  
  **Verification**: Add `tests/test_spec_alignment.py::test_report_not_empty`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create code directory structure (`src/lib/`, `src/metrics/`, `src/experiment/`, `src/analysis/`, `tests/`).  
  **Verification**: Add `tests/test_structure.py::test_code_directories_exist` to assert directories exist.
- [ ] T001a_verify_dirs Verify code directories exist after creation.  
  **Verification**: Add `tests/test_structure.py::test_code_directories_exist`.
- [ ] T001b Create data directory structure (`data/stimuli/`, `data/processed/`, `data/measurements/`, `data/raw/`).  
  **Verification**: Add `tests/test_structure.py::test_data_directories_exist`.
- [ ] T001b_verify_dirs Verify data directories exist after creation.  
  **Verification**: Add `tests/test_structure.py::test_data_directories_exist`.
- [X] T002 Initialize Python 3.11 project with pinned dependencies (`ultralytics`, `opencv-python-headless`, `statsmodels`, `scikit-learn`, `pandas`, `numpy`, `pillow`, `requests`, `streamlit`) in `requirements.txt`.
- [ ] T003_create_lint_files Create linting (`.ruff.toml`) and formatting (`pyproject.toml`) configuration files.  
  **Verification**: Add `tests/test_lint_config.py::test_lint_files_present` checking `.ruff.toml` and `pyproject.toml`.
- [ ] T003_verify_lint_files Verify linting config files exist.  
  **Verification**: Same test as above.
- [X] T004 Implement `src/lib/utils.py` containing `set_global_seed()` and checksum utilities.  
  **Verification**: Add `tests/test_utils.py::test_checksum_functions`.
- [X] T005 Implement data loading helper `src/lib/data_loader.py` that loads from verified local archives without fabricating data.  
  **Verification**: Add `tests/test_data_loader.py::test_local_load_success`.
- [X] T006 Add configuration file `src/config.py` with global random seed constant and path definitions.  
  **Verification**: Add `tests/test_config.py::test_seed_defined`.
- [X] T006a Seed Enforcement Verification: Implement `tests/test_seed_enforcement.py::test_seed_used_by_yolo_and_lmm` to explicitly verify that the seed in `src/config.py` is consumed by YOLOv8n and statsmodels RNGs. **Depends on T006**.
- [X] T007 Add schema validation utilities in `src/lib/schema_validator.py`.  
  **Verification**: Add `tests/test_schema_validation.py::test_backgroundframe_schema`.
- [X] T001c Document traceability of infrastructure tasks (T001a, T001b, T003‑T007) to functional requirements (FR‑001, FR‑002, etc.) in `docs/traceability.md`. **Depends on T001a, T001b, T003‑T007**.  
  **Verification**: Add `tests/test_traceability.py::test_infrastructure_traceability`.
- [X] T060 [P] Verify CPU‑only environment: implement `src/lib/check_cpu.py` that asserts `torch.cuda.is_available()` is false and raises if a GPU is detected.  
  **Verification**: Add `tests/test_cpu_check.py::test_cpu_only`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story can begin.

- [X] T008 [P] Add CI script `ci/check_traceability.sh` that asserts `docs/traceability.md` lists all infrastructure tasks.
- [X] T009 [P] Add CI script `ci/check_spec_alignment.sh` that asserts `docs/spec_alignment_report.md` exists.
- [X] T014a **One-time Setup: Fetch and Archive Real Stimuli**: Implement `src/metrics/fetch_and_archive.py` as a **one-time setup script** (not part of the standard runtime pipeline). It downloads an initial subset of items from the HuggingFace `video-conference-backgrounds` dataset, **verifies dataset authenticity via checksums against a known manifest**, computes SHA‑256 checksums, and stores them in `data/stimuli/raw/`. Subsequent runs of the pilot MUST load from this local archive; this task only runs if the archive is missing. **This task is NOT parallel‑safe; it must complete before dependent tasks.**  
  **Verification**: Add `tests/test_fetch_and_archive.py::test_fetch_and_checksum_success`.
- [X] T032d [P] **Curate Neutral Stimuli**: Implement `src/experiment/curate_neutral.py` to filter fetched clips (from T014a) and select a subset with low visual complexity (e.g., `object_count < 2`) to serve as `data/stimuli/neutral/` for the baseline task. **Depends on T014a**.  
  **Verification**: Add `tests/test_curate_neutral.py::test_neutral_stimuli_categorized`.

---

## Phase 3: User Story 0 - Conduct Human Pilot Study for Metric Validation (Priority: P0) 🎯 MVP

**Goal**: Recruit a small cohort (n=20) to rate background images for perceived visual complexity to validate automated metrics (SC‑001).

- [X] T014 [US0] **Load from Local Archive**: Implement `src/metrics/load_stimuli.py` to load the verified, checksummed images from `data/stimuli/raw/` for the pilot study. This task **strictly reads from the local archive** created by T014a and does not perform live fetching.  
  **Verification**: Add `tests/test_load_stimuli.py::test_load_from_archive_success`.
- [X] T014b [US0] **Verify Stimuli Checksum**: Implement `src/metrics/verify_stimuli.py` to compute and record the SHA‑256 checksum of each loaded stimulus in `state/artifact_hashes` and compare against the archived checksum.  
  **Verification**: Add `tests/test_verify_stimuli.py::test_checksum_match`.
- [X] T014c [US0] **Validate Stimuli Readability**: Implement `src/metrics/validate_stimuli.py` to ensure each image is readable and meets a minimum resolution of 640×360 pixels; log any failures to `logs/validate_stimuli.log`.  
  **Verification**: Add `tests/test_validate_stimuli.py::test_validate_stimuli_reads_and_logs`.
- [ ] T014d_compute [US0] **Record Per‑Stimulus Metadata**: For each stimulus image, write a JSON side‑car file `data/stimuli/metadata/<image_id>.json` containing `entropy`, `color_variance`, and `object_count` as computed by the metric pipeline (T019_pilot), satisfying Constitution Principle VI. **Includes verification that the JSON adheres to the BackgroundFrame schema.**  
  **Verification**: Add `tests/test_stimulus_metadata.py::test_metadata_files_exist` and `tests/test_stimulus_metadata.py::test_metadata_schema_validation`.
- [ ] T011a_real [US0] **Real Recruitment Manager**: Implement `src/experiment/recruitment_real.py` to interface with the Prolific API (or similar) to recruit 20 real participants, store cohort metadata in `data/measurements/cohort.json`.  
  **Verification**: Add `tests/test_recruitment_real.py::test_cohort_creation`.
- [ ] T011 [US0] **Pilot Interface (Real)**: Implement `src/experiment/pilot_interface.py` (Streamlit) to present images and collect complexity ratings from real participants, storing results directly to `data/measurements/human_ratings.csv`. **Logic must include:** (1) Capturing the git commit hash of the app code and recording it in `cohort.json` and `human_ratings.csv` to satisfy Constitution Principle VII; (2) Linking ratings to the specific cohort registered by T011a_real. **Depends on T011a_real**.  
  **Verification**: Add integration test `tests/test_pilot_interface.py::test_end_to_end_flow`.
- [X] T011a_ui [US0] **Pilot UI Implementation**: Add Streamlit UI components (image display, rating slider, submit button) within `pilot_interface.py`.  
  **Verification**: Covered by `test_pilot_interface`.
- [X] T012_impl [US0] **Persist Human Ratings**: Write collected ratings to `data/measurements/human_ratings.csv` with columns `image_id`, `participant_id`, `complexity_score`.  
  **Verification**: Add `tests/test_metrics.py::test_metrics_csv_schema`.
- [X] T012_test [US0] **Human Ratings Persistence Test**: Verify that after a mock rating session the CSV file is created and correctly formatted.  
  **Verification**: Same as above.
- [X] T010a_impl [US0] **Human Ratings Loader**: Implement a loader that reads `data/measurements/human_ratings.csv` into a pandas DataFrame for downstream analysis.  
  **Verification**: Add `tests/test_metrics.py::test_metrics_csv_schema`.
- [X] T010a_test [US0] **Human Ratings Loader Test**: Verify loader returns a DataFrame with expected columns and types.  
  **Verification**: Same test file.
- [X] T019_pilot [US0] **Execute Metric Extraction on Pilot Stimuli**: Run `src/metrics/extract.py` (from T019) on the stimuli loaded in T014. **Depends on T014**. This task generates the automated metrics (entropy, variance, object count) required for the pilot correlation.  
  **Verification**: Add `tests/test_metrics.py::test_pilot_metrics_generated`.
- [ ] T010 [US0] **Compute Pilot Correlation**: Implement `src/metrics/validate.py` to compute Pearson correlation (r) and its p‑value between human ratings (from T011) and automated metrics (from T019_pilot). **Depends on T019_pilot, T011**.  
  **Verification**: Add unit test `tests/test_validate.py::test_correlation_calculation`.
- [ ] T074 [US0] **Compute Individual Metric Correlations**: Extend `src/metrics/validate.py` to compute separate Pearson correlations for each of entropy, color variance, and object count against human scores, storing results in `data/derived/individual_metric_correlations.csv`.  
  **Verification**: Add test `tests/test_validate.py::test_individual_metric_correlations`.
- [X] T013_report_gen [US0] **Generate Pilot Validation Report**: Produce a markdown report `data/derived/pilot_validation_report.md` containing a scatter plot of human vs. automated scores, Pearson r, p‑value, and confidence interval.  
  **Verification**: Add test `tests/test_validation_report.py::test_report_generated`.
- [X] T013_report_test [US0] **Pilot Report Presence Test**: Verify the report file exists after generation.  
  **Verification**: Same test.
- [X] T013b [US0] **Automated Pilot Gate**: Implement `src/experiment/pilot_gate.py` to check the pilot correlation; if r < 0.5, **ABORT PIPELINE (raise SystemExit(1))** and write to `logs/pilot_review_flag.log`.  
  **Verification**: Add `tests/test_pilot_gate.py::test_gate_aborts_on_low_correlation`.

---

## Phase 4: User Story 1 - Compute Visual Complexity Metrics (Priority: P1)

**Goal**: Extract quantitative visual complexity metrics (image entropy, color variance, object detection counts) from background frames using a CPU‑compatible pipeline.

- [X] T019 [FR-001] [US1] **Metric Extraction (Static Images)**: Implement `src/metrics/extract.py` to compute entropy, color variance, and object detection counts using YOLOv8n (CPU‑only). Resize inputs to 640×640 to meet NFR‑001. **Outputs**: `data/processed/metrics.csv` (conforms to `BackgroundFrame` schema) and `data/derived/performance_log.txt` with timing/RAM stats.  
  **Verification**: Add performance test `tests/test_metrics_performance.py::test_performance_constraints` that **asserts duration < 30s**.
- [ ] T020 [US1] **Handle No‑Object Images**: Ensure that images with no detectable objects produce `object_count = 0`.  
  **Verification**: Add unit test `tests/test_metrics.py::test_no_objects_handled`.
- [ ] T021 [US1] **Persist Metrics CSV**: Write the computed metrics to `data/processed/metrics.csv`.  
  **Verification**: Add test `tests/test_metrics.py::test_metrics_csv_schema`.
- [X] T015 [P] [US1] Unit test `test_entropy_calculation` in `tests/test_metrics.py`.
- [X] T016 [P] [US1] Unit test `test_color_variance_calculation` in `tests/test_metrics.py`.
- [ ] T017 [P] [US1] Integration test `test_yolov8n_cpu_inference` in `tests/test_metrics.py`.
- [ ] T018 [P] [US1] Contract test `test_blank_background_edge_case` in `tests/test_metrics.py`.
- [ ] T018a Setup isolated test data directories in `tests/data/`.
- [ ] T018a_test Verify isolated test data directories exist.  
  **Verification**: Add `tests/test_isolated_dirs.py::test_directories_exist`.
- [X] T061 [P] **Performance Test for Metric Extraction**: Verify that processing 10 images at 1080p completes within 30 seconds and Peak RAM stays below a reasonable memory threshold on the GitHub Actions free‑tier runner. **Depends on T019**.  
  **Verification**: Add `tests/test_nfr_performance.py::test_performance_constraints`.
- [X] T066 **Hardware Profile Documentation**: Record that the performance benchmark is executed on the GitHub Actions free‑tier runner (multi‑core CPU, 7 GB RAM).  
- [X] T067 **RAM Limit Details**: Document RAM limit of a modest gigabyte-level amount in `docs/hardware_requirements.md`.
- [X] T066_verify_doc **Verify Hardware Profile Doc**: CI script to assert `docs/hardware_requirements.md` contains the hardware profile section.  
  **Verification**: Add `tests/test_hardware_doc.py::test_hardware_profile_present`.
- [X] T067_verify_doc **Verify RAM Limit Doc**: CI script to assert `docs/hardware_requirements.md` contains the RAM limit statement.  
  **Verification**: Add `tests/test_hardware_doc.py::test_ram_limit_present`.
- [X] T019b [US1] **Frame Extraction from Video Clips**: Implement `src/metrics/extract_frames.py` to extract frames (e.g., one frame per second) from meeting video clips stored in `data/stimuli/` using OpenCV, saving them to a temporary directory for subsequent metric extraction.  
  **Verification**: Add unit test `tests/test_extract_frames.py::test_frames_extracted_correctly`.

---

## Phase 5: Pilot Validation (runs after metrics are available)

**Goal**: Validate automated metrics against human ratings using the data generated in Phases 3 and 4.

- [X] T013_report_gen [US0] **Generate Pilot Validation Report**: Produce a markdown report `data/derived/pilot_validation_report.md` containing a scatter plot of human vs. automated scores, Pearson r, p‑value, and confidence interval.  
  **Verification**: Add test `tests/test_validation_report.py::test_report_generated`.
- [X] T013_report_test [US0] **Pilot Report Presence Test**: Verify the report file exists after generation.  
  **Verification**: Same test.
- [X] T013b [US0] **Automated Pilot Gate**: Implement `src/experiment/pilot_gate.py` to check the pilot correlation; if r < 0.5, **ABORT PIPELINE (raise SystemExit(1))** and write to `logs/pilot_review_flag.log`.  
  **Verification**: Add `tests/test_pilot_gate.py::test_gate_aborts_on_low_correlation`.

---

## Phase 6: User Story 2 - Administer Cognitive Load Assessment (Priority: P2)

**Goal**: Present meeting clips to participants and capture their cognitive load response via NASA‑TLX and a post‑task reaction‑time task.

- [ ] T032a **Dataset Version & Source Recording**: When fetching stimuli/clips (T032) record the dataset version identifier, source URL, and a manifest of cryptographic checksums in `data/metadata/dataset_manifest.json`.  
  **Verification**: Add `tests/test_dataset_manifest.py::test_manifest_contains_version_and_url`.
- [X] T032 **Fetch Real Meeting Clips (Main Study)**: Implement `src/experiment/fetch_clips.py` to download meeting background frames/clips from the same HuggingFace dataset and archive them locally. Compute SHA‑256 checksums, record dataset version, source URL, and store a manifest at `data/metadata/dataset_manifest.json`.  
  **Verification**: Add `tests/test_fetch_clips.py::test_fetch_success`.
- [ ] T032b **Verify Clips & Record Source**: Implement `src/experiment/verify_clips.py` to compute SHA‑256 checksums of clips and write `data/metadata/clip_manifest.json` containing dataset URL, version ID, and per‑clip checksums.  
  **Verification**: Add `tests/test_verify_clips.py::test_metadata_recorded`.
- [ ] T032c **Curate Meeting Backgrounds**: Implement `src/experiment/curate_clips.py` to filter fetched clips (resolution ≥ 640×360, duration ≤ 10 s) and output `data/processed/curated_clips.csv`. Also write `data/metadata/curated_manifest.json` recording provenance (source dataset version, filter criteria).  
  **Verification**: Add `tests/test_curate_clips.py::test_curated_clips_meet_criteria`.
- [ ] T027 [FR-002c] **Counterbalance Generator**: Implement `src/experiment/counterbalance.py` to generate Latin Square designs for stimuli and output `data/processed/counterbalance_order.json`.  
  **Verification**: Add `tests/test_experiment.py::test_counterbalance_output`.
- [ ] T028a [FR-002b] **Implement RT Measurement Mechanism**: Implement `src/experiment/rt_mechanism.py` to handle the baseline reaction‑time task with millisecond‑accurate timing loop, stimulus presentation logic, and response capture. Output `data/derived/rt_measurements.json`.  
  **Verification**: Add `tests/test_experiment.py::test_rt_mechanism_accuracy`.
- [ ] T028b **Pre‑Trial Baseline Enforcer**: Implement `src/experiment/baseline_enforcer.py` to **explicitly validate that the baseline task is administered before experimental trials for every participant session** and fail the session if this ordering is violated.  
  **Verification**: Add `tests/test_experiment.py::test_baseline_ordering_enforced`.
- [ ] T028 [US2] **Baseline Task Handler**: Implement `src/experiment/tasks.py` to load the neutral stimulus from `data/stimuli/neutral/` (produced by T032d) for the baseline condition and invoke the RT measurement mechanism from T028a to capture reaction times. **Depends on T032d**.  
  **Verification**: Add `tests/test_experiment.py::test_baseline_task_loads_neutral_stimulus`.
- [ ] T029 [US2] **Session Server**: Implement `src/experiment/server.py` (Flask) to present clips, capture NASA‑TLX scores, and record reaction times. **Logic must include:** (1) Loading the counterbalanced sequence from `counterbalance_order.json` (T027); (2) **Enforcing** the exact order during the session; (3) **Recording** the specific permutation ID assigned to each participant in the final dataset. **Depends on T027, T032, T032c**.  
  **Verification**: Add `tests/test_experiment.py::test_server_loads_counterbalance`.
- [ ] T030 [US2] **Flag Incomplete Records**: Add logic to flag records missing TLX or RT for exclusion.  
  **Verification**: Add `tests/test_experiment.py::test_incomplete_record_flagging`.
- [ ] T031 [US2] **Save Participant Sessions**: Store sessions in `data/measurements/raw/participant_sessions.csv` with required columns. **Logic must include:** (1) Recording the specific counterbalanced order ID used for each participant to ensure data traceability per FR-002c. **Depends on T027, T029**.  
  **Verification**: Add `tests/test_experiment.py::test_participant_sessions_csv_schema`.
- [ ] T055 **Generate Task‑Difficulty Metadata**: Assign a difficulty level to each curated clip (e.g., based on object count) and store in `data/processed/clip_difficulty.csv`.  
  **Verification**: Add `tests/test_experiment.py::test_clip_difficulty_csv_exists`.
- [ ] T024 [P] **Unit test `test_latin_square_counterbalancing`** in `tests/test_experiment.py`.
- [ ] T025 [P] **Integration test `test_baseline_reaction_time_task`** in `tests/test_experiment.py`.
- [ ] T026 [P] **Test `test_missing_data_flagging`** in `tests/test_experiment.py`.
- [ ] T062 [P] **Counterbalance Uniqueness Test**: Verify that each participant receives a unique order and that the Latin Square properties hold.  
  **Verification**: Add `tests/test_experiment.py::test_counterbalance_uniqueness`.

---

## Phase 7: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Execute linear mixed‑effects models to correlate visual complexity metrics with cognitive load outcomes, controlling for task difficulty and participant ID, while applying multiple-comparison corrections and checking for multicollinearity.

- [ ] T036 **Data Integration**: Merge `data/processed/metrics.csv`, `data/processed/clip_difficulty.csv`, and `data/measurements/raw/participant_sessions.csv` into `data/processed/analysis_input.csv`.  
  **Verification**: Add `tests/test_analysis.py::test_data_integration_columns`.
- [ ] T037 [FR-003] **Linear Mixed‑Effects Models**: Implement `src/analysis/models.py` to run linear mixed-effects models with visual complexity as predictor and cognitive load (NASA-TLX, RT) as outcomes.  
  **Verification**: Add unit test `tests/test_analysis_models.py::test_lmm_runs`.
- [ ] T037a **Real‑Data Validation Gate**: Implement `src/analysis/real_data_gate.py` to **explicitly validate that input data for T037 is flagged as 'Real Human Data'** and block execution if synthetic data is detected.  
  **Verification**: Add `tests/test_analysis.py::test_real_data_gate_blocks_synthetic`.
- [ ] T038 **VIF Calculation**: Implement VIF calculation in `src/analysis/models.py`; flag any predictor with VIF > 5.  
  **Verification**: Add `tests/test_analysis.py::test_vif_calculation`.
- [ ] T038a **VIF Instability Flag**: Implement `src/analysis/vif_flag.py` to **explicitly generate a log entry or flag when VIF > 5 and PCA is not chosen**, satisfying FR‑003.  
  **Verification**: Add `tests/test_analysis.py::test_vif_flag_generated`.
- [ ] T039 **PCA Fallback**: Implement PCA fallback in `src/analysis/models.py` when VIF > 5.  
  **Verification**: Add integration test `tests/test_analysis.py::test_pca_fallback`.
- [ ] T040 **Benjamini‑Hochberg Correction**: Implement correction in `src/analysis/corrections.py`.  
  **Verification**: Add unit test `tests/test_analysis.py::test_benjamini_hochberg_correction`.
- [ ] T040a **Verify BH Applied to All Metrics**: Test that the correction is applied to entropy, variance, and object count hypothesis tests.  
  **Verification**: Add `tests/test_analysis.py::test_bh_applied_all_metrics`.
- [ ] T041 [FR-005] **Sensitivity Analysis Sweep**: Implement `src/analysis/sensitivity.py` to sweep α thresholds **explicitly hardcoded as {0.01, 0.05, 0.1}**. **Logic must include:** (1) Computing the count of significant predictors for each threshold; (2) **Calculating the Standard Deviation (SD) of effect sizes** across the sweep; (3) Writing `data/derived/stability_report.csv` (columns: `alpha_threshold`, `count_significant_predictors`, `sd_effect_size`); (4) Writing `data/derived/effect_size_sd.csv` containing the SD values; (5) Writing `data/derived/stability_conclusion.txt` with the interpretation ('Stable' if SD < 0.05). **Depends on T037**.  
  **Verification**: Add `tests/test_analysis.py::test_sensitivity_sweep`.
- [ ] T041b [FR-005b][SC-005] **Stability Definition Documentation**: Document that stability is defined as both a low count variance across thresholds and SD of effect sizes < 0.05; generate a summary in `data/derived/stability_definition.md`. **Depends on T041**.  
  **Verification**: Add `tests/test_analysis.py::test_stability_definition_present`.
- [ ] T041b_test **Stability Definition Test**: Verify `stability_definition.md` exists and contains the required definition.  
  **Verification**: Same test.
- [ ] T042 [FR-007] **Null‑Simulation (Pipeline Validation)**: Implement `src/analysis/null_sim.py` to run a null‑simulation (effect size = 0) and produce intermediate results required by T042d. Output to `data/derived/validation_only/`.  
  **Verification**: Add `tests/test_analysis.py::test_null_simulation_fwer`.
- [ ] T042b **Null‑Simulation Isolation**: Implement `src/analysis/isolate_null.py` to ensure null‑simulation results are excluded from primary hypothesis reporting and pass the intermediate results to T042c.  
  **Verification**: Add `tests/test_analysis.py::test_null_isolation`.
- [ ] T042c **Pass Null Results Forward**: Transfer null‑simulation outputs to the reporting pipeline (used by T042d).  
  **Verification**: Add `tests/test_analysis.py::test_null_results_forwarded`.
- [ ] T042d **FWER vs Alpha Comparison & Report**: Implement logic that compares observed family‑wise error rate (FWER) from the null‑simulation against each α threshold, generates a markdown report (`data/derived/fwer_validation_report.md`), and logs any violations. Include citation (https://arxiv.org/abs/1505.06549). **Depends on T042c**.  
  **Verification**: Add `tests/test_analysis.py::test_fwer_control`.
- [ ] T042_gate [FR-007] **Pipeline Validation Gate**: Implement `src/analysis/pipeline_gate.py` to **explicitly block T043 (ReportGeneration) if T042d (FWER check) fails**, ensuring the pipeline validation gate is enforced.  
  **Verification**: Add `tests/test_analysis.py::test_pipeline_gate_blocks_on_fwer_failure`.
- [ ] T043 **Report Generation**: Implement `src/analysis/report_gen.py` to generate the final report with fixed‑effect estimates, confidence intervals, adjusted p‑values, VIF scores, FWER (from T042c), and stability metrics. Explicitly exclude any data from `validation_only/`.  
  **Verification**: Add integration test `tests/test_analysis.py::test_full_report_generation`.
- [ ] T054 [SC-002] **Complexity‑TLX Correlation**: Compute Pearson correlation between aggregated visual‑complexity scores and NASA‑TLX scores; output `data/derived/complexity_tlx_correlation.csv` **including both r and its p‑value**.  
  **Verification**: Add test `tests/test_analysis.py::test_complexity_tlx_correlation_file`.
- [ ] T053 [SC-003] **Reaction‑Time Difference Analysis**: Compute the reaction‑time difference between high-complexity and low-complexity conditions relative to each participant's baseline RT; store results in `data/derived/rt_diff.csv`.  
  **Verification**: Add `tests/test_analysis.py::test_rt_difference_computation`.
- [ ] T033 [P] Unit test `test_benjamini_hochberg_correction` in `tests/test_analysis.py`.
- [ ] T034 [P] Unit test `test_vif_calculation` in `tests/test_analysis.py`.
- [ ] T035 [P] Integration test `test_full_analysis_pipeline` in `tests/test_analysis.py`.

---

## Phase 8: User Story 4 - Conduct Main Study with Real Human Participants (Priority: P3)

**Goal**: Collect real human data (NASA‑TLX, reaction times) and run the primary hypothesis test.

- [ ] T056 [US4] **Conduct Main Study**: Implement the full study workflow (recruitment, consent, session scheduling, data capture via `src/experiment/server.py`) and store all collected data in `data/measurements/raw/main_study_sessions.csv` flagged as "Real Human Data".  
  **Verification**: Add CI check `ci/check_main_study_data.sh` that asserts the file exists and contains the required columns.
- [ ] T069 **Detail Main‑Study SOP**: Write a comprehensive SOP (`docs/main_study_sop.md`) covering participant onboarding, consent collection, session scheduling, data capture (NASA‑TLX, RT), real‑data flagging, and post‑study de‑identification.  
  **Verification**: Add test `tests/test_main_study_sop.py::test_sop_complete`.
- [ ] T063 **Real‑Data Flag Check**: Implement CI script `ci/check_real_data_flag.sh` to verify that `data/measurements/raw/main_study_sessions.csv` includes a column `data_source` with the value `"Real Human Data"` for every row.  
  **Verification**: Add `tests/test_main_study_flag.py::test_real_data_flag_present`.

---

## Phase 9: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T044 [P] Update `docs/quickstart.md` with specific CPU‑only setup instructions and YOLOv8n installation steps.  
  **Verification**: Add CI script `ci/check_quickstart.sh` that confirms the CPU‑only section is present.
- [ ] T045 [P] Update `docs/data-model.md` with new entity attributes and metric definitions (BackgroundFrame, ParticipantSession, AnalysisResult, HumanRating).  
  **Verification**: Add CI script `ci/check_data_model.sh` that validates inclusion of new attributes.
- [ ] T046 [P] Update `docs/contracts/` with final API/Interface definitions.  
  **Verification**: Add CI script `ci/check_contracts.sh` that loads each schema and validates against a sample instance.
- [ ] T047 [P] Additional unit tests for edge cases. **Concrete Tests**: `tests/test_edge_cases.py::test_skewed_distribution_handling` (input: skewed array, expected: robust stats), `tests/test_edge_cases.py::test_attention_check_failure` (input: random responses, expected: flag).  
  **Verification**: Add `tests/test_edge_cases.py::test_skewed_distribution_handling` and `tests/test_edge_cases.py::test_attention_check_failure`.
- [ ] T048a **Automated Reproducibility Orchestrator**: Execute sub‑tasks T048a1‑T048a4 sequentially on a fresh temporary directory, then produce `data/derived/reproducibility_summary.md`. Sub‑tasks:  
  - T048a1: Execute full pipeline on minimal real‑data subset.  
  - T048a2: Collect key artifacts (performance log, stability report, FWER report).  
  - T048a3: Summarize results into `reproducibility_summary.md`.  
  - T048a4: Clean temporary directory.  
  **Verification**: Add wrapper test `tests/test_reproducibility.py::test_orchestrator_success`.
- [ ] T048b [P] **Automated Reproducibility Test**: Assert that the orchestrator exits with code 0 and that expected artifacts (`performance_log.txt`, `stability_report.csv`, `fwer_validation_report.md`, etc.) are present.  
  **Verification**: Covered by the wrapper test above.
- [ ] T048c [P] **Preprocess Provenance**: Version the preprocessing scripts (`src/analysis/preprocess.py`) and generate a provenance file `data/derived/preprocess_provenance.md` documenting code version, hash, timestamps.  
  **Verification**: Add test `tests/test_preprocess_provenance.py::test_preprocess_versioning`.
- [ ] T049 [P] Create `docs/data-provenance.md` documenting source URLs, checksums, version IDs, and licensing for all stimulus and clip datasets.  
  **Verification**: Add test `tests/test_data_provenance.py::test_provenance_file_exists`.
- [ ] T050 [P] Add CI workflow (`.github/workflows/pipeline.yml`) that runs the full pipeline on a minimal real‑data subset and fails if any expected artifact is missing.  
  **Verification**: Add CI script `ci/check_ci_workflow.sh` that parses the workflow and ensures artifact checks are present, plus test `tests/test_ci_workflow.py::test_workflow_checks_artifacts`.
- [ ] T051 [P] Document all random‑seed settings in `src/config.py` and reference them in `docs/quickstart.md`.  
  **Verification**: Covered by `tests/test_config.py::test_seed_defined`.
- [ ] T052 [P] Implement schema validation tests that load each JSON/CSV output and verify compliance with schemas defined in `contracts/`.  
  **Verification**: Concrete tests in `tests/test_schema_validation.py`.
- [ ] T061a [P] **NFR‑001 Enforcement Gate**: Implement `ci/check_nfr_001.sh` that **explicitly fails the build if the metric extraction pipeline exceeds 30 seconds**, ensuring NFR‑001 is enforced.  
  **Verification**: Add `tests/test_nfr_enforcement.py::test_nfr_001_gate_fails_on_timeout`.
- [ ] T064 [P] Update `docs/hardware_requirements.md` to explicitly state CPU‑only constraints, RAM limits, and the prohibition of GPU usage for this project.  
  **Verification**: Add CI script `ci/check_hardware_requirements.sh` that searches for the required statements.
- [ ] T070 [P] **Real Data Fetch Failure Test**: Implement `tests/test_data_loader.py::test_fetch_failure_raises` to verify that `src/lib/data_loader.py` raises a `ConnectionError` (or similar) when the real dataset URL is unreachable, ensuring no synthetic fallback occurs.  
  **Verification**: Assert that the test fails if a `try/except` block swallows the error and returns mock data.
- [ ] T075 [P] **Final Report Presence Check**: Add CI script `ci/check_final_report.sh` that asserts `reports/final_report.md` (generated by T043) exists after a successful pipeline run.  
  **Verification**: Add test `tests/test_final_report.py::test_report_file_exists`.