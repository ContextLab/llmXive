---
description: "Task list template for feature implementation"
---

# Tasks: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

**Input**: Design documents from `/specs/001-visual-complexity-cognitive-load/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US0, US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0: Specification Alignment (Critical Prerequisite)

- [ ] T000 [P] Perform a spec‑task alignment review: compare `spec.md` against the drafted `tasks.md`, flag any contradictions, and produce `docs/spec_alignment_report.md`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create code directory structure (`src/lib/`, `src/metrics/`, `src/experiment/`, `src/analysis/`, `tests/`)
- [ ] T001b [P] Create data directory structure (`data/stimuli/`, `data/processed/`, `data/measurements/`, `data/raw/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies (`ultralytics`, `opencv-python-headless`, `statsmodels`, `scikit-learn`, `pandas`, `numpy`, `pillow`, `requests`, `streamlit`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. This phase now includes all data fetching tasks to ensure data availability before implementation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `src/lib/utils.py` containing `set_global_seed()` and checksum utilities
- [~] T014 [US0] **Fetch Real Stimuli (Pilot)**: Implement `src/metrics/fetch_stimuli.py` to download the first 500 items from the 'train' split of the HuggingFace `video-conference-backgrounds` dataset via `datasets.load_dataset('HuggingFaceM4/video-conference-backgrounds', split='train')`.
- [~] T014b [US0] **Verify Stimuli Checksum**: Implement `src/metrics/verify_stimuli.py` to compute and record the SHA‑256 checksum of each downloaded stimulus in `state/artifact_hashes`.
- [~] T014c [US0] **Validate Stimuli Readability**: Implement `src/metrics/validate_stimuli.py` to ensure each image is readable and meets a minimum resolution of 640×360 pixels; log any failures to `logs/validate_stimuli.log`.
- [ ] T014c_test [US0] **Unit test for T014c**: Verify that `validate_stimuli.py` correctly identifies readable images and rejects corrupted or undersized files.
- [~] T032 [US2] **Fetch Real Meeting Clips (Main Study)**: Implement `src/experiment/fetch_clips.py` to download meeting background frames/clips from the same HuggingFace dataset.
- [~] T032b [US2] **Verify Clips & Record Source**: Implement `src/experiment/verify_clips.py` to compute SHA‑256 checksums of clips and record dataset URL and version ID in `research.md`.
- [ ] T032b_test [US2] **Test verification metadata**: Add a unit test that asserts `research.md` contains the expected `dataset_url` and `version_id` fields after T032b runs.
- [~] T032c [US2] **Curate Meeting Backgrounds**: Implement `src/experiment/curate_clips.py` to filter fetched clips based on technical criteria (resolution ≥ 640×360, duration ≤ 10 s) and output `data/processed/curated_clips.csv`.
- [ ] T032c_test [US2] **Integration test for T032c**: Ensure `curated_clips.csv` is created and contains only clips meeting the specified criteria.

---

## Phase 3: User Story 0 - Conduct Human Pilot Study for Metric Validation (Priority: P0) 🎯 MVP

**Goal**: Recruit a small cohort (n=20) to rate background images for perceived visual complexity to validate automated metrics (SC‑001). [UNRESOLVED-CLAIM: c_a4e1f5a4 — status=not_enough_info]

**Independent Test**: Run the pilot study interface, collect 20 human ratings, and verify that the resulting dataset correlates (r > 0.5) with automated metrics.

### Implementation for User Story 0

- [~] T011 [US0] **Remote Pilot Interface**: Implement `src/experiment/pilot_interface.py` (Streamlit) to present images and collect complexity ratings (1-10) via a **Streamlit Cloud** deployment to facilitate remote recruitment of a cohort (n=20). The app must be publicly accessible.
- [ ] T011b [US0] **Recruitment State Manager**: Implement `src/experiment/recruitment.py` to manage participant IDs and generate static invitation templates.
- [ ] T011c [US0] **Data Ingestion**: Implement `src/experiment/ingest.py` to parse external recruitment CSV exports and map them to `data/measurements/human_ratings.csv`.
- [ ] T011d [US0] **Deployment Configuration**: Implement `src/experiment/deploy.py` to configure and deploy the Streamlit app to a public URL (e.g., Streamlit Cloud) and generate the recruitment link for distribution.
- [ ] T012 [US0] Implement data persistence for human ratings: save to `data/measurements/human_ratings.csv` with columns `image_id`, `participant_id`, `complexity_score`.
- [ ] T010 [US0] Implement `src/metrics/validate.py` to compute Pearson correlation between human ratings and automated metrics (entropy, variance, object count).
- [ ] T013 [US0] Generate validation report (scatter plot + p‑value) in `data/derived/pilot_validation_report.md`.
- [ ] T013b [US0] **Automated Pilot Gate**: Implement `src/experiment/pilot_gate.py` to check the pilot correlation; if r < 0.5, exit with a non-zero code to block downstream tasks (US-1/US-2) until the issue is resolved.
- [ ] T007 [P] [US0] Unit test `test_ingest_human_ratings` in `tests/test_metrics.py`.
- [ ] T008 [P] [US0] Unit test `test_correlation_calculation` in `tests/test_metrics.py`.
- [ ] T009 [P] [US0] Integration test `test_pilot_study_data_flow` in `tests/test_metrics.py`.

**Checkpoint**: User Story 0 should be fully functional and testable independently.

---

## Phase 4: User Story 1 - Compute Visual Complexity Metrics (Priority: P1)

**Goal**: Extract quantitative visual complexity metrics (image entropy, color variance, object detection counts) from background frames using a CPU‑compatible pipeline.

**Independent Test**: Run the metric extraction script on a static set of diverse background images and verify that the output JSON contains valid numerical values without errors.

### Implementation for User Story 1

- [ ] T019 [US1] **Metric Extraction**: Implement `src/metrics/extract.py` to compute entropy, color variance, and object detection counts using YOLOv8n. Accept 1080p input but resize internally to 640×640 **to fulfill NFR-001** (process 10x 1080p images < 30s, RAM < 2GB). Output `data/processed/metrics.csv` adhering to the `BackgroundFrame` schema and produce `data/derived/performance_log.txt` with timing/RAM stats.
- [ ] T019a [US1] **Performance Verification**: Add `tests/test_metrics_performance.py` to assert the <30 s / <2 GB constraints and produce `data/derived/performance_log.txt`.
- [ ] T020 [US1] Add logic to handle images with no detectable objects gracefully (object count = 0).
- [ ] T021 [US1] Persist computed metrics to `data/processed/metrics.csv`.
- [ ] T022 [US1] **Optional Validation Against Pilot**: Re‑run correlation check on the full pilot dataset and flag if r < 0.5; this task can be executed after US0 but does not block US1 completion.
- [ ] T023 [US1] **Fallback Object Detection**: Implement fallback using `torchvision.models.ssd300_vgg16` if YOLOv8n fails; ensure fallback also meets NFR‑001 constraints.
- [ ] T023_perf_test [US1] **Performance test for fallback**: Verify fallback model respects <30 s / <2 GB limits.
- [ ] T015 [P] [US1] Unit test `test_entropy_calculation` in `tests/test_metrics.py`.
- [ ] T016 [P] [US1] Unit test `test_color_variance_calculation` in `tests/test_metrics.py`.
- [ ] T017 [P] [US1] Integration test `test_yolov8n_cpu_inference` in `tests/test_metrics.py`.
- [ ] T018 [P] [US1] Contract test `test_blank_background_edge_case` in `tests/test_metrics.py`.
- [ ] T018a [P] [US1] Setup isolated test data directories in `tests/data/`.

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 5: User Story 2 - Administer Cognitive Load Assessment (Priority: P2)

**Goal**: Present meeting clips to participants and capture their cognitive load response via the NASA‑TLX self‑report scale and a post-task reaction-time task.

**Independent Test**: Simulate a participant session where a clip is shown, the NASA‑TLX form is submitted, and the reaction-time task is completed, verifying correct data linkage.

### Implementation for User Story 2

- [ ] T027 [US2] **Counterbalance Generator**: Implement `src/experiment/counterbalance.py` to generate Latin Square designs for the *main study* stimuli and output `data/processed/counterbalance_order.json` to be consumed by T029.
- [ ] T028 [US2] **Baseline Task Handler**: Implement `src/experiment/tasks.py` to handle the baseline reaction‑time task using a **low-complexity or neutral stimulus** loaded specifically from `data/stimuli/neutral/` (FR‑002b) and experimental trials.
- [ ] T029 [US2] **Session Server**: Implement `src/experiment/server.py` (Flask) to present clips, capture NASA‑TLX scores, and record reaction times (FR‑002). Must load the counterbalanced sequence from `data/processed/counterbalance_order.json` (T027) and enforce the exact order.
- [ ] T030 [US2] Add logic to flag incomplete records (missing TLX or RT) for exclusion.
- [ ] T031 [US2] Save participant sessions to `data/measurements/raw/participant_sessions.csv` with required columns.
- [ ] T055 [US2] **Generate Task‑Difficulty Metadata**: Assign a difficulty level (e.g., low, medium, high) to each curated clip based on predefined heuristics (e.g., number of visual elements) and store in `data/processed/clip_difficulty.csv`.
- [ ] T024 [P] [US2] Unit test `test_latin_square_counterbalancing` in `tests/test_experiment.py`.
- [ ] T025 [P] [US2] Integration test `test_baseline_reaction_time_task` in `tests/test_experiment.py`.
- [ ] T026 [P] [US2] Test `test_missing_data_flagging` in `tests/test_experiment.py`.

**Checkpoint**: User Stories 1 AND 2 should both work independently.

---

## Phase 6: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Execute linear mixed‑effects models to correlate visual complexity metrics with cognitive load outcomes, controlling for task difficulty and participant ID, while applying multiple-comparison corrections and checking for multicollinearity.

**Independent Test**: Run the analysis script on a pre-generated synthetic dataset with known correlations and verify correct identification of significant predictors, adjusted p-values, and multicollinearity diagnostics.

### Implementation for User Story 3

- [ ] T036 [US3] **Data Integration**: Merge `data/processed/metrics.csv`, `data/processed/clip_difficulty.csv`, and `data/measurements/raw/participant_sessions.csv` into `data/processed/analysis_input.csv`. [DEPENDS ON T021, T031, T055]
- [ ] T036_test [US3] **Integration test**: Verify that `analysis_input.csv` contains all required columns and rows after the merge.
- [ ] T037 [US3] Implement `src/analysis/models.py` to run linear mixed‑effects models with visual complexity as predictor and cognitive load as outcome (FR‑003).
- [ ] T038 [US3] Implement VIF calculation in `src/analysis/models.py`; flag any predictor with VIF > 5.
- [ ] T039 [US3] Implement PCA fallback in `src/analysis/models.py` when VIF > 5.
- [ ] T040 [US3] Implement Benjamini‑Hochberg correction in `src/analysis/corrections.py` (FR‑004).
- [ ] T041 [P] [US3] Implement `src/analysis/sensitivity.py` to sweep p‑value thresholds {0.01,0.05,0.1} and output `data/derived/sensitivity_report.csv` with columns `count_significant_predictors` and `sd_effect_size`.
- [ ] T042 [US3] **Null-Simulation (Pipeline Validation)**: Implement `src/analysis/null_sim.py` to run a null‑simulation (effect size = 0) and report observed FWER; **output results to `data/derived/validation_only/`** and label all outputs as "Pipeline Validation" to strictly isolate from primary analysis.
- [ ] T042b [US3] **Null-Simulation Isolation**: Implement `src/analysis/isolate_null.py` to move null-simulation results to `data/derived/validation_only/` and add a gating check to ensure these are excluded from the primary hypothesis report.
- [ ] T043 [US3] **Report Generation**: Implement `src/analysis/report_gen.py` to generate the final report with fixed‑effect estimates, confidence intervals, adjusted p‑values, VIF scores, and FWER. **Explicitly exclude** any data from `data/derived/validation_only/` from the primary hypothesis section and include stability metrics (count of significant predictors and SD of effect sizes) as required by FR-005b.
- [ ] T054 [US3] **Complexity‑TLX Correlation**: Compute Pearson correlation (including p‑value) between aggregated visual‑complexity scores and NASA‑TLX scores; output `data/derived/complexity_tlx_correlation.csv`.
- [ ] T033 [P] [US3] Unit test `test_benjamini_hochberg_correction` in `tests/test_analysis.py`.
- [ ] T034 [P] [US3] Unit test `test_vif_calculation` in `tests/test_analysis.py`.
- [ ] T035 [P] [US3] Integration test `test_full_analysis_pipeline` in `tests/test_analysis.py`.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 7: Main Study Execution (Priority: P3)

**Goal**: Conduct the main study with real human participants to collect the final dataset for hypothesis testing.

### Implementation for User Story 4

- [ ] T056 [US4] **Conduct Main Study**: Execute the recruitment of n=50-100 real participants, manage the live data collection pipeline via the deployed app (T011d), and ensure all collected data (NASA-TLX, reaction times) is stored as "Real Human Data" in `data/measurements/raw/main_study_sessions.csv`.

---

## Phase 8: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Update `docs/quickstart.md` with specific CPU‑only setup instructions and YOLOv8n installation steps.
- [ ] T045 [P] Update `docs/data-model.md` with new entity attributes and metric definitions.
- [ ] T046 [P] Update `docs/contracts/` with final API/Interface definitions.
- [ ] T047 [P] Additional unit tests for edge cases (skewed distributions, attention‑check failures) in `tests/`.
- [ ] T048a [P] **Automated Reproducibility Orchestrator**: Run sub‑tasks T048a1‑T048a4 and T048b sequentially to validate the entire pipeline on a real, small subset of data.
- [ ] T048a1 [P] Set up a fresh temporary directory, install dependencies, and pin random seeds.
- [ ] T048a2 [P] Execute T014, T019, and T036‑T043 on a 5‑image / 2‑participant subset.
- [ ] T048a3 [P] Verify checksums of derived artifacts against `state/artifact_hashes`.
- [ ] T048a4 [P] Summarize reproducibility outcomes in `data/derived/reproducibility_summary.md`.
- [ ] T048b [P] **Automated Reproducibility Test**: Assert that T048a exits with code 0 and that expected artifacts (`performance_log.txt`, `sensitivity_report.csv`, etc.) are present.

---

## Phase Dependencies

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Stories (Phase 3‑6)**: Depend on Foundational.
 - US0 must complete before optional validation tasks (T022) but does not block US1.
 - US1 can run after Foundational; validation (T022) is optional.
 - US2 can run after Foundational and after clips are curated (T032c).
 - US3 runs after US1 (metrics) and US2 (participant data) are available.
 - Main Study (Phase 7) runs after US2 is fully deployed.
- **Polish (Phase 8)**: Depends on all prior phases.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (except explicit order between fetch, verify, validate).
- US1 and US2 can run in parallel once Foundational is complete.
- Tests within each story are parallelizable.
- Analysis sub‑tasks (T036‑T043) can run in parallel where dependencies allow.

---

## Implementation Strategy

### MVP First (User Story 0 & 1 Only)

1. Complete Phase 0 (spec‑task alignment).
2. Complete Phase 1 (Setup).
3. Complete Phase 2 (Foundational).
4. Complete Phase 3 (Pilot Validation).
5. Complete Phase 4 (Metric Extraction).
6. **STOP and VALIDATE**: Ensure pilot correlation r > 0.5.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Parallel work:
 - Developer A: US0 & US1.
 - Developer B: US2.
 - Developer C: US3 (waits for data).
3. Integrate and demo each story independently.

---

## Notes

- All YOLO inference is CPU‑only; no `load_in_8bit` or CUDA usage.
- All data are real; no fabricated inputs.
- NFR‑001 is met by resizing to 640×640 internally as a performance optimization for 1080p input.
- T048a orchestrates reproducibility without violating the "no synthetic data" rule.
- T054 fulfills SC‑002; T055 fulfills FR‑003's task‑difficulty control.
- Redundant directory creation removed; race conditions eliminated.
- Every task now has a concrete deliverable and, where appropriate, a corresponding test.