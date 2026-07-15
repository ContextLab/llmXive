# Tasks: The Impact of Predictive Coding Errors on Subjective Time Perception

**Input**: Design documents from `/specs/001-predictive-coding-time-perception/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [ ] T001 Create project structure per implementation plan (`mkdir -p data/raw data/processed code figures analysis contracts`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas==2.0.3, numpy==1.24.3, statsmodels==0.14.0, pingouin==0.5.3, joblib==1.3.2, matplotlib==3.8.0, seaborn==0.13.0, openml==0.14.2, datasets==2.14.0, pyyaml==6.0.1)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/README.md` schema for dataset metadata and exclusion logs (fields: dataset_id, status, reason)
- [ ] T005 [P] Create `contracts/dataset.schema.yaml` defining required columns (duration_estimate, stimulus_sequence, participant_id)
- [ ] T006 [P] Create `contracts/output.schema.yaml` defining analysis results structure
- [X] T007 Setup environment configuration management for random seeds in `code/config.py`
- [ ] T008 Implement chunked data loading utility in `code/utils.py` to handle datasets >500 MB within 7 GB RAM limits <!-- SKIPPED: YAML+regex parse failed (while parsing a block mapping
 in "<unicode string>", line 2, column 1:
 I have implemented the chunked d...
 ^
expected <block end>, but found '-'
 in "<unicode string>", line 18, column 1:
 - Uses `pandas.read_csv()` with...
 ^) -->
- [X] T009 Document verified dataset IDs (OpenML/HF) in `data/README.md` 'Verified datasets' block. If no valid time-perception datasets are known, create a `data/README.md` section explicitly stating "Data Gap: No valid datasets found" and block further execution. (Plan: Gate 0)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download valid time-perception datasets, filter for sequential stimuli, and compute surprisal metrics.

**Independent Test**: Can be fully tested by executing the data download and preprocessing scripts and verifying that output CSV files contain the required columns (duration estimate, stimulus timing, condition label, participant ID, surprisal metric) with ≥100 valid rows.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py` (Dep: T005)
- [X] T011 [US1] Integration test for data download and Gate 0 validation in `tests/integration/test_download_gate0.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download.py` to fetch datasets from OpenML/HuggingFace using IDs from `data/README.md` (created in T009) (FR-001)
- [X] T013 [US1] Implement Gate 0 logic in `code/download.py` to verify presence of `duration_estimate`, `stimulus_sequence`, and `participant_id`. If no valid dataset is found, halt execution and write `gate0_status.json` with status="blocked" and reason. (Plan: Gate 0, SC-001)
- [~] T014 [US1] Implement filtering logic to exclude datasets lacking sequential stimuli or predictability manipulations (e.g., random noise, non-sequential) as per FR-002. Log exclusion reasons. (FR-002)
- [ ] T015 [US1] Create `code/preprocess.py` with full implementation of Markov surprisal calculation logic (Shannon entropy of transition) and data loading functions. (FR-003, Assumption 1)
- [ ] T016 [US1] Implement Markov surprisal calculation in `code/preprocess.py` using 'Shannon entropy of the transition' (FR-003, Assumption 1)
- [ ] T017 [US1] Generate standardized CSV output in `data/processed/standardized.csv` with checksums
- [ ] T017b [US1] Save 'transition-probability tables' and 'Markov model state' as versioned artifacts in `data/processed/` (Constitution VI)
- [ ] T018 [US1] Update `data/README.md` with exclusion logs and reasons for any dropped datasets

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Fit linear mixed-effects models, calculate effect sizes, and perform sensitivity analysis.

**Independent Test**: Can be fully tested by running the analysis script on a sample dataset and verifying that model outputs include effect sizes (Cohen's d), confidence intervals, p-values for the surprisal main effect, and the calculated MDE.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py` (Dep: T006)
- [ ] T020 [P] [US2] Unit test for MDE calculation logic in `tests/unit/test_mde_calc.py`

### Implementation for User Story 2

- [ ] T021 [US2] [Dep: T017] Implement `code/analysis.py` to fit LMM: `Duration ~ Surprisal + Sequence_Length + Modality + (1 | Participant_ID)` (FR-004). Save model summary to `analysis/results.json` with keys: coef, pval, ci.
- [ ] T022 [US2] Implement convergence check and fallback to random-intercept-only model if convergence fails (Edge Case)
- [ ] T022b [US2] Define the 90% convergence threshold as a constant in `code/config.py`. Measure and report the convergence rate (SC-002). (Note: Do not invalidate results, only report).
- [ ] T023 [US2] Implement multiple-comparison correction (Bonferroni/Benjamini-Hochberg) for p-values. Include logic: only apply correction if `num_tests > 1`. (FR-005)
- [ ] T023b [US2] Implement verification logic to ensure Family-Wise Error Rate is controlled at α≤0.05 and log `fwer_control_status` to `analysis/results.json`. (SC-003)
- [ ] T024 [US2] Implement effect size calculation (Cohen's d) with 95% CI using `pingouin` (FR-006)
- [ ] T025 [US2] Implement sensitivity analysis to calculate Minimum Detectable Effect (MDE) for power=0.80. Include logic: 'If observed effect < MDE, report as limitation' (FR-007)
- [ ] T025b [US2] Ensure MDE results are logged to `analysis/results.json` for *every* dataset analyzed, regardless of outcome. (SC-005)
- [ ] T025c [US2] Implement cutoff-sweeping sensitivity analysis if decision cutoffs are introduced (Assumption 7)
- [ ] T026 [US2] Implement normality check (Shapiro-Wilk, α=0.05) and fallback to Wilcoxon signed-rank test if non-normal (Spec: Edge Cases)
- [ ] T027 [US2] Log all results (coefficients, p-values, MDE, convergence status) to `analysis/results.json`
- [ ] T028 [US2] [Dep: T028b] Implement bootstrap resampling in `code/analysis.py` using `joblib.Parallel(n_jobs=2)` for robust CI estimation. (FR-009)
- [ ] T028b [US2] Implement bootstrap resampling strategy with fixed `n_jobs=2` to ensure compliance with SLA targets and 2-core constraint. (FR-009, Assumption 10)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reproducible Reporting (Priority: P3)

**Goal**: Generate forest plots, residual diagnostics, and ensure reproducible environment.

**Independent Test**: Can be fully tested by executing the visualization script and verifying that output plots (forest plot, residual diagnostics) are generated in `figures/` and that the Dockerfile builds successfully.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Integration test for Dockerfile build and full analysis run in `tests/integration/test_reproducibility.py`

### Implementation for User Story 3

- [ ] T030 [US3] [Dep: T027] Implement `code/visualize.py` to generate forest plots of condition effects (FR-008)
- [ ] T031 [US3] [Dep: T027] Implement `code/visualize.py` to generate residual diagnostic plots (FR-008)
- [ ] T032 [US3] Ensure all plots are saved at ≥300 DPI in `figures/` directory
- [ ] T033 [US3] Create `Dockerfile` with `FROM python:slim`, `WORKDIR /app`, `COPY requirements.txt`, `RUN pip install`. Create `code/run_pipeline.py` (or shell script) that executes download, preprocess, analysis, and visualize in sequence. Set `CMD ["python", "code/run_pipeline.py"]` to ensure full pipeline execution. (US-3)
- [ ] T033a [US3] Validate Dockerfile against GitHub Actions runner architecture (CPU-only, ≤7 GB RAM) (US-3)
- [ ] T034 [US3] Create `tests/integration/test_runtime.py` to verify full pipeline execution time < 6h (SC-004)
- [ ] T034a [US3] Execute full pipeline in clean environment (Docker/runner simulation) and verify SLA compliance with 2 CPU/7GB RAM constraints (SC-004, Assumption 10)
- [ ] T034b [US3] Generate `reproducibility-checklist.md` and `quickstart.md` explicitly guiding an external reviewer to reproduce results within 6 hours. (SC-006)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `data/README.md`
- [ ] T036 Code cleanup and refactoring in `code/`
- [ ] T037 [P] Run `quickstart.md` validation to ensure reproducibility (SC-006)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Requires output from US1 (`data/processed/standardized.csv`) - Tasks marked [Dep: T017]
- **User Story 3 (P3)**: Requires output from US2 (`analysis/results.json`) - Tasks marked [Dep: T027]

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Integration test for data download and Gate 0 validation in tests/integration/test_download_gate0.py"

# Launch implementation tasks that don't depend on each other:
Task: "Implement code/download.py to fetch datasets..."
Task: "Implement code/preprocess.py to compute surprisal..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Gate 0 must pass)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Analysis) - *Note: Must wait for T017 completion*
 - Developer C: User Story 3 (Visualization) - *Note: Must wait for T027 completion*
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
- **Critical Constraint**: No task may load models in 8-bit/4-bit, use CUDA, or exceed a substantial amount of RAM. All analysis must run on CPU-only free-tier CI.