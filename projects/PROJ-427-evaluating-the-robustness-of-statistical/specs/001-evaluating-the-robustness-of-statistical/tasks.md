---
description: "Task list template for feature implementation"
---

# Tasks: Evaluating the Robustness of Statistical Methods to Common Data Errors

**Input**: Design documents from `/specs/001-evaluate-statistical-robustness/`
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

- [ ] T001 [P] Create project directory structure with exact tree: `data/raw`, `data/corrupted`, `code`, `results`, `tests`. **MUST include creating empty `__init__.py` files in `code/` and `tests/` directories** to ensure Python package recognition. **Note**: The path `data/corrupted` is used for error‑injected data as per Plan.md Project Structure.
- [ ] T002 [P] Initialize Python project with dependencies: pandas, numpy, scipy, statsmodels, matplotlib, seaborn, pyyaml, pytest
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes ground‑truth data generation (FR‑006, FR‑007) and skeleton creation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `contracts/dataset.schema.yaml` defining valid tabular dataset structures
- [ ] T005a [P] Create `contracts/injection.schema.yaml` defining error types (replacement, misclassification, MCAR) and a field `error_rates: list[float]` to be loaded from a configuration file. **MUST explicitly state that the schema validates the structure of a list of floats, not specific values.**
- [ ] T005b [P] [TDD] [FR-002] [Constitution-VI] Write a unit test in `tests/unit/test_schema_validation.py` that loads `contracts/injection.schema.yaml` and a sample `config/error_rates.yaml`, asserting that `error_rates` is a non-empty list of floats. **This test must be written BEFORE implementation tasks T020‑T022 to ensure schema consistency, validating the structure of deferred values without asserting specific rates.**
- [~] T006 [P] Create `contracts/result.schema.yaml` defining output metrics (p-value, CI bounds, effect size, Type I flag)
- [~] T007 [P] Create `code/download.py` skeleton (empty file with imports and main function stub)
- [~] T008 [P] Create `code/inject.py` skeleton (empty file with imports and main function stub)
- [~] T009 [P] Create `code/analyze.py` skeleton (empty file with imports and main function stub)
- [~] T010 [P] Create `code/simulate.py` skeleton (empty file with imports and main function stub)
- [~] T011 [P] Create `code/visualize.py` skeleton (empty file with imports and main function stub)
- [~] T012 [P] Create `code/main.py` skeleton (CLI entry point stub)
- [~] T013a [P] Implement `code/simulate.py` to generate **synthetic datasets** (FR‑006) with known population parameters (mean, variance). Pin global random seeds (via T046) and write all outputs (CSV files, metadata JSON with `ground_truth_type: 'population_parameters'`) to `data/corrupted/synthetic_grid/`.
- [~] T013b [P] Implement `code/simulate.py` to generate **null‑hypothesis datasets** (FR‑007) via label permutation or equal-mean simulation. Pin global random seeds and write outputs (CSV files, metadata JSON with `ground_truth_type: 'permutation'`) to `data/corrupted/null_hypothesis/`.
- [~] T014 Implement validation logic in `code/simulate.py` that checks synthetic and null‑hypothesis outputs against `contracts/result.schema.yaml`, records SHA‑256 checksums, and logs status in `state/simulation_artifacts.yaml`. **Depends: T013a, T013b**.
- [~] T046 [P] Add `code/random_seed.py` that sets deterministic seeds for `random`, `numpy`, and any other libraries used. All scripts must import and call `set_seed()` at start. Include a unit test `tests/unit/test_random_seed.py` confirming that repeated runs with the same seed produce identical injected‑error counts.
- [~] T047 [P] Implement a citation‑verification step using the Reference‑Validator Agent. After any artifact that contains citations is written, run verification and store results in `state/citation_log.yaml`. Fail the task if any citation is `unreachable` or `mismatch`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Benchmarking Data with Controlled Error Injection (Priority: P1) 🎯 MVP

**Goal**: Create a reproducible pipeline that takes clean public datasets and systematically injects specific data errors to establish ground‑truth baselines.

**Independent Test**: Run the injection script on a single small CSV file, verify the output contains exactly the specified percentage of modified rows, and confirm original parameters are recoverable from the unmodified subset.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T015 [P] [US1] Unit test for `code/inject.py` random value replacement logic in `tests/unit/test_injection.py`. **Function name**: `test_replacement_preserves_distribution`. **Assertion**: `assert injected_count == int(total_rows * rate)` and `assert original_mean == unmodified_subset_mean`.
- [ ] T016 [P] [US1] Unit test for `code/inject.py` category misclassification logic in `tests/unit/test_injection.py`. **Function name**: `test_misclassification_shifts_frequencies`. **Assertion**: `assert abs(new_freq - expected_shifted_freq) < tolerance`.
- [ ] T017 [P] [US1] Unit test for `code/inject.py` MCAR missingness logic in `tests/unit/test_injection.py`. **Function name**: `test_mcar_introduces_nans`. **Assertion**: `assert nan_count == int(total_cells * rate)`.

### Implementation for User Story 1

- [ ] T019a [P] Create `config/datasets.yaml` listing **5‑10** UCI dataset URLs with metadata tags (`type: numerical|categorical|mixed`). Verify list length ≥ 5. **MUST use direct HTTPS URLs** (e.g., `) to ensure fetchability on free-tier runners without interactive login.
- [ ] T019b [P] Implement `code/download.py` to iterate over `config/datasets.yaml`, download each CSV to `data/raw/`, verify HTTP success, and preserve original filenames. **MUST handle 404 errors gracefully by logging and skipping, ensuring the pipeline continues.**
- [ ] T019c [P] Extend `code/download.py` (or a new helper) to **clean** each downloaded file: validate against `contracts/dataset.schema.yaml`, coerce column types, replace empty strings with `NaN`, and write cleaned files to `data/raw/cleaned/`.
- [ ] T019d [P] Compute SHA‑256 checksums for each cleaned dataset and record them in `state/dataset_checksums.yaml`.
- [ ] T019e [P] Verify dataset diversity: count numerical‑only, categorical‑only, and mixed datasets; assert **≥ 2** numerical‑only and **≥ 2** categorical‑only datasets. Fail the pipeline otherwise.
- [ ] T019 [P] Orchestrate the full download‑clean‑verify pipeline by invoking T019a‑e in sequence. This task has no parallel tag because it aggregates the subtasks.
- [ ] T018a [P] [US1] Write integration test `tests/integration/test_download.py` that validates `code/download.py` correctly downloads, cleans, checksums, and records diversity. **Depends: T019, T004**.
- [ ] T020 [US1] Implement `code/inject.py` to perform **random value replacement** using a uniform distribution spanning each column's observed min/max. Iterate over `error_rates` loaded from `config/error_rates.yaml`. Output injected files to `data/corrupted/`.
- [ ] T021 [US1] Implement `code/inject.py` to perform **category misclassification** based on observed frequency distributions, iterating over the same error rates. Output to `data/corrupted/`.
- [ ] T022 [US1] Implement `code/inject.py` to introduce **MCAR missingness** (NaN) randomly across rows/columns, iterating over the same error rates. Output to `data/corrupted/`.
- [ ] T023 [US1] Ensure `code/inject.py` logs the specific error rate, error type, and random seed for every generated file in `data/corrupted/`.
- [ ] T024 [US1] Add validation logic to ensure each injected dataset conforms to `contracts/injection.schema.yaml` and that the actual injected proportion matches the declared rate.

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Execute Standard Statistical Tests on Corrupted Data (Priority: P2)

**Goal**: Run standard statistical tests on clean and error‑injected datasets to calculate empirical Type I error rates, CI coverage, and effect‑size bias.

**Independent Test**: Run the analysis script on a simulated dataset with known parameters; verify it outputs correct p‑values, CIs, and effect‑size bias for both clean and corrupted versions without crashing.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US2] Unit test for `code/analyze.py` t‑test execution in `tests/unit/test_analyze.py`. **Function name**: `test_ttest_returns_pvalue_and_ci`. **Assertion**: `0 <= p_value <= 1` and `len(ci) == 2`.
- [ ] T026 [P] [US2] Unit test for regression bias in `tests/unit/test_analyze.py`. **Function name**: `test_regression_calculates_bias`. **Assertion**: `bias == estimated_coef - truth_coef`.
- [ ] T027 [P] [US2] Unit test for chi‑squared in `tests/unit/test_analyze.py`. **Function name**: `test_chi_squared_returns_statistic`. **Assertion**: `statistic >= 0`.

### Implementation for User Story 2

- [ ] T029a [P] Implement `handle_missing_data(df: pd.DataFrame) -> pd.DataFrame` in `code/analyze.py` that performs **listwise deletion** (`df.dropna()`) and returns the reduced dataframe. Also compute and record `N_original` and `N_after_deletion` in a temporary result object. **MUST calculate power_loss as `(N_original - N_after_deletion) / N_original` and write this value to `results/power_loss.json`**. **Depends: T013a, T013b**.
- [ ] T029d [P] Implement `calculate_power_loss()` in `code/analyze.py` that reads `N_original` and `N_after_deletion` from T029a's output, calculates `power_loss = (N_original - N_after_deletion) / N_original`, and writes the result to `results/power_loss.json`. **Depends: T029a**.
- [ ] T028a [US2] Implement `run_ttest()` in `code/analyze.py` to perform a two‑sample t‑test, output p‑value, 95 % CI for the mean difference, and effect size (Cohen's d) **bias** (`estimated_d - true_d`). Save results to `results/raw_metrics/ttest_*.json`.
- [ ] T028b [US2] Implement `run_anova()` in `code/analyze.py` to perform one‑way ANOVA, output F‑statistic, p‑value, and group means CI. Calculate **effect size bias** using Eta-squared (`estimated_eta2 - true_eta2`). Save to `results/raw_metrics/anova_*.json`.
- [ ] T028c [US2] Implement `run_chi_squared()` in `code/analyze.py` to perform chi‑squared test on categorical data, output statistic and p‑value. Calculate **effect size bias** using Cramér's V (`estimated_cramers_v - true_cramers_v`). Save to `results/raw_metrics/chi2_*.json`.
- [ ] T028d [US2] Implement `run_regression()` in `code/analyze.py` to fit linear regression, output coefficient, 95 % CI, **effect‑size bias** (`estimated_coef - true_coef`), and p‑value. Save to `results/raw_metrics/regression_*.json`.
- [ ] T030a [P] Implement `determine_iterations()` in `code/simulate.py` that defines the convergence criterion (Standard Error of the metric < 0.005) and sets a hard cap of a predetermined maximum number of iterations. This logic must be reusable by the simulation loop.
- [ ] T030 [US2] Implement the **simulation loop** in `code/simulate.py` that iterates over each clean dataset, each error type, each `error_rate` from config, and uses the convergence logic from T030a to determine the number of iterations. For each iteration it calls the appropriate injection function (T020‑T022) to produce a corrupted dataset, then invokes the four analysis functions (T028a‑d) on that dataset. Log all parameters (seed, error type, rate) and write intermediate results to `data/corrupted/` and `results/raw_metrics/`. **Depends: T013a, T013b, T030a, T020, T021, T022, T028a, T028b, T028c, T028d**.
- [ ] T029b [P] In `code/analyze.py`, implement CI‑coverage calculation: read true population parameters from `synthetic_metadata.json` (generated by T013a) and compute the proportion of CIs that contain the true value. Record `ci_coverage_rate` per configuration. **Depends: T030**.
- [ ] T029c [P] Implement sample‑mean deviation calculation against true population mean (from `synthetic_metadata.json`). Record `sample_mean_deviation`.
- [ ] T032 [US2] Aggregate results from all iterations to compute **empirical Type I error rates** (proportion of null‑hypothesis rejections) and **CI coverage rates**. Save aggregated metrics to `results/aggregated_metrics.json`. **Depends: T029b**.
- [ ] T032b [US2] Aggregate **effect‑size bias** across regression runs, reporting mean bias and confidence intervals per error type/rate. Save to `results/effect_size_bias.json`.

**Checkpoint**: User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Visualize and Aggregate Degradation Metrics (Priority: P3)

**Goal**: Aggregate results across simulation runs and error rates, generating visualizations (degradation curves) and summary tables.

**Independent Test**: Feed the visualization script a JSON log of simulation results; verify it produces a PNG plot with error rate on the x‑axis and Type I error rate on the y‑axis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for `code/visualize.py` line‑graph generation in `tests/unit/test_visualize.py`. **Function name**: `test_plot_generates_file`. **Assertion**: `assert os.path.exists(output_path)`.
- [ ] T034 [P] [US3] Unit test for summary‑table generation in `tests/unit/test_visualize.py`. **Function name**: `test_table_generates_correct_rows`. **Assertion**: `assert len(rows) == expected_count`.

### Implementation for User Story 3

- [ ] T035 [P] Implement `code/visualize.py` to plot **Error Rate vs. Type I Error** degradation curves for each statistical test. Save PNGs to `results/plots/`.
- [ ] T036 [P] Extend `code/visualize.py` to plot **Error Rate vs. CI Coverage** curves for each test.
- [ ] T037 [US3] Generate comparative summary tables (CSV) showing coverage‑failure rates across tests and error levels. Save to `results/tables/`.
- [ ] T038 [US3] Ensure all plots are saved with descriptive filenames that include dataset name, error type, and metric.
- [ ] T039 [US3] Extend `code/main.py` to compile all results (aggregated metrics, bias reports, plots) into a single `results/summary.json` for downstream consumption.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Update `README.md` and `quickstart.md` to include a **"Running the pipeline"** section. Verify the files pass `markdownlint` with zero errors.
- [ ] T041 [P] Refactor `code/download.py` and `code/inject.py` to use **chunked reading/writing** (e.g., `pandas.read_csv(..., chunksize=100_000)`). Add a CI test using `memory_profiler` that asserts peak memory usage **< 7 GB** when processing the largest dataset.
- [ ] T043 [P] Add explicit edge‑case unit tests in `tests/unit/test_edge_cases.py`:
 - `test_small_sample_size` verifies graceful handling when N < 10 (e.g., skips unstable tests, logs warning).
 - `test_categorical_only_ttest_skip` ensures t‑test is skipped for purely categorical data and records a skip flag.
- [ ] T044 [P] Add a quickstart validation script `bash quickstart.sh` that runs the full pipeline end‑to‑end. The task must assert exit code 0 and confirm that expected artifacts (cleaned datasets, result JSONs, plots) exist in their respective directories.
- [ ] T045 [P] Measure total pipeline execution time (from start of `code/main.py` to completion of all result files) and assert it is **< `RUNNER_TIMEOUT_HOURS`** (read from `config/runtime.yaml` or environment variable, default several hours). Record the runtime in `results/runtime.json`. **Depends: All previous phases**.
- [ ] T048 [P] Add a CI step that runs `pytest` with coverage and fails if overall test coverage drops below **[deferred]**.
- [ ] T049 [P] Ensure `state/projects/PROJ-427-evaluating-the-robustness-of-statistical.yaml` is updated with content hashes after every artifact creation (already part of Constitution VI but made explicit here).
- [ ] T050 [P] Document the complete reproducibility checklist in `docs/reproducibility.md` and add a lint check that the file contains entries for seed setting, dataset checksums, and citation verification.
- [ ] T051 [P] [FR-002] [Constitution-VI] Add a validation script `code/verify_error_rates.py` that reads `results/aggregated_metrics.json` and asserts that results exist for **all** combinations of the three error types and the four specified error rates from the config file. Fail the pipeline if any combination is missing.
- [ ] T052 [P] [FR-006] [FR-007] Add a validation script `code/verify_ground_truth.py` that confirms `data/corrupted/synthetic_grid/` contains datasets with `ground_truth_type: 'population_parameters'` and `data/corrupted/null_hypothesis/` contains datasets with `ground_truth_type: 'permutation'`, ensuring the distinction required for SC-001 and SC-002 is maintained.
- [ ] T053 [P] [US1] [US2] Add a sanity check in `code/main.py` that verifies the **data flow order**: ensure that no analysis task (T028a-d) is invoked on a dataset file that has not been generated by an injection task (T020-22) or a download task (T019b) in the same run session. Log a warning if a missing file is detected.

**Dependencies & Execution Order**

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Stories (Phases 3‑5)** → **Polish (Phase N)**
- All tasks marked `[P]` operate on distinct files and may run in parallel *provided* their dependencies are satisfied.
- Tasks that produce or modify the same file (e.g., T013a/T013b/T014) are sequenced via explicit dependencies rather than parallel tags.