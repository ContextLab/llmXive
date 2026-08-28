# Tasks: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

**Input**: Design documents from `/specs/001-validity-equipartition-granular/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The spec explicitly requests independent tests for energy accuracy (US1), statistical classification (US2), sensitivity sweeps (US3), and regression fit (US4). Tests are INCLUDED.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/`, `artifacts/` at repository root
- Paths shown below assume single project structure as defined in `plan.md`

<!--
 ============================================================================
 IMPORTANT: The tasks below are generated based on the provided spec.md and plan.md.

 Tasks are organized by User Story priority (P1 -> P2 -> P3).
 Each task includes specific file paths and dependencies.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and test data generation

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `artifacts/`, `tests/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, statsmodels, pyyaml, tqdm, pytest)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`
- [ ] T020a [P] [Setup] Define parameters for synthetic test datasets: Maxwell‑Boltzmann (mean=1.0, scale=0.1) and Pareto (shape=2.0). Output to `artifacts/test_params.json`.
- [ ] T020b [P] [Setup] Generate `data/derived/test_thermal_data.csv` and `data/derived/test_nonthermal_data.csv` using parameters from T020a. Files are prefixed with `test_` and are **not** used as primary scientific input.

**Data Source Validation (Simplified)**
- [X] T060 [P] [Foundational] Create `data/config.yaml` template with minimal required fields: `mass`, `radius`, `material_type`, `frequency_bins`. No complex schema validation or automated resolver logic.
- [X] T009 [P] [Foundational] Implement `code/ingestion.py` function `load_and_sample` to accept a `--data-source` CLI argument (local path). **Sampling Algorithm**: If total rows > 1,000,000, default to 1 M rows using `itertools.islice`. Must fail loudly on fetch failure, record random seed, sample indices and row count in `artifacts/sampling_metadata.json`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

- [X] T006 [P] [Foundational] Create `code/config.py` to load material properties (mass, inertia, roughness proxy) and frequency bins from `data/config.yaml`
- [X] T007 [P] [Foundational] Implement `code/main.py` orchestration script with argument parsing for pipeline stages
- [X] T008 [P] [Foundational] Setup `tests/conftest.py` with fixtures for synthetic data generation and random seed pinning
- [X] T010 [P] [Foundational] Implement `code/ingestion.py` function `validate_metadata` to validate required metadata fields (mass, radius, material type) in the dataset header. If missing, FLAG the dataset as 'incomplete' for those fields and proceed with available components (e.g., kinetic only if z-axis is missing). **Constraint**: Do NOT raise a ValueError for missing metadata; instead, set a `metadata_incomplete` boolean column and log a warning. <!-- ATOMIZE: requested -->
- [X] T010a [P] [Foundational] Implement `code/ingestion.py` function `handle_kinetic_only_fallback` to process datasets flagged as 'incomplete' (from T010) by calculating only available energy components (translational, rotational) and setting potential/vibrational energy to NaN or 0 with a warning. **Dependency**: Requires T010.
- [X] T011 [P] [Foundational] Implement `code/ingestion.py` function to handle missing z‑axis data by adding a `pot_incomplete` boolean column to the output dataframe and writing a specific warning log entry (Edge Case: missing z‑axis). **Dependency**: Requires T010.

---

## Phase 3: User Story 1 - Data Ingestion and Energy Component Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest particle tracking data and driving logs to compute $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ for every particle/frame.

**Independent Test**: Run ingestion script on a small synthetic CSV subset; verify calculated energies match manual calculations within a high‑precision tolerance.

**Dependency Order**: T014a → T015 → T016 → T016a → T017 → T018 → T019b → T019. (T029 is independent).

### Tests for User Story 1

- [X] T012 [P] [US1] Unit test for energy formulas in `tests/test_energy.py` (verify $E_{trans}=0.5mv^2$, etc. with known inputs)
- [X] T013 [P] [US1] Integration test for missing frame interpolation in `tests/test_ingestion.py` (verify linear interpolation logic)
- [X] T014 [P] [US1] Integration test for material‑specific mass application in `tests/test_ingestion.py` (verify steel vs. polymer constants)
- [ ] T012a [P] [US1] **Independent Test**: Generate a synthetic dataset with known ground-truth velocities and positions. Calculate expected energies manually and save to `artifacts/manual_baseline.csv`. Run the ingestion pipeline on this data, compare computed energies to `artifacts/manual_baseline.csv`, and output `artifacts/energy_verification_report.json` containing the max absolute error. **Constraint**: If max error > 1e-9, set `repair_needed: true` in the report to trigger a re-run of T018.

### Implementation for User Story 1

- [ ] T014a [US1] Implement `code/ingestion.py` function to ingest and parse driving signal logs (FR‑001). Outputs `data/derived/driving_signals.csv`. **Dependency**: Must be executed before T029.
- [X] T015 [US1] Implement `code/ingestion.py` function to load and sync particle tracking CSVs with driving signal logs (FR‑001). Synchronize by timestamp.
- [X] T016 [US1] Implement `code/ingestion.py` function to handle missing frames via linear interpolation or flagging (Edge Case: missing frames). If a gap exceeds the configured threshold, log a warning and set a `gap_flag` column.
- [X] T016a [US1] **New**: Implement `code/ingestion.py` function `calculate_tracking_failure_rate` to compute the percentage of missing frames per time window. If the rate > 20%, flag the window for exclusion. **Dependency**: Requires T016.
- [X] T017 [US1] Implement `code/ingestion.py` function to compute $v$ and $\omega$ via finite differences from positions/orientations.
- [X] T018b [US1] **Documentation**: Create `docs/methodology_notes.md` with a concise operational definition of $E_{vib}$. **Provisional Formula**: If no verified source is found, use $E_{vib} = m \\cdot \\text{var}(a) \\cdot (\\Delta t)^2$ (where $a$ is acceleration, $\\Delta t$ is time step). This formula yields units of Joules ($kg \\cdot (m/s^2)^2 \\cdot s^2 = kg \\cdot m^2/s^2$). **Citation Rule**: Do NOT write a specific paper title or author in this document unless a verified, real citation (DOI/arXiv) is confirmed by the Reference-Validator. If no verified source exists, explicitly label the formula as "Provisional (Unverified Source)" and proceed. **Constraint**: Must be completed before T018 runs, but T018 uses the formula text directly, not the file.
- [X] T018 [US1] **Prerequisite (Sequential)**: Implement `code/ingestion.py` function to calculate $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ using independent physics formulas. $E_{vib}$ uses the provisional formula from T018b: $E_{vib} = m \\cdot \\text{var}(a) \\cdot (\\Delta t)^2$. Reads `window_size_N` (integer) from `data/config.yaml`. Generates `data/derived/energy_intermediate.csv`. **Constraint**: All energy values must be in Joules. Verify units of $E_{vib}$ are Joules before writing. **Dependency**: Requires T018b text definition.
- [ ] T019b [US1] **Repair Energy Calculation**: Re-implement `code/ingestion.py` energy calculation logic to ensure `data/derived/energy_samples.csv` is generated correctly. **Specific Failure Mode**: Fix the truncated logic in function `compute_energy` to handle all rows and ensure E_vib units are Joules (m * var(a) * dt). **Verification**: Verify E_vib column in `energy_samples.csv` has values > 0 and units match Joules. **Constraint**: This task is **blocking** and **sequential**. It MUST invalidate and overwrite the output of T018 if T018 is marked 'Completed' but the output is incorrect. **Dependency**: Requires T018, T018b.
- [ ] T019 [US1] Output final `energy_samples.csv` to `data/derived/` with columns: `particle_id`, `timestamp`, `E_trans`, `E_rot`, `E_pot`, `E_vib`, `pot_incomplete`. Record the random seed and sampling rule (from T009) in `artifacts/sampling_metadata.json`. Compute SHA‑256 hash of the CSV and store in `artifacts/energy_samples.hash`.

**Chirp Handling (Edge Case: Non-stationary signals)**
- [ ] T029 [US1] Handle non‑stationary (chirped) driving signals: compute instantaneous frequency via `scipy.signal.hilbert`. If `--chirp-handling=exclude` (default), generate `artifacts/chirp_handling_result.csv` with strategy='excluded' and value=mask_index. If `--chirp-handling=bin`, generate `artifacts/chirp_handling_result.csv` with strategy='binned' and value=frequency_bin. **Output**: Unified artifact `artifacts/chirp_handling_result.csv` with columns `timestamp`, `strategy`, `value`. **Dependency**: Consumes output of T014a. **Constraint**: Implements both 'exclude' and 'bin' paths in a single task with a unified schema.

### Additional US1 Tests

- [ ] T021 [P] [US1] Unit test for correct handling of the `test_` prefix (ensures synthetic data are ignored by downstream analysis).
- [ ] T022 [P] [US1] Verify that `artifacts/sampling_metadata.json` correctly records the seed and sampling rule.
- [~] T023b [P] [US1] Explicitly link T021/T022 to `test_thermal_data.csv` and `test_nonthermal_data.csv` to resolve cross-phase ambiguity.

---

## Phase 4: User Story 2 - Statistical Deviation Assessment and Hypothesis Testing (Priority: P2)

**Goal**: Compare observed energy distributions against Maxwell‑Boltzmann prediction using KS and Chi‑squared tests.

**Independent Test**: Run analysis on "thermal" vs "non‑thermal" labeled datasets; verify p‑values and rejection flags match expected ground truth.

**Dependency**: Requires `data/derived/energy_samples.csv` (T019) and `artifacts/chirp_handling_result.csv` (T029, optional).

### Entry Gate

- [~] T054 [US2] Implement `code/main.py` dependency check: verify `data/derived/energy_samples.csv` exists and is valid; if missing, exit with `ERROR: Dependency file data/derived/energy_samples.csv missing. Run US1 first.`

### Implementation for User Story 2

- [X] T025a [US2] **Reconciliation**: Implement `code/stats.py` logic to ensure the primary hypothesis test is the Kolmogorov‑Smirnov test with Lilliefors correction (FR‑003) against the Maxwell‑Boltzmann distribution, overriding any plan summary references to simple ratio comparisons. **Constraint**: The code MUST prioritize FR-003.
- [~] T024 [US2] Implement `code/stats.py` function `bin_energy_data` to read `data/derived/energy_samples.csv`, apply the `chirp_handling_result.csv` (if present) to exclude or bin data, and bin by driving frequency (fixed intervals) and material type. If `chirp_handling_result.csv` is missing, assume no chirp handling is needed and proceed with full data. **Constraint**: Raise `FileNotFoundError` with the exact message if the file is missing or has a `test_` prefix.
- [ ] T025 [US2] Implement Kolmogorov‑Smirnov test with **Lilliefors correction** (as mandated by FR‑003 and Constitution Principle VII) comparing each binned empirical distribution to the theoretical Maxwell‑Boltzmann CDF. The correction MUST account for parameter estimation from the sample. **Constraint**: Lilliefors correction is REQUIRED. Vanilla KS is NOT allowed.
- [ ] T071 [P] [US2] Unit test for KS test logic with Lilliefors correction in `tests/test_stats.py` (verify p‑value calculation against known distribution). **Dependency**: Requires synthetic test data from T020b and implementation T025.
- [ ] T072 [P] [US2] Unit test for Chi‑squared test logic in `tests/test_stats.py` (verify statistic and rejection boolean). **Dependency**: Requires synthetic test data from T020b and implementation T026.
- [ ] T022b [P] [US2] Unit test `test_rejects_test_prefix` in `tests/test_stats.py` to verify that `bin_energy_data` explicitly rejects files with `test_` prefix and logs the rejection reason.
- [ ] T026 [US2] Implement Chi‑squared goodness‑of‑fit test using a standard binning algorithm (e.g., Freedman‑Diaconis or Sturges) selected based on data distribution, integrating the Maxwell‑Boltzmann PDF (scale estimated from sample mean) to obtain expected counts.
- [ ] T027 [US2] Apply Benjamini‑Hochberg (FDR) correction across all frequency‑material bins.
- [ ] T028 [US2] Generate `artifacts/statistical_results.json` containing test type, statistic, raw p‑value, corrected p‑value, rejection flag, and `n_samples` per bin. Also log the effective sample size for each bin (see T057).
- [ ] T023 [P] [US2] Integration test for multi‑frequency aggregation in `tests/test_stats.py` (verify summary table generation).

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis on decision thresholds ($\alpha$) and discrepancy boundaries to ensure robustness.

**Independent Test**: Execute sensitivity sweep on fixed dataset; verify output report lists variation in rejection rates across thresholds.

**Dependency**: Reads `artifacts/statistical_results.json` from T028.

### Tests for User Story 3

- [ ] T030 [P] [US3] Unit test for threshold sweep logic in `tests/test_sensitivity.py` (verify iteration over $\alpha \in \{0.01,0.05,0.10\}$)
- [ ] T031 [P] [US3] Unit test for discrepancy boundary sweep in `tests/test_sensitivity.py` (verify iteration over boundaries $\{1\%,5\%,10\%\}$)

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/sensitivity.py` function `sweep_alpha` to iterate over the specified $\alpha$ values, count rejections per bin, and store results.
- [ ] T033 [US3] Implement `code/sensitivity.py` function `sweep_quasi_thermal_boundary` to iterate over energy‑ratio boundaries $\{1\%,5\%,10\%\}$ and record classification rates.
- [ ] T034 [US3] Generate `artifacts/sensitivity_analysis_report.json` containing threshold vs. rejection‑rate data.
- [ ] T035 [US3] Verify robustness: ensure the rejection decision for the **primary frequency bin** remains identical across $\alpha \in \{0.01,0.05,0.10\}$. Output `artifacts/stability_check.json` with a boolean `stable_across_thresholds` and per‑threshold decisions for the primary bin only.

---

## Phase 6: User Story 4 - Regression Analysis of Deviation Drivers (Priority: P3)

**Goal**: Perform linear regression to relate deviation magnitude to driving frequency and material roughness, and test significance.

**Independent Test**: Run regression on synthetic dataset with known slope/intercept; verify calculated coefficients match within 1 % tolerance.

**Dependency**: Reads `artifacts/statistical_results.json` from T028.

### Tests for User Story 4

- [ ] T036 [P] [US4] Unit test for linear regression fit in `tests/test_regression.py` (verify slope/intercept calculation)
- [ ] T037 [P] [US4] Unit test for t‑test significance in `tests/test_regression.py` (verify p‑value calculation for slope)

### Implementation for User Story 4

- [ ] T038 [US4] Implement `code/regression.py` function `prepare_predictors` to map material type to roughness proxy (from `data/config.yaml`) and assemble predictor matrix (frequency, roughness) and target vector (deviation magnitude from `statistical_results.json`).
- [ ] T039 [US4] Fit ordinary least‑squares linear model, compute slope, intercept, $R^2$, and store in `artifacts/regression_results.json`.
- [ ] T040 [US4] Perform t‑tests on regression coefficients, report p‑values (especially for the slope relating deviation to driving frequency).
- [ ] T041 [US4] Persist results (coefficients, statistics, p‑values) in `artifacts/regression_results.json`.
- [ ] T042 [US4] Verify regression validity: Implement logic to calculate the t-statistic and p-value for the slope coefficient. Output `artifacts/regression_validity_check.json` containing the slope p-value and a boolean `is_significant` (True if p < 0.05). **Constraint**: Do NOT assert a pass/fail; report the metric for SC-005 verification.
- [ ] T042b [US4] Explicitly verify SC-005: Implement a check that confirms `artifacts/regression_validity_check.json` exists and contains the required fields (slope_p_value, is_significant). Output a boolean `sc005_verified` to `artifacts/sc005_check.json`.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates in `README.md` and `docs/`
- [ ] T044 [P] Run `ruff check --fix` on all code files to remove unused imports and fix formatting
- [ ] T045 [P] Refactor loops in `code/ingestion.py` to use vectorized NumPy operations for performance
- [ ] T046 [P] Add unit test `test_large_dataset_memory` in `tests/unit/` to verify memory usage stays within acceptable limits with large inputs
- [ ] T047 [P] Add unit test `test_empty_bin_handling` in `tests/unit/` to verify graceful handling of empty frequency bins
- [ ] T048 [P] Run `quickstart.md` validation to ensure end‑to‑end pipeline execution
- [ ] T050 [P] [Polish] Implement `code/ingestion.py` function `stream_dataset` using `datasets.load_dataset(..., streaming=True)` for chunked processing of large Zenodo/OpenGranular datasets. Integrate with `load_and_sample` (T009) to sample on‑the‑fly when dataset size > 14 GB.
- [ ] T051 [P] [Polish] Extend `artifacts/sampling_metadata.json` with a `sampling_rule` object describing split, chunking, and row count used for any real sample taken.
- [ ] T052 [P] [Polish] Add unit test `test_loader_fail_loudly` verifying that the data loader raises a `RuntimeError` immediately upon fetch failure, with no silent synthetic fallback.
- [ ] T057 [P] [Polish] Extend `code/stats.py` to log and report the effective sample size (`n_samples`) for each frequency‑material bin in `artifacts/statistical_results.json`.
- [ ] T058 [P] [Polish] Add unit test `test_sample_size_reporting` verifying that `n_samples` in `statistical_results.json` matches the actual row count per bin in `energy_samples.csv`.
- [ ] T059 [P] [Polish] Implement `code/regression.py` function to generate a diagnostic plot (`artifacts/regression_diagnostic.png`) showing the fitted line, residuals, and 95 % confidence intervals for deviation vs. frequency.
- [ ] T063 [P] [US3] Implement `code/ingestion.py` function `verify_chirp_segments` to explicitly count the number of frames excluded due to the `chirp_handling_result.csv` (from T029) and log the percentage of total data lost. If >20% of frames in a specific time window are excluded, raise a `DataExclusionWarning`, flag the bin in `artifacts/exclusion_report.json`, and **exclude the window from the final `energy_samples.csv`**. If a frequency bin has < 50 samples after exclusion, flag it as 'insufficient_data' in the report. **Constraint**: Aligns with spec Edge Case thresholds (20% of frames in window).
- [ ] T064 [P] [US2] Implement `code/stats.py` function `calculate_effective_bins` to dynamically adjust Chi-squared bin counts based on the `n_samples` reported in T057, ensuring no bin has an expected count < 5. If adjustment is needed, log the new bin edges to `artifacts/bin_adjustments.json`.
- [ ] T065 [P] [US3] Extend `code/sensitivity.py` to perform a "leave-one-out" cross-validation on the frequency bins to ensure the robustness of the threshold sweep results is not driven by a single outlier bin. Output `artifacts/cv_sensitivity_report.json`.
- [ ] T066 [P] [US4] Implement `code/regression.py` function `check_multicollinearity` to calculate the Variance Inflation Factor (VIF) for the frequency and roughness predictors. If VIF > 5, log a warning in `artifacts/regression_diagnostics.json` and flag the model fit as potentially unstable.
- [ ] T067 [P] [Polish] Create `docs/data_lineage.md` to explicitly document the flow of data from the raw Zenodo/UCI source through `energy_samples.csv`, `chirp_handling_result.csv`, and `statistical_results.json`, including the specific sampling rule and exclusion criteria used in the current run.
- [ ] T068 [P] [Polish] Add a `--dry-run` flag to `code/main.py` that validates all dependencies, file paths, and configuration schemas without executing any heavy computation or data loading, ensuring the environment is ready before a full run.
