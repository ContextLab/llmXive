# Tasks: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

**Input**: Design documents from `/specs/001-assessing-the-validity-of-statistical-si/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-436-assessing-the-validity-of-statistical-si/`)
- [X] T002 Initialize Python 3.11 project with dependencies: `scikit-learn`, `statsmodels`, `scipy`, `pandas`, `numpy`, `seaborn`, `matplotlib`, `requests`, `openml`, `miceforest`, `joblib` in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `data_loader.py` in `code/` to download RCT datasets from OpenML IDs using `openml` library, ensuring strict failure-on-missing behavior (no synthetic fallback, raise error if file/ID not found)
- [X] T004b [P] [Foundational] Implement dataset size validation in `code/data_loader.py`: check if N < 100; if so, skip the dataset and log a warning (do not crash) (Spec Assumptions, SC-004)
- [ ] T005 [P] Implement `config.py` in `code/` to load and validate `SimulationConfig` (dataset source, mechanism, rate, outcome type)
- [ ] T006 [P] Setup directory structure: `data/raw/`, `data/processed/`, `code/`, `tests/`
- [ ] T007 Create base data models/contracts in `contracts/` (JSON schemas for `SimulationConfig`, `ErrorMetric`, `PValueDistribution`)
- [X] T008 Configure `pytest` environment and logging infrastructure in `code/__init__.py`
- [X] T009 [P] Implement helper functions for statistical tests (Wilcoxon vs t-test selection based on outcome type) in `code/metrics.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Simulate Missing Data Mechanisms and Calculate Empirical Type I Error (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic missing data patterns (MCAR, MAR, MNAR) on real RCT datasets with known ground truth (null hypothesis) to calculate empirical Type I error rates.

**Independent Test**: Run a single simulation loop (a sufficient number of iterations, fixed seed, specific dataset, defined missingness rate) and verify output includes p-value distribution and empirical error rate.

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test for `simulate_missingness` in `tests/unit/test_simulation.py` (verify MCAR/MAR/MNAR logic and permutation order)
- [ ] T011 [P] [US1] Unit test for `calculate_type1_error` in `tests/unit/test_metrics.py` (verify binomial test and p-value counting)
- [X] T012 [P] [US1] Integration test for full US1 pipeline on a small OpenML dataset in `tests/integration/test_us1_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `permute_treatment_labels` function in `code/simulation.py` to establish true null hypothesis (FR-002, FR-003)
- [X] T014 [US1] Implement `simulate_mcar` in `code/simulation.py` (random missingness)
- [X] T015 [US1] Implement `simulate_mar` in `code/simulation.py` (missingness dependent on observed covariates, e.g., age) (FR-002, FR-009)
- [X] T015b [P] [US1] Implement `generate_and_validate_synthetic_covariates` in `code/simulation.py` to ensure r=0.3 ±0.05 correlation with outcome before MAR simulation (FR-009). **MUST be triggered ONLY if the loaded dataset lacks sufficient covariates, as orchestrated in T017.**
- [X] T016 [US1] Implement `simulate_mnar` in `code/simulation.py` (missingness dependent on **ORIGINAL (unpermuted)** outcome values; treatment labels are permuted separately to establish null) **[Plan Override: FR-002]**. **This task depends on T013 for the permuted treatment labels but uses original outcome values for the missingness mechanism.**
- [X] T017 [US1] Implement `run_simulation_iteration` in `code/simulation.py` to orchestrate: Permute -> Simulate Missing -> Analyze -> Store P-value
- [X] T018 [US1] Implement `aggregate_results` in `code/metrics.py` to calculate empirical Type I error rate (count p < 0.05 / total iterations)
- [X] T019 [US1] Create `main_us1.py` in `code/` to execute a single condition (e.g., [deferred] MAR, 500 iterations) and output `data/processed/us1_results.json`

**Checkpoint**: At this point, User Story 1 (Type I Error) should be fully functional and testable independently

---

## Phase 3.5: Power Analysis (Supporting SC-004) - BLOCKING PREREQUISITE FOR US1 CHECKPOINT

**Goal**: Implement the alternative hypothesis simulation required by SC-004 to measure statistical power (d=0.5). This is distinct from the Type I error (null) logic in Phase 3.

- [X] T019c [US1] Implement `simulate_alternative_hypothesis` in `code/simulation.py` to inject a non-zero treatment effect (Cohen's d=0.5) while maintaining the missingness simulation logic (SC-004)
- [X] T019d [US1] Implement `calculate_statistical_power` in `code/metrics.py` to aggregate power estimates across iterations for the alternative hypothesis (SC-004)
- [ ] T019e [US1] Create `main_power_analysis.py` in `code/` to EXECUTE the alternative hypothesis sweep (multiple rates, mechanisms) and output `data/processed/power_results.json` to satisfy SC-004.

**Checkpoint**: Power analysis logic and execution are complete; US1 validation can now proceed to check both Type I error and Power.

---

## Phase 4: User Story 2 - Identify Tipping Points via Sensitivity Analysis (Priority: P2)

**Goal**: Systematically vary missingness rates ([deferred] to [deferred] in steps) and analyze deviation of Complete-Case (CC) method from nominal 0.05 error rate to identify "tipping points".

**Independent Test**: Execute batch simulation across multiple missingness rates and verify output contains error rate trend and flags specific rate where error exceeds threshold.

### Tests for User Story 2

- [ ] T020 [P] [US2] Unit test for `identify_tipping_point` in `tests/unit/test_metrics.py` (verify FDR correction and threshold logic)
- [X] T021 [P] [US2] Integration test for sensitivity analysis sweep in `tests/integration/test_us2_sensitivity.py`

### Implementation for User Story 2

- [ ] T022a [US2] Create `configure_sweep_rates.py` in `code/` to explicitly CONFIGURE and POPULATE `SimulationConfig` with the required sweep rates (A range of values with incremental steps) for the sensitivity analysis.
- [X] T022b [US2] Implement `validate_condition_matrix` in `code/main.py` to verify that the sweep configuration generates the full 8 rates x 3 mechanisms x 3 methods = 72 conditions before proceeding.
- [X] T022 [US2] Implement `run_sensitivity_sweep` in `code/main.py` to iterate over missingness rates loaded from `SimulationConfig` (not hardcoded) (FR-004)
- [X] T023 [US2] Implement `compare_to_nominal` in `code/metrics.py` to detect when CC error rate exceeds the threshold defined as >10% relative increase over the nominal 0.05 level (i.e., threshold = 0.05 * 1.10 = 0.055). **This task depends on the output artifact from T018 (data/processed/us1_results.json).**
- [X] T024 [US2] Implement `apply_fdr_correction` in `code/metrics.py` using Benjamini-Hochberg procedure across all 72 experimental conditions (combinations of rates, mechanisms, and methods), ensuring the count matches the validation from T022b. (FR-008)
- [X] T025 [US2] Implement `generate_tipping_point_report` in `code/main.py` to output CSV/JSON listing the specific rate where CC fails (SC-002)
- [X] T026 [US2] Create visualization script in `code/visualize.py` to plot error rate curves vs. missingness rate and mark tipping points

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compare Complete-Case vs. Imputation Methods (Priority: P3)

**Goal**: Compare Complete-Case (CC) analysis against Multiple Imputation (MI) and Inverse Probability Weighting (IPW) to demonstrate relative validity.

**Independent Test**: Run a single condition (e.g., [deferred] MAR) with CC, MI, IPW and verify output lists three distinct empirical Type I error rates.

### Tests for User Story 3

- [X] T027 [P] [US3] Unit test for `run_multiple_imputation` in `tests/unit/test_analysis.py` (verify `miceforest` usage and Rubin's rules)
- [X] T028 [P] [US3] Unit test for `run_inverse_probability_weighting` in `tests/unit/test_analysis.py`
- [X] T029 [P] [US3] Integration test for method comparison in `tests/integration/test_us3_comparison.py`

### Implementation for User Story 3

- [X] T030 [US3] Implement `run_complete_case_analysis` in `code/analysis.py` (t-test for continuous, Wilcoxon for binary) (FR-005, FR-007)
- [X] T031 [US3] Implement `run_multiple_imputation` in `code/analysis.py` using `miceforest` with multiple imputations and Rubin's rules for p-values (FR-005)
- [X] T032 [US3] Implement `run_inverse_probability_weighting` in `code/analysis.py` (calculate weights based on missingness probability) (FR-005)
- [X] T033 [US3] Implement `compare_methods` in `code/main.py` to aggregate results for CC, MI, IPW under the same condition
- [X] T034 [US3] Implement `generate_comparison_report` in `code/main.py` to output table showing CC inflation vs. MI/IPW stability (SC-003, SC-005)
- [X] T035 [US3] Update visualization script in `code/visualize.py` to overlay CC, MI, and IPW error curves

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T036 [P] Update `README.md` with execution instructions, seed handling, and expected outputs
- [ ] T037 Code cleanup: Ensure all data loading fails loudly (no synthetic fallbacks) per plan constraints
- [ ] T038 Performance optimization: Ensure vectorized operations in `simulation.py` and parallel iteration via `joblib` (multi-core)
- [ ] T039 [P] Run full integration test suite (`tests/integration/`) on a representative dataset
- [ ] T040 Validate `quickstart.md` (if generated) and ensure all artifacts are checksummed
- [ ] T041 Generate final `data/processed/final_results.json` containing all simulation data for report generation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Uses US1 simulation logic but adds sweeping logic
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses US1 simulation logic but adds comparison analysis

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading and config (Foundational) before simulation logic
- Simulation logic before analysis logic
- Core implementation before integration

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models/Functions within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for simulate_missingness in tests/unit/test_simulation.py"
Task: "Unit test for calculate_type1_error in tests/unit/test_metrics.py"
Task: "Integration test for full US1 pipeline in tests/integration/test_us1_pipeline.py"

# Launch all models/functions for User Story 1 together:
Task: "Implement permute_treatment_labels function in code/simulation.py"
Task: "Implement simulate_mcar in code/simulation.py"
Task: "Implement simulate_mar in code/simulation.py"
Task: "Implement simulate_mnar in code/simulation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Core simulation engine)
4. **STOP and VALIDATE**: Test US1 independently (verify Type I error is controlled at the nominal significance level under MCAR)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Tipping points)
4. Add User Story 3 → Test independently → Deploy/Demo (Method comparison)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Simulation Engine)
 - Developer B: User Story 2 (Sensitivity Analysis)
 - Developer C: User Story 3 (Method Comparison)
3. Stories complete and integrate independently

---

## Notes

- **[P]** tasks = different files, no dependencies
- **[Story]** label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: Data loading MUST fail loudly if real data is unavailable; NO synthetic fallbacks (Plan constraint).
- **Critical Constraint**: MNAR simulation must use **ORIGINAL (unpermuted)** outcome values (after treatment permutation), not synthetic values (Plan override of FR-002).
- **Critical Constraint**: Binary outcomes MUST use Wilcoxon/Logistic tests, not t-tests (FR-007).
- **Critical Constraint**: FDR correction MUST be applied across all conditions (FR-008).
- **Critical Constraint**: Synthetic covariates for MAR MUST be validated for r=0.3 correlation (FR-009).
- **Critical Constraint**: Datasets with N < 100 MUST be skipped and logged (Spec Assumptions).
- **Critical Constraint**: Power analysis (d=0.5) MUST be implemented (SC-004).
- **Critical Constraint**: The condition matrix must be validated as 72 conditions (8 rates x 3 mechanisms x 3 methods) before FDR application.