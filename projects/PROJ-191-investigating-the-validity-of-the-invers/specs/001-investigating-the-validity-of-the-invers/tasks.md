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

**Purpose**: Project initialization and basic structure

- [ ] T001 Create the full project directory tree `projects/PROJ-191-investigating-the-validity-of-the-invers/` with sub‑directories (`code/`, `tests/`, `data/`, `docs/`, `code/data/`, `code/models/`, `code/inference/`, `code/robustness/`, `code/utils/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/contract/`, `tests/integration/`) **in a single atomic operation**.
- [X] T002 Initialize a Python 3.11 project and write pinned dependencies to `code/requirements.txt`.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement versioning utility for atomic state updates in `code/utils/versioning.py`.
- [ ] T005 [P] Setup logging infrastructure and configuration management in `code/config.py`.
- [X] T006 Create base data model for `HarmonizedDataset` in `code/data/loaders.py`.
- [ ] T007 [P] Ensure directory structure for `data/raw/`, `data/processed/`, and `data/results/` exists (use robust `mkdir -p` logic).

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Acquisition and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Download raw force‑vs‑separation data from arXiv, convert to SI units, align on a common grid, and construct a full covariance matrix.

**Independent Test**: Execute `code/data/download.py` and `code/data/harmonize.py` against the provided arXiv URLs; verify output is a single CSV/JSON file containing aligned force data, separation distances, and a valid positive‑definite covariance matrix with no missing values in the 10⁻⁵–10⁻⁴ m range.

### Tests for User Story 1 (OPTIONAL)

- [ ] T010 [P] [US1] Unit test for SI unit conversion logic in `tests/unit/test_harmonize.py`.
- [ ] T011 [P] [US1] Contract test for data schema validation in `tests/contract/test_harmonized_dataset.py`.
- [ ] T012 [P] [US1] Integration test for end‑to‑end download and harmonization in `tests/integration/test_data_pipeline.py`.

### Implementation for User Story 1

- [ ] T013-A [US1] Implement `code/data/download.py` to fetch **arXiv:2106.08611 ** supplementary data from
 ` (or the exact CSV URL if provided in the supplement) and store it under `data/raw/2106.08611/`. Verify checksum and record it.
- [ ] T013-B [US1] Implement `code/data/download.py` to fetch **arXiv:2305.06325 ** calibration curves from
 ` (or the exact CSV URL if provided) and store under `data/raw/2305.06325/`. Verify checksum and record it.
- [ ] T013-VAL [US1] After both T013-A and T013-B have completed, invoke the Reference‑Validator Agent to confirm title‑token‑overlap ≥ 0.7 with the primary sources; halt the pipeline with a clear error if validation fails. *(Runs sequentially after the two download tasks.)*
- [ ] T014 [P] [US1] Implement unit conversion (dynes → N, micrometers → m) and grid alignment in `code/data/harmonize.py`.
- [ ] T015 [US1] Implement **full** covariance matrix construction in `code/data/harmonize.py` by parsing statistical uncertainties (`stat_err`) and systematic error budgets (`sys_err` or `systematic` fields) from the source files; if systematic fields are missing, fall back to a conservative scaling of statistical errors.
- [ ] T015-TRANS [US1] Generate a **block‑diagonal/banded** approximation of the covariance for fast likelihood evaluation while **preserving the original full covariance matrix** inside the `HarmonizedDataset` object.
- [ ] T016 [US1] Implement fallback logic: if fewer than three independent runs are detected after downloads, automatically switch to bootstrap resampling of the available runs; otherwise proceed with the normal leave‑one‑out path (handled in T030). *(Runs after T013‑VAL.)*

**Checkpoint**: User Story 1 should now be fully functional and testable independently.

---

## Phase 4: User Story 2 - Bayesian Model Inference (Priority: P2)

**Goal**: Run `emcee` MCMC to estimate posteriors for α and λ, and `dynesty` nested sampling to compute Bayesian evidence for model comparison.

**Independent Test**: Run `code/inference/mcmc.py` and `code/inference/nested.py` on the harmonized dataset; verify output includes posterior samples, Bayes factor, and Gelman‑Rubin < 1.01 within the 6‑hour limit.

### Tests for User Story 2 (OPTIONAL)

- [ ] T018 [P] [US2] Unit test for Yukawa force model implementation in `tests/unit/test_physics.py`.
- [ ] T019 [P] [US2] Unit test for log‑likelihood function with banded covariance in `tests/unit/test_likelihood.py`.
- [ ] T020 [P] [US2] Integration test for MCMC convergence detection in `tests/integration/test_mcmc_diagnostics.py`.
- [ ] T025-TEST [US2] Unit test for injection‑recovery logic (FR‑008) in `tests/unit/test_injection_recovery.py`.
- [ ] T026-TEST [US2] Unit test for null‑simulation baseline logic (FR‑009) in `tests/unit/test_null_simulation.py`.

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement Newtonian and Yukawa‑modified force models in `code/models/physics.py`.
- [ ] T022 [US2] Implement log‑likelihood function using the **banded approximation** produced by T015‑TRANS. **Dependency**: must run after T015‑TRANS completes; the full covariance matrix remains stored in the dataset for reporting.
- [ ] T023 [US2] Implement `emcee` runner that **starts with a minimum of 5 000 steps** and then continues in batches of 1 000 steps **until** the Gelman‑Rubin statistic falls below 1.01. No hard upper bound on total steps is imposed; if the 6‑hour runtime limit is approached, the automatic subsampling logic in T027 will be triggered to reduce the data size before further steps.
- [ ] T024 [US2] Implement `dynesty` nested sampler for both Newtonian and Yukawa models in `code/inference/nested.py`.
- [ ] T025 [US2] Implement injection‑recovery test (FR‑008) to validate that a known non‑zero α injected into simulated data is recovered within the 95 % credible interval.
- [ ] T026 [US2] Implement null‑simulation test (FR‑009) to establish the baseline false‑positive rate for the Bayes factor K.
- [ ] T027 [US2] Add runtime monitoring: **if wall‑clock time exceeds 5 hours**, automatically subsample the dataset by selecting a random [deferred] of points **without replacement**, then re‑sort the selected points by separation to preserve monotonic order. Restart the inference with the reduced dataset to stay within the 6‑hour limit.
- [ ] T038 [US2] After the primary run, compute the Bayes‑factor comparison metric against the null‑simulation baseline from T026 and log the result for SC‑002 reporting.

**Checkpoint**: User Stories 1 & 2 should now work independently.

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform leave‑one‑experiment‑out cross‑validation and systematic uncertainty inflation tests to ensure result stability.

**Independent Test**: Run `code/robustness/cross_val.py` and `code/robustness/uncertainty.py`; verify Bayes factors and credible‑upper‑limit shifts stay < 15 % across all iterations.

### Tests for User Story 3 (OPTIONAL)

- [ ] T028 [P] [US3] Unit test for leave‑one‑out logic in `tests/unit/test_cross_val.py`.
- [ ] T029 [P] [US3] Integration test for uncertainty inflation stability in `tests/integration/test_robustness.py`.

### Implementation for User Story 3

- [ ] T030 [US3] Implement leave‑one‑experiment‑out cross‑validation loop in `code/robustness/cross_val.py`. **Conditional logic**: if the harmonized dataset contains ≥ 3 independent runs, perform true leave‑one‑out; otherwise automatically switch to bootstrap resampling (as flagged by T016). Store each iteration’s α upper‑limit for later analysis.
- [ ] T031 [US3] Implement systematic uncertainty inflation test in `code/robustness/uncertainty.py`.
- [ ] T032 [US3] Implement parallel execution of robustness iterations using `multiprocessing`.
- [ ] T033 [US3] Calculate the **coefficient of variation (CV)** of the credible‑upper‑limits across all robustness iterations, where
 **CV = (standard deviation ÷ mean) × [deferred]**. Log the CV percentage; if **CV > 15 %**, emit a **warning** (not a fatal error) indicating potential instability while allowing the pipeline to continue.
- [ ] T038 [US3] (already defined in Phase 4) compares the primary Bayes factor against the null‑simulation baseline and logs the metric.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Generate visualization plots for posteriors and Bayes factors in `code/utils/plotting.py`.
- [ ] T035-A [P] Update `README.md` with project overview, prerequisites, and high‑level run command.
- [ ] T035-B [P] Update `docs/quickstart.md` with detailed pipeline execution instructions, data paths, and troubleshooting guide.
- [ ] T036 Run full pipeline end‑to‑end validation and verify `state/projects/PROJ-191...yaml` updates correctly.
- [ ] T037 [P] Optimize likelihood evaluation speed (tune banded covariance bandwidth) if total runtime exceeds 2.5 hours.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately. **T001 must run first**.
- **Foundational (Phase 2)**: Depends on Setup completion – BLOCKS all user stories.
- **User Stories (Phase 3‑5)**: All depend on Foundational completion.
 - User Story 1 can start after Phase 2.
 - User Story 2 starts after Phase 2 **and** after the harmonized dataset from US 1 is available.
 - User Story 3 starts after Phase 2 **and** after inference results from US 2 are available.
- **Polish (Phase 6)**: Depends on completion of all desired user stories.

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
Task: "Implement code/data/download.py to fetch arXiv:2106.08611 supplementary data..."
Task: "Implement code/data/download.py to fetch arXiv:2305.06325 calibration curves..."
Task: "Validate downloaded files with Reference‑Validator..."
Task: "Implement unit conversion and grid alignment in code/data/harmonize.py"
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
- Avoid vague tasks, file conflicts, or cross‑story hidden dependencies.
