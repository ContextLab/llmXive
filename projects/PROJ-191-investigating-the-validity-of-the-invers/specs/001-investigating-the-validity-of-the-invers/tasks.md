# Tasks: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

**Input**: Design documents from `/specs/001-investigating-the-inverse-square-law/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
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

- [ ] T001-A-INIT-CODE Create the code directory tree at the repository root: `projects/PROJ-191-investigating-the-validity-of-the-invers/code/` using the shell command `mkdir -p projects/PROJ-191-investigating-the-validity-of-the-invers/code`.

- [ ] T001-B-INIT-DATA Create the data directory tree: `projects/PROJ-191-investigating-the-validity-of-the-invers/data/` including `data/raw/`, `data/processed/`, `data/results/` using the shell command `mkdir -p projects/PROJ-191-investigating-the-validity-of-the-invers/data/{raw,processed,results}`.

- [ ] T001-C-INIT-TEST Create the test directory tree: `projects/PROJ-191-investigating-the-validity-of-the-invers/tests/` including `tests/unit/`, `tests/contract/`, `tests/integration/` using the shell command `mkdir -p projects/PROJ-191-investigating-the-validity-of-the-invers/tests/{unit,contract,integration}`.

- [ ] T002 Initialize a Python project in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/` and write pinned dependencies to `projects/PROJ-191-investigating-the-validity-of-the-invers/code/requirements.txt`.
 1. Create `requirements.txt` with the following EXACT pinned versions:
 ```
 numpy==1.26.4
 scipy==1.13.1
 pandas==2.2.2
 emcee==3.1.6
 dynesty==2.1.4
 astropy==6.1.1
 requests==2.32.3
 pytest==8.3.2
 ruamel.yaml==0.18.6
 ```
 2. **Execute**: Run `python -m venv venv` to create an isolated environment, then `source venv/bin/activate` (or `venv\Scripts\activate` on Windows), and finally `pip install -r requirements.txt`.

- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `.ruff.toml` and adding `[tool.black]` / `[tool.ruff]` sections to `pyproject.toml` in the root directory.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement versioning utility for atomic state updates in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/utils/versioning.py`.
- [X] T005 [P] Setup logging infrastructure and configuration management in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/config.py`.
- [X] T006 [P] Create base data model for `HarmonizedDataset` in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/data/models.py`. **Alignment**: This alignes with the plan's "Project Structure" section. **Definition**: Implement a Pydantic model with fields `separation_m` (np.ndarray, shape (N,)), `force_n` (np.ndarray, shape (N,)), `covariance_matrix` (np.ndarray, shape (N, N)), and `metadata` (dict).

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Acquisition and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Download raw force‑vs‑separation data from arXiv, convert to SI units, align on a common grid, and construct a full covariance matrix.

**Independent Test**: Execute `code/data/download.py` and `code/data/harmonize.py` against the provided arXiv URLs; verify output is a single CSV/JSON file containing aligned force data, separation distances, and a valid positive‑definite **full (diagonal)** covariance matrix with no missing values in the microscopic separation distance range.

**Sequential Flow**: T013-VALIDATE-IDS → T013-DATA → T013-PARSE → T013-ORCH-ROUTE → (T014/T015 OR T013-BOOTSTRAP)

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Unit test for SI unit conversion logic in `tests/unit/test_harmonize.py`.
- [X] T011 [P] [US1] Contract test for data schema validation in `tests/contract/test_harmonized_dataset.py`.
- [X] T012 [P] [US1] Integration test for end‑to‑end download and harmonization in `tests/integration/test_data_pipeline.py`.

### Implementation for User Story 1

- [ ] T013-VALIDATE-IDS [US1] **ID Verification**: Implement `code/data/validator.py` to verify arXiv IDs using native HTTP requests.
 1. Use `requests` to fetch metadata for `arXiv:2106.08611` and `arXiv:2305.06325` from `https://export.arxiv.org/api/query?id_list=2106.08611,2305.06325`.
 2. Verify the ID exists and returns a valid response (HTTP success status).
 3. Raise `RuntimeError` if the ID is invalid or the source is unreachable.
 4. Do NOT invoke any external CLI agents.

- [ ] T013-DATA [US1] **Data Acquisition**: Implement `code/data/download.py` to **fetch** arXiv:2106.08611 and arXiv:2305.06325.
 1. Call `code/data/validator.py` (T013-VALIDATE-IDS) first. On failure, raise `RuntimeError`.
 2. Unpack tarballs to `data/raw/`.
 3. Scan for files matching `*_run*.csv` (or metadata `experiment_id`) to count independent experimental runs.
 4. Write the count of runs to `data/processed/run_count.json`.
 5. **Do NOT** implement conditional logic here. Just output the count.
 6. **Dependency**: Runs after T013-VALIDATE-IDS.

- [ ] T013-PARSE [US1] **Parser**: Implement logic in `code/data/parsers.py` to parse the raw CSV files extracted by T013‑DATA.
 1. Read headers, map columns to force, separation, and uncertainty fields.
 2. **Calibration Extraction**: Search for files matching regex patterns `calibration.*csv` or `calib.*dat` within the tarball. Extract force-vs-separation data or calibration parameters.
 3. Construct intermediate `HarmonizedDataset` objects.
 4. **Dependency**: Runs after T013-DATA.

- [ ] T013-ORCH-ROUTE [US1] **Orchestration & Routing**: Implement `code/data/orchestrator.py` to route the pipeline based on run count.
 1. Read `data/processed/run_count.json`.
 2. **If** `count >= 3`: Execute T014 (harmonize) and T015 (covariance) logic.
 3. **If** `count < 3`: Execute T013-BOOTSTRAP logic immediately.
 4. This task acts as the control flow bridge, ensuring the correct path is taken.
 5. **Output**: Write `data/processed/orchestration_status.json` with the chosen path.
 6. **Dependency**: Runs after T013-DATA and T013-PARSE.
 7. **Invocation**: Explicitly invoke T013-BOOTSTRAP via a function call or subprocess if `count < 3`.

- [ ] T013-BOOTSTRAP [US1] **Bootstrap Resampling Fallback**: Implement `code/data/bootstrap.py` to generate bootstrap resamples if `len(runs) < 3`.
 1. Read the raw data parsed by T013-PARSE.
 2. Perform row-wise bootstrap resampling with N=1000 samples (as stipulated in the plan).
 3. **Construct the final 'full' covariance matrix** (diagonal with systematic propagation) for each resample, as required by FR-002.
 4. Output the resampled dataset(s) to `data/processed/robustness/bootstrap/`.
 5. **Dependency**: Runs after T013-PARSE (triggered by T013-ORCH-ROUTE).

- [X] T014 [P] [US1] Implement unit conversion (dynes → N, micrometers → m) and grid alignment in `code/data/harmonize.py`. **Edge‑case handling**: Detect non‑overlapping separation ranges; interpolate missing points or exclude non‑overlapping regions and log a warning as required by the spec.

- [ ] T015-A-COV-CONSTRUCT [US1] **Covariance Construction (Diagonal)**: Implement construction of the diagonal covariance matrix in `code/data/harmonize.py`.
 1. Combine statistical uncertainties and systematic error budgets into a diagonal matrix.
 2. Output as `data/processed/covariance_matrix_diagonal.npy`.
 3. **Dependency**: Runs after T014.

- [ ] T015-A-COV-VERIFY [US1] **Covariance Verification**: Verify the diagonal matrix is positive‑definite.
 1. Verify the matrix is positive‑definite using `scipy.linalg.cholesky` with `check_finite=False`.
 2. Log any errors.
 3. **Dependency**: Runs after T015-A-COV-CONSTRUCT.

- [ ] T015-B-COV-BAND [US1] **Covariance Construction (Banded)**: Implement construction of the banded covariance matrix in `code/data/harmonize.py`.
 1. Construct a **banded covariance matrix** (bandwidth = 20) to test the impact of unmodeled correlations.
 2. Verify the matrix is positive‑definite.
 3. Output as `data/processed/covariance_matrix_banded.npy`.
 4. **Dependency**: Runs after T014.

- [ ] T015-C-COV-SENS [US1] **Covariance Sensitivity Analysis**: Implement `code/data/sensitivity.py` to compare diagonal vs. banded results.
 1. Run a quick inference test (using a reduced step count) on both the diagonal and banded matrices.
 2. Compare the resulting Bayes factors and credible limits.
 3. Document the justification for using the diagonal matrix (e.g., "Diagonal and banded results differ by < X%").
 4. Output `data/processed/covariance_sensitivity_report.json`.
 5. **Dependency**: Runs after T015-A-COV-VERIFY and T015-B-COV-BAND.

- [ ] T015-Z-RESOLVE-COV [US1] **Covariance Requirement Resolution**: Implement logic to formally resolve the FR-002 requirement.
 1. Read `data/processed/covariance_sensitivity_report.json`.
 2. If the difference is negligible (< 1%), select the diagonal matrix; otherwise, select the banded matrix.
 3. Write `data/processed/covariance_strategy.json` with the selected matrix path.
 4. **Crucially**: Explicitly document in `data/processed/covariance_resolution_log.json` that a true full covariance matrix (with off-diagonal terms) is impossible due to missing source data, and that the diagonal/banded approximation is the only scientifically valid "full" matrix under the constraints. This log serves as the formal resolution for FR-002.
 5. **Dependency**: Runs after T015-C-COV-SENS.

**Checkpoint**: User Story 1 should now be fully functional and testable independently.

---

## Phase 4: User Story 2 - Bayesian Model Inference (Priority: P2)

**Goal**: Run `emcee` MCMC to estimate posteriors for α and λ, and `dynesty` nested sampling to compute Bayesian evidence for model comparison.

**Independent Test**: Run `code/inference/mcmc.py` and `code/inference/nested.py` on the harmonized dataset; verify output includes posterior samples, Bayes factor, and Gelman‑Rubin < 1.01 **after the full run** within the prescribed time limit.

### Tests for User Story 2 (OPTIONAL)

- [X] T018 [P] [US2] Unit test for Yukawa force model implementation in `tests/unit/test_physics.py`.
- [X] T019 [P] [US2] Unit test for log‑likelihood function with full covariance in `tests/unit/test_likelihood.py`.
- [X] T020 [P] [US2] Integration test for MCMC convergence detection in `tests/integration/test_mcmc_diagnostics.py`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement Newtonian and Yukawa‑modified force models in `code/models/physics.py`.
- [ ] T022 [P] [US2] Implement log‑likelihood function using the **full** covariance matrix from T015. Employ Cholesky decomposition for numerical stability. **Dependency**: Runs after T015-Z-RESOLVE-COV and T021.

- [ ] T027-DECIDE [US2] **Feasibility Decision**: Implement logic in `code/data/config.py` to decide whether to subsample based on dataset size.
 1. **Check**: Read the actual harmonized dataset artifact (output of T014/T015) to measure its size. If the dataset size exceeds available RAM or projected runtime, set a flag `needs_subsample = True`.
 2. **Output**: `data/processed/data_config.json` with `needs_subsample` flag.
 3. **Dependency**: Runs after T015-Z-RESOLVE-COV and T014/T015 (harmonized dataset).

- [ ] T027-GEN [US2] **Data Subsample Generation**: Implement `code/data/subsampling.py` to generate the subsampled dataset.
 1. If `needs_subsample` is True, select a pre-defined subset: **random sample with seed 42** (or every Nth point if deterministic selection is preferred).
 2. **Covariance Handling**: Construct a **block-diagonal matrix** (bandwidth = 20) to retain local correlation structure.
 3. Output the subsampled dataset and covariance to `data/processed/subsampled_data.json` and `data/processed/subsampled_cov.npy`.
 4. **Dependency**: Runs after T027-DECIDE.

- [ ] T023-MCMC [US2] **MCMC Execution**: Implement `emcee` runner in `code/inference/mcmc.py`.
 1. Run in **batches** of steps with a sufficient number of walkers.
 2. After each batch, compute the Gelman‑Rubin statistic.
 3. **Stop Condition**: Run until Gelman‑Rubin < 1.01 OR until steps (HARD CAP 5000). If 5000 steps are reached without convergence, stop and flag the result as "unconverged". Do NOT continue running.
 4. **Runtime Enforcement**: Measure elapsed time. If projected total time exceeds 5.5 hours, **automatically trigger T027-GEN (subsampling)** and re-run the inference on the subsampled data. Do NOT fail the task.
 5. Load the dataset from `data/processed/subsampled_data.json` if it exists (triggered by T027-GEN), otherwise use the full harmonized dataset from T015-Z-RESOLVE-COV.
 6. Store chains in `data/results/mcmc_chains.npy`. **Dependency**: Runs after T022 and T027-DECIDE/T027-GEN (if subsampled) or T015-Z-RESOLVE-COV (if full).

- [X] T024 [US2] Implement `dynesty` nested sampler for both Newtonian and Yukawa models in `code/inference/nested.py`.
- [ ] T025-INJECTION [US2] **Injection‑Recovery Test**: Implement `code/robustness/injection.py`.
 1. Generate synthetic data with a known non-zero α and realistic noise using the full covariance matrix.
 2. Run a local inference instance (re‑using T021/T022 logic, independent of T023‑MCMC).
 3. Compute `distance = |injected_alpha – recovered_alpha_median|`.
 4. Determine pass: `SC005_PASS = (injected_alpha within 95% credible interval of recovered samples)`.
 5. Output `data/results/injection_recovery_report.json` with all metrics. **Dependency**: Runs after T021 and T022.
- [ ] T026-THRESHOLD [US2] **Null-Simulation Threshold Definition**: Implement logic in `code/robustness/null_simulation.py` to define the acceptable false-positive rate.
 1. Define the acceptable false-positive rate threshold as a configurable parameter.
 2. Output `data/processed/null_threshold.json` with `threshold` and `rationale`.
 3. **Dependency**: Runs after T021 and T022.
- [ ] T026-NULL-SIM [US2] **Null‑Simulation Test**: Implement `code/robustness/null_simulation.py`.
 1. Generate synthetic data with α = 0 but realistic systematic errors.
 2. Run inference.
 3. Compute `false_positive = (Bayes_factor_K > 3)`.
 4. **Verification Step**: Calculate the p-value of the primary Bayes factor (from T023/T024) against the null distribution generated here.
 5. **Pass Condition**: Use the threshold defined in T026-THRESHOLD to determine `SC002_BASELINE_PASS` (true if false‑positive rate < threshold).
 6. Output `data/results/null_baseline_report.json` with `true_alpha`, `recovered_alpha_median`, `bayes_factor_K`, `false_positive_detected`, `null_distribution` (array), `threshold`, and `SC002_BASELINE_PASS`. **Dependency**: Runs after T021, T022, and T026-THRESHOLD.
 7. **Note**: If performance requires, this task can be parallelized internally, but is listed as a single task for dependency clarity.

**Checkpoint**: User Stories 1 & 2 should now work independently.

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform leave‑one‑experiment‑out cross-validation and systematic uncertainty inflation tests to ensure result stability.

**Independent Test**: Run `code/robustness/cross_val.py` and `code/robustness/uncertainty.py`; verify Bayes factors and credible‑upper‑limit shifts stay < 15% across all iterations.

### Tests for User Story 3 (OPTIONAL)

- [X] T028 [P] [US3] Unit test for leave‑one‑out logic in `tests/unit/test_cross_val.py`.
- [X] T029 [P] [US3] Integration test for uncertainty inflation stability in `tests/integration/test_robustness.py`.

### Implementation for User Story 3

- [ ] T030-LOO [US3] **Leave-One-Out Cross-Validation**: Implement `code/robustness/cross_val.py`.
 1. **Primary method**: If `runs ≥ 3`, iteratively omit one experimental run.
 2. **Re-Harmonization**: For each iteration, **re-run T014/T015 logic** (T030-LOO-REHARMONIZE) to generate a 'subset_harmonized' artifact with a valid covariance matrix for the subset.
 3. **Execution**: Call the `run_inference()` function defined in T023-MCMC for each iteration using the subset artifact.
 4. Store each iteration's credible upper limit for α for later analysis. **Dependency**: Runs after T013-ORCH-ROUTE, T015-Z-RESOLVE-COV, and T023-MCMC.

- [ ] T030-LOO-REHARMONIZE [US3] **Re-Harmonization for LOO**: Implement logic to re-harmonize data for a subset.
 1. Take a subset of the raw data (excluding one run).
 2. Re-run unit conversion and grid alignment (T014 logic) and covariance construction (T015 logic) for this subset.
 3. Output a `subset_harmonized` artifact.
 4. **Dependency**: Runs after T013-PARSE and within the T030-LOO loop.

- [ ] T030-BOOT [US3] **Bootstrap Robustness Fallback**: Implement `code/robustness/bootstrap_robustness.py`.
 1. **Fallback method**: If `runs < 3`, **execute the bootstrap resampling loop** (using the resamples generated in T013-BOOTSTRAP) to perform the robustness analysis. Do NOT skip.
 2. **Iteration**: Implement T030-BOOT-ITERATE to iterate over each resample.
 3. **Execution**: Call the `run_inference()` function for each resample.
 4. Store each iteration's credible upper limit for α for later analysis. **Dependency**: Runs after T013-BOOTSTRAP and T023-MCMC.

- [ ] T030-BOOT-ITERATE [US3] **Bootstrap Iteration**: Implement logic to iterate over bootstrap resamples.
 1. Loop through each resampled dataset generated by T013-BOOTSTRAP.
 2. Feed each dataset into the inference loop (T023-MCMC).
 3. Ensure each iteration's result is stored separately.
 4. **Dependency**: Runs after T013-BOOTSTRAP and T023-MCMC.

- [ ] T002-CONFIG-INFLATION [US3] **Define Inflation Factor Configuration**: Implement logic in `code/config.py` to load or create the systematic uncertainty inflation factor.
 1. Attempt to read the key `inflation_factor` from `data/processed/config.json`.
 2. **Strict Check**: If the key is missing or the file does not exist, **raise a `RuntimeError`** with the message: "Missing inflation_factor in config.json. Please update the configuration file explicitly and increment the project version." Do NOT create a default.
 3. Store the loaded value in `data/processed/config.json` for downstream tasks.
 4. **Dependency**: Runs after T002/T005 (config setup).

- [X] T031 [US3] Implement systematic uncertainty inflation test in `code/robustness/uncertainty.py`. **Parameter**: Read `INFLATION_FACTOR` from `data/processed/config.json` (defined in T002-CONFIG-INFLATION). Apply it multiplicatively to the covariance matrix. **Re-run inference** (T022/T023 logic) with modified inputs. Verify that the Bayes factor changes by a negligible amount; log the result. **Dependency**: Runs after T023-MCMC and T002-CONFIG-INFLATION.

- [X] T033 [US3] Calculate the robustness metrics in `code/robustness/metrics.py`.
 1. **Metric 1**: Calculate the **Coefficient of Variation (CV)** of the 95th percentile credible upper limits: `std / mean`.
 2. **Zero-Check**: If `mean_limit < 1e-10`, set `relative_shift = 0.0` and log a warning "Mean limit near zero; metric set to 0.0".
 3. **Acceptance Criterion**: Verify `CV < 0.15` as defined in SC-003.
 4. **Artifact**: Write `data/results/robustness_metrics.json` containing `cv`, `threshold` (0.15), and `pass` (boolean: `cv < 0.15`).
 5. If `pass` is false, flag the result as "unstable" in the report. **Dependency**: Runs after T030-LOO or T030-BOOT.

- [ ] T040-LITERATURE-COMP [US2/US3] **Literature Comparison Artifact**: Implement `code/robustness/literature_comparison.py`.
 1. Load the credible upper limits on α from `data/results/robustness_metrics.json` or `data/results/bayes_factor.json`.
 2. Format these limits into a table or JSON structure for direct comparison with literature values (e.g., arXiv:2305.06325).
 3. Output `data/results/literature_comparison.json` with fields `alpha_limit`, `lambda_range`, `literature_reference`, and `comparison_notes`.
 4. **Dependency**: Runs after T033 and T026-NULL-SIM.

- [ ] T039-REPORT [US2/US3] **Aggregation**: Aggregate the pass/fail status from T025 (SC‑005) and T026 (SC‑002) into a single summary artifact `data/results/validity_report.json`. Include fields `SC005_PASS`, `SC002_KASS_RAFTERY_PASS`, `SC002_BASELINE_PASS`, and embed the detailed metrics from the injection and null‑simulation reports. **Dependency**: Runs after T025, T026-NULL-SIM, and T033.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Generate visualization plots for posteriors and Bayes factors in `code/utils/plotting.py`.
- [X] T035-A [P] Update `README.md` with project overview, prerequisites, and high‑level run command.
- [X] T035-B [P] Update `docs/quickstart.md` with detailed pipeline execution instructions, data paths, and troubleshooting guide.
- [X] T036 Run full pipeline end‑to‑end validation and verify `state/projects/PROJ-191...yaml` updates correctly.
 1. Verify `data/results/validity_report.json` exists and contains `pass=true`.
 2. Log success or failure.
 3. **Dependency**: Runs after T039.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately. **T001-A-INIT-CODE must run first**.
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
Task: "Implement code/data/validator.py (T013-VALIDATE-IDS)"
Task: "Implement code/data/download.py to fetch arXiv:2106.08611, 2305.06325..."
Task: "Parse raw tarball contents into HarmonizedDataset (T013-PARSE)..."
Task: "Implement unit conversion and grid alignment in code/data/harmonize.py"
Task: "Implement covariance construction (T015-A-COV-CONSTRUCT, T015-B-COV-BAND)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

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