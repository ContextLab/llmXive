# Tasks: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

**Input**: Design documents from `/specs/001-investigating-the-inverse-square-law/`
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

**Purpose**: Project initialization, pre-flight checks, and basic structure

- [ ] T001 Create the full project directory tree at the repository root: `projects/PROJ-191-investigating-the-validity-of-the-invers/` with sub‑directories (`code/`, `tests/`, `data/`, `docs/`, `code/data/`, `code/models/`, `code/inference/`, `code/robustness/`, `code/utils/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/contract/`, `tests/integration/`) **in a single atomic operation**.
- [X] T002 Initialize a Python project and write pinned dependencies to `projects/PROJ-191-investigating-the-validity-of-the-invers/code/requirements.txt`.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement versioning utility for atomic state updates in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/utils/versioning.py`.
- [X] T005 [P] Setup logging infrastructure and configuration management in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/config.py`.
- [X] T006 [P] Create base data model for `HarmonizedDataset` in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/data/models.py`. **Alignment**: This aligns with the plan's "Project Structure" section which implies data models should reside in a dedicated model file (e.g., `models.py`) and the `data-model.md` phase output.
- [X] T007 [P] Ensure directory structure for `data/raw/`, `data/processed/`, and `data/results/` exists (use robust `mkdir -p` logic).

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Acquisition and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Download raw force‑vs‑separation data from arXiv, convert to SI units, align on a common grid, and construct a full covariance matrix.

**Independent Test**: Execute `code/data/download.py` and `code/data/harmonize.py` against the provided arXiv URLs; verify output is a single CSV/JSON file containing aligned force data, separation distances, and a valid positive‑definite full covariance matrix (or block-diagonal fallback) with no missing values in the microscopic separation distance range.

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Unit test for SI unit conversion logic in `tests/unit/test_harmonize.py`.
- [X] T011 [P] [US1] Contract test for data schema validation in `tests/contract/test_harmonized_dataset.py`.
- [X] T012 [P] [US1] Integration test for end‑to‑end download and harmonization in `tests/integration/test_data_pipeline.py`.

### Implementation for User Story 1

- [ ] T013-VALIDATOR [US1] **Validator Implementation**: Implement `code/agents/validator.py` with a function `validate_reference(url: str, threshold: float = 0.7) -> bool`. This function MUST fetch the arXiv metadata, compute title-token-overlap, and return True/False. **Dependency**: None.
- [ ] T013-DATA [US1] **Data Acquisition**: Implement `code/data/download.py` to **fetch** arXiv:2106.08611 and arXiv:2305.06325. **Logic**:
 1. For each URL, invoke `validate_reference` (T013-VALIDATOR). If validation fails, raise `RuntimeError`.
 2. Unpack tarballs to `data/raw/`.
 3. **Run Count Check**: Count independent experimental runs found. **If len(runs) < 3 **:
 - **If** `config.py` allows fallback: Set `USE_BOOTSTRAP=true` in `data/processed/state.json` and log "Bootstrap fallback triggered: < 3 runs found".
 - **Else**: Raise `RuntimeError` with message "Primary path requires ≥3 runs. Only found {count}. Fallback disabled."
 4. **Dependency**: Must run after T013-VALIDATOR.
- [ ] T013-3RD-RUN [US1] **Third Run Fetch**: Implement logic in `code/data/download.py` to **fetch** arXiv:1909.03356 (if available) as the third independent run. **Logic**:
 1. Invoke `validate_reference`. If validation fails or file missing, log warning but **do not halt** (as this is an optional third source to meet the count).
 2. **Dependency**: Must run after T013-VALIDATOR.
- [ ] T013-CHECK-THRESHOLD [US1] **Threshold Enforcement**: Re-evaluate run count after T013-3RD-RUN. **If** total runs < 3:
 - **If** `USE_BOOTSTRAP` was set (from T013-DATA): Proceed.
 - **Else**: Raise `RuntimeError` "Primary path requires ≥3 runs. Fallback not enabled."
 - **Output**: Final `state.json` with `USE_BOOTSTRAP` flag set correctly. **Dependency**: Must run after T013-DATA and T013-3RD-RUN.
- [ ] T013-PARSE [US1] **Parser**: Implement logic in `code/data/parsers.py` to **parse** the raw CSV files extracted by T013-DATA and T013-3RD-RUN: read headers, map columns to force/separation/uncertainty fields, and construct the intermediate `HarmonizedDataset` structure. **Dependency**: Must run after T013-DATA and T013-3RD-RUN.
- [X] T014 [P] [US1] Implement unit conversion (dynes → N, micrometers → m) and grid alignment in `code/data/harmonize.py`. **Edge Case Logic**: Explicitly implement detection of non-overlapping separation ranges; if detected, **interpolate** missing points or **exclude** non-overlapping regions and **log a warning** as per spec edge cases. **Dependency**: Must run after T013-PARSE.
- [ ] T015-COV [US1] **Covariance Construction**: Implement **full** covariance matrix construction in `code/data/harmonize.py` by parsing statistical uncertainties (`stat_err`) and systematic error budgets (`sys_err` or `systematic` fields). **Fallback Logic**:
 1. If N (data points) <= 200: Construct full N×N covariance matrix.
 2. If N > 200: **Automatically switch** to block-diagonal approximation with **bandwidth=20 ** (preserving local correlations as per Plan.md).
 3. Verify the resulting matrix is positive-definite; if not, raise an error.
 4. **Output**: Store as `data/processed/covariance_matrix.npy`. **Dependency**: Must run after T014.
- [ ] T016 [US1] **Fallback Logic**: Implement logic to check the run count (from T013-CHECK-THRESHOLD). **If fewer than three independent runs are detected**, write `USE_BOOTSTRAP: true` to `data/processed/state.json`. **Crucial**: This task MUST run even if T015-COV succeeded with a fallback, ensuring the bootstrap flag is set correctly regardless of covariance strategy. **Dependency**: Must run after T013-CHECK-THRESHOLD.

**Checkpoint**: User Story 1 should now be fully functional and testable independently.

---

## Phase 4: User Story 2 - Bayesian Model Inference (Priority: P2)

**Goal**: Run `emcee` MCMC to estimate posteriors for α and λ, and `dynesty` nested sampling to compute Bayesian evidence for model comparison.

**Independent Test**: Run `code/inference/mcmc.py` and `code/inference/nested.py` on the harmonized dataset; verify output includes posterior samples, Bayes factor, and Gelman‑Rubin < 1.01 within the 6‑hour limit.

### Tests for User Story 2 (OPTIONAL)

- [X] T018 [P] [US2] Unit test for Yukawa force model implementation in `tests/unit/test_physics.py`.
- [X] T019 [P] [US2] Unit test for log‑likelihood function with full covariance in `tests/unit/test_likelihood.py`.
- [X] T020 [P] [US2] Integration test for MCMC convergence detection in `tests/integration/test_mcmc_diagnostics.py`.
- [X] T025-TEST [US2] Unit test for injection‑recovery logic (FR‑008) in `tests/unit/test_injection_recovery.py`.
- [ ] T026-TEST [US2] Unit test for null‑simulation baseline logic (FR‑009) in `tests/unit/test_null_simulation.py`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement Newtonian and Yukawa‑modified force models in `code/models/physics.py`.
- [ ] T022 [US2] Implement log‑likelihood function using the covariance matrix from T015-COV (full or block-diagonal). Use Cholesky decomposition for numerical stability. **Dependency**: Must run after T015-COV.
- [ ] T027-SUBSAMPLE [US2] **Feasibility Pilot**: Run a **pilot likelihood evaluation** on a **small subset** (e.g., 100 points) of the harmonized dataset to measure ops/sec. **Decision Logic**:
 1. If estimated runtime for full dataset > 5.5 hours: Generate `data/processed/data_config.json` with `mode: "subsample"`, `subset_indices`: [random N points], and `covariance_bandwidth`: 20.
 2. If estimated runtime < 5.5 hours: Generate `data/processed/data_config.json` with `mode: "full"`.
 3. **Output**: `data/processed/data_config.json`. **Dependency**: Must run after T022.
- [ ] T023 [US2] Implement `emcee` runner: Run a minimum of 5000 steps. **Crucial**: Continue running in batches of steps until the Gelman-Rubin statistic < 1.01 **OR** a configurable maximum step limit (`MAX_MCMC_STEPS` in `config.py`) is reached. **Time Limit**: Enforce a hard wall-clock time limit of hours. If approached, **log a warning** "TIME_LIMIT_REACHED", **attempt to reduce step count in batches**, but **DO NOT stop early** unless convergence is achieved or 5000 steps reached. If time limit is exceeded, **flag the result as `TIME_LIMITED`** but do not discard partial convergence data. **Input**: Read `data/processed/data_config.json` (T027) to determine if subsampling is required. **Dependency**: Must run after T022 and T027-SUBSAMPLE. <!-- ATOMIZE: requested -->
- [X] T024 [US2] Implement `dynesty` nested sampler for both Newtonian and Yukawa models in `code/inference/nested.py`.
- [ ] T025-INJECTION [US2] **Injection-Recovery Test**: Implement `code/robustness/injection.py`. **Logic**:
 1. Generate simulated data with a known non-zero α and realistic noise.
 2. Run a local inference instance (using T021/T022 logic, independent of T023).
 3. **Calculate**: `distance = abs(injected_alpha - recovered_alpha_median)`.
 4. **Determine Pass**: `SC005_PASS = (recovered_alpha_median within 95% CI of injected value)`.
 5. **Output**: `data/results/injection_recovery_report.json` containing `injected_alpha`, `recovered_alpha_median`, `95% CI`, `distance`, and `SC005_PASS` (calculated boolean). **Dependency**: Must run after T021 and T022.
- [ ] T026-NULL-SIM [US2] **Null-Simulation Test**: Implement `code/robustness/null_simulation.py`. **Logic**:
 1. Generate simulated data where α=0 is true but systematic errors are present.
 2. Run a local inference instance.
 3. **Calculate**: `false_positive = (Bayes_factor_K > 3)`.
 4. **Output**: `data/results/null_baseline_report.json` containing `true_alpha`, `recovered_alpha_median`, `bayes_factor_K`, `false_positive_detected`, and `SC002_BASELINE_PASS` (calculated boolean: true if false_positive rate is acceptable). **Dependency**: Must run after T021 and T022.

**Checkpoint**: User Stories 1 & 2 should now work independently.

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform leave‑one‑experiment‑out cross-validation and systematic uncertainty inflation tests to ensure result stability.

**Independent Test**: Run `code/robustness/cross_val.py` and `code/robustness/uncertainty.py`; verify Bayes factors and credible‑upper‑limit shifts stay < 15% across all iterations.

### Tests for User Story 3 (OPTIONAL)

- [X] T028 [P] [US3] Unit test for leave‑one‑out logic in `tests/unit/test_cross_val.py`.
- [X] T029 [P] [US3] Integration test for uncertainty inflation stability in `tests/integration/test_robustness.py`.

### Implementation for User Story 3

- [X] T030 [US3] Implement leave‑one‑experiment‑out cross‑validation loop in `code/robustness/cross_val.py`. **Conditional logic**:
 1. If `USE_BOOTSTRAP` flag (from T013-CHECK-THRESHOLD) is false AND runs >= 3: Perform true leave-one-out (remove one run, re-infer).
 2. If `USE_BOOTSTRAP` flag is true OR runs < 3: **Implement bootstrap resampling**: Sample N rows **with replacement** from the dataset. For each bootstrap sample, extract the corresponding block-diagonal covariance sub-matrix and re-infer. **Algorithm**: Use `numpy.random.choice` with `replace=True` to select indices; re-calculate mean and covariance for the sample.
 3. Store each iteration's α upper‑limit (high percentile) for later analysis. **Dependency**: Must run after T013-CHECK-THRESHOLD.
- [X] T031 [US3] Implement systematic uncertainty inflation test in `code/robustness/uncertainty.py`. **Parameter**: Read the inflation factor from `code/config.py`. Apply it to the covariance matrix. Verify the Bayes factor changes by a negligible amount (e.g., < 0.1 log-units). **Dependency**: Must run after T023.
- [ ] T032 [US3] Implement parallel execution of robustness iterations using `multiprocessing`.
- [ ] T033 [US3] Calculate the **coefficient of variation (CV)** of the credible‑upper‑limits (95th percentile) across all robustness iterations, where **CV = (standard deviation ÷ mean) × 100 **. Log the CV percentage; if **CV > 15%**, **log a warning and flag the result** (do NOT raise an error) to match the spec's intent to "assess stability" and "log" results. **Dependency**: Must run after T030.
- [ ] T038 [US2/US3] **Single Source of Truth & SC-002 Verification**: Compute the Bayes‑factor comparison metric. **Check 1**: Compare the primary Bayes factor K against the null-simulation baseline from `data/results/null_baseline_report.json` (T026) to ensure the result is not a systematic artifact. **Check 2**: Compare K against the **Kass–Raftery scale** (K > 3 indicates substantial evidence for the Yukawa model). **Output**: Log the result for SC‑002 reporting, including an explicit PASS/FAIL status if K <= 3 (insufficient evidence) or if the baseline comparison fails (result is likely an artifact). **Dependency**: Must run after T026 and T033.
- [ ] T039-REPORT [US2/US3] **Aggregation**: Aggregate the pass/fail status from T025 (SC-005) and T026 (SC-002) into a single summary artifact `data/results/validity_report.json`. Explicitly log the SC-005 status (recovered α within 95% CI) as a distinct field `SC005_PASS` and the SC-002 baseline status as `SC002_BASELINE_PASS`. Include the detailed metrics from the injection and null simulation reports. **Dependency**: Must run after T025, T026, and T038.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Generate visualization plots for posteriors and Bayes factors in `code/utils/plotting.py`.
- [ ] T035-A [P] Update `README.md` with project overview, prerequisites, and high‑level run command.
- [ ] T035-B [P] Update `docs/quickstart.md` with detailed pipeline execution instructions, data paths, and troubleshooting guide.
- [ ] T036 Run full pipeline end‑to‑end validation and verify `state/projects/PROJ-191...yaml` updates correctly.
- [ ] T037 [P] Optimize likelihood evaluation speed (tune Cholesky implementation) if total runtime exceeds a predefined threshold.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately. **T001 must run first**.
- **Foundational (Phase 2)**: Depends on Setup completion – BLOCKS all user stories.
- **User Stories (Phase 3‑5)**: All depend on Foundational completion.
 - User Story 1 can start after Phase 2.
 - User Story 2 starts after Phase 2 **and** after the harmonized dataset from US 1 is available.
 - User Story 3 starts after Phase 2 **and** after inference results from US 2 are available.
- **Polish (Phase 6)**: Depends on completion of all desired user stories.

### Within Each User Story

- **TDD Flow**: Test tasks (e.g., T010‑T012, T025‑TEST, T026‑TEST) must be written and **FAIL** before their corresponding implementation tasks are executed.
- Models before services, services before endpoints, core implementation before integration, story complete before moving to next priority.
- Parallel opportunities are indicated by the `[P]` tag where safe.

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for SI unit conversion logic in tests/unit/test_harmonize.py"
Task: "Contract test for data schema validation in tests/contract/test_harmonized_dataset.py"
Task: "Integration test for end‑to‑end download and harmonization in tests/integration/test_data_pipeline.py"

# Launch implementation tasks (ordered where required):
Task: "Implement code/agents/validator.py (T013-VALIDATOR)"
Task: "Implement code/data/download.py to fetch arXiv:2106.08611, 2305.06325..."
Task: "Parse raw tarball contents into HarmonizedDataset (T013-PARSE)..."
Task: "Implement unit conversion and grid alignment in code/data/harmonize.py"
Task: "Implement covariance construction with block-diagonal fallback (T015-COV)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup).
2. Complete Phase 2 (Foundational) – blocks all stories.
3. Complete Phase 3 (User Story 1).
4. **STOP and VALIDATE**: Test User Story 1 independently.
5. Deploy/demo if ready.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add User Story 1 → test → demo (MVP!).
3. Add User Story 2 → test → demo.
4. Add User Story 3 → test → demo.
5. Each story adds value without breaking prior stories.

### Parallel Team Strategy

- With multiple developers:
 1. Team finishes Setup + Foundational together.
 2. Once Foundational is done:
 - Dev A: User Story 1
 - Dev B: User Story 2
 - Dev C: User Story 3
 3. Stories integrate independently.

---

## Notes

- `[P]` tasks = different files, no dependencies (unless explicitly noted).
- `[Story]` label maps task to a specific user story for traceability.
- Each user story should be independently completable and testable.
- Verify tests fail before implementing; commit after each logical group.
- Stop at any checkpoint to validate story independently.
- Avoid vague tasks, file conflicts, or cross‑story hidden dependencies.
