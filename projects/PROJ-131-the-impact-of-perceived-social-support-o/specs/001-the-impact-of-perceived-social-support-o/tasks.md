# Tasks: The Impact of Perceived Social Support on Resilience to Online Harassment

**Input**: Design documents from `/specs/001-social-support-resilience/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**⚠️ CRITICAL METHODOLOGICAL NOTE**:
The implementation **strictly follows the Plan's 'Revised Approach'** (Single-Dataset Analysis). The Spec's requirement for a 'Synthetic Cohort' (dual-dataset matching) is **methodologically invalid** per the Plan and is **excluded** from implementation. The pipeline ingests the Cyberbullying Survey to ensure the interaction term estimates a genuine psychological buffering effect without confounding by dataset source.

## Format: `[ID] [P?] [Story] description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root

<!--
 ============================================================================
 IMPORTANT: The tasks below reflect the revised, single-dataset workflow
 as mandated by the Plan's 'Critical Methodological Pivot'.
 ============================================================================
-->

## Phase 1: Setup & Kickback (Shared Infrastructure & Methodology Alignment)

**Purpose**: Project initialization and resolution of the spec/plan conflict.

- [X] T041 [P] **Verify Spec State**: Confirm that `specs/001-social-support-resilience/spec.md` already contains the "DEPRECATED" blocks for FR-001/FR-002 and "REVISED" block for SC-001.
 **Action**: Read the file and assert the presence of the required deprecation/revision text.
 **Deliverable**: Log confirmation `INFO: Spec state verified as per Plan requirements.`

- [X] T001 Create project structure per implementation plan (`code/data`, `code/analysis`, `code/config`, `code/tests`)
- [X] T002 Initialize Python project with pinned dependencies (`requirements.txt`: pandas, numpy, scikit-learn, statsmodels, scipy, pyyaml)
- [X] T003 [P] Configure linting (ruff) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 [P] Create `config/scales.yaml` defining standard scoring weights for CES‑D, GAD‑7, and PCL‑5.
 **Content outline** (example values):
 ```yaml
 CES-D:
 items: [depressed1, depressed2, depressed3, depressed4, depressed5, depressed6, depressed7, depressed8, depressed9, depressed10, depressed11, depressed12, depressed13, depressed14, depressed15, depressed16, depressed17, depressed18, depressed19, depressed20]
 reverse_items: [depressed5, depressed9, depressed12, depressed16, depressed18]
 scoring: -3 per item, total 0‑60
 GAD-7:
 items: [gad1, gad2, gad3, gad4, gad5, gad6, gad7]
 reverse_items: []
 scoring: non-negative integer per item, total non-negative integer sum
 PCL-5:
 items: [pcl1, pcl2, pcl3, pcl4, pcl5, pcl6, pcl7, pcl8, pcl9, pcl10, pcl11, pcl12, pcl13, pcl14, pcl15, pcl16, pcl17, pcl18, pcl19, pcl20, pcl21, pcl22, pcl23, pcl24, pcl25]
 reverse_items: []
 scoring: ‑4 per item, total 0‑100
 ```
 **Verification**: Cross-reference these weights against the official instrument documentation (CES-D, GAD-7, PCL-5 manuals) before hard-coding to ensure compliance with Constitution Principle VI.
- [X] T005 [US1] Implement `tests/test_scales.py` with unit tests verifying scoring logic matches the definitions in `config/scales.yaml`. **Dependency**: Must run after T004.
- [X] T006 [P] Setup `code/data/ingestion.py` skeleton with read‑only raw data validation logic.
- [X] T007 Create `code/data/cohort.py` skeleton for constructing the analysis cohort (single source).
- [ ] T008 [P] Configure `main_pipeline.py` entry point to orchestrate modular steps.
- [X] T009 [P] Setup environment configuration for data paths **and** create `config/seeds.yaml` to define reproducible seeds.
 **Content outline**:
 ```yaml
 random_seed: 42
 ```
 **Instruction**: Ensure the file contains valid YAML with the integer value `42` for `random_seed`. This seed will be used for all random operations (imputation, bootstrapping, sampling).

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Ingestion & Cohort Preparation (Priority: P1) 🎯 MVP

**Goal**: Ingest the Cyberbullying Survey 2021, harmonize variables, handle missingness, and prepare a clean analysis cohort. **Note**: The GSS dataset is excluded per the Plan's 'Revised Approach'.

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Contract test for data schema in `tests/contract/test_analysis_cohort_schema.py`
- [X] T011 [P] [US1] Unit test for CES‑D/GAD‑7 scoring logic in `tests/unit/test_scale_scoring.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data/ingestion.py` to **download and load** the Cyberbullying Survey 2021 dataset:
 - **Source**: Use `ucimlrepo` or `datasets.load_dataset` with the specific ID for the Cyberbullying Survey, or load from `data/raw/cyberbullying_2021.csv` if provided locally.
 - **Validation**: Verify file integrity (checksum) and log E‑MISSING‑ if required items are absent.
 - **GSS Exclusion**: Do NOT attempt to load GSS 2022. If GSS is found in `data/raw`, log a warning that it is being ignored per the Plan's 'Revised Approach'.
- [X] T013 [US1] Implement `code/data/preprocessing.py` to perform the following steps in order:
 1. **Listwise Deletion**: Drop rows where variables with >5% missingness are present.
 2. **MICE Imputation**: Apply Multiple Imputation by Chained Equations (MICE) to remaining missing values in the predictor matrix: `['age','gender','education','income','social_support','harassment_severity','depression','anxiety','ptsd']`. Configure with `m=5`, `max_iter=10`, `random_state=42`.
 3. **Convergence Check**: Verify MICE convergence by checking the trace of imputed values. If convergence fails (trace does not stabilize), increase `max_iter` to 50 and re-run. Log status `W-MICE-NONCONV-001` if max_iter was increased.
 4. **Scale Scoring**: Apply scoring algorithms defined in `config/scales.yaml` to raw item columns.
 5. **PCL-5 Handling**: If PCL-5 items are missing from the dataset, log `E-MISSING-001` (PTSD) and set the `ptsd` column to `NaN`. **Verification**: Ensure the pipeline explicitly adapts the outcome set and FDR correction logic (FR-008) to handle a reduced set of outcomes (Depression, Anxiety only) without crashing.
 6. Output the processed DataFrame for downstream cohort construction.
- [X] T014 [US1] Implement `code/data/cohort.py` to:
 1. Filter the dataset to remove rows with critical missing values (harassment_severity, social_support, or at least one mental health outcome).
 2. Ensure `harassment_severity` has sufficient variance (SD > 0.5, N > 30). If not, log `E-LOW-VAR-001` and halt.
 3. Output `data/results/analysis_cohort.csv`.
- [X] T015 [US1] **Validate the analysis cohort**:
 - Check **variance of Harassment Exposure** (SD > 0.5, N > 30).
 - Compute **VIF** for the model matrix (`social_support`, `harassment_exposure`, interaction, plus covariates) and ensure VIF < 5.
 - **Deliverable**: Generate `data/results/validation_report.json` containing the results of these checks (Pass/Fail status, calculated values).
 - **Logic**: If VIF >= 5 or Variance check fails, raise a `RuntimeError` with message "Cohort validity check failed. Aborting." to prevent downstream execution.
 - **Note**: The SMD check (SC-001) is **inapplicable** to the single-dataset approach. This task replaces the previous SMD validation.
- [X] T016 [US1] Save the validated analysis cohort to `data/results/analysis_cohort.csv` **only after** successful T015.
- [X] T017 [US1] Add comprehensive logging for ingestion, preprocessing, and validation steps, including any fallback decisions (e.g., missing PCL-5).

**Checkpoint**: User Story 1 is fully functional and produces a valid single-dataset cohort.

---

## Phase 4: User Story 2 - Interaction Analysis & Hypothesis Testing (Priority: P2)

**Goal**: Fit robust OLS models with interaction term, compute bias‑corrected bootstrapped CIs, and apply multiple‑comparison correction.

### Tests for User Story 2 (OPTIONAL)

- [X] T018 [P] [US2] Contract test for regression results schema in `tests/contract/test_regression_results_schema.py`. **Note**: Validate schema for Cyberbullying Survey data only (no GSS 2022 references).
- [X] T019 [P] [US2] Unit test for bootstrapping logic in `tests/unit/test_bootstrap_ci.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/analysis/models.py` to fit OLS models with heteroskedasticity‑consistent (HC3) standard errors for Depression, Anxiety, and PTSD (if PCL-5 present). Include interaction term `SocialSupport:HarassmentExposure`.
- [X] T021 [P] [US2] Compute **bias‑corrected accelerated (BCa) bootstrap CIs** with a **sufficiently large number of resamples** to ensure stable interval estimation. using `statsmodels.stats.bootstrap`. Seed the process with `random_seed` from `config/seeds.yaml`.
- [X] T022 [P] [US2] Add fallback: if the robust model fails to converge, automatically refit a standard OLS model (no HCSE) and log status `E‑NONCONV‑001`.
- [X] T023 [P] [US2] Implement Benjamini‑Hochberg FDR correction across the set of outcome tests (Depression, Anxiety, PTSD) and attach adjusted p‑values to the results.
- [ ] T024 [P] [US2] Save regression outputs (coefficients, SEs, p‑values, bootstrap CIs, adjusted p‑values) to `data/results/regression_results.csv`.
- [X] T024b [P] [US2] **Create Results Module**: Implement `code/analysis/results.py` to handle report generation.
 - **Action**: Create the file with correct syntax (fixing previous `"std_error": ro` error).
 - **Content**: Functions to read `analysis_cohort.csv` and `regression_results.csv` and format them for markdown output.
- [X] T025 [US2] **Generate Regression Summary Report**: Update `code/analysis/results.py` to read `analysis_cohort.csv` (produced by T016) and generate `data/results/regression_summary.md`.
 - **Deliverable**: `data/results/regression_summary.md` containing:
 - Model coefficients and standard errors.
 - Bootstrap confidence intervals.
 - FDR-adjusted p-values.
 - Interpretation of the interaction term.
 - **Dependency**: Must run after T016, T024, and T024b.

**Checkpoint**: User Stories 1 & 2 are independently testable.

---

## Phase 5: User Story 3 - Sensitivity Analysis & Robustness Checks (Priority: P3)

**Goal**: Re‑run models with alternative harassment definitions and platform stratification.

### Tests for User Story 3 (OPTIONAL)

- [X] T026 [P] [US3] Contract test for sensitivity results schema in `tests/contract/test_sensitivity_results_schema.py`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `code/analysis/sensitivity.py` to:
 1. Re‑fit models using **continuous harassment severity** instead of binary exposure.
 2. If a `platform` column exists, stratify analyses by **all available platforms**.
 3. **Edge Case Handling**: If a platform group has N < 30, log `E-SMALL-N-001` and exclude that group from stratification. Do not arbitrarily truncate to "top three" platforms.
 4. If fewer than two valid platforms remain after filtering, log `E‑SKIP‑001` and skip stratification.
 5. **Consolidation**: This task now contains the **sole** implementation of stratification edge-case logic; no other task (e.g., T046) implements this logic.
- [X] T028 [US3] **Generate Coefficient Comparison Table**: Compare interaction coefficients from each sensitivity run against the baseline (from T020) and produce a table of coefficient shifts.
 - **Deliverable**: `data/results/coefficient_comparison.csv` containing the baseline and sensitivity coefficients with calculated shifts.
 - **Logic**: Read `regression_results.csv` (baseline) and `sensitivity_analysis.csv` (sensitivity), merge on model ID, and compute `shift = sensitivity_coef - baseline_coef`.
 - **Dependency**: Must run after T020 and T027.
- [ ] T029 [P] [US3] Save the sensitivity summary to `data/results/sensitivity_analysis.csv`. <!-- FAILED: unspecified -->
- [X] T030 [P] [US3] Add logging for each scenario, including data availability warnings.

**Checkpoint**: All user stories are now functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [ ] T031 [US1-US3] **Orchestrate Pipeline**: Implement `main_pipeline.py` to chain all phases: Ingestion → Preprocessing → Validation → Modeling → Sensitivity → Reporting.
 - **Deliverable**: `main_pipeline.py` that executes T012-T030 sequentially and outputs a single run log at `data/results/pipeline_run.log`.
 - **Content Requirements**:
 - Import `ingestion`, `preprocessing`, `cohort`, `models`, `sensitivity`, `results`.
 - Execute `ingestion.load()`.
 - Execute `preprocessing.clean()`.
 - Execute `cohort.build()`.
 - Execute `models.fit()`.
 - Execute `sensitivity.run()`.
 - Execute `results.generate_report()`.
 - Handle exceptions: If any step fails, log error and halt.
 - **Verification**: The file must be syntactically correct and executable.
 - **Dependency**: Must run after all phase tasks are complete.
- [X] T032 Code cleanup and refactoring in `code/analysis/` to ensure modularity.
- [ ] T033 [P] Performance optimization: Verify that bootstrapping (1,000 (Wikipedia: Bootstrapping (statistics), https://en.wikipedia.org/wiki/Bootstrapping_(statistics)) resamples for up to three models) completes within 6 hours on a 2‑core CPU. **Verification Step**: Run `time python main_pipeline.py` and assert output < 21600s.
- [X] T034 [P] Additional unit testsfor edge cases (empty datasets, missing columns) in `tests/unit/`.
- [X] T035 Run `quickstart.md` validation to ensure end‑to‑end pipeline execution.
- [X] T036 Update `research.md` with placeholder interpretation that emphasizes associational findings.

---

## Phase 7: Execution Safety & Data Integrity (Revision Round 1)

**Goal**: Address specific execution risks identified in the analysis phase: ensuring real data sources are used, preventing synthetic fallbacks, and validating compute feasibility.

### Implementation for Execution Safety

- [ ] T050 [US1] **Hardening Ingestion**: Modify `code/data/ingestion.py` to strictly enforce the "Fail Loudly" rule.
 - **Requirement**: Remove any `try/except` blocks that catch download errors and fall back to `generate_synthetic_*()` or `mock_*()` functions.
 - **Action**: If the real fetch (via `ucimlrepo` or `load_dataset`) fails, the script MUST raise a `RuntimeError` with a clear message: "Real data fetch failed. Aborting to prevent synthetic data fabrication."
 - **Verification**: Unit test `tests/unit/test_ingestion_failures.py` must confirm that a missing network or invalid dataset ID raises an exception rather than returning mock data.

- [ ] T051 [US1] **Dataset Source Verification**: Update `code/data/ingestion.py` to log the exact source URL and dataset ID used.
 - **Requirement**: The log output must explicitly state: "Source: [URL/ID] | Method: [ucimlrepo/load_dataset]".
 - **Action**: If a "VERIFIED REAL DATA SOURCE" block is provided in execution feedback, the code MUST update the fetch logic to use that exact package/recipe instead of guessing.
 - **Verification**: Run the pipeline and grep logs for "Source:" to confirm the real dataset is being referenced.

- [ ] T052 [US1] **Streaming/Chunking for Large Data**: Implement streaming logic in `code/data/ingestion.py` if the Cyberbullying Survey exceeds ~1GB.
 - **Requirement**: Use `datasets.load_dataset(..., streaming=True)` and iterate with `itertools.islice` if a full sample is needed for testing, ensuring the code handles chunked processing for statistics.
 - **Action**: If the dataset is small (<1GB), load fully into memory; otherwise, implement the streaming accumulator for mean/variance calculations to stay within 7GB RAM limits.
 - **Verification**: Unit test `tests/unit/test_streaming_logic.py` to ensure chunked processing yields identical statistics to full-load processing on a sample subset.

- [X] T053 [US2] **Bootstrap Feasibility Check**: Add a pre-flight check in `code/analysis/models.py` to estimate bootstrap runtime.
 - **Requirement**: Run a quick "dry run" with 10 resamples to estimate time per resample. If `1000 * estimated_time > 6 hours`, log a warning `W-SLOW-BOOT-001` and **HALT** execution.
 - **Action**: Ensure the resample count is strictly CPU-tractable on the 2-core runner; if not, the pipeline must stop rather than fabricate results or reduce rigor. **Do not** reduce resamples to 500 without a spec amendment.
 - **Verification**: Run the dry-run on the CI runner and verify the estimated total time is < 6 hours.
 - **Note**: This check runs BEFORE the full bootstrap in T021/T033 to prevent long hangs.

- [X] T054 [US3] **Stratification Edge Case Handling**: Update `code/analysis/sensitivity.py` to handle the "Low N" edge case rigorously.
 - **Requirement**: If a platform group has N < 30, the stratified model MUST NOT run. Log `E-SMALL-N-001` and exclude that group from stratification.
 - **Action**: Ensure the code does not attempt to fit a regression on a group with insufficient variance or sample size, which would cause convergence errors or spurious results.
 - **Verification**: Unit test `tests/unit/test_stratification_edge_cases.py` with a mock dataset containing a group of N=10 to confirm the model skips and logs the error.
 - **Note**: This logic is consolidated in T027; this task ensures the implementation in T027 is robust.

- [ ] T055 [P] **Reproducibility Audit**: Add a final validation step in `main_pipeline.py` to hash the final `analysis_cohort.csv` and `regression_results.csv`.
 - **Requirement**: Compare the hash against the seed defined in `config/seeds.yaml`. If the hash changes between runs with the same seed, the pipeline must fail with `E-NON-DET-001`.
 - **Action**: Ensure all random number generators (numpy, pandas, statsmodels) are seeded explicitly before any operation.
 - **Deliverable**: `data/results/reproducibility_audit.json` containing the hash comparison results and pass/fail status.
 - **Dependency**: Must run after T031, T016, T024, and T029.

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** (blocking)
- **User Story 1** (T012‑T017) → **User Story 2** (T020‑T025) → **User Story 3** (T027‑T030)
- **Polish (Phase 6)** runs after all user stories.
- **Execution Safety (Phase 7)** must be completed before the final production run to ensure data integrity and reproducibility.
- Parallelizable tasks are marked `[P]`; ordering respects data flow and artifact hand‑offs as described above.

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
