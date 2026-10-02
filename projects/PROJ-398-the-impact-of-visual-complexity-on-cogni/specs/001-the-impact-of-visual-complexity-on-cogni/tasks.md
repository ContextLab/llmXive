---
description: "Task list template for feature implementation"
---

# Tasks: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

**Input**: Design documents from `/specs/001-visual-complexity-on-cognitive-load/`
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
- [ ] T001b Create data directory structure (`data/stimuli/`, `data/processed/`, `data/measurements/`, `data/raw/`).
 **Verification**: Add `tests/test_structure.py::test_data_directories_exist` to assert directories exist.
- [X] T002 Initialize Python 3.11 project with pinned dependencies (`ultralytics`, `opencv-python-headless`, `statsmodels`, `scikit-learn`, `pandas`, `numpy`, `pillow`, `requests`, `streamlit`) in `requirements.txt`.
- [ ] T003 Configure linting (ruff) and formatting (black) tools.
 **Verification**: Add `tests/test_lint_config.py::test_lint_files_present` checking `.ruff.toml` and `pyproject.toml`.
- [X] T004 Implement `src/lib/utils.py` containing `set_global_seed()` and checksum utilities.
 **Verification**: Add `tests/test_utils.py::test_checksum_functions`.
- [X] T005 Implement data loading helper `src/lib/data_loader.py` that loads from verified local archives without fabricating data.
 **Verification**: Add `tests/test_data_loader.py::test_local_load_success`.
- [ ] T006 Add configuration file `src/config.py` with global random seed constant and path definitions.
 **Verification**: Add `tests/test_config.py::test_seed_defined`.
- [X] T006a Seed Enforcement Verification: Implement `tests/test_seed_enforcement.py::test_seed_used_by_yolo_and_lmm` to explicitly verify that the seed in `src/config.py` is consumed by YOLOv8n and statsmodels RNGs. **Depends on T006**.
- [X] T007 Add schema validation utilities in `src/lib/schema_validator.py`.
 **Verification**: Add `tests/test_schema_validation.py::test_backgroundframe_schema`.
- [ ] T001c Document traceability of infrastructure tasks (T001a, T001b, T003‑T007) to functional requirements (FR‑001, FR‑002, etc.) in `docs/traceability.md`. **Depends on T001a, T001b, T003‑T007**.
 **Verification**: Add `tests/test_traceability.py::test_infrastructure_traceability`.
- [ ] T001d Document traceability of directory‑creation tasks (T001a, T001b) to functional requirements (FR‑001, FR‑002, FR‑003) in `docs/traceability.md`.
 **Verification**: Add `tests/test_traceability.py::test_directory_traceability`.
- [ ] T060 [P] Verify CPU‑only environment: implement `src/lib/check_cpu.py` that asserts `torch.cuda.is_available()` is false and raises if a GPU is detected.
 **Verification**: Add `tests/test_cpu_check.py::test_cpu_only`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story can begin.

- [X] T008 [P] Add CI script `ci/check_traceability.sh` that asserts `docs/traceability.md` lists all infrastructure tasks.
- [X] T009 [P] Add CI script `ci/check_spec_alignment.sh` that asserts `docs/spec_alignment_report.md` exists.
- [ ] T014a [P] **One-time Setup: Fetch and Archive Real Stimuli**: Implement `src/metrics/fetch_and_archive.py` as a **one-time setup script** (not part of the standard runtime pipeline). It downloads the first 500 items from the HuggingFace `video-conference-backgrounds` dataset, **verifies dataset authenticity via checksums against a known manifest**, computes SHA‑256 checksums, and stores them in `data/stimuli/raw/`. Subsequent runs of the pilot MUST load from this local archive; this task only runs if the archive is missing. **This task is NOT parallel‑safe; it must complete before T014, T014b, T014c, etc.**
 **Verification**: Add `tests/test_fetch_and_archive.py::test_fetch_and_checksum_success`.
- [ ] T032d [P] **Curate Neutral Stimuli**: Implement `src/experiment/curate_neutral.py` to filter fetched clips (from T014a) and select a subset with low visual complexity (e.g., `object_count < 2`) to serve as `data/stimuli/neutral/` for the baseline task. **Depends on T014a**.
 **Verification**: Add `tests/test_curate_neutral.py::test_neutral_stimuli_categorized`.

---

## Phase 3: User Story 0 - Conduct Human Pilot Study for Metric Validation (Priority: P0) 🎯 MVP

**Goal**: Recruit a small cohort (n=20) to rate background images for perceived visual complexity to validate automated metrics (SC‑001).

### Implementation for User Story 0

- [ ] T014 [US0] **Load from Local Archive**: Implement `src/metrics/load_stimuli.py` to load the verified, checksummed images from `data/stimuli/raw/` for the pilot study. This task **strictly reads from the local archive** created by T014a and does not perform live fetching.
 **Verification**: Add `tests/test_load_stimuli.py::test_load_from_archive_success`.
- [X] T014b [US0] **Verify Stimuli Checksum**: Implement `src/metrics/verify_stimuli.py` to compute and record the SHA‑256 checksum of each loaded stimulus in `state/artifact_hashes` and compare against the archived checksum.
 **Verification**: Add `tests/test_verify_stimuli.py::test_checksum_match`.
- [ ] T014c [US0] **Validate Stimuli Readability**: Implement `src/metrics/validate_stimuli.py` to ensure each image is readable and meets a minimum resolution of 640×360 pixels; log any failures to `logs/validate_stimuli.log`.
 **Verification**: Add `tests/test_validate_stimuli.py::test_validate_stimuli_reads_and_logs`.
- [ ] T014d [US0] **Record Per‑Stimulus Metadata**: For each stimulus image, write a JSON side‑car file `data/stimuli/metadata/<image_id>.json` containing `entropy`, `color_variance`, and `object_count` as computed by the metric pipeline (T019), satisfying Constitution Principle VI.
 **Verification**: Add `tests/test_stimulus_metadata.py::test_metadata_files_exist`.
- [ ] T011a-sim [US0] **Simulated Recruitment Manager**: Implement `src/experiment/recruitment_sim.py` to generate a static, deterministic cohort of human participants with realistic demographics and pre-generated complexity ratings (based on a seed). Saves cohort to `data/measurements/cohort.json`. **This replaces external API calls to ensure reproducibility.**
 **Verification**: Add `tests/test_recruitment_sim.py::test_cohort_generation`.
- [X] T065 [US0] **Resolve Recruitment Platform Details**: Document the Prolific API usage (for future main study) and the simulation approach for the pilot in `docs/recruitment_details.md`. **Completed**.
 **Verification**: Add `tests/test_recruitment_platform.py::test_api_integration`.
- [ ] T011 [US0] **Local Pilot Interface**: Implement `src/experiment/pilot_interface.py` (Streamlit) to present images and collect complexity ratings via a **local mock server** that loads the static cohort from `data/measurements/cohort.json`. Data is entered via an in‑app form or loaded from the pre-filled state.
 **Verification**: Add integration test `tests/test_pilot_interface.py::test_end_to_end_flow`.
- [ ] T011d [US0] **Local Pilot Deployment**: Implement `src/experiment/deploy.py` to configure and deploy the Streamlit app to a **local URL accessible only to the runner or a local developer** for the pilot study.
 **Verification**: Add test `tests/test_deploy.py::test_local_deployment_url_generated`.
- [ ] T010a [US0] **Load Human Ratings CSV**: Implement a loader that reads `data/measurements/human_ratings.csv` into a pandas DataFrame for downstream analysis.
 **Verification**: Add `tests/test_metrics.py::test_metrics_csv_schema`.
- [ ] T010 [US0] **Compute Pilot Correlation**: Implement `src/metrics/validate.py` to compute Pearson correlation (r) and its p‑value between human ratings and automated metrics (entropy, variance, object count).
 **Verification**: Add unit test `tests/test_validate.py::test_correlation_calculation`.
- [ ] T012 [US0] **Persist Human Ratings**: Write collected ratings to `data/measurements/human_ratings.csv` with columns `image_id`, `participant_id`, `complexity_score`.
 **Verification**: Add test `tests/test_metrics.py::test_metrics_csv_schema`.
- [ ] T013 [US0] **Generate Pilot Validation Report**: Produce a markdown report `data/derived/pilot_validation_report.md` containing a scatter plot of human vs. automated scores, Pearson r, p‑value, and confidence interval.
 **Verification**: Add test `tests/test_validation_report.py::test_report_generated`.
- [ ] T013b [US0] **Automated Pilot Gate**: Implement `src/experiment/pilot_gate.py` to check the pilot correlation; if r < 0.5, **ABORT PIPELINE (raise SystemExit(1))** and write to `logs/pilot_review_flag.log`.
 **Verification**: Add test `tests/test_pilot_gate.py::test_gate_aborts_on_low_correlation` that asserts non-zero exit code.
- [ ] T022 [US0] **Optional Validation Against Full Pilot**: Re‑run correlation on the full pilot dataset after metric extraction; flag if r < 0.5.
 **Verification**: Add test `tests/test_full_pilot_correlation.py::test_full_correlation_threshold`.

---

## Phase 4: User Story 1 - Compute Visual Complexity Metrics (Priority: P1)

**Goal**: Extract quantitative visual complexity metrics (image entropy, color variance, object detection counts) from background frames using a CPU‑compatible pipeline.

### Implementation for User Story 1

- [ ] T020 [US1] **Handle No‑Object Images**: Ensure that images with no detectable objects produce `object_count = 0`.
 **Verification**: Add unit test `tests/test_metrics.py::test_no_objects_handled`.
- [ ] T021 [US1] **Persist Metrics CSV**: Write the computed metrics to `data/processed/metrics.csv`.
 **Verification**: Add test `tests/test_metrics.py::test_metrics_csv_schema`.
- [X] T015 [P] [US1] Unit test `test_entropy_calculation` in `tests/test_metrics.py`.
- [X] T016 [P] [US1] Unit test `test_color_variance_calculation` in `tests/test_metrics.py`.
- [ ] T017 [P] [US1] Integration test `test_yolov8n_cpu_inference` in `tests/test_metrics.py`.
- [ ] T018 [P] [US1] Contract test `test_blank_background_edge_case` in `tests/test_metrics.py`.
- [ ] T018a [P] [US1] Setup isolated test data directories in `tests/data/`.
- [ ] T061 **Performance Test for Metric Extraction**: Verify that processing 10 images at 1080p completes within 30 seconds **on the GitHub Actions free‑tier runner** and that peak RAM usage stays below **2048MB** (2GB). **Depends on T019**.
 **Verification**: Add `tests/test_nfr_performance.py::test_performance_constraints` that asserts `peak_rss < 2048MB`.
- [X] T066 **Hardware Profile Documentation**: Record that the performance benchmark is executed on the GitHub Actions free‑tier runner (2‑core CPU, 7 GB RAM). This file documents the environment used for NFR‑001 verification.
- [X] T067 **RAM Limit Details**: Document RAM limit of 2GB, expected peak RSS ≤ 1.8GB, with profiling methodology documented.
- [ ] T019 [US1] **Metric Extraction (Static Images)**: Implement `src/metrics/extract.py` to compute entropy, color variance, and object detection counts using YOLOv8n (CPU‑only). Resize inputs to 640×640 to meet NFR‑001. **Outputs**: `data/processed/metrics.csv` (conforms to `BackgroundFrame` schema) and `data/derived/performance_log.txt` with timing/RAM stats. **Verification**: Add performance test `tests/test_metrics_performance.py::test_performance_constraints` that **asserts duration < 30s and fails build if exceeded**.
- [X] T019b [US1] **Frame Extraction from Video Clips**: Implement `src/metrics/extract_frames.py` to extract frames (e.g., one frame per second) from meeting video clips stored in `data/stimuli/` using OpenCV, saving them to a temporary directory for subsequent metric extraction.
 **Verification**: Add unit test `tests/test_extract_frames.py::test_frames_extracted_correctly`.

---

## Phase 5: Pilot Validation (runs after metrics are available)

- [ ] T010 [US0] **Compute Pilot Correlation**: Implement `src/metrics/validate.py` to compute Pearson correlation (r) and p‑value between human ratings and automated metrics (entropy, variance, object count). **Depends on T012**.
 **Verification**: Add unit test `tests/test_validate.py::test_correlation_calculation`.

---

## Phase 6: User Story 2 - Administer Cognitive Load Assessment (Priority: P2)

**Goal**: Present meeting clips to participants and capture their cognitive load response via NASA‑TLX and a post‑task reaction‑time task.

### Implementation for User Story 2

- [ ] T032a **Dataset Version & Source Recording**: When fetching stimuli/clips (T032), record the dataset version identifier, source URL, and a manifest of SHA‑256 checksums in `data/metadata/dataset_manifest.json`. This ensures reproducibility and single source of truth.
 **Verification**: Add `tests/test_dataset_manifest.py::test_manifest_contains_version_and_url`.
- [ ] T032 **Fetch Real Meeting Clips (Main Study)**: Implement `src/experiment/fetch_clips.py` to download meeting background frames/clips from the same HuggingFace dataset and archive them locally. Compute SHA‑256 checksums, record dataset version, source URL, and store a manifest at `data/metadata/dataset_manifest.json`.
 **Verification**: Add `tests/test_fetch_clips.py::test_fetch_success`.
- [ ] T032b **Verify Clips & Record Source**: Implement `src/experiment/verify_clips.py` to compute SHA‑256 checksums of clips and write `data/metadata/clip_manifest.json` containing dataset URL, version ID, and per‑clip checksums.
 **Verification**: Add `tests/test_verify_clips.py::test_metadata_recorded`.
- [ ] T032c **Curate Meeting Backgrounds**: Implement `src/experiment/curate_clips.py` to filter fetched clips (resolution ≥ 640×360, duration ≤ 10 s) and output `data/processed/curated_clips.csv`. Also write `data/metadata/curated_manifest.json` recording provenance (source dataset version, filter criteria).
 **Verification**: Add `tests/test_curate_clips.py::test_curated_clips_meet_criteria`.
- [ ] T027 [US2] **Counterbalance Generator**: Implement `src/experiment/counterbalance.py` to generate Latin Square designs for stimuli and output `data/processed/counterbalance_order.json`.
 **Verification**: Add `tests/test_experiment.py::test_counterbalance_output`.
- [ ] T028a [US2] **Implement RT Measurement Mechanism**: Implement `src/experiment/rt_mechanism.py` to handle the baseline reaction‑time task with millisecond‑accurate timing loop, stimulus presentation logic, and response capture. Output `data/derived/rt_measurements.json`.
 **Verification**: Add `tests/test_experiment.py::test_rt_mechanism_accuracy`.
- [ ] T028b [US2] **Pre‑Trial Baseline Enforcer**: Implement `src/experiment/baseline_enforcer.py` to **explicitly validate that the baseline task is administered before experimental trials for every participant session** and fail the session if this ordering is violated.
 **Verification**: Add `tests/test_experiment.py::test_baseline_ordering_enforced`.
- [ ] T028 [US2] **Baseline Task Handler**: Implement `src/experiment/tasks.py` to load the neutral stimulus from `data/stimuli/neutral/` (produced by T032d in Phase 2) for the baseline condition and invoke the RT measurement mechanism from T028a to capture reaction times. **Depends on T032d**.
 **Verification**: Add `tests/test_experiment.py::test_baseline_task_loads_neutral_stimulus`.
- [ ] T029 [US2] **Session Server**: Implement `src/experiment/server.py` (Flask) to present clips, capture NASA‑TLX scores, and record reaction times. Load counterbalanced sequence from `counterbalance_order.json` and enforce exact order.
 **Verification**: Add `tests/test_experiment.py::test_server_loads_counterbalance`.
- [ ] T030 [US2] **Flag Incomplete Records**: Add logic to flag records missing TLX or RT for exclusion.
 **Verification**: Add `tests/test_experiment.py::test_incomplete_record_flagging`.
- [ ] T031 [US2] **Save Participant Sessions**: Store sessions in `data/measurements/raw/participant_sessions.csv` with required columns.
 **Verification**: Add `tests/test_experiment.py::test_participant_sessions_csv_schema`.
- [ ] T055 [US2] **Generate Task‑Difficulty Metadata**: Assign a difficulty level to each curated clip (e.g., based on object count) and store in `data/processed/clip_difficulty.csv`.
 **Verification**: Add `tests/test_experiment.py::test_clip_difficulty_csv_exists`.
- [ ] T024 [P] [US2] Unit test `test_latin_square_counterbalancing` in `tests/test_experiment.py`.
- [ ] T025 [P] [US2] Integration test `test_baseline_reaction_time_task` in `tests/test_experiment.py`.
- [ ] T026 [P] [US2] Test `test_missing_data_flagging` in `tests/test_experiment.py`.
- [ ] T062 [P] **Counterbalance Uniqueness Test**: Verify that each participant receives a unique order and that the Latin Square properties hold.
 **Verification**: Add `tests/test_experiment.py::test_counterbalance_uniqueness`.

---

## Phase 7: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Execute linear mixed‑effects models to correlate visual complexity metrics with cognitive load outcomes, controlling for task difficulty and participant ID, while applying multiple‑comparison corrections and checking for multicollinearity.

### Implementation for User Story 3

- [ ] T036 [US3] **Data Integration**: Merge `data/processed/metrics.csv`, `data/processed/clip_difficulty.csv`, and `data/measurements/raw/participant_sessions.csv` into `data/processed/analysis_input.csv`.
 **Verification**: Add `tests/test_analysis.py::test_data_integration_columns`.
- [ ] T037 [US3] Implement `src/analysis/models.py` to run linear mixed‑effects models with visual complexity as predictor and cognitive load (NASA‑TLX, RT) as outcomes.
 **Verification**: Add unit test `tests/test_analysis_models.py::test_lmm_runs`.
- [ ] T037a [US3] **Real‑Data Validation Gate**: Implement `src/analysis/real_data_gate.py` to **explicitly validate that input data for T037 is flagged as 'Real Human Data'** and block execution if synthetic data is detected.
 **Verification**: Add `tests/test_analysis.py::test_real_data_gate_blocks_synthetic`.
- [ ] T038 [US3] Implement VIF calculation in `src/analysis/models.py`; flag any predictor with VIF > 5.
 **Verification**: Add `tests/test_analysis.py::test_vif_calculation`.
- [ ] T038a [US3] **VIF Instability Flag**: Implement `src/analysis/vif_flag.py` to **explicitly generate a log entry or flag when VIF > 5 and PCA is not chosen**, satisfying FR‑003.
 **Verification**: Add `tests/test_analysis.py::test_vif_flag_generated`.
- [ ] T039 [US3] Implement PCA fallback in `src/analysis/models.py` when VIF > 5.
 **Verification**: Add integration test `tests/test_analysis.py::test_pca_fallback`.
- [ ] T040 [US3] Implement Benjamini‑Hochberg correction in `src/analysis/corrections.py`.
 **Verification**: Add unit test `tests/test_analysis.py::test_benjamini_hochberg_correction`.
- [ ] T040a [US3] **Verify BH Applied to All Metrics**: Test that the correction is applied to entropy, variance, and object count hypothesis tests.
 **Verification**: Add `tests/test_analysis.py::test_bh_applied_all_metrics`.
- [ ] T041 [P] [US3] Implement `src/analysis/sensitivity.py` to sweep α thresholds **explicitly hardcoded as {0.01, 0.05, 0.1}** and output `data/derived/stability_report.csv` and `data/derived/stability_conclusion.txt` containing the **interpretive conclusion ('Stable' or 'Unstable')** based on the SD threshold (**SD < 0.05**). CSV columns: `alpha_threshold`, `count_significant_predictors`, `sd_effect_size`.
 **Verification**: Add `tests/test_analysis.py::test_sensitivity_sweep`.
- [ ] T042 [US3] **Null‑Simulation (Pipeline Validation)**: Implement `src/analysis/null_sim.py` to run a null‑simulation (effect size = 0) and produce intermediate results required by T042c. Output to `data/derived/validation_only/`.
 **Verification**: Add `tests/test_analysis.py::test_null_simulation_fwer`.
- [ ] T042b [US3] **Null‑Simulation Isolation**: Implement `src/analysis/isolate_null.py` to ensure null‑simulation results are excluded from primary hypothesis reporting and pass the intermediate results to T042c.
 **Verification**: Add `tests/test_analysis.py::test_null_isolation`.
- [ ] T042d [US3] **FWER vs Alpha Comparison & Report**: Implement logic that compares observed family‑wise error rate (FWER) from the null‑simulation against each α threshold, generates a concise markdown report (`data/derived/fwer_validation_report.md`), and logs any violations. Include citation (, https://arxiv.org/abs/1505.06549).
 **Verification**: Add `tests/test_analysis.py::test_fwer_control`.
- [ ] T068 [US3] **Finalize FWER Comparison Implementation**: Incorporate the statistical reference in the report narrative, ensuring proper citation handling.
 **Verification**: Add `tests/test_fwer_report.py::test_citation_present`.
- [ ] T042e [US3] **Pipeline Validation Gate**: Implement `src/analysis/pipeline_gate.py` to **explicitly block T043 (ReportGeneration) if T042d (FWER check) fails**, ensuring the pipeline validation gate is enforced.
 **Verification**: Add `tests/test_analysis.py::test_pipeline_gate_blocks_on_fwer_failure`.
- [ ] T043 [US3] **Report Generation**: Implement `src/analysis/report_gen.py` to generate the final report with fixed‑effect estimates, confidence intervals, adjusted p‑values, VIF scores, FWER (from T042c), and stability metrics. Explicitly exclude any data from `validation_only/`.
 **Verification**: Add integration test `tests/test_analysis.py::test_full_report_generation`.
- [ ] T054 [US3] **Complexity‑TLX Correlation**: Compute Pearson correlation between aggregated visual‑complexity scores and NASA‑TLX scores; output `data/derived/complexity_tlx_correlation.csv` **including both r and its p‑value**.
 **Verification**: Add `tests/test_analysis.py::test_complexity_tlx_correlation_file`.
- [ ] T054c [US3] **Record Correlation p‑value**: Extend T054 to also store the p‑value alongside r in the same CSV (satisfying SC‑002).
 **Verification**: Same as above.
- [ ] T053 [US3] **Reaction‑Time Difference Analysis (SC‑003)**: Compute the reaction‑time difference between high‑complexity and low‑complexity conditions relative to each participant's baseline RT; store results in `data/derived/rt_diff.csv`.
 **Verification**: Add `tests/test_analysis.py::test_rt_difference_computation`.
- [ ] T033 [P] [US3] Unit test `test_benjamini_hochberg_correction` in `tests/test_analysis.py`.
- [ ] T034 [P] [US3] Unit test `test_vif_calculation` in `tests/test_analysis.py`.
- [ ] T035 [P] [US3] Integration test `test_full_analysis_pipeline` in `tests/test_analysis.py`.

---

## Phase 8: User Story 4 - Conduct Main Study with Real Human Participants (Priority: P3)

**Goal**: Collect real human data (NASA‑TLX, reaction times) and run the primary hypothesis test.

- [ ] T056 [US4] **Conduct Main Study**: Implement the full study workflow (recruitment, consent, session scheduling, data capture via `src/experiment/server.py`) and store all collected data in `data/measurements/raw/main_study_sessions.csv` flagged as "Real Human Data".
 **Verification**: Add CI check `ci/check_main_study_data.sh` that asserts the file exists and contains the required columns.
- [ ] T069 [US4] **Detail Main‑Study Workflow**: Write a comprehensive SOP (`docs/main_study_sop.md`) covering participant onboarding, consent collection, session scheduling, data capture (NASA‑TLX, RT), real‑data flagging, and post‑study de‑identification.
 **Verification**: Add test `tests/test_main_study_sop.py::test_sop_complete`.
- [ ] T063 [P] [US4] **Real‑Data Flag Check**: Implement CI script `ci/check_real_data_flag.sh` to verify that `data/measurements/raw/main_study_sessions.csv` includes a column `data_source` with the value `"Real Human Data"` for every row.
 **Verification**: Add `tests/test_main_study_flag.py::test_real_data_flag_present`.

---

## Phase 9: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T044 [P] Update `docs/quickstart.md` with specific CPU‑only setup instructions and YOLOv8n installation steps.
 **Verification**: Add CI script `ci/check_quickstart.sh` that confirms the CPU‑only section is present.
- [ ] T045 [P] Update `docs/data-model.md` with new entity attributes and metric definitions.
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
- [ ] T048b [P] **Automated Reproducibility Test**: Assert that T048a exits with code 0 and that expected artifacts (`performance_log.txt`, `stability_report.csv`, `fwer_validation_report.md`, etc.) are present.
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

---

## Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Story 0 (Phase 3)** → **User Story 1 (Phase 4)** → **Pilot Validation (Phase 5)** → **User Story 2 (Phase 6)** → **User Story 3 (Phase 7)** → **User Story 4 (Phase 8)** → **Polish (Phase 9)**
- Parallelism is indicated by `[P]` tags; tasks respect data‑flow ordering.