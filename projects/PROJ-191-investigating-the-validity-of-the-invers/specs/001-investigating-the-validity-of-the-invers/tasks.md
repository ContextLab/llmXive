# Tasks: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

**Input**: Design documents from `/specs/001-investigating-the-inverse-square-law/`
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

**Purpose**: Project initialization, pre-flight checks, and basic structure

- [ ] T000-VERIFY-ARXIV [P] **Pre-flight Check**: Verify that the arXiv supplementary files for `2106.08611` and `2305.06325` are accessible via `HEAD` requests to their canonical URLs before any download attempts. **URLs**: ` and `. **Rule**: If either URL returns 404 or fails to connect, raise a `RuntimeError` immediately with a clear message indicating the missing assumption. Do NOT proceed to T013 if this check fails. **Dependency**: None.
- [ ] T001-SETUP [P] **Atomic Setup**: Create the entire project directory structure in a single atomic operation. **Paths**: `projects/PROJ-191-investigating-the-validity-of-the-invers/` (root), `projects/PROJ-191-investigating-the-validity-of-the-invers/code/`, `projects/PROJ-191-investigating-the-validity-of-the-invers/tests/`, `projects/PROJ-191-investigating-the-validity-of-the-invers/tests/unit/`, `projects/PROJ-191-investigating-the-validity-of-the-invers/tests/contract/`, `projects/PROJ-191-investigating-the-validity-of-the-invers/tests/integration/`, `projects/PROJ-191-investigating-the-validity-of-the-invers/docs/`, `projects/PROJ-191-investigating-the-validity-of-the-invers/data/raw/`, `projects/PROJ-191-investigating-the-validity-of-the-invers/data/processed/`, `projects/PROJ-191-investigating-the-validity-of-the-invers/data/results/`. **Logic**: Use `os.makedirs(..., exist_ok=True)` for all paths. **Dependency**: None.
- [ ] T002 Initialize a Python 3.11 project and write pinned dependencies to `projects/PROJ-191-investigating-the-validity-of-the-invers/code/requirements.txt`.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement versioning utility for atomic state updates in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/utils/versioning.py`.
- [X] T005 [P] Setup logging infrastructure and configuration management in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/config.py`.
- [ ] T006 [P] Create base data model for `HarmonizedDataset` in `projects/PROJ-191-investigating-the-validity-of-the-invers/code/data/models.py`. **Alignment**: This aligns with the plan's "Project Structure" section which implies data models should reside in a dedicated model file (e.g., `models.py`) and the `data-model.md` phase output.
- [X] T007 [P] Ensure directory structure for `data/raw/`, `data/processed/`, and `data/results/` exists (use robust `mkdir -p` logic).

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Acquisition and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Download raw force‑vs‑separation data from arXiv, convert to SI units, align on a common grid, and construct a full covariance matrix (statistical + systematic).

**Independent Test**: Execute `code/data/download.py` and `code/data/harmonize.py` against the provided arXiv URLs; verify output is a single CSV/JSON file containing aligned force data, separation distances, and a valid positive‑definite **full** covariance matrix with no missing values in the microscopic separation distance range.

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Unit test for SI unit conversion logic in `tests/unit/test_harmonize.py`.
- [X] T011 [P] [US1] Contract test for data schema validation in `tests/contract/test_harmonized_dataset.py`.
- [X] T012 [P] [US1] Integration test for end‑to‑end download and harmonization in `tests/integration/test_data_pipeline.py`.

### Implementation for User Story 1

- [ ] T013-DOWNLOAD [US1] Implement `code/data/download.py` to **fetch** supplementary data from **arXiv:2106.08611** and **arXiv:2305.06325**. **Strategy**: Attempt the canonical arXiv e-print URL (e.g., `) for each ID. **Rule**: If the primary URL fails (404/redirect), raise a `RuntimeError` immediately. Do NOT generate synthetic data. Do NOT guess alternative URLs. **Do NOT** parse the CSV content here; only extract the file. **Parallel Safety**: Use `os.makedirs(..., exist_ok=True)` for each dataset directory independently. Store raw CSV files under `data/raw/2106.08611/` and `data/raw/2305.06325/` respectively. **Checksum Verification**: Verify checksums against a `checksums.txt` file included in the arXiv tarball if present; if not, compute SHA-256 of the downloaded file and store it in `state/` for reproducibility. **Dependency**: T000-VERIFY-ARXIV.
- [ ] T013-VALIDATE [US1] **Validation**: Implement logic in `code/data/validate.py` to **verify** that the fetched arXiv IDs (2106.08611, 2305.06325) match the "Assumptions" section of `spec.md` and that the downloaded files exist and are non-empty. **Dependency**: Must run after T013-DOWNLOAD. **Rule**: If validation fails, raise a `RuntimeError` and halt the pipeline.
- [ ] T013-PARSE [US1] **Parser**: Implement logic in `code/data/parsers.py` to **parse** the raw CSV files extracted by T013-DOWNLOAD: read headers, map columns to force/separation/uncertainty fields, and construct the intermediate `HarmonizedDataset` structure. **Dependency**: Must run after T013-VALIDATE.
- [X] T014 [P] [US1] Implement unit conversion (dynes → N, micrometers → m) and grid alignment in `code/data/harmonize.py`. **Edge Case Logic**: Explicitly implement detection of non-overlapping separation ranges; if detected, **interpolate** missing points or **exclude** non-overlapping regions and **log a warning** as per spec edge cases. **Dependency**: Must run after T013-PARSE.
- [ ] T015 [US1] **Covariance Construction**: Implement logic in `code/data/harmonize.py` to construct the **full** covariance matrix. **Logic**: Propagate statistical uncertainties (`stat_err`) and systematic error budgets (`sys_err` or `systematic`) to build the full N×N matrix. **Constraint**: This task MUST produce a valid full covariance matrix as required by FR-002 and Constitution Principle VI. **Memory Handling**: If the matrix is too large for RAM, implement **chunked construction** (building the matrix in blocks and saving to disk) or **sparse representation** (if off-diagonals are negligible, but explicitly store the full matrix in dense format for the final output) to ensure the artifact is produced. **Do NOT** raise `MemoryError` or fall back to a diagonal approximation. **Output**: Store the result as `data/processed/covariance_matrix.npy`. **Dependency**: Must run after T014.
- [ ] T016 [US1] **Fallback Logic & State Flagging**: Implement logic to count **independent experimental runs** from the harmonized dataset (preserving `run_id` metadata from T014/T015). If the count is < 3, write a runtime state flag `{"use_bootstrap": true, "run_count": <count>}` to `data/processed/state.json`. **Dependency**: Must run after T014/T015 (where run count is known). **Rule**: If the harmonized dataset lacks `run_id` metadata, raise a `RuntimeError` indicating the data structure is insufficient for LOO/Bootstrap selection. **Schema**: The JSON file MUST contain keys `use_bootstrap` (boolean) and `run_count` (integer). **Note**: Do NOT modify `config.py`; use runtime state file. **Dependency**: T014, T015.

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
- [ ] T022 [US2] Implement log‑likelihood function using the covariance matrix from T015 (full). Use Cholesky decomposition for numerical stability. **Dependency**: Must run after T015 (ensures covariance artifact exists).
- [ ] T023 [US2] Implement `emcee` runner: Run **exactly 100 walkers**. **Logic**: Run the sampler for **up to 5000 steps**, but **STOP EARLY** if the Gelman-Rubin statistic drops below 1.01. **Constraint**: If convergence is reached before 5000 steps, stop immediately. If 5000 steps are reached and convergence is not achieved, log a warning and flag the result as "unconverged". **Do NOT** force a minimum of 5000 steps if convergence is met earlier. **Dependency**: Must run after T022 (log-likelihood) and T015 (covariance).
- [X] T024 [US2] Implement `dynesty` nested sampler for both Newtonian and Yukawa models in `code/inference/nested.py`.
- [ ] T025-IMP [P] [US2] **Implementation**: Implement injection‑recovery test (FR‑008) in `code/robustness/injection.py`: **Generate simulated data** with a known non-zero α, **run a local inference instance** (using T021/T022 logic), and assert that the recovered value falls within the credible interval of the posterior. Fail the task if recovery is not achieved. **Dependency**: Must run after T021 and T022.
- [ ] T026-IMP [P] [US2] **Implementation**: Implement null‑simulation test (FR‑009) in `code/robustness/null_simulation.py`: **Generate simulated data** where α=0 is true but systematic errors are present, **run a local inference instance**, and establish the baseline false‑positive rate for the Bayes factor K. **Dependency**: Must run after T021 and T022.

**Checkpoint**: User Stories 1 & 2 should now work independently.

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform leave‑one‑experiment‑out cross-validation and systematic uncertainty inflation tests to ensure result stability.

**Independent Test**: Run `code/robustness/cross_val.py` and `code/robustness/uncertainty.py`; verify Bayes factors and credible‑upper‑limit shifts stay < 15% across all iterations.

### Tests for User Story 3 (OPTIONAL)

- [X] T028 [P] [US3] Unit test for leave‑one‑out logic in `tests/unit/test_cross_val.py`.
- [ ] T029 [P] [US3] Integration test for uncertainty inflation stability in `tests/integration/test_robustness.py`.

### Implementation for User Story 3

- [ ] T030-LOO [US3] **Primary Method**: Implement leave‑one‑experiment‑out cross‑validation loop in `code/robustness/cross_val.py`. **Conditional Logic**: Check `data/processed/state.json` for `use_bootstrap` flag. If `false` (indicating ≥3 independent runs), perform true leave‑one‑out. **Graceful Fallback**: If `state.json` is missing or `use_bootstrap` is not `false`, raise a `RuntimeError` with a clear message: "T016 state file missing or invalid; cannot proceed with LOO. Ensure T016 completed successfully." **Dependency**: Must run after T016, T014, and T015. **Output**: Store each iteration's α upper‑limit (high percentile) for later analysis.
- [ ] T030-BOOTSTRAP [US3] **Fallback Method**: Implement bootstrap resampling in `code/robustness/cross_val.py`. **Conditional Logic**: Check `data/processed/state.json` for `use_bootstrap` flag. If `true` (indicating <3 independent runs), perform bootstrap resampling with `config.BOOTSTRAP_ITERATIONS` (default 1000) iterations with replacement. **Graceful Fallback**: If `state.json` is missing or `use_bootstrap` is not `true`, raise a `RuntimeError` with a clear message: "T016 state file missing or invalid; cannot proceed with Bootstrap. Ensure T016 completed successfully." **Dependency**: Must run after T016, T014, and T015. **Output**: Store each iteration's α upper‑limit (high percentile) for later analysis.
- [ ] T031 [US3] Implement systematic uncertainty inflation test in `code/robustness/uncertainty.py`. **Parameter**: Read the inflation factor from `research.md` or `config.yaml` (key: `config.COVARIANCE_INFLATION_FACTOR`). **Default**: If not set, use a default factor and log a warning that a default was used. Apply it to the covariance matrix. **Verification**: Calculate the variation in the [deferred] credible upper limits across iterations and verify it is < 15% (as per SC-003). Log the result. **Dependency**: Must run after T015 (covariance) and T024 (nested sampling for Bayes factor).
- [ ] T032 [P] [US3] Implement parallel execution of robustness iterations using `multiprocessing`. **Target**: Parallelize the `run_robustness_iteration` function. **Workers**: Use 4 workers or `os.cpu_count()`. **Strategy**: Split the list of experiments (for LOO) or bootstrap indices across workers. **Dependency**: Must run after T030-LOO and T030-BOOTSTRAP.
- [ ] T033 [US3] Calculate the **coefficient of variation (CV)** of the credible‑upper‑limits (95th percentile) across all robustness iterations, where **CV = (standard deviation ÷ mean) × 100**. Log the CV percentage; if **CV > 15%**, write a `data/results/robustness_failure_report.json` and log a CRITICAL warning, but **do not** raise an exception (to allow the pipeline to complete and report the failure). **Dependency**: Must run after T030-LOO and T030-BOOTSTRAP.
- [ ] T038 [US2/US3] **Single Source of Truth**: Compute the Bayes‑factor comparison metric against the null‑simulation baseline from T026-IMP and log the result for SC‑002 reporting. **Dependency**: Must run after T024 (primary Bayes factor), T026-IMP (null baseline), and T033 (robustness CV).

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Generate visualization plots for posteriors and Bayes factors in `code/utils/plotting.py`.
- [ ] T035-A [P] Update `README.md` with project overview, prerequisites, and high‑level run command.
- [ ] T035-B [P] Update `docs/quickstart.md` with detailed pipeline execution instructions, data paths, and troubleshooting guide.
- [ ] T036 Run full pipeline end‑to‑end validation and verify `state/projects/PROJ-191...yaml` updates correctly.
- [ ] T037 [P] Optimize likelihood evaluation speed (tune Cholesky implementation) if total runtime exceeds a pre-established threshold.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately. **T000-VERIFY-ARXIV and T001-SETUP must run first**.
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
Task: "Implement code/data/download.py to fetch arXiv:2106.08611 supplementary data..."
Task: "Validate downloaded files with Reference‑Validator..."
Task: "Parse raw tarball contents into HarmonizedDataset (T013-PARSE)..."
Task: "Implement unit conversion and grid alignment in code/data/harmonize.py"
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
