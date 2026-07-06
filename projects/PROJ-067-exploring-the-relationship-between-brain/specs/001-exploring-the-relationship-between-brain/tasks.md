# Tasks: Exploring the Relationship Between Brain Network Dynamics and Individual Differences in Dream Recall Frequency

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `results/`, `tests/` at repository root
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

- [X] T001 [P] Create directory structure: `code/`, `data/`, `results/`, `tests/`, `contracts/`
- [X] T002 [P] Create `code/__init__.py` to establish package structure
- [X] T003 [P] Initialize a Python project with pinned dependencies in `code/requirements.txt` (nilearn, networkx, scikit-learn, scipy, pandas, numpy, joblib, requests, nibabel) using a compatible modern Python version.
- [X] T004 [P] Configure linting (ruff) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] **Spec Deviation Log (Documentation)**: Create `docs/deviation_log.md` to formally record the "Schaefer-400 vs Schaefer-100" conflict, the Plan's decision to use Schaefer-100 for statistical validity, and reference the formal Requirement Change Record (RCR) created in T005b. This task MUST complete before T006.
- [X] T005b [P] **Formal Requirement Change Record (RCR)**: Create `docs/requirement_change_record_Schaefer100.md` as a formal artifact to update the requirement traceability for FR-004. This document MUST explicitly state that FR-004's mandate for "Schaefer-400" is formally amended to "Schaefer-100" due to statistical validity constraints (rank-deficiency), and link to the Plan's deviation note. This resolves the traceability gap between the Spec and the implemented artifact. This task MUST complete before T025.
- [X] T006 [P] **Config Initialization**: Initialize `code/utils/config.py` with default values for seeds, paths, and constants (window_size=30, step_size=10, atlas='Schaefer100', deviation_flag=True), explicitly initializing the flag referenced in T005.
- [X] T007 [P] Implement `code/utils/memory_monitor.py` to track RSS via `/proc/self/status` and raise exceptions if >7GB
- [ ] T008 [P] Create `contracts/` directory with `subject_metrics.schema.yaml` and `results_schema.yaml`
- [ ] T009 [P] Initialize `data/` directory structure (`raw/`, `processed/`, `metrics/`, `atlas/`) and `.gitignore` for large files
- [ ] T010 [P] Initialize `results/` directory structure (`plots/`) and `tests/` directory structure (`contract/`, `unit/`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download resting-state fMRI data from a designated OpenNeuro dataset., validate "dream recall frequency" metadata, perform ICA-AROMA denoising and normalization under 7GB RAM constraints.

**Independent Test**: Execute download and preprocessing on a subset of subjects; verify output NIfTI files exist, directory size ≤7GB, and peak memory log entry <7GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for downloaded metadata schema in `tests/contract/test_metadata_schema.py`
- [ ] T012 [P] [US1] Unit test for memory monitor threshold violation in `tests/unit/test_memory_monitor.py`
- [ ] T013 [P] [US1] Unit test for FD calculation and exclusion logic in `tests/unit/test_preprocess.py`

### Implementation for User Story 1

- [~] T014 [US1] **Metadata Validation (Phase 0 Gate)**: Implement `code/data/validate_metadata.py` to fetch ds000228 metadata, verify existence of "dream recall frequency" field, and **HALT** execution if missing (FR-001, Plan Phase 0).
- [~] T015 [US1] **Subject Filtering & N=50 Enforcement**: Implement `code/data/filter_subjects.py` to load validated metadata, filter for subjects with "dream recall frequency", **sort by subject ID ascending, select the first valid subjects, and truncate the list to a fixed number of entries**, then generate `data/raw/valid_subjects.json`. **If fewer than 50 valid subjects are found, raise a FatalError with message "Insufficient subjects for N=50 target"**. The output file MUST contain exactly 50 entries before T016 executes (FR-001, US1 Acceptance Scenario 2).
- [~] T016 [US1] Implement `code/data/download.py` to fetch ds000228 NIfTI files for subjects listed in `data/raw/valid_subjects.json` (T015 output) (FR-001).
- [~] T017 [US1] Implement `code/data/preprocess.py` to run ICA-AROMA denoising and spatial normalization to **MNI152NLin2009cAsym** template. **Use specific ICA-AROMA flags: --afni, --no-reports**. Ensure the pipeline accepts preprocessed NIfTI inputs and outputs normalized, denoised files (FR-002).
- [~] T018 [US1] Integrate `memory_monitor.py` into `preprocess.py` to abort if RSS >7GB (FR-002, SC-004).
- [~] T019 [US1] Implement Framewise Displacement (FD) calculation in `preprocess.py` and exclude subjects with FD >0.5mm (Edge Case).
- [~] T020 [US1] Add logging for excluded subjects (missing metadata or high motion) and total processing count.
- [~] T021 [US1] Ensure intermediate files are cleaned up or compressed to stay within 7GB total directory size (US1 Acceptance Scenario 1).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dynamic Connectivity Metric Extraction (Priority: P2)

**Goal**: Calculate network flexibility and stability metrics for DMN, Salience, and Hippocampal networks using a Schaefer atlas with a high-resolution parcellation., sliding window correlation, and Louvain clustering.

**Independent Test**: Run metric extraction on a single preprocessed subject; verify output CSV contains flexibility and stability values for specified networks.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T022 [P] [US2] Contract test for metrics CSV schema in `tests/contract/test_metrics_schema.py`
- [~] T023 [P] [US2] Unit test for sliding window correlation matrix generation in `tests/unit/test_metrics.py`
- [~] T024 [P] [US2] Unit test for Louvain clustering state transition calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [~] T026 [US2] **Atlas Label Verification & Mapping**: Implement `code/analysis/verify_atlas_labels.py` to check if Schaefer-100 contains "Hippocampal-Memory" label. If missing, generate `data/atlas/network_label_map.csv` with columns `region_id`, `network_name`, `source_label`, `mapped_label`. **Mapping Logic**: Map any region where `source_label` contains 'Hippocampal' or 'Memory' to `mapped_label`='Hippocampal-Memory'. This task MUST complete before T025.
- [~] T025 [US2] Implement `code/analysis/metrics.py` to load Schaefer-100 atlas (verified by T026) and parcellate preprocessed NIfTI files. **If `network_label_map.csv` exists (from T026), use it to dynamically map regions to the required network ROIs (DMN, Salience, Hippocampal-Memory)**. (Plan Deviation, T005b).
- [~] T027 [US2] Implement sliding window correlation (a fixed-duration window, a defined time step) in `metrics.py` (FR-003).
- [~] T028 [US2] Implement Louvain clustering on time-varying connectivity matrices to generate discrete community partitions (FR-003).
- [~] T029 [US2] Calculate Flexibility (state transitions per unit time) for DMN, Salience, and **mapped** Hippocampal-Memory networks using `network_label_map.csv` (FR-004, T026).
- [~] T030 [US2] Calculate Stability (Mean Dwell Time) for the same networks (FR-004).
- [~] T031 [US2] Output subject-level metrics to `data/metrics/subject_metrics.csv` with proper headers and JSON/CSV validation (FR-008).
- [~] T032 [US2] Add logic to exclude subjects from analysis if metadata is missing at this stage with a warning (US2 Acceptance Scenario 4).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Goal**: Perform Spearman correlation between network metrics and dream recall frequency, apply FDR correction, run a sufficient number of permutation iterations to ensure robust statistical inference., and generate post-hoc power analysis.

**Independent Test**: Run analysis on extracted metrics; verify output includes correlation coefficient, corrected p-value, permutation null distribution plot, and power analysis result.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T033 [P] [US3] Contract test for final results JSON schema in `tests/contract/test_results_schema.py`
- [~] T034 [P] [US3] Unit test for Spearman correlation calculation in `tests/unit/test_stats.py`
- [~] T035 [P] [US3] Unit test for FDR correction logic in `tests/unit/test_stats.py`
- [~] T036 [P] [US3] Unit test for permutation test loop and p-value derivation in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [~] T037 [US3] Implement `code/analysis/stats.py` to load metrics and dream recall frequency values (FR-005).
- [~] T038 [US3] Perform Spearman correlation analysis between metrics and dream recall frequency (FR-005).
- [~] T039 [US3] Apply False Discovery Rate (FDR) correction to all correlation p-values (FR-006, SC-002).
- [~] T040 [US3] Implement permutation test with **exactly 1000 iterations** to generate null distribution (FR-007, SC-003).
- [~] T041 [US3] Calculate and report post-hoc power analysis (detectable effect size) for N=50 (FR-009, SC-001).
- [ ] T042 [US3] Generate `results/stats.json` containing rho, uncorrected p, FDR-corrected p, and permutation p-value (FR-008).
- [ ] T043 [US3] Generate correlation scatter plot and null distribution histogram in `results/plots/` (US3 Acceptance Scenario 3).
- [ ] T044 [US3] Ensure null results (p > 0.05) are fully reported with plots and coefficients, not suppressed (Edge Case).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T045 [P] Update `code/main.py` to orchestrate the full pipeline (Download → Preprocess → Metrics → Stats) **with built-in wall-clock timing instrumentation for each phase** (SC-005).
- [ ] T049 [P] **Runtime Verification**: Implement a check in `main.py` that **raises a RuntimeError if total runtime > 4 hours** and logs results to `results/runtime_log.json`, asserting total <= 4 hours (SC-005, T045).
- [ ] T050 [P] **CI Pipeline Enforcement**: Update `.github/workflows/ci.yml` (or equivalent CI config) to treat the `RuntimeError` raised by T049 as a **build failure**. This ensures the 4-hour target is enforced by the build system, not just logged.
- [ ] T046 [P] Run `pytest` on all contract and unit tests to ensure full pipeline validity.
- [ ] T047 [P] Validate `results/stats.json` against `contracts/results_schema.yaml`.
- [ ] T048 [P] Update `README.md` or `quickstart.md` with execution instructions for the 4-hour CI limit.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T005 (Spec Deviation Log)** and **T005b (RCR)** MUST complete before T006 (Config) and any downstream tasks.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **CRITICAL**: Must complete before US2 as it produces the input data.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **MUST** wait for US1 to produce preprocessed NIfTI files.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **MUST** wait for US2 to produce `subject_metrics.csv`.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- **Phase 0 Gate (T014)** before **Subject Filtering (T015)**
- **Subject Filtering (T015)** before **Download (T016)**
- **Download (T016)** before **Preprocessing (T017)**
- **Preprocessing (T017)** before **Metric Extraction (T025-T032)**
- **Atlas Label Verification (T026)** before **Parcellation (T025)** and **Metric Calculation (T029-T030)**
- **Metric Extraction (T031)** before **Statistical Analysis (T037-T044)**

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T005->T006)
- Once Foundational phase completes, US2 and US3 *could* theoretically start in parallel if mock data were available, but in practice US2 depends on US1 output.
- All tests for a user story marked [P] can run in parallel
- Different statistical tests (T033-T036) can run in parallel

---

## Parallel Example: User Story 3

```bash
# Launch all unit tests for User Story 3 together:
Task: "Unit test for Spearman correlation calculation in tests/unit/test_stats.py"
Task: "Unit test for FDR correction logic in tests/unit/test_stats.py"
Task: "Unit test for permutation test loop in tests/unit/test_stats.py"

# These can run once the stats.py module skeleton exists.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) - **Ensure T005 (Deviation) and T005b (RCR) are done**.
3. Complete Phase 3: User Story 1 (Data Download & Preprocessing) - **Ensure T014 (Validate) and T015 (Filter) are done**.
4. **STOP and VALIDATE**: Verify data exists, is <7GB, and metadata is present.
5. Deploy/demo if ready (showing data pipeline works).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (on US1 output) → Deploy/Demo
4. Add User Story 3 → Test independently (on US2 output) → Deploy/Demo
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Metrics - can start with mock data if needed, but final run waits for A)
 - Developer C: User Story 3 (Stats - can start with mock data if needed, but final run waits for B)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on CPU-only CI with a limited number of cores and constrained RAM.. No GPU, no 8-bit models, no heavy deep learning.
- **Data Integrity**: No synthetic data generation. All analysis must use real OpenNeuro data.
- **Atlas Choice**: Use Schaefer-100 (per Plan) instead of Schaefer-400 to ensure statistical validity on short windows. **Documented in T005 and T005b**.
- **Runtime**: T049 must raise RuntimeError if > 4h. T050 ensures CI fails on this error.