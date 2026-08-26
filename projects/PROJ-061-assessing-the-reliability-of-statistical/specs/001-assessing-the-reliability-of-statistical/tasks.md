# Tasks: Assessing the Reliability of Statistical Power Calculations in Real-World Datasets

**Input**: Design documents from `/specs/001-assessing-the-reliability-of-statistical/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directories: `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/`, `docs/` and create `__init__.py` in all Python packages (`code/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`). (Note: This coarse task will be atomized by the downstream runner). <!-- ATOMIZE: requested -->

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and validation that MUST be complete before ANY user story or real-data processing can begin.
**⚠️ CRITICAL**: No user story work or real-data processing can begin until this phase is complete, including the Synthetic Ground Truth validation.

- [ ] T004a [P] **Select and list 10 diverse public datasets** (continuous, count, binary) from UCI/OpenML satisfying FR-001 and Constitution Principle VII. **Specific List**: Use the following hardcoded IDs to guarantee the balanced distribution:
 - Continuous (3): `iris`, `wine`, `wine_quality_red`
 - Count (3): `concrete`, `airfoil`, `yacht`
 - Binary (4): `breast_cancer`, `heart_disease`, `pima`, `ionosphere`
 **Action**: Save these specific IDs, URLs, and outcome types to `code/config.py` as a JSON list. **Verification**: Add a check to confirm the list contains exactly 3 continuous, 3 count, and 4 binary datasets. **Depends on**: None.
- [X] T004 Implement `code/loaders.py`: Dataset fetching from UCI/OpenML using the list from T004a with checksum validation and PII scan. **Depends on T004a**.
- [ ] T005 [P] Implement `code/config.py`: Centralized configuration for random seeds (fixed), dataset lists (from T004a), and hyperparameters (including BOOTSTRAP_ITERATIONS=1000). **Depends on T004a**.
- [ ] T006 [P] Create `code/utils.py`: Logging, file I/O helpers, and checksum recording functions
- [ ] T007 [P] Define `contracts/power_estimate.schema.yaml` and `contracts/violation_config.schema.yaml`
- [ ] T008 Implement `code/validators.py`:
 1. **Bootstrap Validity Check** (FR-010): Compare bootstrap variance to analytical variance and flag unreliable estimates. The threshold MUST be a configurable parameter `VALIDITY_THRESHOLD` in `code/config.py` with a **a default value determined by the method's requirements**. Add a validation step to ensure this threshold is set to a non-zero, non-infinite value before running.
 2. **Explicit Exclusion Logic**: If a dataset is flagged as unreliable, it MUST be excluded from the final bias calculation.
 3. **Achieved Magnitude Verification** (FR-009): Framework to verify and log achieved violation magnitudes (e.g., AR coefficient).
 **Depends on T004 and T005**.
- [ ] T030 [P] **Generate Synthetic Ground Truth Data**: Create a script `code/synthetic_data.py` to generate synthetic datasets with **known parameters** (specific effect size, variance, sample size) required for the [deferred] recovery check. **Output**: Save to `data/raw/synthetic_ground_truth.json` with fields: `true_effect_size`, `true_power`, `dataset_params`. **Depends on T005**.
- [ ] T031a [P] **Implement Synthetic Test Logic**: Implement `code/power_empirical.py` synthetic test mode logic: Load synthetic data from T030, run bootstrap, verify recovery rate matches true power within 5% (FR-008). **Depends on T004, T005, T008, T013, T030**.
- [ ] T031b [Validation] **Execute** the Synthetic Ground Truth test (T031a) and act as a **blocking gate**. **Logic**: Run the test. If the recovery rate is not within 5%, retry with seeds `[SEED + 1, SEED + 2, SEED + 3]` up to 3 times. If still failing after 3 retries, raise `RuntimeError` with message "Synthetic Ground Truth validation failed after 3 retries" and **halt the pipeline**. **Expected Artifacts**: Write results to `data/results/synthetic_validation.json` with fields: `recovery_rate`, `pass` (bool), `seeds_tried`. **Depends on T031a**.

**Checkpoint**: Foundation ready - validation passed, dataset list selected, user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Power vs. Empirical Ground Truth (Priority: P1) 🎯 MVP

**Goal**: Compare standard theoretical power calculations against empirical power estimates derived from bootstrapping on real-world datasets without induced violations.

**Independent Test**: Run pipeline on `mtcars` (or similar) with no violations; verify `data/results/baseline.json` contains theoretical power, empirical power (bootstrap resampling), and absolute error.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test: Write code for `PowerEstimate` JSON schema validation in `tests/contract/test_schemas.py` (expected to FAIL initially)
- [ ] T011 [P] [US1] Integration test: Write code for baseline pipeline integration test on `iris` dataset in `tests/integration/test_pipeline.py` (expected to FAIL initially)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/power_theory.py`: Theoretical power calculation for two-sample t-test (Cohen's d = 0.5) using `statsmodels`
- [ ] T013 [US1] Implement `code/power_empirical.py`: Bootstrap simulation engine. **Constraint**: Set `BOOTSTRAP_ITERATIONS=1000` in `code/config.py` and **enforce minimum 1000 iterations in code**. Preserve data distribution. **Depends on T004, T005, T012**.
- [ ] T014 [US1] Implement main pipeline logic in `code/main.py` to load dataset (from T004a list), compute theoretical vs empirical, and save results to `data/results/baseline.json` conforming to `contracts/power_estimate.schema.yaml` (keys: theoretical_power, empirical_power, absolute_error). **Expected Artifacts**: `data/results/baseline.json`. **Depends on T012, T013, T004, T005, T008**.
- [ ] T015 [US1] Add validation logic to skip datasets with N < 30, log "insufficient sample size", and do not process further.
- [ ] T016 [US1] Add logic to handle missing values via listwise deletion before power calculation, and add a verification step to log the count of dropped rows and confirm deletion was applied before calculation.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Controlled Violation Induction and Bias Mapping (Priority: P2)

**Goal**: Systematically inject specific assumption violations (heavy-tailed noise, autocorrelation, heterogeneity) and re-compare theoretical vs. empirical power to generate bias curves.

**Independent Test**: Run pipeline with AR(1) injection on a time-series subset; verify `data/results/violations.json` shows a distinct shift in bias compared to baseline.

### Tests for User Story 2

- [ ] T017 [P] [US2] Unit test for heavy-tailed noise injection in `tests/unit/test_perturbations.py`
- [ ] T018 [P] [US2] Unit test for AR(1) autocorrelation injection in `tests/unit/test_perturbations.py`
- [ ] T019 [P] [US2] Unit test for effect size heterogeneity injection in `tests/unit/test_perturbations.py`
- [ ] T020 [P] [US2] Integration test for bias calculation with induced violations in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/perturbations.py`: Injection modules for:
 1. Heavy-tailed noise (t-distribution)
 2. AR(1) autocorrelation
 3. **Effect size heterogeneity via mixing two sub-populations** with **configurable parameters** (default: mixing_ratio=0.2, separation=1.5 standard deviations).
 **Depends on T004, T005**.
- [ ] T021b-Config [US2] **Define parameter lists** for violation magnitudes in `code/config.py` to generate bias curves (SC-001). **Specific Parameters**:
 - AR coefficients: `[, 0.3, 0.5]`
 - Contamination rates (heavy-tail): `[, 0.1, 0.3]`
 - Mixing ratios (heterogeneity): varied across a spectrum from homogeneous to heterogeneous conditions.
 - Separation values (heterogeneity): `[, 1.0, 1.5]`
 **Iteration Count**: Enforce `BOOTSTRAP_ITERATIONS=1000` for all sweeps. **Depends on T021**.
- [ ] T021b-Sweep [US2] **Implement sweep loop** in `code/main.py` to iterate over violation configurations (from T021b-Config) and apply perturbations. **Dependencies**: T021b-Config, T021. **Depends on T021b-Config, T021**.
- [ ] T021b-Curve [US2] **Generate bias curves** by calculating and recording bias magnitude for each violation type and magnitude. **Output Format**: Save to `data/results/bias_curves.json` as a list of objects with keys: `violation_type`, `parameter_value`, `bias_magnitude` (absolute error), `iterations_used`. **Enforce a sufficient number of iterations to ensure convergence.**. **Expected Artifacts**: `data/results/bias_curves.json`. **Depends on T021b-Sweep**.
- [ ] T022 [US2] Implement `code/main.py` extension to iterate over violation configurations (from T021b-Sweep) and append results to `data/results/violations.json`. **Expected Artifacts**: `data/results/violations.json`. **Depends on T021b-Sweep**.
- [ ] T023 [US2] **Apply** verification logic from T008 in `code/validators.py` to check if injected AR(1) coefficient matches target and log achieved magnitude (FR-009). **Depends on T021**.
- [ ] T024 [US2] Add conditional logic to skip autocorrelation injection if data is not time-ordered (check for column named 'time'/'date' or numeric index); if absent, skip AR(1) and log warning: "[Dataset X] skipped: no temporal structure".
- [ ] T025 [US2] Ensure all perturbation tasks run on CPU-only logic (no GPU dependencies)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis on decision thresholds for classifying "significant" power bias to ensure findings are robust.

**Independent Test**: Run analysis with varying significance thresholds; verify output table shows classification counts for each threshold.

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for sensitivity analysis logic with varying thresholds in `tests/unit/test_validators.py`
- [ ] T027 [P] [US3] Integration test for sensitivity report generation in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T028-Config [US3] Define a list of significance thresholds `THRESHOLDS` to be evaluated across a range of values (e.g., a set of small positive constants) in `code/config.py`. **Depends on T022**.
- [ ] T028-Sweep [US3] Implement sensitivity analysis loop in `code/main.py` to sweep thresholds across the configured range. **Dependencies**: T028-Config, T021b-Curve (to ensure bias data exists). **Depends on T028-Config, T021b-Curve**.
- [ ] T028-Report [US3] Generate summary report in `data/results/sensitivity_analysis.json` showing count/percentage of "high bias" cases per threshold. **Depends on T028-Sweep**.
- [ ] T029b [US3] **Implement mixed-effects regression model** to measure sensitivity (SC-005). The predictor is the *induced* violation magnitude and the outcome is the observed bias. Generate statistical output (coefficients, p-values) to `data/results/regression_analysis.json`. **Depends on T021b-Curve**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Synthetic Ground Truth (Priority: P1 - Critical Path)

**Goal**: Validate the bootstrap methodology and ensure the pipeline meets the 6-hour runtime constraint on CPU-only hardware.
**⚠️ CRITICAL**: This phase runs ONLY after T031b (Phase 2) has passed. T034 (Full Run) is blocked until T031b passes.

**Independent Test**: Run "Synthetic Ground Truth" test (T031b) - already completed in Phase 2. Now run full pipeline on real data.

- [ ] T032 [Validation] **Profile and Enforce Runtime**: Run a dry-run on the **dataset with the largest N** from the T004a list to estimate total runtime. **If estimated total runtime > 6 hours, raise RuntimeError ** with message "Estimated runtime exceeds 6-hour limit; implement subsampling (T032b) or optimize." **DO NOT prune datasets.** **Generate artifact**: `data/results/runtime_enforcement_report.json` documenting the estimate and action taken. **Depends on T031b**.
- [ ] T032b [Validation] **Implement Stratified Subsampling**: If T032 fails, implement streaming/chunking logic in `code/power_empirical.py` to process large datasets in batches without loading entirely into memory, ensuring the full dataset contributes to the result while staying within memory limits. **Depends on T032 failure**.
- [ ] T033 [Validation] (If not fully covered in T008) Add specific "Bootstrap Validity Check" invocation in `code/validators.py` to flag unreliable estimates if variance discrepancy exceeds threshold (FR-010) - *Note: Logic defined in T008, T033 ensures invocation in final pipeline*
- [ ] T034 [Validation] **Run full pipeline** on 10 diverse datasets (from T004a list) covering continuous, count, binary outcomes. **Expected Artifacts**: `data/results/baseline.json`, `data/results/violations.json`, `data/results/bias_curves.json`, `data/results/sensitivity_analysis.json`. **This task is gated by T031b success and T032 enforcement.**

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` including `quickstart.md`
- [ ] T036 Run `ruff`/`flake8` and fix all linting errors
- [ ] T037 Refactor `code/main.py` (T014) to explicitly use `code/validators.py` (T008) for all data processing steps
- [ ] T038 Optimize `code/power_empirical.py` (T013) loop for CPU efficiency (e.g., vectorization, multiprocessing)
- [ ] T039 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**:
 - **T009** (Directory Setup) is merged into T001.
 - **T031b** (Synthetic Ground Truth Gate) MUST complete and PASS before **any** real-data processing (Phase 3, 4, 5, 6) begins.
 - Blocks all user story implementation and real-data runs.
- **User Stories (Phase 3+)**: All depend on Foundational (Phase 2) completion.
 - User stories can then proceed in parallel (if staffed) or sequentially.
- **Validation (Phase 6)**:
 - **T034** (Full Run) is strictly gated by **T031b** (Synthetic Validation) passing and **T032** (Runtime Enforcement) completing.
 - T034 runs after US1/US2/US3 implementation to verify full pipeline integration.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **Validation (Phase 6)**: Must run after US1 implementation to verify bootstrap logic before full-scale US2/US3 runs, but T031b (the validation logic) must pass BEFORE any real data runs.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (except T004a -> T004/T005 ordering) can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Specific Task Chains (Resolved Ordering)

- **Phase 4 (US2) Chain**:
 - T021 (Implement Perturbations) -> T021b-Config (Define Parameters) -> T021b-Sweep (Implement Sweep) -> T021b-Curve (Generate Curves)
 - T021b-Sweep also blocks T022 (Main Extension).
 - T021b-Config is the explicit blocking prerequisite for T021b-Sweep.
 - T021b-Sweep explicitly depends on T021.
- **Phase 5 (US3) Chain**:
 - T028-Config (Define Thresholds) -> T028-Sweep (Implement Sweep) -> T028-Report (Generate Report)
 - T028-Sweep depends on T021b-Curve (the artifact containing bias data).
 - T029b (Regression Analysis) depends on T021b-Curve (from Phase 4).

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Write contract test code for PowerEstimate JSON schema in tests/contract/test_schemas.py (expected to FAIL)"
Task: "Write integration test code for baseline pipeline on iris dataset in tests/integration/test_pipeline.py (expected to FAIL)"

# Launch all models for User Story 1 together:
Task: "Implement code/power_theory.py"
Task: "Implement code/power_empirical.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes T031b validation)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (T031b passed)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done (T031b passed):
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: T031b (Synthetic Ground Truth) must pass before T014 (US1) or T034 (Full Run) execute on real data.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence