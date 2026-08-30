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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (code/, data/raw, data/processed, tests/)
- [X] T002 Initialize Python project with requirements.txt (pandas, numpy, scipy, scikit-learn, statsmodels, pyyaml, pytest, miceforest)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools (Create `.ruff.toml` and `pyproject.toml` with rules)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006a [P] **Create Dataset Schema**: Create `specs/001-evaluating-the-impact-of-data-imputation/contracts/dataset.schema.yaml` defining fields for `true_mean`, `true_variance`, `missingness_mechanism`, and data types. **Specific Instruction**: Must be a valid JSON Schema/YAML file.
- [ ] T006b [P] **Create Imputation Result Schema**: Create `specs/001-evaluating-the-impact-of-data-imputation/contracts/imputation_result.schema.yaml` defining fields for `method`, `variance_estimate`, `standard_error`, and `convergence_diagnostics`.
- [ ] T006c [P] **Create Bias Metric Schema**: Create `specs/001-evaluating-the-impact-of-data-imputation/contracts/bias_metric.schema.yaml` defining fields for `method`, `bias_percentage`, `is_pass_sc002`, and `reference_value`.
- [ ] T004 [FR-001] **Implement Data Fetcher**: Implement `code/data/loader.py` with a configurable, verified URL fetcher for GSS/ACS data. The system MUST: (1) Use the specific URL `https://gss.norc.org/documents/stata/GSS2018.dta` (or verified CSV equivalent); (2) **Check for a verified local cache** at `data/raw/cache/GSS2018.dta` if the URL fails; (3) Dynamically check for the presence of `weight`, `psu`, and `strata` columns; (4) **ABORT** analysis for any variable if these columns are missing, logging the specific missing column to `state/manifest.yaml` (satisfying Principle V); (5) Preserve design variables in the output artifact. Output the downloaded and parsed data to `data/raw/gss_2018_subset.csv`. <!-- FAILED: unspecified -->
- [ ] T004b [FR-001] **Execute Data Fetch**: Run the fetcher defined in T004 to download the GSS 2018 subset from `https://gss.norc.org/documents/stata/GSS2018.dta` (or verified CSV equivalent). **Logic**: (1) Attempt URL download; (2) If failed, check `data/raw/cache/` for a verified checksummed copy; (3) If cache exists and valid, use it; (4) If both fail, raise `DataFetchError` (no synthetic fallback). Save to `data/raw/gss_2018_subset.csv`, compute SHA-256 checksum, and record in `state/manifest.yaml`. **Depends on T004**.
- [ ] T005 [FR-002b] **Implement Synthetic Data Generator**: Implement `code/data/synthetic.py` to create datasets with known super-population parameters. **Parameters**: Read `n`, `true_mean`, `true_variance`, `missing_rate`, `mechanism` from `code/config.py` (e.g., `base_seed=42`). The generator MUST: (1) Output the synthetic dataset artifact to `data/processed/synthetic_mar_v1.csv` conforming to `contracts/dataset.schema.yaml`; (2) Output a metadata JSON file `data/processed/synthetic_mar_v1_meta.json` containing `true_mean`, `true_variance`, and `missingness_mechanism` fields as the **source of truth** for bias calculation (SC-001, FR-003). **Depends on T006a**.
- [ ] T005b [FR-002b] **Execute Synthetic Generator**: Run the generator defined in T005 to produce `data/processed/synthetic_mar_v1.csv` and `data/processed/synthetic_mar_v1_meta.json`. Verify the outputs against the schema and record checksums in `state/manifest.yaml`. **Depends on T005**.
- [X] T007 Implement `code/update_state.py` to generate content hashes for artifacts and update `state/manifest.yaml` under the key `artifact_hashes` (Constitution Principle V).
- [X] T008 [P] Implement `code/config.py` containing the `SeedManager` class/utility to derive distinct per-chain seeds from a base seed (e.g., base_seed + chain_id) to ensure reproducible convergence diagnostics for MICE, ensuring 4 distinct chains do not initialize identically. **Must explicitly implement logic to generate 4 unique seeds for downstream MICE runs.**
- [X] T009 [FR-001] **Design-Based Variance Estimator (Missing Columns)**: Implement design-based variance estimation utility in `code/variance/design.py` (Taylor series linearization) that explicitly detects missing design columns (`psu`, `strata`) and **ABORTS** analysis for that variable if they are missing. **Explicit Requirement**: Log the specific missing column (e.g., "missing psu") to `state/manifest.yaml` before aborting to satisfy Principle V. Do not proceed with fallback.
- [X] T009b [FR-001] [Edge Case] **Small-Cluster Fallback (PSU=1)**: Implement small-cluster fallback logic in `code/variance/design.py` to detect clusters where `psu` size = 1; issue a warning and flag variance as "potentially unstable", but do not abort (distinct from T009's missing column abort).
- [X] T009c [FR-003] Implement Jackknife variance estimator in `code/variance/design.py` to calculate robust design-based variance for real-world datasets. This task is required to satisfy FR-003 and SC-002 (relative efficiency calculation) where Taylor Series is insufficient for the benchmark.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Data Pipeline & Baseline Variance Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest a complex survey dataset, apply complete-case analysis, and calculate baseline variance estimates using design weights.

**Independent Test**: Run pipeline on a small, known subset of GSS data; verify mean and variance match GSS documentation or manual `survey` package logic.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US1] Contract test for data ingestion schema in `tests/contract/test_data_ingestion.py`
- [X] T015 [P] [US1] Integration test for complete-case variance calculation in `tests/integration/test_baseline_variance.py`

### Implementation for User Story 1

- [X] T016 [US1] Implement GSS/ACS data loading in `code/data/loader.py` handling weights, strata, and PSU, using the dynamic verification logic defined in T004. **Explicit Verification**: Must verify `status` is "success" before writing `baseline_results.json`; if design columns are missing, write `status: "failed"` and abort variable processing.
- [X] T017 [US1] Implement shared missingness detection utility in `code/data/loader.py` to skip variables with >30% missingness and log a warning, reusable across all user stories.
- [X] T018 [US1] Implement Complete-Case analysis logic in `code/imputation_pipeline.py`
- [X] T019 [US1] Implement design-based variance calculation (Taylor series) for complete-case data in `code/variance/design.py`, utilizing the PSU=1 warning logic from T009b and the missing column abort logic from T009. **Explicitly distinguish**: if `psu`/`strata` are missing, abort (T009); if `psu` size=1, warn (T009b).
- [ ] T020 [US1] **Output JSON Summary**: Write a Python script (part of `code/main.py` or `code/imputation/run_all.py`) to serialize the baseline results dict to `data/processed/baseline_results.json`. The JSON MUST contain keys `mean`, `variance`, `status` (value must be "success"), and `design_type`. **Verification**: Run `jq '.status == "success" and.mean != null and.variance != null' data/processed/baseline_results.json` to confirm the file exists and is valid. If calculation fails, write `status: "failed"`. **Depends on T019**.
- [ ] T021 [US1] [Edge Case] **Write PSU=1 Warnings**: Implement logic to write detected PSU=1 warnings to `data/processed/psu1_warnings.json`. This task uses the detection logic from T009b to trigger a simplified variance estimator (or exclusion) and records the warning/exclusion evidence in `data/processed/psu1_warnings.json`. **Schema Requirements**: The JSON MUST contain keys `variable`, `psu_count`, and `action_taken`. **Verification**: Run `jq '.variable and.psu_count != null and (.action_taken == "warn" or.action_taken == "exclude")' data/processed/psu1_warnings.json` to confirm.
- [X] T021b [FR-002b] **Log Imputation Mechanism Transparency**: Implement logging in `code/imputation/mice.py` to explicitly record the `missingness_mechanism` (MCAR/MAR) assumed for each imputation run in `data/processed/imputation_logs.json`. This satisfies Constitution Principle VII and the plan's T021 reference. **Schema**: Log entry must include `variable`, `mechanism`, `chain_id`, and `timestamp`. **Depends on T005b**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synthetic Validation & Imputation Method Implementation (Priority: P2)

**Goal**: Validate imputation methods using synthetic data (known ground truth) and apply to real-world datasets for relative efficiency comparison.

**Independent Test**: Run synthetic generator, apply MICE (m=5) and Single Mean Imputation; verify MICE variance estimates are closer to true variance than Single Imputation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US2] Contract test for synthetic data generation in `tests/contract/test_synthetic_generator.py`. **Specific Test**: Implement `test_synthetic_produces_known_variance()` which generates data and asserts that the calculated variance matches `true_variance` within a small tolerance.
- [X] T023 [P] [US2] Integration test for MICE convergence and bias calculation in `tests/integration/test_imputation_validation.py`. **Specific Test**: Implement `test_mice_bias_vs_single()` which runs MICE and Single Mean, calculates bias against ground truth, and asserts `abs(mice_bias) <= 0.8 * abs(single_bias)`.

### Implementation for User Story 2

- [X] T024 [US2] Implement Single Mean Imputation as a reusable function in `code/imputation_pipeline.py`
- [X] T025a [US2] **MICE Chain Runner**: Implement `run_mice_chains()` in `code/imputation_pipeline.py`. Explicitly run 4 independent instances of `miceforest.ImputedDataSet` with `max_iter=1000` each, deriving distinct seeds from T008 for each instance. **Consume the `missingness_mechanism` field from T005b's output artifact** to log the assumed mechanism (MCAR/MAR) for every imputation run, satisfying Constitution Principle VII. **Explicitly discard the initial iterations per chain as burn-in** before pooling. **(Depends on T005b)**.
- [X] T025b [US2] **Burn-in & Pooling**: Implement `pool_imputations()` in `code/imputation_pipeline.py`. **Explicitly discard the initial 500 iterations per chain** before pooling the remaining `m` imputations via Rubin's Rules. The function MUST accept `m` (number of imputations) as a configurable parameter to support sensitivity sweeps.
- [X] T025c [US2] **Binary Outcome Handling**: Implement `configure_pmm()` in `code/imputation_pipeline.py`. For binary target variables, configure `miceforest` with `predictive_mean_matching=True` and `RandomForestRegressor`.
- [X] T026 [US2] [FR-002] **Implement Retry Logic**: Implement Retry Logic in `code/imputation_pipeline.py`: On convergence failure (R-hat >= 1.05), retry up to 3 times with a new seed (`base_seed + 100*attempt`). Log the specific seed and attempt number to `data/processed/imputation_logs.json`. If still failing, set `status: warning` and record `error_message`. **Depends on T008**.
- [X] T011 [US2] **Implement MICE Orchestration**: Implement `code/imputation/run_all.py` to orchestrate the full imputation pipeline. **Logic**: (1) Load data from T004b/T005b; (2) Route to Single Mean (T024) or MICE (T025); (3) Handle binary outcomes (T026); (4) Trigger retry logic (T026) on failure; (5) Output pooled results. **Depends on T008, T024, T025, T026**. **(Moved from Phase 2 to Phase 4)**.
- [X] T027 [US2] [FR-003] **Bias Calculation**: Implement bias calculation in `code/metrics/bias.py` that: (1) Consumes output artifacts from `data/processed/synthetic_mar_v1_meta.json` (T005b), `data/processed/single_mean_results.json` (T024), and `data/processed/mice_results.json` (T025); (2) Validates the artifact schema; (3) Calculates percentage bias for **both MCAR and MAR** mechanisms; (4) **Computes the ratio (|MICE_bias| / |Single_bias|)**; (5) **Logs the result and sets `is_pass_sc002` boolean** based on whether MICE bias magnitude is <= 80% of Single Imputation bias magnitude. Output to `data/processed/bias_metrics.json`. **(Depends on T005b, T024, T025c, T026)**.
- [X] T028 [US2] [FR-003] Implement relative efficiency calculation against Jackknife/BRR benchmark for real data in `code/metrics/bias.py`. (Depends on T009c).
- [X] T012 [US2] **Implement Bias Calculation Logic**: Implement the core bias calculation logic in `code/metrics/bias.py` that consumes artifacts from T005b (Synthetic Meta) and T009c (Jackknife). **Logic**: (1) For synthetic data, calculate `(est_var - true_var) / true_var`; (2) For real data, calculate `abs(est_var - jackknife_var) / jackknife_var`. **Depends on T005b, T009c**. **(Restored to Phase 4)**. <!-- FAILED: unspecified -->
- [X] T029 [US2] Generate comparison table (percentage bias) for synthetic and real datasets in `data/processed/imputation_comparison.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis & Methodological Reporting (Priority: P3)

**Goal**: Perform sensitivity analysis on imputation thresholds and generate a report with multiplicity corrections and associational framing.

**Independent Test**: Verify report contains "Multiplicity Correction" section and "Sensitivity Analysis" table varying a parameter (e.g., m or iterations).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Contract test for report schema in `tests/contract/test_report_schema.py`. **Specific Test**: Implement `test_report_contains_associational_footer()` which asserts the presence of the mandatory footer string.
- [X] T031 [P] [US3] Integration test for sensitivity analysis sweep in `tests/integration/test_sensitivity_analysis.py`. **Specific Test**: Implement `test_sweep_produces_stable_bias()` which runs the sweep and asserts that the standard deviation of bias rates across {5, 10, 20} is < 5%.

### Implementation for User Story 3

- [X] T032 [US3] [FR-004] **Multiplicity Correction**: Implement Holm-Bonferroni correction for p-values in paired t-tests in `code/metrics/bias.py`. **Explicitly state** that Holm-Bonferroni satisfies FR-004's "Bonferroni or similar" requirement. Apply correction to the specific pairwise tests: CC vs Single, Single vs MICE, CC vs MICE. Store raw and adjusted p-values in `BiasMetric`.
- [ ] T033a [US3] [FR-005] **Sweep Orchestrator**: Implement the sweep orchestrator in `code/main.py` that defines the parameter loop for `m` over a range of small integer values. **(Depends on T024, T025)**.
- [ ] T033b [US3] [FR-005] **Sweep Execution**: Implement the execution logic that runs the full pipeline (T024/T025) for each `m` value on both real and synthetic datasets. **(Depends on T033a)**.
- [ ] T033c [US3] [FR-005] **Artifact Generation**: Implement the logic to generate `data/processed/sensitivity_sweep_results.json` and the "Sensitivity Analysis" table in the final report. **(Depends on T033b)**.
- [ ] T035 [US3] [FR-005] **Stability Analysis**: Implement stability analysis in `code/metrics/bias.py` that: (1) Computes `stability_score = std(bias_rates)` across the sweep defined in T033 (parameter range {10, 20, and a lower bound}); (2) Verifies the condition "variation in bias < 5%" as per SC-003; (3) Stores result in `SensitivitySweepResult`. **(Depends on T033)**.
- [X] T034 [US3] [FR-006] Generate final report in `data/processed/final_report.md` that: (1) **Explicitly inserts the phrase "associational"** to label all findings; (2) **Strictly avoids causal language**; (3) **Includes the mandatory footer: "All findings are associational; no causal claims are made."**; (4) **Includes "Multiplicity Correction" (from T032) and "Sensitivity Analysis" (from T033) sections**; (5) Satisfies FR-006. **(Depends on T032, T033, T035)**.
- [ ] T013 [P] **Implement Main Entry Point**: Implement `code/main.py` to orchestrate the full pipeline. **Logic**: (1) Load config; (2) Run T004b (if needed); (3) Run T005b (if needed); (4) Run T011 (imputation); (5) Run T027 (bias); (6) Run T033 (sensitivity); (7) Generate report (T034). **Depends on T011, T027, T033**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] **Documentation**: Update `README.md` with usage examples, installation instructions, and a "How to Run" section. Update `docs/` with API references for `code/imputation_pipeline.py`.
- [ ] T037 **Code Cleanup**: Refactor `code/imputation_pipeline.py` to reduce cyclomatic complexity to < 10. Remove unused imports and dead code.
- [X] T038 [P] **Unit Tests**: Add unit tests in `tests/unit/` for edge cases: `test_mnar_handling.py` (MNAR detection), `test_psu1_detection.py` (PSU=1 warning trigger).
- [X] T039 Run `quickstart.md` validation to ensure all commands execute successfully.
- [X] T040 Final verification of all JSON outputs against contract schemas using `code/validate_schemas.py`.
- [ ] T041 [P] **Enforce Subset Limit**: Update `code/data/loader.py` to explicitly enforce the subset limit of ≤ 50,000 rows as per Plan.md Technical Context, ensuring the dataset fits within RAM limits without requiring streaming infrastructure.
- [ ] T042 [P] **Strict Data Loader**: Refactor `code/data/loader.py` to remove any `try/except` blocks that fall back to synthetic data. If the real fetch from the verified URL fails, the script MUST raise a `DataFetchError` and halt execution. **Preserve the dynamic check for presence of weight, psu, strata logic from T004** during this refactoring. This prevents silent fabrication and ensures the execution stage re-tries with a verified source.
- [ ] T043 [US2] **Explicit Sample Definition**: Update `code/data/synthetic.py` to explicitly state the sample size and sampling rule (e.g., `itertools.islice` first N rows) if a subset is used. Add a metadata field `sampling_rule` to `synthetic_mar_v1_meta.json` to document the exact method used, ensuring transparency.
- [ ] T044 [US2] **Convergence Retry Verification**: Update `code/imputation_pipeline.py` (T026) to log the specific seed used for each retry attempt in `data/processed/imputation_logs.json`. This provides an audit trail for the "3 attempts" rule and ensures the retry logic is deterministic and traceable.
- [X] T045 [US3] **Report Footer Verification**: Add a pre-commit hook or CI step that parses `data/processed/final_report.md` and asserts the presence of the exact string "All findings are associational; no causal claims are made." to prevent accidental omission of the mandatory disclaimer.
- [X] T046 [P] **Runtime Monitoring**: Implement a runtime monitoring script in `code/monitor_runtime.py` that asserts `runtime ≤ 6 hours` (the standard time limit of the GitHub Actions free-tier runner as per SC-004) and logs the result to `state/manifest.yaml`.
- [ ] T048 [US2] **MNAR Sensitivity Check**: Implement a specific test case in `tests/integration/test_imputation_validation.py` that injects a known MNAR mechanism into the synthetic data and verifies that the system correctly flags the bias as "potentially directional" rather than calculating a precise bias percentage, adhering to the assumption that MNAR results are sensitivity checks only.

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
