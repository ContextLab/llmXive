# Tasks: Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions

**Input**: Design documents from `/specs/001-investigating-the-relationship-between-b/`
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

- [X] T001a [P] Create root directories: `src/`, `tests/`, `data/raw/`, `data/processed/`, `docs/`, `state/`
- [X] T001b [P] Create code structure: `code/preprocessing/`, `code/topology/`, `code/behavioral/`, `code/analysis/`, `code/utils/`, `code/models/`
- [X] T001c [P] Create test structure: `tests/unit/`, `tests/integration/`
- [X] T002 [P] Initialize Python 3.11 project with pinned dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (flake8), formatting (black), and type checking (mypy)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. This phase establishes the YAML-based Single Source of Truth for artifact tracking as mandated by Constitution Principle III. **Note**: The Plan's mention of "SQLite" in Phase 2 is a legacy artifact; this project uses YAML-only state tracking per Constitution Principle III and Plan Notes ("No SQLite database is used").

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `code/utils/config.py` for environment variables and path management
- [X] T006 [P] Create `code/utils/update_state.py` to handle versioning and hash tracking (Constitution Principle III). This script initializes and updates the `state/projects/PROJ-361-*.yaml` file, defining the YAML schema for artifact checksums and serving as the single source of truth.
- [X] T007 [P] Setup `git_hooks/pre-commit` script that runs `code/utils/update_state.py` on artifact changes
- [X] T008 [P] Implement `code/utils/logging_utils.py` for standardized error handling and motion threshold logging
- [ ] T009 [P] Create base Python dataclasses: `Subject`, `ConnectivityMatrix`, `TopologyMetrics`, `IllusionScore` in `code/models/` for in-memory processing (no SQL persistence)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download and preprocess resting-state fMRI data from OpenNeuro, extract BOLD time series.

**Independent Test**: Verify that `data/raw/` contains valid NIfTI files for at least 50 subjects and that `code/preprocessing/extract_timeseries.py` produces a T×N matrix with no NaN values for a single subject.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Unit test for `download_openneuro.py` schema validation in `tests/unit/test_download.py`. **Specifics**: Input: `data/raw/dataset_description.json` (simulated). Expected: `FileNotFoundError` if path missing, `ValueError` if `id` field missing. Assertion: Verify the script raises `RuntimeError` with message "Real data fetch failed" if the OpenNeuro API returns 404.
- [X] T011 [P] [US1] Unit test for fMRIPrep config schema validation and mock output structure in `tests/unit/test_fmriprep_config.py`. **Specifics**: Verify `run_fmriprep.sh` parses valid BIDS inputs and generates a mock output file structure that matches the expected schema, ensuring reproducibility without running the heavy container in CI.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/preprocessing/download_openneuro.py` to fetch ds004285 data for at least 50 subjects to `data/raw/`. Must handle credentials, verify checksums, and ensure output NIfTI files are stored in `data/raw/{subject_id}/`. **Must fail loudly if the dataset is unreachable; no synthetic fallback.**
- [X] T013 [US1] Implement `code/preprocessing/run_fmriprep.sh` to execute containerized fMRIPrep (pinned version `poldracklab/fmriprep:23.1.0`) with HCP configuration.
- [X] T014 [US1] Implement `code/preprocessing/extract_timeseries.py` to map Schaefer parcellation ROIs (multiple parcellations) to preprocessed BOLD data.
- [X] T015 [US1] Implement motion quality control logic in `code/utils/quality_control.py` to calculate **mean FD** for ALL subjects, record the value, and exclude subjects with mean FD > 0.5mm (per Spec Constraints).
- [ ] T016 [US1] Add validation to ensure output matrices of dimensions T×N contain no NaN values.
- [ ] T017 [US1] Add logging for preprocessing completion and exclusion reasons (referencing T015's recorded FD).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Network Topology Metric Computation (Priority: P2)

**Goal**: Compute functional connectivity matrices and derive five graph theory metrics (modularity, path length, clustering, efficiency, small-worldness).

**Independent Test**: The metric computation can be tested on a single subject's connectivity matrix to verify that the output values fall within the theoretical bounds for each metric and that the Louvain algorithm converges within a sufficient number of iterations on CPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for `compute_connectivity.py` correlation matrix bounds in `tests/unit/test_connectivity.py`
- [ ] T019 [P] [US2] Unit test for `compute_metrics.py` Louvain convergence and metric bounds in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/topology/compute_connectivity.py` to generate 200x200 Pearson correlation matrices from time-series data.
- [ ] T021 [US2] Implement `code/topology/compute_metrics.py` using `bctpy` to calculate: modularity (Louvain, fixed seed), path length, clustering, efficiency, small-worldness. Input: adjacency matrix (numpy array); Output: JSON object with metrics. Must flag subjects where global_efficiency > 1.0 or path_length <= 0.
- [ ] T022 [US2] Implement logic in `code/topology/metrics_utils.py` to handle disconnected graphs (replace infinite path length with NaN) and log the event.
- [ ] T023 [US2] Implement outlier detection for `global_efficiency` > 1.0 or non-positive path length.
- [ ] T024 [US2] Save raw five metrics to `data/processed/topology_metrics_raw.json`. **CRITICAL**: This file is the primary input for US-3. Output must contain exactly the five metrics defined in the Data Model.
- [ ] T026 [US2] Verify that `data/processed/topology_metrics_raw.json` exists and is readable before proceeding to US-3.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 4 - Behavioral Data Extraction (Priority: P1) 🎯 MVP

**Goal**: Extract existing visual illusion susceptibility scores (Müller-Lyer and Ponzo) from the OpenNeuro ds004285 dataset and link them to Subject IDs.
*Note: This phase aligns with the Plan's strategy of using existing OpenNeuro data.*

**Independent Test**: The extraction can be tested by running the script on a subset and verifying that scores are correctly linked to Subject IDs and match the expected schema.

### Implementation for User Story 4

- [ ] T044 [US4] Implement `code/behavioral/extract_openneuro_scores.py` to **scan for behavioral data in BIDS format** (JSON, TSV, events.tsv) within `data/raw/`. Parse the first valid source found for all subjects. If no data is found, fail loudly. Output to `data/behavioral/collected_scores.csv`.
- [ ] T045 [US4] Implement `code/behavioral/validate_schema.py` to ensure extracted scores match the required schema (Study ID, Müller-Lyer, Ponzo) and handle missing values.
- [ ] T046 [US4] Implement `code/behavioral/merge_datasets.py` to cross-reference extracted behavioral data with fMRI subject IDs (from T012/T015). Exclude subjects with missing fMRI or behavioral data. Output final merged dataset to `data/processed/merged_dataset.csv`. **Depends on T015** (exclusion list).

**Checkpoint**: Behavioral data is now extracted and merged with fMRI data, ready for analysis

---

## Phase 6: User Story 3 - Correlation Analysis and Statistical Reporting (Priority: P3)

**Goal**: Correlate topology metrics with illusion scores, apply FDR correction, and generate reports.

**Independent Test**: The analysis can be tested by injecting a synthetic dataset where a known correlation exists, verifying that the script correctly identifies the p-value < 0.05 and flags it as significant after FDR correction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T052 [P] [US3] Unit test for FDR correction logic in `tests/unit/test_statistics.py`
- [ ] T053 [P] [US3] Integration test for full correlation pipeline on mock data in `tests/integration/test_correlation.py`

### Implementation for User Story 3

- [ ] T054 [US3] Implement `code/analysis/correlation_analysis.py` to compute Pearson/Spearman correlations between the **raw five metrics** (from T024) and illusion scores. {{claim:c_de009304}} (1705.04312, https://arxiv.org/abs/1705.04312). **Depends on T046** (merged dataset) and **T026** (metric verification).
- [ ] T055 [US3] Implement logic to handle cases where no significant correlations are found (generate full table with explicit null statement).
- [ ] T056 [US3] Implement `code/analysis/generate_plots.py` to create scatter plots with regression lines and CI shading for significant findings.
- [ ] T059 [US3] **Mandatory**: Implement `code/analysis/reproducibility_check.py` to re-run analysis on a **[deferred] random seed subset**, compare correlation coefficients, and assert tolerance (**difference < 0.01**). **Depends on T054** (correlation table). **Must pass before report generation**.
- [ ] T057 [US3] Generate final report in `data/processed/report.md` framing findings as "associational" only (FR-007). **Must include a validation step to verify the generated file contains the required phrasing**.
- [ ] T058 [US3] Calculate and report effect sizes (Cohen's d or r) for all tested pairs.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns (Reviewer Revisions)

**Purpose**: Address specific feedback from simulated reviewers regarding levels of explanation, stimulus "texture", and data integrity.

- [ ] T060 [P] **Reproducibility**: (Already covered in T059 as mandatory).
- [ ] T061 [P] **Reviewer Address (Plan: Reviewer Feedback Integration)**: Update `docs/research_limitations.md` to explicitly anchor findings at the **systems/network level** of explanation. Clearly state that while the study correlates topology with behavior, it does not claim to trace mechanisms to synaptic plasticity or molecular genetics, acknowledging this as a scope limitation (per Spec Constraints).
- [ ] T062 [P] **Reviewer Address (Plan: Reviewer Feedback Integration)**: Update `docs/research_limitations.md` to discuss the "texture" of the illusion. Extract specific visual stimuli parameters (line lengths, angles, background patterns) from the OpenNeuro dataset metadata files (e.g., `participants.tsv` or `dataset_description.json`). Explicitly state that the current analysis measures the *frequency/magnitude of the error* rather than the topological shape of the stimulus itself, and propose that future work could apply Topological Data Analysis (TDA) to the stimulus geometry.
- [ ] T063 [P] **Data Integrity**: Verify that `code/preprocessing/download_openneuro.py` strictly enforces the download of **real** data from `https://openneuro.org/datasets/ds004285` and fails if the dataset is unreachable, ensuring no synthetic data is used for the primary hypothesis test.
- [ ] T064 [P] **Collinearity Check**: Implement `code/topology/check_collinearity.py` to calculate Variance Inflation Factors (VIF) for the raw metrics. **Must include logic to {{claim:c_1ff28e9e}}.**
- [ ] T065 [P] **Code Cleanup**: Add CI job `lint` that runs `black --check code/` and `flake8 code/` to enforce formatting compliance.
- [ ] T066 [P] **Performance**: Run CI job `perf-check` on a representative subject subset to verify `compute_metrics.py` runs within a predefined CPU time limit.
- [ ] T067 [P] Additional unit tests for edge cases (disconnected graphs, single module partition) in `tests/unit/`.
- [ ] T068 Run `quickstart.md` validation to ensure end-to-end reproducibility.
- [ ] T069 Update `README.md` with instructions for running the full subject analysis on external compute.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → US1/US4 → US2 → US3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P1)**: Can start after Foundational (Phase 2) - Independent data extraction from OpenNeuro
 - **Critical Note**: Task T046 (Merge) requires the exclusion list from T015 (US1). **Depends on T015**.
- **User Story 2 (P2)**: Depends on US1 completion (needs time-series data)
- **User Story 3 (P3)**: Depends on US2 (topology metrics) and US4 (behavioral scores) completion

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US4 can start in parallel
- US2 and US3 must wait for their upstream dependencies

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for download_openneuro.py schema validation"
Task: "Unit test for fMRIPrep config schema validation"

# Launch all models for User Story 1 together:
Task: "Implement download_openneuro.py"
Task: "Implement run_fmriprep.sh"
```

---

## Implementation Strategy

### MVP First (User Story 1 & 4 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Pipeline)
4. Complete Phase 5: User Story 4 (Behavioral Extraction)
5. **STOP and VALIDATE**: Test data ingestion and merging on a cohort of subjects

The research question, method, and references remain unchanged as required.
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 + US4 → Test data ingestion → Deploy/Demo (MVP!)
3. Add US2 → Compute metrics → Test independently → Deploy/Demo
4. Add US3 → Correlate and report → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (fMRI Pipeline)
 - Developer B: User Story 4 (Behavioral Data Extraction)
 - Developer C: User Story 2 (Topology Metrics) - *Note: Can start once US1 is partially ready*
3. US3 (Analysis) starts once US2 and US4 are complete

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on CPU-only CI (limited cores, GB RAM). No GPU, no 8-bit quantization, no deep learning training.
- **Data Integrity**: No synthetic data generation for hypothesis testing; use real OpenNeuro ds004285 data for fMRI and behavioral scores.
- **Reviewer Concerns**: Tasks T061 and T062 explicitly address the feedback from simulated reviewers regarding the level of explanation and the "texture" of the illusion, referencing Plan: Reviewer Feedback Integration.
- **Metadata Management**: All artifact tracking is handled exclusively via the YAML state file (`state/...yaml`) as per Constitution Principle III. No SQLite database is used.