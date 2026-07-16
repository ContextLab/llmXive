# Tasks: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

**Input**: Design documents from `/specs/001-gene-regulation/`  
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-015-improving-accessibility-and-usability-of/`)
- [X] T002 Initialize Python project with pinned dependencies in `requirements.txt` (scipy, matplotlib, pandas, jupyter, streamlit).
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup data directory structure: `data/raw/` (immutable), `data/processed/`
- [X] T005 [P] Implement checksumming utility for raw data integrity in `code/utils/checksum.py`
- [X] T006 [P] Setup random seed fixing infrastructure in `code/utils/seed.py`
- [X] T007 [P] Create base data models (`Participant`, `Session`, `Metric`) in `code/models/data_models.py` with explicit attributes: `Participant` (id, disability_type, interface_sequence), `Session` (session_id, participant_id, interface_type, start_time, end_time, error_count, explanation_engagement_time_seconds, sus_score, status, dropout_reason), `Metric` (metric_name, interface_type, mean, std_dev, p_value, confidence_interval, test_method).
- [X] T008 [P] Configure error handling and logging infrastructure in `code/utils/logger.py`
- [X] T009 [P] Setup environment configuration management for study parameters in `code/config/settings.py`
- [X] T009b [P] Generate `contracts/session.schema.yaml` defining the JSON schema for session data (fields: participant_id, disability_type, interface_type, sequence, start_time, end_time, error_count, explanation_engagement_time_seconds, sus_score, status, dropout_reason). **Deliverable**: `contracts/session.schema.yaml`. **Dependencies**: None (Foundational).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 - XAI Interface Configuration (Priority: P0) 🎯 MVP

**Goal**: Implement the mechanism to configure and deploy Traditional vs. Explainable interface variants with XAI overlays.

**Independent Test**: The configuration module can be tested by loading a task definition and verifying that two distinct UI renders are generated: one without overlays and one with the specified XAI overlays, ensuring the XAI data is correctly bound to the UI elements.

### Implementation for User Story 0

- [X] T010 [P] [US0] Implement `TraditionalInterface` renderer in `code/simulator/interfaces/traditional.py`
- [X] T011 [P] [US0] Implement `ExplainableInterface` renderer in `code/simulator/interfaces/explainable.py`
- [X] T012a [US0] Create the skeleton Streamlit app entry point `code/simulator/app.py` (basic layout, no collectors yet)
- [X] T013a [US0] Implement `XAIOverlayGenerator` using **SHAP** (or LIME) on a real, publicly‑available dataset (e.g., UCI Breast Cancer). The generator must produce feature‑level SHAP values that can be visualized as heatmaps over UI elements. **Deliverable**: A function `generate_overlay(task_input) -> dict` returning SHAP values for each UI feature.
- [X] T013b [US0] Implement `ConfigurableXAIWrapper` in `code/simulator/xai_wrapper.py` that selects the XAI technique (SHAP, LIME, or a simple attention‑heatmap) at runtime and provides the appropriate overlay to `ExplainableInterface`. **Depends on successful build of T013a**. **Deliverable**: A class `ConfigurableXAIWrapper` with method `get_overlay(task_input, technique)` returning the overlay data.
- [X] T014 [US0] Add session logging logic to record `interface_variant` in `code/simulator/session_logger.py`

**Checkpoint**: At this point, the simulator can render both interface types with real XAI overlays and log which variant was presented.

---

## Phase 4: User Story 1 - Core Usability Benchmarking (Priority: P1) 🎯 MVP

**Goal**: Execute the standardized usability test protocol, collecting metrics (time, errors, SUS, engagement) for both interfaces with Latin Square counterbalancing.

**Independent Test**: The research pipeline can be fully tested by running the data collection script on a simulated dataset or a small pilot group (n=5) to verify that completion times, error counts, explanation engagement times, and SUS scores are correctly logged and formatted for downstream statistical analysis.

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement `LatinSquareCounterbalancer` in `code/simulator/counterbalance.py` to assign `Traditional->Explainable` or `Explainable->Traditional` sequences
- [X] T016 [US1] Implement data collection handlers for `completion_time`, `error_count`, and `explanation_engagement_time` in `code/simulator/metrics_collector.py`
- [X] T016b [US1] Ensure `explanation_engagement_time` is logged to **raw** session files under `data/raw/` as part of the session JSON (aligned with FR‑001). **Deliverable**: Raw JSON includes `explanation_engagement_time_seconds`.
- [X] T017 [US1] Integrate all collectors (T016, T016b, T015) and SUS questionnaire into the Streamlit app flow in `code/simulator/app.py` ensuring sequence order is respected. Implement SUS validation: reject if >1 item missing; if ≤1 missing, impute with participant mean and log imputation.
- [X] T019b [US1] Implement `DataValidator` in `code/simulator/data_validator.py` to enforce strict schema validation against `contracts/session.schema.yaml` **before** any logging occurs. Abort with a clear error if the schema file is missing.
- [X] T019 [US1] Implement raw data logging to `data/raw/session_{session_id}.json`. The JSON **must** contain the fields defined in `contracts/session.schema.yaml`. The task **must abort** if the schema file is absent (enforced by T019b). **Deliverable**: One JSON file per completed (or incomplete) session stored under `data/raw/`.
- [X] T020 [US1] Implement dropout handling: log `dropout_reason` and set `status='incomplete'` for partial sessions in `code/simulator/session_logger.py`

**Checkpoint**: The system can collect real‑time interaction data, handle dropouts, and store immutable raw logs with schema validation.

---

## Phase 5: User Story 2 - Statistical Significance Analysis (Priority: P2)

**Goal**: Perform statistical analysis (Repeated Measures ANOVA, Holm‑Bonferroni) on collected metrics to determine significance.

**Independent Test**: The analysis module can be tested independently by feeding it a pre‑generated CSV file with known distributions and verifying that ANOVA F‑statistics, adjusted p‑values, and effect sizes are calculated correctly. The script must also validate column presence and types.

### Implementation for User Story 2

- [X] T021-exclude [US2] Implement exclusion logic in `code/analysis/data_cleaner.py` to filter out sessions where `status='incomplete'`. **Output**: `data/processed/cleaned_sessions.csv`.
- [X] T021 [US2] Orchestrate the cleaning pipeline (apply exclusion, SUS imputation, type coercion). **Dependencies**: T021-exclude, T004, T019b, `contracts/session.schema.yaml`, T019.
- [X] T022 [US2] Implement Shapiro‑Wilk normality test on difference scores in `code/analysis/stat_utils.py` and log results to `data/processed/normality_log.txt` (audit only).
- [X] T023a-legacy [US2] **(Legacy path for spec compliance)** Implement Shapiro‑Wilk test on differences; if p < 0.05, use Wilcoxon Signed‑Rank; otherwise, use Paired T‑Test. **Note**: Levene’s test is omitted as it is inappropriate for paired designs. Results are written to `data/processed/legacy_test_results.csv`.
- [X] T023a [US2] Implement **Repeated Measures ANOVA** for Completion Time, Error Count, and SUS in `code/analysis/stat_utils.py`. Normality results are logged only; ANOVA is always run per Constitution Principle VII. **Deliverable**: `data/processed/metrics_summary.csv` with columns `metric_name, interface_type, F_statistic, p_value, adjusted_p_value, effect_size`.
- [X] T023a-amendment [US2] Create amendment document `specs/001-improving-accessibility-and-usability-of/contracts/fr_002_amendment.md` that:
  1. States FR‑002’s original T‑Test/Wilcoxon/Levene flow is superseded.
  2. Describes the new ANOVA‑only logic.
  3. Provides traceability references to T023a and T023a-legacy.
- [X] T023a-integrate [US2] Update `specs/001-improving-accessibility-and-usability-of/spec.md` to reference the ANOVA amendment (flagged for kickback – spec update required).
- [X] T023b-exclude-enforce [US2] Ensure `explanation_engagement_time` is **excluded** from the ANOVA input but still retained for descriptive reporting. Log the exclusion to `data/processed/exclusion_log.txt`.
- [X] T023b [US2] Compute descriptive statistics (mean, std) for `explanation_engagement_time` and output to `data/processed/descriptive_stats.csv`.
- [X] T024 [US2] Implement Holm‑Bonferroni correction for the multiple ANOVA comparisons in `code/analysis/stat_utils.py`.
- [X] T024a [US2] Verify primary ANOVA p‑value < 0.05 before applying Holm‑Bonferroni; write verification result to `data/processed/primary_test_verification.txt`.
- [X] T025a [US2] Create skeleton `code/analysis/run_analysis.py` with CLI (`--input`, `--output`) and basic orchestration calls.
- [X] T025b [US2] Complete `run_analysis.py`:
  - Load `data/processed/cleaned_sessions.csv`.
  - Validate **exact columns**: `participant_id` (str), `interface_type` (enum: traditional|explainable), `completion_time_seconds` (float ≥ 0), `error_count` (int ≥ 0), `sus_score` (int 0‑100), `explanation_engagement_time_seconds` (float ≥ 0).
  - Enforce data‑type checks and allowed value ranges; abort with clear error messages on mismatch.
  - Execute Shapiro‑Wilk logging (T022), ANOVA (T023a), Holm‑Bonferroni (T024), descriptive stats (T023b), and power analysis (T036).
  - Write `metrics_summary.csv`, `report_summary.txt`, and verify that the CSV contains the required columns before exiting.
  - Exit code 0 on success, non‑zero on validation failure.
- [X] T036 [US2] Implement `PowerCalculator` in `code/analysis/power_analysis.py`:
  - Compute statistical power given N, effect size (eta‑squared), and α = 0.05.
  - **Deliverable**: `data/processed/power_flags.json` with schema `{ "subgroup": "<str>", "N": <int>, "power": <float>, "flag": "<UNDERPOWERED|OK>" }`.
- [X] T026 [US2] Generate `data/processed/metrics_summary.csv` (handled within T025b).

**Checkpoint**: The pipeline now cleans raw data, runs ANOVA with proper corrections, produces descriptive stats, and outputs power‑analysis flags.

---

## Phase 6: User Story 3 - Reproducible Visualization and Reporting (Priority: P3)

**Goal**: Generate publication‑quality visualizations and a single executable Jupyter notebook documenting the pipeline.

**Independent Test**: Run the notebook on a small sample dataset; verify that all figures are created, have correct axis labels, and that the notebook completes without errors.

### Implementation for User Story 3

- [X] T027 [US3] Implement visualization functions in `code/analysis/visualizer.py`:
  - Box plot for Completion Time, Error Count, SUS with 95 % CI error bars.
  - Save each figure as **PNG** at a high resolution in `figures/` with filenames `completion_time.png`, `error_count.png`, `sus_score.png`.
- [X] T028 [US3] Compile `code/analysis/analysis.ipynb` that:
  1. Loads raw data, runs cleaning, performs ANOVA, creates visualizations, runs power analysis.
  2. Contains markdown explanations for each step.
  3. Saves all generated artifacts.
- [X] T029c [US3] Add a verification task that executes `analysis.ipynb` on a fresh runner and writes `notebook_execution_log.txt` containing a SHA‑256 checksum of the notebook, execution status (SUCCESS/FAIL), and timestamps. This satisfies SC‑004 reproducibility evidence.
- [X] T030 [US3] Ensure the notebook is fully deterministic: pin random seeds, use exact file paths, and verify that re‑running produces identical checksums for generated figures.

**Checkpoint**: The project now provides reproducible visualizations, a runnable notebook, and verifiable execution evidence.
