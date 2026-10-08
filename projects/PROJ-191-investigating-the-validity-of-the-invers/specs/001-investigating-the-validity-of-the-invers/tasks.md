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

- [ ] T001-A-INIT-CODE Create the code directory tree at the repository root: `projects/PROJ-191-investigating-the-validity-of-the-invers/code/` using the shell command `mkdir -p projects/PROJ-191-investigating-the-validity-of-the-invers/code`.

- [ ] T001-B-INIT-DATA Create the data directory tree: `projects/PROJ-191-investigating-the-validity-of-the-invers/data/` including `data/raw/`, `data/processed/`, `data/results/` using the shell command `mkdir -p projects/PROJ-191-investigating-the-validity-of-the-invers/data/{raw,processed,results}`.

- [ ] T001-C-INIT-TEST Create the test directory tree: `projects/PROJ-191-investigating-the-validity-of-the-invers/tests/` including `tests/unit/`, `tests/contract/`, `tests/integration/` using the shell command `mkdir -p projects/PROJ-191-investigating-the-validity-of-the-invers/tests/{unit,contract,integration}`.

- [ ] T002-A [P] Initialize a Python project virtual environment.
 1. Run `python -m venv venv` in the root directory `projects/PROJ-191-investigating-the-validity-of-the-invers/`.
 2. Verify `venv/bin/activate` exists.
 3. **Constraint**: Ensure the virtual environment is using a compatible Python version. If not, create a new venv with `python3.11 -m venv venv`.

- [ ] T002-B [P] Install pinned dependencies.
 1. Create `requirements.txt` at `projects/PROJ-191-investigating-the-validity-of-the-invers/code/requirements.txt` (as per plan structure) with the following EXACT pinned versions:
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
 psutil==5.9.8
 ```
 2. **Execute**: Activate the environment (`source venv/bin/activate`) and run `pip install -r projects/PROJ-191-investigating-the-validity-of-the-invers/code/requirements.txt`.

- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `.ruff.toml` and adding `[tool.black]` / `[tool.ruff]` sections to `pyproject.toml` in the `projects/PROJ-191-investigating-the-validity-of-the-invers/code/` directory.

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

**Sequential Flow**: T013-VALIDATE-IDS → T013-DATA → T013-PARSE → T014 → T027-DECIDE → T015-COV-CONSTRUCT

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
 5. **Dependency**: Runs after T013-VALIDATE-IDS.

- [ ] T013-PARSE [US1] **Parser**: Implement logic in `code/data/parsers.py` to parse the raw CSV files extracted by T013‑DATA.
 1. Read headers, map columns to force, separation, and uncertainty fields.
 2. **Calibration Extraction**: Search for files matching regex patterns `calibration.*csv` or `calib.*dat` within the tarball. Extract force-vs-separation data or calibration parameters.
 3. Construct intermediate `HarmonizedDataset` objects.
 4. **Dependency**: Runs after T013-DATA.

- [ ] T014 [P] [US1] Implement unit conversion (dynes → N, micrometers → m) and grid alignment in `code/data/harmonize.py`. **Edge‑case handling**: Detect non‑overlapping separation ranges; interpolate missing points or exclude non‑overlapping regions and log a warning as required by the spec.

- [ ] T027-DECIDE [US1] **Memory Strategy Decision**: Implement logic in `code/data/config.py` to enforce `numpy.memmap` for the covariance matrix.
 1. **Check**: Read the raw data size and check available RAM using `psutil.virtual_memory().available`.
 2. **Condition**: **Always** set `use_memmap = True` for the covariance matrix construction to guarantee compliance with the plan's rejection of subsampling and strict memory limits. Do NOT trigger subsampling under any condition.
 3. **Constraint**: **Do NOT trigger subsampling**. The plan explicitly rejects subsampling. The system MUST use `numpy.memmap` to preserve statistical power.
 4. **Output**: `data/processed/data_config.json` with `use_memmap = True` and `needs_subsample = False`.
 5. **Dependency**: Runs after T014.

- [ ] T013-ORCH-ROUTE [US1] **Orchestration & Routing**: Implement `code/data/orchestrator.py` to route the pipeline based on run count.
 1. Read `data/processed/run_count.json`.
 2. **If** `count >= 3`: Execute T014 (harmonize) and T015 (covariance) logic.
 3. **If** `count < 3`: Set `use_lopbo = True` in `data/processed/orchestration_status.json`. (Plan mandates Leave-One-Block-Out, NOT bootstrap).
 4. This task acts as the control flow bridge, ensuring the correct path is taken.
 5. **Output**: Write `data/processed/orchestration_status.json` with the chosen path and `use_lopbo` flag.
 6. **Dependency**: Runs after T013-DATA and T013-PARSE.
 7. **Note**: Do NOT invoke any bootstrap logic. T013-BOOTSTRAP does not exist.

- [ ] T015-COV-CONSTRUCT [US1] **Covariance Construction (Full Diagonal with Memmap)**: Implement construction of the full N x N diagonal covariance matrix in `code/data/harmonize.py`.
 1. Combine statistical uncertainties and systematic error budgets into a diagonal matrix.
 2. **CRITICAL**: Use `numpy.memmap` to construct and store this matrix. Do NOT load the full N x N matrix into RAM. The file must be `data/processed/covariance_matrix_full.npy` (memmap format).
 3. This satisfies the "full matrix" requirement (off-diagonals = 0) while acknowledging the lack of off-diagonal data in the source and preserving statistical power.
 4. Verify the matrix is positive‑definite using `scipy.linalg.cholesky` (on a small sample or via Cholesky on the diagonal vector if full check is too heavy).
 5. **Dependency**: Runs after T014 and T027-DECIDE.

- [ ] T015-COV-LOG [US1] **Covariance Documentation**: Implement `code/data/covariance_log.py` to document the approximation.
 1. Read `data/processed/covariance_sensitivity_report.json` (if exists) or log directly.
 2. Write `data/processed/covariance_resolution_log.json` explicitly stating: "A true full covariance matrix with off-diagonal terms is impossible due to missing source data. The 'full' matrix constructed (T015-COV-CONSTRUCT) uses zero off-diagonals, which is the scientifically valid approximation for uncorrelated data. Memmap is used to preserve statistical power without exceeding RAM."
 3. **Dependency**: Runs after T015-COV-CONSTRUCT.

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
- [ ] T022 [P] [US2] Implement log‑likelihood function using the **full diagonal covariance matrix** from T015-COV-CONSTRUCT. Employ Cholesky decomposition for numerical stability. **Constraint**: Use `numpy.memmap` to load the covariance matrix to avoid RAM overflow. **Dependency**: Runs after T015-COV-CONSTRUCT and T021.

- [ ] T023-MCMC [US2] **MCMC Execution**: Implement `emcee` runner in `code/inference/mcmc.py`.
 1. Run in **batches** of steps with a sufficient number of a cohort of walkers.
 2. **Constraint**: Run for a **minimum of 5000 steps**. If Gelman-Rubin < 1.01 after 5000 steps, stop. If Gelman-Rubin >= 1.01, continue running until convergence (no hard step cap, only until convergence is achieved). **Do NOT stop early if convergence is reached before 5000 steps.**
 3. **Diagnostics**: Compute Gelman-Rubin after each batch and log it.
 4. **Runtime Enforcement**: Measure elapsed time. Calculate `projected_time = (current_steps / elapsed_time) * max_steps`. If `projected_time > 5.5 hours`, **log a warning but DO NOT subsample**. The plan mandates `numpy.memmap` to handle large data, not subsampling.
 5. Load the dataset from `data/processed/covariance_matrix_full.npy` (T015-COV-CONSTRUCT) using **`numpy.memmap`**. **Do NOT load from `subsampled_data.json` as that artifact is forbidden.**
 6. Store chains in `data/results/mcmc_chains.npy`. **Dependency**: Runs after T022 and T015-COV-CONSTRUCT.

- [X] T024 [US2] Implement `dynesty` nested sampler for both Newtonian and Yukawa models in `code/inference/nested.py`.
- [ ] T025-INJECTION [US2] **Injection‑Recovery Test**: Implement `code/robustness/injection.py`.
 1. Generate synthetic data with a known non-zero α and realistic noise using the full covariance matrix from the loaded dataset.
 2. Run a local inference instance (re‑using T021/T022 logic, independent of T023‑MCMC).
 3. Compute `distance = |injected_alpha – recovered_alpha_median|`.
 4. Determine pass: `SC005_PASS = (injected_alpha within 95% credible interval of recovered samples)`.
 5. Output `data/results/injection_recovery_report.json` with all metrics. **Dependency**: Runs after T021 and T022.
- [ ] T026-NULL-SIM [US2] **Null‑Simulation Test**: Implement `code/robustness/null_simulation.py`.
 1. Generate synthetic data with α = 0 but realistic systematic errors using the full covariance matrix.
 2. Run inference multiple times to generate a null distribution of Bayes factors.
 3. **Verification Step**: Calculate the false positive rate as the proportion of null runs where Bayes_factor_K > 3.
 4. **Output**: Output `data/results/null_baseline_report.json` with `true_alpha`, `recovered_alpha_median`, `bayes_factor_K`, `false_positive_rate` (calculated from null distribution), `null_distribution` (array of Bayes factors from multiple runs), `p_value` (calculated against the observed primary Bayes factor). **Do NOT hardcode a pass/fail threshold here.** The pass/fail logic is in T039.
 5. **Dependency**: Runs after T021, T022.
 6. **Note**: If performance requires, this task can be parallelized internally, but is listed as a single task for dependency clarity.

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
 2. **Re-Harmonization**: For each iteration, **call `harmonize.harmonize_subset()`** with the excluded run ID to generate a 'subset_harmonized' artifact with a valid covariance matrix for the subset.
 3. **Memory Constraint**: **Use `numpy.memmap` for all intermediate subset harmonizations** to avoid loading full N x N covariance matrices into RAM.
 4. **Execution**: Call the `run_inference()` function defined in `code/inference/mcmc.py` (T021/T022) for each iteration using the subset artifact.
 5. Store each iteration's credible upper limit for α for later analysis.
 6. **Fallback**: If `runs < 3`, **read `data/processed/orchestration_status.json`**. If `use_lopbo` is True, **execute the Leave-One-Block-Out (LOPBO) loop** on the largest dataset. **Do NOT use bootstrap resampling.**
 7. **Dependency**: Runs after T013-ORCH-ROUTE, T015-COV-CONSTRUCT, and T022 (inference module).

- [ ] T030-LOO-REHARMONIZE [US3] **Re-Harmonization for LOO**: Implement logic to re-harmonize data for a subset.
 1. Take a subset of the raw data (excluding one run).
 2. Re-run unit conversion and grid alignment (T014 logic) and covariance construction (T015 logic) for this subset.
 3. Output a `subset_harmonized` artifact at `data/processed/loo_subset_{id}_harmonized.json`.
 4. **Dependency**: Runs after T013-PARSE and within the T030-LOO loop.

- [X] T002-CONFIG-INFLATION [US3] **Define Inflation Factor Configuration**: Implement logic in `code/config.py` to load or create the systematic uncertainty inflation factor.
 1. Attempt to read the key `inflation_factor` from `data/processed/config.json`.
 2. **Default**: If the key is missing or the file does not exist, **set a default value of 2.0** (as per the plan's '[deferred]' intent) and log a warning. Do NOT raise a RuntimeError.
 3. Store the loaded value in `data/processed/config.json` for downstream tasks.
 4. **Dependency**: Runs after T002/T005 (config setup).

- [X] T031 [US3] Implement systematic uncertainty inflation test in `code/robustness/uncertainty.py`. **Parameter**: Read `INFLATION_FACTOR` from `data/processed/config.json` (defined in T002-CONFIG-INFLATION). Apply it multiplicatively to the covariance matrix. **Re-run inference** (T022/T023 logic) with modified inputs. Verify that the Bayes factor changes by a negligible amount; log the result. **Dependency**: Runs after T023-MCMC and T002-CONFIG-INFLATION.

- [X] T033 [US3] Calculate the robustness metrics in `code/robustness/metrics.py`.
 1. **Metric 1**: Calculate the **Coefficient of Variation (CV)** of the 95th percentile credible upper limits: `std / mean`.
 2. **Zero-Check**: If `mean_limit < 1e-10`, set `relative_shift = 0.0` and log a warning "Mean limit near zero; metric set to 0.0".
 3. **Acceptance Criterion**: Verify `CV < 0.15` as defined in SC-003.
 4. **Artifact**: Write `data/results/robustness_metrics.json` containing `cv`, `threshold` (0.15), and `pass` (boolean: `cv < 0.15`).
 5. If `pass` is false, flag the result as "unstable" in the report. **Dependency**: Runs after T030-LOO.

- [ ] T040-LITERATURE-COMP [US2/US3] **Literature Comparison Artifact**: Implement `code/robustness/literature_comparison.py`.
 1. Load the credible upper limits on α from `data/results/robustness_metrics.json` or `data/results/bayes_factor.json`.
 2. Format these limits into a table or JSON structure for direct comparison with literature values (e.g., arXiv:2305.06325).
 3. Output `data/results/literature_comparison.json` with fields `alpha_limit`, `lambda_range`, `literature_reference`, and `comparison_notes`.
 4. **Dependency**: Runs after T033 and T026-NULL-SIM.

- [ ] T039-REPORT [US2/US3] **Aggregation**: Aggregate the pass/fail status from T025 (SC‑005) and T026 (SC‑002) into a single summary artifact `data/results/validity_report.json`. Include fields `SC005_PASS`, `SC002_KASS_RAFTERY_PASS`, `SC002_BASELINE_PASS` (calculated by comparing primary Bayes factor to the `null_distribution` from T026), and embed the detailed metrics from the injection and null‑simulation reports. **Dependency**: Runs after T025, T026-NULL-SIM, and T033.

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
Task: "Implement covariance construction (T015-COV-CONSTRUCT)"
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
- **Important**: The plan explicitly rejects "bootstrap resampling" and "banded covariance" matrices. Only "Leave-One-Block-Out" (LOPBO) and "full diagonal covariance" are authorized.