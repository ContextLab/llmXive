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

**Purpose**: Project initialization, pre‑flight checks, and basic structure

- [ ] T001-ROOT Create the root project directory tree at the repository root: `projects/PROJ-191-investigating-the-validity-of-the-invers/` using the shell command `mkdir -p projects/PROJ-191-investigating-the-validity-of-the-invers`.
- [ ] T001-CODE [P] Create the `code/` directory and all required sub‑directories within the project root: `code/`, `code/data/`, `code/models/`, `code/inference/`, `code/robustness/`, `code/utils/` using the shell command `mkdir -p projects/PROJ-191-investigating-the-validity-of-the-invers/code/{data,models,inference,robustness,utils}`.
- [ ] T001-DATA [P] Create the `data/` directory and all required sub‑directories: `data/raw/`, `data/processed/`, `data/results/` using the shell command `mkdir -p projects/PROJ-191-investigating-the-validity-of-the-invers/data/{raw,processed,results}`.
- [ ] T001-TESTS [P] Create the `tests/` directory and all required sub‑directories: `tests/unit/`, `tests/contract/`, `tests/integration/` using the shell command `mkdir -p projects/PROJ-191-investigating-the-validity-of-the-invers/tests/{unit,contract,integration}`.
- [ ] T002 Initialize a Python project in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/` and write pinned dependencies to `projects/PROJ-191-investigating-the-validity-of-the-invers/code/requirements.txt` using `pip freeze` after installing core dependencies.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `.ruff.toml` and adding `[tool.black]` / `[tool.ruff]` sections to `pyproject.toml` in the root directory.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement versioning utility for atomic state updates in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/utils/versioning.py`.
- [X] T005 [P] Setup logging infrastructure and configuration management in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/config.py`.
- [X] T006 [P] Create base data model for `HarmonizedDataset` in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/data/models.py`. **Alignment**: This aligns with the plan's "Project Structure" section. **Definition**: Implement a Pydantic model with fields `separation_m` (np.ndarray, shape (N,)), `force_n` (np.ndarray, shape (N,)), `covariance_matrix` (np.ndarray, shape (N, N)), and `metadata` (dict). **Dependency**: Runs after T005. <!-- FAILED: unspecified -->
- [ ] T007 [P] Ensure directory structure for `data/raw/`, `data/processed/`, and `data/results/` exists (use robust `mkdir -p` logic).

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Acquisition and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Download raw force‑vs‑separation data from arXiv, convert to SI units, align on a common grid, and construct a full covariance matrix.

**Independent Test**: Execute `code/data/download.py` and `code/data/harmonize.py` against the provided arXiv URLs; verify output is a single CSV/JSON file containing aligned force data, separation distances, and a valid positive‑definite **full** covariance matrix with no missing values in the microscopic separation distance range.

**Sequential Flow**: T013-AGENT → T013-DOC-CIT → T013-DATA → T013-CALIB-VAL → T013-CALIB-DSK → T013-PARSE → T014 → T015-COV

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Unit test for SI unit conversion logic in `tests/unit/test_harmonize.py`.
- [X] T011 [P] [US1] Contract test for data schema validation in `tests/contract/test_harmonized_dataset.py`.
- [X] T012 [P] [US1] Integration test for end‑to‑end download and harmonization in `tests/integration/test_data_pipeline.py`.

### Implementation for User Story 1

- [ ] T013-AGENT [US1] **Validator Invocation**: Implement logic in `code/agents/validator.py` to invoke the official **Reference‑Validator Agent** CLI.
 1. Command: `reference-validator --arxiv-id <id>`.
 2. Expected Exit Code: `0` for success, `1` for failure.
 3. On failure (non-zero exit), raise `RuntimeError` with the agent's error message.
 4. Verify arXiv:2106.08611 and arXiv:2305.06325. [UNRESOLVED-CLAIM: c_a7951992 — status=not_enough_info]
- [ ] T013-DOC-CIT [US1] **Document Citation Validation**: Implement logic in `code/agents/validator.py` to validate all external citations found in `research.md` and `plan.md` against their primary sources as required by Constitution Principle II.
 1. Parse `research.md` and `plan.md` for citation patterns (e.g., `arXiv:xxxx.xxxxx`).
 2. Invoke the Reference-Validator Agent for each found ID.
 3. Raise `RuntimeError` if any citation is unreachable or mismatched.
- [ ] T013-DATA [US1] **Data Acquisition**: Implement `code/data/download.py` to **fetch** arXiv:2106.08611 and arXiv:2305.06325.
 1. Call the Reference‑Validator Agent (T013‑AGENT) and Document Citation Validator (T013-DOC-CIT). On failure, raise `RuntimeError`.
 2. Unpack tarballs to `data/raw/`.
 3. Scan for files matching `*_run*.csv` (or metadata `experiment_id`) to count independent experimental runs.
 4. **If** `len(runs) < 3`: **log a warning** `"Insufficient runs (<3) for leave‑one‑out cross‑validation; robustness stage will use bootstrap fallback."` Continue execution; downstream robustness tasks will handle the fallback.
 5. **If** `len(runs) >= 3`: proceed normally.
 6. **Dependency**: Runs after T013-AGENT and T013-DOC-CIT.
- [ ] T013-CALIB-VAL [US1] **Calibration Curve Validation**: Implement logic in `code/agents/validator.py` to validate the specific arXiv ID or URL for the calibration curves mentioned in the spec for arXiv:2305.06325 (if distinct from the main paper).
 1. Identify the specific file or section in the arXiv source containing calibration curves.
 2. Invoke the Reference-Validator Agent for the identified ID/URL.
 3. Raise `RuntimeError` if validation fails.
 4. **Dependency**: Runs after T013-DATA.
- [ ] T013-CALIB-DSK [US1] **Calibration Curve Data Fetch**: Implement logic in `code/data/download.py` to specifically fetch and parse the "calibration curves" data file mentioned in the spec for arXiv:2305.06325.
 1. Identify the specific file containing calibration curves within the arXiv:2305.06325 tarball.
 2. Download and store in `data/raw/calibration/`.
 3. Parse the file to extract force-vs-separation data or calibration parameters.
 4. **Dependency**: Runs after T013-CALIB-VAL.
- [ ] T013-PARSE [US1] **Parser**: Implement logic in `code/data/parsers.py` to parse the raw CSV files extracted by T013‑DATA and T013-CALIB-DSK: read headers, map columns to force, separation, and uncertainty fields, and construct intermediate `HarmonizedDataset` objects. **Dependency**: Runs after T013-DATA, T013-CALIB-VAL, and T013-CALIB-DSK.
- [X] T014 [P] [US1] Implement unit conversion (dynes → N, micrometers → m) and grid alignment in `code/data/harmonize.py`. **Edge‑case handling**: Detect non‑overlapping separation ranges; interpolate missing points or exclude non‑overlapping regions and log a warning as required by the spec.
- [ ] T015-COV [US1] **Covariance Construction**: Implement construction of a **full covariance matrix** in `code/data/harmonize.py` by combining statistical uncertainties and systematic error budgets.
 1. **Primary Strategy**: Attempt to construct a full matrix including off-diagonal terms if the source data provides systematic correlation information.
 2. **Documentation Prerequisite**: If the source data explicitly lacks off-diagonal terms, **first** document this absence in the output metadata as a prerequisite for the fallback.
 3. **Fallback Strategy**: If and only if the source data explicitly lacks off-diagonal terms (after documentation), construct a diagonal matrix.
 4. **Sensitivity Analysis**: Implement logic to construct a **banded covariance matrix** (bandwidth = 20) to test the impact of unmodeled correlations as required by the Plan's Complexity Tracking.
 5. Verify the matrix is positive‑definite using `scipy.linalg.cholesky` with `check_finite=False` and a tolerance for eigenvalues. Raise an error if not.
 6. Output as `data/processed/covariance_matrix.npy`. **Dependency**: Runs after T014.

**Checkpoint**: User Story 1 should now be fully functional and testable independently.

---

## Phase 4: User Story 2 - Bayesian Model Inference (Priority: P2)

**Goal**: Run `emcee` MCMC to estimate posteriors for α and λ, and `dynesty` nested sampling to compute Bayesian evidence for model comparison.

**Independent Test**: Run `code/inference/mcmc.py` and `code/inference/nested.py` on the harmonized dataset; verify output includes posterior samples, Bayes factor, and Gelman‑Rubin < 1.01 **after the full run** within the 6-hour limit.

### Tests for User Story 2 (OPTIONAL)

- [ ] T018 [P] [US2] Unit test for Yukawa force model implementation in `tests/unit/test_physics.py`.
- [ ] T019 [P] [US2] Unit test for log‑likelihood function with full covariance in `tests/unit/test_likelihood.py`.
- [ ] T020 [P] [US2] Integration test for MCMC convergence detection in `tests/integration/test_mcmc_diagnostics.py`.
- [ ] T025-TEST [US2] Unit test for injection‑recovery logic (FR‑008) in `tests/unit/test_injection_recovery.py`.
- [ ] T026-TEST [US2] Unit test for null‑simulation baseline logic (FR‑009) in `tests/unit/test_null_simulation.py`.

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement Newtonian and Yukawa‑modified force models in `code/models/physics.py`.
- [ ] T022 [US2] Implement log‑likelihood function using the **full** covariance matrix from T015‑COV. Employ Cholesky decomposition for numerical stability. **Dependency**: Runs after T015‑COV.
- [ ] T027-SUBSAMPLE [US2] **Feasibility & Subsampling**: Implement logic in `code/data/config.py` to decide whether to subsample based on an *estimated* runtime.
 1. **Estimation Formula**: Measure the actual wall-clock time taken for the first 100 steps of the MCMC run (batch). Project the total runtime using: `total_estimated_time = (batch_wall_time /) * 5000`.
 2. **Threshold**: If `total_estimated_time > 5.5` hours (leaving a 0.5-hour buffer for retries within the 6-hour limit), set mode = "subsample" and select the first 2000 points (or the largest subset that keeps estimated runtime ≤ 5.5h).
 3. **Recording**: Record the mode and selected indices in `data/processed/data_config.json`.
 4. **Covariance Handling**: When subsampling, the covariance matrix is stored as a **block‑diagonal** matrix (bandwidth = 20) to retain local correlation structure.
 5. **Output**: `data/processed/data_config.json`. **Dependency**: Runs after T022 (log-likelihood implementation complete).
- [ ] T023-MCMC [US2] **MCMC Execution**: Implement `emcee` runner in `code/inference/mcmc.py`.
 1. Run in **batches** of steps with 100 walkers.
 2. After each batch, compute the Gelman‑Rubin statistic.
 3. **Stop Condition**: Run until Gelman‑Rubin < 1.01. Extend steps indefinitely if convergence is not met by 5000 steps. Do NOT impose a hard step cap.
 4. **Timeout Enforcement**: Implement a hard wall-clock timeout of a fixed duration. If the limit is reached before convergence, stop the run, log `"TIME_LIMIT_REACHED"`, and flag the result as unreliable. Do NOT attempt to re-run after the timeout.
 5. Store chains in `data/results/mcmc_chains.npy`. **Dependency**: Runs after T022 and T027‑SUBSAMPLE.
- [ ] T024 [US2] Implement `dynesty` nested sampler for both Newtonian and Yukawa models in `code/inference/nested.py`.
- [ ] T025-INJECTION [US2] **Injection‑Recovery Test**: Implement `code/robustness/injection.py`.
 1. Generate synthetic data with a known non-zero α and realistic noise using the full covariance matrix.
 2. Run a local inference instance (re‑using T021/T022 logic, independent of T023‑MCMC).
 3. Compute `distance = |injected_alpha – recovered_alpha_median|`.
 4. Determine pass: `SC005_PASS = (recovered_alpha_median within 95 % CI of injected value)`.
 5. Output `data/results/injection_recovery_report.json` with all metrics. **Dependency**: Runs after T021 and T022.
- [ ] T026-NULL-SIM [US2] **Null‑Simulation Test**: Implement `code/robustness/null_simulation.py`.
 1. Generate synthetic data with α = 0 but realistic systematic errors.
 2. Run inference.
 3. Compute `false_positive = (Bayes_factor_K > 3)`.
 4. Output `data/results/null_baseline_report.json` with `true_alpha`, `recovered_alpha_median`, `bayes_factor_K`, `false_positive_detected`, and `SC002_BASELINE_PASS` (true if false‑positive rate is acceptable). **Dependency**: Runs after T021 and T022.

**Checkpoint**: User Stories 1 & 2 should now work independently.

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform leave‑one‑experiment‑out cross-validation and systematic uncertainty inflation tests to ensure result stability.

**Independent Test**: Run `code/robustness/cross_val.py` and `code/robustness/uncertainty.py`; verify Bayes factors and credible‑upper‑limit shifts stay < 15% across all iterations.

### Tests for User Story 3 (OPTIONAL)

- [ ] T028 [P] [US3] Unit test for leave‑one‑out logic in `tests/unit/test_cross_val.py`.
- [ ] T029 [P] [US3] Integration test for uncertainty inflation stability in `tests/integration/test_robustness.py`.

### Implementation for User Story 3

- [ ] T030 [US3] Implement leave‑one‑experiment‑out cross-validation loop in `code/robustness/cross_val.py`.
 1. **Primary method**: If `runs ≥ 3`, iteratively omit one experimental run, recompute the harmonized dataset, and re‑run inference.
 2. **Fallback method**: If `runs < 3`, perform **row bootstrap resampling** with **N = 1000** samples (as stipulated in the plan). For each bootstrap sample, recompute the diagonal (or block‑diagonal) covariance and re‑run inference.
 3. Store each iteration's 95 % credible upper limit for α for later analysis. **Dependency**: Runs after T014, T015, and T023‑MCMC.
- [ ] T031 [US3] Implement systematic uncertainty inflation test in `code/robustness/uncertainty.py`. **Parameter**: Read `INFLATION_FACTOR` from `code/config.py`. If missing, use default value `1.1`. Apply it multiplicatively to the covariance matrix. Verify that the Bayes factor changes by a negligible amount; log the result. **Dependency**: Runs after T023‑MCMC.
- [ ] T032-CV [US3] Implement parallel execution of cross-validation iterations in `code/robustness/cross_val.py` using `concurrent.futures.ProcessPoolExecutor` with `max_workers` set to available CPU cores. The unit of work is the `run_inference_for_subset` function for each left-out run.
- [ ] T032-UNC [US3] Implement parallel execution of uncertainty inflation iterations in `code/robustness/uncertainty.py` using `concurrent.futures.ProcessPoolExecutor`. The unit of work is the `run_inference_with_inflated_covariance` function for each inflation factor.
- [ ] T033 [US3] Calculate the robustness metrics in `code/robustness/metrics.py`.
 1. **Metric 1**: Calculate the Coefficient of Variation (CV) of the credible‑upper‑limits (95th percentile) across all robustness iterations (`CV = (std / mean) * 100`).
 2. **Metric 2**: Calculate the **relative shift**: `(max_limit - min_limit) / mean_limit`.
 3. **Acceptance Criterion**: Verify `relative_shift < 0.15` ([deferred]) as defined in SC-003.
 4. **Artifact**: Write `data/results/robustness_metrics.json` containing `cv_value`, `relative_shift`, `threshold` (0.15), and `pass` (boolean: `relative_shift < 0.15`).
 5. If `pass` is false, flag the result as "unstable" in the report. **Dependency**: Runs after T030.
- [ ] T038 [US2/US3] **Single Source of Truth & SC‑002 Verification**:
 1. Load Bayes factor `K` from the primary inference (`data/results/bayes_factor.json`).
 2. Load null‑simulation baseline statistics (`mean`, `std`) from `data/results/null_baseline_report.json`.
 3. Compute `SC002_KASS_RAFTERY_PASS = (K > 3)`.
 4. Compute `SC_BASELINE_PASS = (K < baseline_mean + 2 × baseline_std)`.
 5. Log both pass/fail statuses. **Dependency**: Runs after T026‑NULL‑SIM, T033, and T023‑MCMC.
- [ ] T039-REPORT [US2/US3] **Aggregation**: Aggregate the pass/fail status from T025 (SC‑005) and T038 (SC‑002) into a single summary artifact `data/results/validity_report.json`. Include fields `SC005_PASS`, `SC002_KASS_RAFTERY_PASS`, `SC002_BASELINE_PASS`, and embed the detailed metrics from the injection and null‑simulation reports. **Dependency**: Runs after T025, T026‑NULL‑SIM, and T038.

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

- **Setup (Phase 1)**: No dependencies – can start immediately. **T001-ROOT must run first**.
- **Foundational (Phase 2)**: Depends on Setup completion – BLOCKS all user stories.
- **User Stories (Phase 3‑5)**: All depend on Foundational completion.
 - User Story 1 can start after Phase 2.
 - User Story 2 starts after Phase 2 **and** after the harmonized dataset from US 1 is available.
 - User Story 3 starts after Phase 2 **and** after inference results from US 2 are available.
- **Polish (Phase 6)**: Depends on completion of all desired user stories.

### Within Each User Story

- **TDD Flow**: Test tasks (e.g., T010‑T012, T025‑TEST, T026‑TEST) must be written and **FAIL** before their corresponding implementation tasks are executed.
- Models before services, services before endpoints, core implementation before integration, story complete before moving to next priority.
- Parallel opportunities are indicated by the `[P]` tag where safe.

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for SI unit conversion logic in tests/unit/test_harmonize.py"
Task: "Contract test for data schema validation in tests/contract/test_harmonized_dataset.py"
Task: "Integration test for end‑to‑end download and harmonization in tests/integration/test_data_pipeline.py"

# Launch implementation tasks (ordered where required):
Task: "Implement code/agents/validator.py (T013-AGENT)"
Task: "Implement code/data/download.py to fetch arXiv:2106.08611, 2305.06325..."
Task: "Parse raw tarball contents into HarmonizedDataset (T013-PARSE)..."
Task: "Implement unit conversion and grid alignment in code/data/harmonize.py"
Task: "Implement full covariance construction (T015-COV)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup).
2. Complete Phase 2 (Foundational) – blocks all stories.
3. Complete Phase 3 (User Story 1).
4. **STOP and VALIDATE**: Test User Story 1 independently.
5. Deploy/demo if ready.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add User Story 1 → test → demo (MVP!).
3. Add User Story 2 → test → demo.
4. Add User Story 3 → test → demo.
5. Each story adds value without breaking prior stories.

### Parallel Team Strategy

- With multiple developers:
 1. Team finishes Setup + Foundational together.
 2. Once Foundational is done:
 - Dev A: User Story 1
 - Dev B: User Story 2
 - Dev C: User Story 3
 3. Stories integrate independently.

---

## Notes

- `[P]` tasks = different files, no dependencies (unless explicitly noted).
- `[Story]` label maps task to a specific user story for traceability.
- Each user story should be independently completable and testable.
- Verify tests fail before implementing; commit after each logical group.
- Stop at any checkpoint to validate story independently.
- Avoid vague tasks, file conflicts, or hidden cross‑story dependencies.