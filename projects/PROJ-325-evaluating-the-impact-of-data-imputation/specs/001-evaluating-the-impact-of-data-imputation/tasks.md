# Tasks: Evaluating the Impact of Data Imputation on Variance Estimation in Public Surveys

**Input**: Design documents from `/specs/001-evaluating-imputation-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (as per plan.md structure)
- Paths shown below assume single project - adjusted based on plan.md structure

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

- [ ] T001 Create project structure per implementation plan (code/, data/raw, data/processed, tests/)
- [X] T002 Initialize Python project with requirements.txt (pandas, numpy, scipy, scikit-learn, statsmodels, pyyaml, pytest, miceforest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [FR-001] Implement `code/data_ingestion.py` with a configurable, verified URL fetcher for GSS/ACS data that dynamically checks for the presence of `weight`, `psu`, and `strata` columns before proceeding. The system MUST preserve these design variables (weights, strata, PSU) in the output artifact. Output the downloaded and parsed data to `data/raw/gss_2018_subset.csv`.
- [ ] T005 [P] [FR-002b] Implement `code/synthetic_generator.py` to create datasets with known super-population parameters (mean, variance) and controlled missingness (MCAR/MAR), outputting `true_mean`, `true_variance`, `missingness_mechanism`, and the synthetic dataset artifact to `data/processed/synthetic_mar_v1.csv` conforming to `contracts/dataset.schema.yaml`.
- [ ] T006 Create base data contracts in `specs/contracts/` with specific filenames: `dataset.schema.yaml`, `imputation_result.schema.yaml`, `bias_metric.schema.yaml`.
- [X] T007 Implement `code/update_state.py` to generate content hashes for artifacts and update `state/manifest.yaml` under the key `artifact_hashes` (Constitution Principle V).
- [X] T008 [P] Implement `code/config.py` containing the `SeedManager` class/utility to derive distinct per-chain seeds from a base seed (e.g., base_seed + chain_id) to ensure reproducible convergence diagnostics for MICE, ensuring 4 distinct chains do not initialize identically. **Must explicitly implement logic to generate 4 unique seeds for downstream MICE runs.**
- [X] T009 [FR-001] Implement design-based variance estimation utility in `code/variance_estimator.py` (Taylor series linearization) that explicitly detects missing design columns (`psu`, `strata`) and **ABORTS** analysis for that variable if they are missing. Do not proceed with fallback.
- [X] T009b [Edge Case] Implement small-cluster fallback logic in `code/variance_estimator.py` to detect clusters where `psu` size = 1; issue a warning and flag variance as "potentially unstable", but do not abort (distinct from T009's missing column abort).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Data Pipeline & Baseline Variance Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest a complex survey dataset, apply complete-case analysis, and calculate baseline variance estimates using design weights.

**Independent Test**: Run pipeline on a small, known subset of GSS data; verify mean and variance match GSS documentation or manual `survey` package logic.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data ingestion schema in `tests/contract/test_data_ingestion.py`
- [X] T011 [P] [US1] Integration test for complete-case variance calculation in `tests/integration/test_baseline_variance.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement GSS/ACS data loading in `code/data_ingestion.py` handling weights, strata, and PSU, using the dynamic verification logic defined in T004.
- [X] T013 [US1] Implement shared missingness detection utility in `code/data_ingestion.py` to skip variables with >30% missingness and log a warning, reusable across all user stories.
- [X] T014 [US1] Implement Complete-Case analysis logic in `code/imputation_pipeline.py`
- [ ] T015 [US1] Implement design-based variance calculation (Taylor series) for complete-case data in `code/variance_estimator.py`, utilizing the PSU=1 warning logic from T009b (but NOT the abort logic from T009, as T009 is for missing columns).
- [ ] T016 [US1] Output JSON summary with status "success" for US1 in `data/processed/baseline_results.json` with required keys: `mean`, `variance`, `status`, `design_type`.
- [ ] T017 [US1] Add robust error handling for small cluster sizes (PSU=1) with warning and exclusion logic (Integrated into T009b/T015)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synthetic Validation & Imputation Method Implementation (Priority: P2)

**Goal**: Validate imputation methods using synthetic data (known ground truth) and apply to real-world datasets for relative efficiency comparison.

**Independent Test**: Run synthetic generator, apply MICE (m=5) and Single Mean Imputation; verify MICE variance estimates are closer to true variance than Single Imputation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for synthetic data generation in `tests/contract/test_synthetic_generator.py`
- [ ] T019 [P] [US2] Integration test for MICE convergence and bias calculation in `tests/integration/test_imputation_validation.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement Single Mean Imputation as a reusable function in `code/imputation_pipeline.py`
- [ ] T021a [US2] Implement MICE Chain Runner in `code/imputation_pipeline.py`: Explicitly run 4 independent instances of `miceforest.ImputedDataSet` with `max_iter=1000` each, deriving distinct seeds from T008 for each instance. **Consume the `missingness_mechanism` field from T005's output artifact** to log the assumed mechanism (MCAR/MAR) for every imputation run, satisfying Constitution Principle VII. **Discard the initial burn-in iterations of the pooled process** (interpreted as the total burn-in period) before pooling the remaining `m` imputations via Rubin's Rules. The function MUST accept `m` (number of imputations) as a configurable parameter to support sensitivity sweeps. Handle binary outcomes using Predictive Mean Matching (PMM) with `RandomForestRegressor` (integrated logic, no separate task).
- [ ] T021b [US2] [REMOVED] Convergence diagnostics logic integrated into T021a.
- [ ] T021c [US2] Implement Retry Logic in `code/imputation_pipeline.py`: On convergence failure, retry up to 3 times with a new seed (`base_seed + 100*attempt`). If still failing, set `status: warning` and record `error_message`.
- [ ] T022 [US2] **REMOVED**: Logic for convergence check and retry logic is fully integrated into T021a-c.
- [ ] T023 [US2] [FR-003] Implement bias calculation in `code/analysis.py` that: (1) Consumes output artifacts from T005 (synthetic ground truth including `true_variance`), T020 (Single Mean), and T021 (MICE); (2) Validates the artifact schema; (3) Calculates percentage bias; (4) **Computes the ratio (|MICE_bias| / |Single_bias|) ONLY if missingness_mechanism == MAR**; (5) **Logs the result and sets `is_pass_sc002` boolean** based on whether MICE bias magnitude is <= 80% of Single Imputation bias magnitude in synthetic MAR scenarios, **without raising an exception** if the condition is not met. Output to `data/processed/bias_metrics.json`.
- [ ] T024 [US2] [FR-003] Implement relative efficiency calculation against Jackknife/BRR benchmark for real data in `code/analysis.py`.
- [ ] T025 [US2] Generate comparison table (percentage bias) for synthetic and real datasets in `data/processed/imputation_comparison.json`
- [ ] T026 [US2] **REMOVED**: Binary Outcome Handling (PMM) is integrated into T021a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis & Methodological Reporting (Priority: P3)

**Goal**: Perform sensitivity analysis on imputation thresholds and generate a report with multiplicity corrections and associational framing.

**Independent Test**: Verify report contains "Multiplicity Correction" section and "Sensitivity Analysis" table varying a parameter (e.g., m or iterations).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for report schema in `tests/contract/test_report_schema.py`
- [ ] T028 [P] [US3] Integration test for sensitivity analysis sweep in `tests/integration/test_sensitivity_analysis.py`

### Implementation for User Story 3

- [ ] T029 [US3] [FR-004] Implement Holm-Bonferroni correction for p-values in paired t-tests in `code/analysis.py`. (Note: Holm-Bonferroni is stricter than generic Bonferroni and mandated by the Plan).
- [ ] T030 [US3] Implement sensitivity analysis sweep in `code/analysis.py` that: (1) Orchestrates a loop over the reusable functions defined in T020 and T021; (2) **Sweeps the parameter `m` (number of imputations) over a set of concrete values.** (as defined in FR-005, used to resolve SC-003 ambiguity); (3) **Reports the variation in variance bias rate** for each value in the set.
- [ ] T031 [US3] [FR-006] Generate final report in `data/processed/final_report.md` that: (1) **Explicitly inserts the phrase "associational"** to label all findings; (2) **Strictly avoids causal language**; (3) **Includes the mandatory footer: "All findings are associational; no causal claims are made."**; (4) Satisfies FR-006.
- [ ] T032 [US3] Include "Multiplicity Correction" and "Sensitivity Analysis" sections in final report
- [ ] T033 [US3] Implement stability analysis in `code/analysis.py` that: (1) Computes `stability_score = std(bias_rates)` across the sweep defined in T030 (parameter range {5, 10, 20}); (2) Verifies the condition "variation in bias < 5%" as per SC-003; (3) Stores result in `SensitivitySweepResult`.
- [ ] T034 [US3] **REMOVED**: Redundant with T009 and T015.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `README.md` and `docs/`
- [ ] T036 Code cleanup and refactoring in `code/`
- [ ] T037 Performance optimization to ensure runtime < 6 hours on CPU-only runner
- [ ] T038 [P] Additional unit tests in `tests/unit/` for edge cases (MNAR handling, PSU=1 detection)
- [ ] T039 Run quickstart.md validation
- [ ] T040 Final verification of all JSON outputs against contract schemas

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for data ingestion schema in tests/contract/test_data_ingestion.py"
Task: "Integration test for complete-case variance calculation in tests/integration/test_baseline_variance.py"

# Launch all models for User Story 1 together:
Task: "Implement GSS/ACS data loading in code/data_ingestion.py"
Task: "Implement missingness detection and variable filtering in code/data_ingestion.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
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
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence