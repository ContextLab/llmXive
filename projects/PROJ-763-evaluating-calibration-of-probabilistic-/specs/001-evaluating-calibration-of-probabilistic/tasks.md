# Tasks: Evaluating Calibration of Probabilistic Weather Forecasts

**Input**: Design documents from `/specs/001-evaluating-calibration-of-probabilistic-/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-763-evaluating-calibration-of-probabilistic-/code/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (pandas, numpy, scikit-learn, properscoring, pymc, arviz, matplotlib, seaborn, requests, tqdm, statsmodels)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup directory structure: `data/raw/`, `data/processed/`, `results/`, `src/`, `tests/`, `scripts/`
- [ ] T005 [P] Implement `src/utils.py` with logging configuration, random seed setting, and error handling utilities
- [ ] T006 [P] Create `scripts/hash_artifacts.py` to compute SHA-256 hashes for `data/` and `results/` and write to `state/` (Constitution Principle V)
- [ ] T007 Implement `src/download.py` (FR-001): Download SubseasonalRodeo dataset via `wget`/`requests`, verify checksum, and **FAIL LOUDLY** (raise exception) if download fails or checksum mismatches. **Explicitly check for `probability_value` fields in the loaded data; if missing, halt execution immediately with error code `NO_PROB_DATA` and generate `data_unavailability_report.md`. NO synthetic fallbacks. This is the EXCLUSIVE Data Availability Gate for the entire pipeline.**
- [ ] T008 [P] Implement `src/align.py` (FR-002): Align forecast probabilities with observations by `grid_id`, `lead_time`, and `date`. Discard records with missing values. Handle edge cases (zero observed events) gracefully. **Assumes data has passed the Data Availability Gate in T007; do NOT re-check for `probability_value` here.**
- [ ] T008b [P] Implement `src/data/autocorr.py` (Plan Phase 0): Calculate the Autocorrelation Function (ACF) of forecast errors and determine `lag_95` and `effective_autocorrelation_length`. **Mandate generation of `data/processed/autocorr_metadata.json` containing the schema: `{"lag_95": <int>, "effective_autocorrelation_length": <int>}`.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Calibration Assessment (Priority: P1) 🎯 MVP

**Goal**: Download dataset, align data, compute baseline metrics (Brier, CRPS, Reliability Diagrams) for raw forecasts.

**Independent Test**: The pipeline executes successfully, outputting `results/results_baseline.csv` (non-null metrics) and `results/reliability_diagram_raw.png`.

### Implementation for User Story 1

- [ ] T009 [US1] Implement `src/metrics.py`: Brier score and CRPS calculation functions handling edge cases (division by zero, empty bins).
- [ ] T010 [US1] Implement `src/metrics.py`: Kernel-smoothed reliability diagram generation and plotting logic.
- [ ] T011 [US1] Implement `src/main.py` (Baseline Module): Orchestrate data loading, alignment, and baseline metric computation. **CRITICAL: After loading data, explicitly validate that `probability_value` fields exist. If missing, halt execution immediately with error code `NO_PROB_DATA` and generate `data_unavailability_report.md` (Data Availability Gate enforcement).** Output `results/results_baseline.csv` (schema: metric_name, lead_time, method, value, confidence_interval, convergence_status) and `results/reliability_diagram_raw.png`.
- [ ] T013 [P] [US1] Unit tests for metric logic in `tests/unit/test_metrics.py` (Brier, CRPS).
- [ ] T014 [P] [US1] Contract test for `results_baseline.csv` schema in `tests/contract/test_baseline_schema.py`.

**Checkpoint**: MVP Definition of Done for US1 is met (T011, T013, T014). T012 is a Success Criterion validation, not a blocking MVP deliverable.

---

## Phase 3.5: Success Criteria Validation (SC-004)

**Purpose**: Validate Success Criteria that are not part of the MVP Independent Test but are required for the full project.

- [ ] T012 [US1] Implement `src/metrics.py`: Probability Integral Transform (PIT) histogram calculation and KS statistic computation (SC-004). Generate `results/pit_histogram.png` and `results/pit_data.csv`. **Note**: This task validates SC-004 but is not required for the US1 Independent Test (MVP).

---

## Phase 4: User Story 2 - Isotonic Recalibration (Priority: P2)

**Goal**: Apply isotonic regression to correct biases and measure improvement vs. baseline.

**Independent Test**: Pipeline outputs `results_isotonic.csv` and `reliability_diagram_isotonic.png`. Brier score improves (or within noise) vs baseline.

### Implementation for User Story 2

- [ ] T015 [US2] Implement `src/recalibrate_isotonic.py`: Isotonic regression fitting on a chronological train-test split. **Explicitly iterate over each lead time AND variable (precipitation, temperature) for the fitting process.** Handle sparse lead times (<100 samples) by fallback to raw forecast. **Output: A dictionary of fitted models keyed by (lead_time, variable).**
- [ ] T015b [US2] Implement `src/recalibrate_isotonic.py` (Sensitivity): **Explicitly orchestrate the re-running of the isotonic model with /40 and 80/20 split ratios.** **Loop over split ratios [0.6, 0.8], invoke the fitting logic from T015 for each ratio, and generate distinct result artifacts (`results_isotonic_60_40.csv`, `results_isotonic_80_20.csv`).** **Mandate that these sensitivity runs also respect the per-variable/lead-time granularity for the resulting artifacts.**
- [ ] T017a [US2] Implement `src/compare.py` (Standard DM): Diebold-Mariano test logic with Shapiro-Wilk pre-check and Wilcoxon fallback for **Baseline vs. Isotonic** comparison. **Explicitly mandate iterating over every lead_time and variable combination.** **Input: The per-bin models and results from T015.** **Output: A table of DM test results for each (lead_time, variable) pair.**
- [ ] T017b [US2] Implement `src/compare.py` (Sensitivity Bootstrap): **Trigger condition: varying split ratios.** Implement bootstrapped confidence intervals for score differences as required by FR-006 for sensitivity analysis runs. **Input: The sensitivity artifacts from T015b.**
- [ ] T016 [US2] Implement `src/main.py` (Isotonic Module): **Depends on T017a/T017b outputs.** Apply fitted isotonic model to test split, compute recalibrated metrics, and output `results/results_isotonic.csv` and `results/reliability_diagram_isotonic.png`.
- [ ] T018 [P] [US2] Unit tests for isotonic logic and chronological splitting in `tests/unit/test_isotonic.py`.
- [ ] T019 [P] [US2] Contract test for `results_isotonic.csv` schema in `tests/contract/test_isotonic_schema.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bayesian Hierarchical Recalibration (Priority: P3)

**Goal**: Implement Bayesian hierarchical logistic regression with lead-time decay prior. Compare to isotonic.

**Independent Test**: Pipeline outputs `results_bayesian.csv` with convergence status. R-hat ≤ 1.05. CRPS improves vs isotonic (or comparable).

### Implementation for User Story 3

- [ ] T020 [US3] Implement `src/recalibrate_bayesian.py`: Define Bayesian hierarchical logistic regression model in PyMC. **Mandate implementation of the exponential decay functional form** as the structured prior to respect the physics of forecast degradation (lead-time decay). **Explicitly define support for prior strengths: 'weak', 'medium', 'strong'.**
- [ ] T021 [US3] Implement `src/recalibrate_bayesian.py`: **Depends on T020.** MCMC sampling logic with **4 chains** (not 2) and a sufficient number of draws (500) for a *single* prior configuration. Include convergence diagnostics (R-hat, ESS). **Verify runtime against SC-005 (60 mins); if exceeded, reduce draws and re-run.** Handle non-convergence by flagging in output. **This task defines the standard sampling procedure.**
- [ ] T021b [US3] Implement `src/recalibrate_bayesian.py` (Sensitivity): **Orchestrate the iteration over the 'weak', 'medium', and 'strong' prior strengths defined in T020.** **Explicitly mandate calling the sampling logic from T021 for EACH of these prior strength iterations.** **Log the comparative results of these three runs.**
- [ ] T022 [US3] Implement `src/main.py` (Bayesian Module): Generate posterior predictive probabilities, compute metrics, and output `results/results_bayesian.csv`.
- [ ] T023a [US3] Implement `src/compare.py` (Baseline vs. Bayesian): Diebold-Mariano/Wilcoxon test logic for **Baseline vs. Bayesian** comparison. **Explicitly include conditional logic to skip this test if the Bayesian model convergence status is 'Unconverged' or 'Exploratory'.** Calculate confidence intervals for score differences.
- [ ] T023b [US3] Implement `src/compare.py` (Isotonic vs. Bayesian): Diebold-Mariano/Wilcoxon test logic for **Isotonic vs. Bayesian** comparison. **Explicitly include conditional logic to skip this test if the Bayesian model convergence status is 'Unconverged' or 'Exploratory'.** Calculate confidence intervals for score differences.
- [ ] T023 [US3] Implement `src/compare.py` (Full Comparison Matrix): Aggregate results from T017a (Baseline vs. Isotonic), T023a (Baseline vs. Bayesian), and T023b (Isotonic vs. Bayesian) into a single comparison table. **If T023a or T023b are skipped due to convergence status, explicitly mark those cells as 'N/A' or 'Skipped (Unconverged)' rather than crashing.** Handle bootstrapping logic if sensitivity analysis is triggered (per FR-006).
- [ ] T024 [P] [US3] Unit tests for model definition and sampling logic in `tests/unit/test_bayesian.py`.
- [ ] T025 [P] [US3] Contract test for `results_bayesian.csv` schema (including `convergence_status` column) in `tests/contract/test_bayesian_schema.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T026 [P] Documentation updates in `docs/` and `README.md` explaining the pipeline and statistical methods.
- [ ] T027 Code cleanup and refactoring (ensure PEP8, docstrings).
- [ ] T028 Performance optimization: Ensure streaming/chunking logic in `src/align.py` and `src/metrics.py` fits within 7GB RAM constraints.
- [ ] T029 [P] Run `scripts/hash_artifacts.py` and verify `state/` file generation.
- [ ] T030 Run full pipeline integration test and verify runtime ≤ 30 minutes (SC-005).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data alignment logic (reused)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data alignment logic (reused)

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
Task: "Contract test for baseline schema in tests/contract/test_baseline_schema.py"
Task: "Unit tests for metric logic in tests/unit/test_metrics.py"

# Launch all models for User Story 1 together:
Task: "Implement Brier/CRPS functions in src/metrics.py"
Task: "Implement Reliability Diagram plotting in src/metrics.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Baseline metrics, raw reliability diagram).
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Baseline)
   - Developer B: User Story 2 (Isotonic)
   - Developer C: User Story 3 (Bayesian)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Do NOT use synthetic data fallbacks. If `src/download.py` fails, the pipeline must stop.
- **CRITICAL**: Ensure Bayesian MCMC chains are scaled (target a sufficient number of draws and chains) to fit 6h CI limit and verify runtime.
- **CRITICAL**: Handle sparse data in isotonic regression (fallback to raw) as per edge cases.
- **CRITICAL**: Explicitly iterate over variables and lead times in isotonic and baseline tasks.
- **CRITICAL**: Implement exponential decay functional form for Bayesian prior.
- **CRITICAL**: Ensure all comparison pairs (Baseline vs Isotonic, Baseline vs Bayesian, Isotonic vs Bayesian) are tested.
- **CRITICAL**: Use bootstrapped CIs for sensitivity analysis (varying split ratios) as per FR-006.
- **CRITICAL**: PIT histogram (T012) is a Success Criterion (SC-004) but not part of the US1 MVP Independent Test.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence