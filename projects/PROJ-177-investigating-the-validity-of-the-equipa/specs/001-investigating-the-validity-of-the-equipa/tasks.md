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

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `artifacts/`, `tests/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, statsmodels, pyyaml, tqdm, pytest)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/checksum_raw_data.py` to generate SHA-256 hashes for `data/raw/` and write the checksums to `state/checksums.yaml` (Constitution Principle III)
- [X] T005 [P] Implement `code/hash_artifacts.py` to generate content hashes for `artifacts/` and update `state/checksums.yaml` (Constitution Principle V)
- [X] T006 Create `code/config.py` to load material properties (mass, inertia, roughness proxy) and frequency bins from `data/config.yaml`
- [X] T007 Implement `code/main.py` orchestration script with argument parsing for pipeline stages
- [X] T008 Setup `tests/conftest.py` with fixtures for synthetic data generation and random seed pinning

**Data Source Validation (Foundational)**
- [X] T060 [P] [Foundational] Define the schema for `data/config.yaml` to include a `data_source` section with fields: `source_type` (zenodo|uciml|local), `source_id` (string), `expected_columns` (list), and `checksum` (SHA-256). This task creates the empty/placeholder schema file. **Constraint**: Do NOT populate `source_id` with a placeholder ID in this task.
- [X] T061 [Foundational] Validate that `source_type` and `source_id` are present and non‑empty in `data/config.yaml` BEFORE T062 writes to it. If missing, exit with a clear error. **Dependency**: Requires T060. **Note**: T061 runs BEFORE T062 to prevent writing invalid data.
- [X] T062 [Foundational] Automated Data Source Resolution: Implement `code/ingestion.py` function `fetch_and_validate_source` that (1) reads `DATA_SOURCE_ID` environment variable, (2) falls back to a `VERIFIED_REAL_DATA_SOURCE` block if provided in the execution feedback, (3) raises a clear, descriptive error if neither is present. **Outcome**: Fully automated, reproducible data‑source configuration without hardcoded placeholders. **Dependency**: Requires T061 to pass.
- [X] T063b [P] [Foundational] Implement `code/verify_foundational.py` to run checksums and schema validation on the outputs of T060-T062. If validation fails, raise a `RuntimeError` preventing US1 execution. **Dependency**: Requires T061.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

- [X] T009 [P] [Foundational] Implement `code/ingestion.py` function `load_and_sample` to accept a generic `--data-source` CLI argument (local path or generic dataset ID). **Sampling Algorithm**: Read `SAMPLE_SIZE` from `data/config.yaml`. If not set **and** total rows > 1,000,000 **or** estimated file size > 14 GB, default to 1 M rows using `itertools.islice`. Must fail loudly on fetch failure, record random seed, sample indices and row count in `artifacts/sampling_metadata.json`. **Dependency**: Requires successful validation from T061.
- [X] T010 [P] [Foundational] Implement `code/ingestion.py` function `validate_metadata` to validate required metadata fields (mass, radius, material type) in the dataset header. If missing, FLAG the dataset as 'incomplete' for those fields and proceed with available components (e.g., kinetic only if z-axis is missing). **Constraint**: Do NOT raise a ValueError for missing metadata; instead, set a `metadata_incomplete` boolean column and log a warning.
- [X] T010a [P] [Foundational] Implement `code/ingestion.py` function `handle_kinetic_only_fallback` to process datasets flagged as 'incomplete' (from T010) by calculating only available energy components (translational, rotational) and setting potential/vibrational energy to NaN or 0 with a warning. **Dependency**: Requires T010.
- [X] T011 [P] [Foundational] Implement `code/ingestion.py` function to handle missing z‑axis data by adding a `pot_incomplete` boolean column to the output dataframe and writing a specific warning log entry (Edge Case: missing z‑axis). **Dependency**: Requires T010.

---

## Phase 3: User Story 1 - Data Ingestion and Energy Component Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest particle tracking data and driving logs to compute $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ for every particle/frame.

**Independent Test**: Run ingestion script on a small synthetic CSV subset; verify calculated energies match manual calculations within a high‑precision tolerance.

**Dependency Order**: T014a → T015 → T016 → T017 → T018. (T020a/T020b are independent test data generation).

### Tests for User Story 1

- [X] T012 [P] [US1] Unit test for energy formulas in `tests/test_energy.py` (verify $E_{trans}=0.5mv^2$, etc. with known inputs)
- [X] T013 [P] [US1] Integration test for missing frame interpolation in `tests/test_ingestion.py` (verify linear interpolation logic)
- [X] T014 [P] [US1] Integration test for material‑specific mass application in `tests/test_ingestion.py` (verify steel vs. polymer constants)

### Implementation for User Story 1

- [X] T014a [US1] Implement `code/ingestion.py` function to ingest and parse driving signal logs (FR‑001). Outputs `data/derived/driving_signals.csv`. **Dependency**: Must be executed before T029.
- [X] T015 [US1] Implement `code/ingestion.py` function to load and sync particle tracking CSVs with driving signal logs (FR‑001). Synchronize by timestamp.
- [X] T016 [US1] Implement `code/ingestion.py` function to handle missing frames via linear interpolation or flagging (Edge Case: missing frames). If a gap exceeds the configured threshold, log a warning and set a `gap_flag` column.
- [X] T017 [US1] Implement `code/ingestion.py` function to compute $v$ and $\omega$ via finite differences from positions/orientations.
- [X] T018b [US1] **Prerequisite (Sequential)**: Create `docs/methodology_notes.md` with a concise operational definition of $E_{vib}$ as 'Vibrational Energy' calculated by integrating the power proxy over the window: $E_{vib} = m \cdot \text{var}(a) \cdot \Delta t$, yielding units of Joules (kg·m²/s²). Cite a specific, verified granular-physics paper (e.g., 'P. E. Kollmann, et al. (2019) Granular Physics' or a specific DOI). **Constraint**: Must be completed BEFORE T018. **Dependency**: None (except doc setup).
- [X] T018 [US1] Implement `code/ingestion.py` function to calculate $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ using independent physics formulas. $E_{vib}$ uses the definition from T018b: $E_{vib} = m \cdot \text{var}(a) \cdot \Delta t$, where $\Delta t$ is the time step derived from the frame rate. Reads `window_size_N` (integer) from `data/config.yaml`. Generates `data/derived/energy_intermediate.csv`. **Constraint**: All energy values must be in Joules. Verify units of $E_{vib}$ are Joules before writing. **Dependency**: Requires T018b completion.
- [X] T019 [US1] Output final `energy_samples.csv` to `data/derived/` with columns: `particle_id`, `timestamp`, `E_trans`, `E_rot`, `E_pot`, `E_vib`, `pot_incomplete`. Record the random seed and sampling rule (from T009) in `artifacts/sampling_metadata.json`. Compute SHA‑256 hash of the CSV and store in `artifacts/energy_samples.hash`. **Status**: Completed.

**Chirp Handling (Edge Case: Non-stationary signals)**
- [X] T029 [US1] Handle non‑stationary (chirped) driving signals: compute instantaneous frequency via Hilbert transform. If `--chirp-handling=exclude` (default), generate `artifacts/chirp_handling_result.csv` with strategy='excluded' and value=mask_index. If `--chirp-handling=bin`, generate `artifacts/chirp_handling_result.csv` with strategy='binned' and value=frequency_bin. **Output**: Unified artifact `artifacts/chirp_handling_result.csv` with columns `timestamp`, `strategy`, `value`. **Dependency**: Consumes output of T014a. **Constraint**: Implements both 'exclude' and 'bin' paths in a single task with a unified schema.

### Test Data Generation (still in Phase 3)

- [X] T020a [US1] Define parameters for synthetic test datasets: Maxwell‑Boltzmann (mean=1.0, scale=0.1) and Pareto (shape=2.0). Output to `artifacts/test_params.json`.
- [X] T020b [US1] Generate `data/derived/test_thermal_data.csv` and `data/derived/test_nonthermal_data.csv` using parameters from T020a. Files are prefixed with `test_` and are **not** used as primary scientific input. **Dependency**: Requires T020a.

### Additional US1 Tests

- [X] T021 [P] [US1] Unit test for correct handling of the `test_` prefix (ensures synthetic data are ignored by downstream analysis).
- [X] T022 [P] [US1] Verify that `artifacts/sampling_metadata.json` correctly records the seed and sampling rule.
- [X] T023b [P] [US1] Explicitly link T021/T022 to `test_thermal_data.csv` and `test_nonthermal_data.csv` to resolve cross-phase ambiguity.

---

## Phase 4: User Story 2 - Statistical Deviation Assessment and Hypothesis Testing (Priority: P2)

**Goal**: Compare observed energy distributions against Maxwell‑Boltzmann prediction using KS and Chi‑squared tests.

**Independent Test**: Run analysis on "thermal" vs "non‑thermal" labeled datasets; verify p‑values and rejection flags match expected ground truth.

**Dependency**: Requires `data/derived/energy_samples.csv` (T019) and `artifacts/chirp_handling_result.csv` (T029).

### Entry Gate

- [X] T054 [US2] Implement `code/main.py` dependency check: verify `data/derived/energy_samples.csv` exists and is valid; if missing, exit with `ERROR: Dependency file data/derived/energy_samples.csv missing. Run US1 first.`

### Implementation for User Story 2

- [X] T024 [US2] Implement `code/stats.py` function `bin_energy_data` to read `data/derived/energy_samples.csv`, apply the `chirp_handling_result.csv` (unified schema) to exclude or bin data, and bin by driving frequency (fixed intervals) and material type. Raise `FileNotFoundError` with the exact message if the file is missing or has a `test_` prefix. **Status**: Completed.
- [X] T025 [US2] Implement Kolmogorov‑Smirnov test with **Lilliefors correction** (as mandated by FR‑003 and Constitution Principle VII) comparing each binned empirical distribution to the theoretical Maxwell‑Boltzmann CDF. The correction MUST account for parameter estimation from the sample. **Constraint**: Lilliefors correction is REQUIRED. Vanilla KS is NOT allowed. **Status**: Completed.
- [X] T071 [P] [US2] Unit test for KS test logic with Lilliefors correction in `tests/test_stats.py` (verify p‑value calculation against known distribution). **Dependency**: Requires synthetic test data from T020b and implementation T025.
- [X] T072 [P] [US2] Unit test for Chi‑squared test logic in `tests/test_stats.py` (verify statistic and rejection boolean). **Dependency**: Requires synthetic test data from T020b and implementation T026.
- [X] T022b [P] [US2] Unit test `test_rejects_test_prefix` in `tests/test_stats.py` to verify that `bin_energy_data` explicitly rejects files with `test_` prefix and logs the rejection reason.
- [X] T026 [US2] Implement Chi‑squared goodness‑of‑fit test using Freedman‑Diaconis bin edges, integrating the Maxwell‑Boltzmann PDF (scale estimated from sample mean) to obtain expected counts. **Status**: Completed.
- [X] T027 [US2] Apply Benjamini‑Hochberg (FDR) correction across all frequency‑material bins. **Status**: Completed.
- [X] T028 [US2] Generate `artifacts/statistical_results.json` containing test type, statistic, raw p‑value, corrected p‑value, rejection flag, and `n_samples` per bin. Also log the effective sample size for each bin (see T057). **Status**: Completed.
- [X] T023 [P] [US2] Integration test for multi‑frequency aggregation in `tests/test_stats.py` (verify summary table generation).

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis on decision thresholds ($\alpha$) and discrepancy boundaries to ensure robustness.

**Independent Test**: Execute sensitivity sweep on fixed dataset; verify output report lists variation in rejection rates across thresholds.

**Dependency**: Reads `artifacts/statistical_results.json` from T028.

### Tests for User Story 3

- [X] T030 [P] [US3] Unit test for threshold sweep logic in `tests/test_sensitivity.py` (verify iteration over $\alpha \in \{0.01,0.05,0.10\}$)
- [X] T031 [P] [US3] Unit test for discrepancy boundary sweep in `tests/test_sensitivity.py` (verify iteration over boundaries $\{1\%,5\%,10\%\}$)

### Implementation for User Story 3

- [X] T032 [US3] Implement `code/sensitivity.py` function `sweep_alpha` to iterate over the specified $\alpha$ values, count rejections per bin, and store results.
- [X] T033 [US3] Implement `code/sensitivity.py` function `sweep_quasi_thermal_boundary` to iterate over energy‑ratio boundaries $\{1\%,5\%,10\%\}$ and record classification rates.
- [X] T034 [US3] Generate `artifacts/sensitivity_analysis_report.json` containing threshold vs. rejection‑rate data.
- [X] T035 [US3] Verify robustness: ensure the rejection decision for the **primary frequency bin** remains identical across $\alpha \in \{0.01,0.05,0.10\}$. Output `artifacts/stability_check.json` with a boolean `stable_across_thresholds` and per‑threshold decisions for the primary bin only. **Status**: Completed.

---

## Phase 6: User Story 4 - Regression Analysis of Deviation Drivers (Priority: P3)

**Goal**: Perform linear regression to relate deviation magnitude to driving frequency and material roughness, and test significance.

**Independent Test**: Run regression on synthetic dataset with known slope/intercept; verify calculated coefficients match within 1 % tolerance.

**Dependency**: Reads `artifacts/statistical_results.json` from T028.

### Tests for User Story 4

- [X] T036 [P] [US4] Unit test for linear regression fit in `tests/test_regression.py` (verify slope/intercept calculation)
- [X] T037 [P] [US4] Unit test for t‑test significance in `tests/test_regression.py` (verify p‑value calculation for slope)

### Implementation for User Story 4

- [X] T038 [US4] Implement `code/regression.py` function `prepare_predictors` to map material type to roughness proxy (from `data/config.yaml`) and assemble predictor matrix (frequency, roughness) and target vector (deviation magnitude from `statistical_results.json`).
- [X] T039 [US4] Fit ordinary least‑squares linear model, compute slope, intercept, $R^2$, and store in `artifacts/regression_results.json`.
- [X] T040 [US4] Perform t‑tests on regression coefficients, report p‑values (especially for the slope relating deviation to driving frequency).
- [X] T041 [US4] Persist results (coefficients, statistics, p‑values) in `artifacts/regression_results.json`.
- [X] T042 [US4] Verify regression validity: Implement logic to calculate the t-statistic and p-value for the slope coefficient. Output `artifacts/regression_validity_check.json` containing the slope p-value and a boolean `is_significant` (True if p < 0.05). **Constraint**: Do NOT assert a pass/fail; report the metric for SC-005 verification.
- [X] T042b [US4] Explicitly verify SC-005: Implement a check that confirms `artifacts/regression_validity_check.json` exists and contains the required fields (slope_p_value, is_significant). Output a boolean `sc005_verified` to `artifacts/sc005_check.json`.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T043 [P] Documentation updates in `README.md` and `docs/`
- [X] T044 [P] Run `ruff check --fix` on all code files to remove unused imports and fix formatting
- [X] T045 [P] Refactor loops in `code/ingestion.py` to use vectorized NumPy operations for performance
- [X] T046 [P] Add unit test `test_large_dataset_memory` in `tests/unit/` to verify memory usage stays within acceptable limits with large inputs
- [X] T047 [P] Add unit test `test_empty_bin_handling` in `tests/unit/` to verify graceful handling of empty frequency bins
- [X] T048 [P] Run `quickstart.md` validation to ensure end‑to‑end pipeline execution
- [X] T049a [P] [Polish] Implement `code/ingestion.py` CLI flag `--local-only` to enforce local‑only mode. If `--data-source` is a remote ID and `--local-only` is set, raise an error. If not set, allow remote fetching but enforce sampling if row count > 1 M.
- [X] T049b [P] [Polish] Add unit test `test_external_fetch_fails` asserting that fetching a remote dataset without sampling enabled raises a clear error, and that sampling works when enabled.
- [X] T050 [P] [Polish] Implement `code/ingestion.py` function `stream_dataset` using `datasets.load_dataset(..., streaming=True)` for chunked processing of large Zenodo/OpenGranular datasets. Integrate with `load_and_sample` (T009) to sample on‑the‑fly when dataset size > 14 GB.
- [X] T051 [P] [Polish] Extend `artifacts/sampling_metadata.json` with a `sampling_rule` object describing split, chunking, and row count used for any real sample taken.
- [X] T052 [P] [Polish] Add unit test `test_loader_fail_loudly` verifying that the data loader raises a `RuntimeError` immediately upon fetch failure, with no silent synthetic fallback.
- [X] T053 [P] [Polish] Implement logic to adopt a "VERIFIED REAL DATA SOURCE" block (if provided by execution feedback) as the sole source of truth, updating `data/config.yaml` and removing any hand‑rolled fetch code.
- [X] T055 [P] [Polish] Implement `code/ingestion.py` function `fetch_zenodo` that requires a valid Zenodo record ID (e.g., `12345`). Raises `ValueError` with a clear message if missing/invalid.
- [X] T056 [P] [Polish] Implement `code/ingestion.py` function `fetch_uci` that requires a valid UCI dataset ID (e.g., `123`). Raises `ValueError` with a clear message if missing/invalid.
- [X] T057 [P] [Polish] Extend `code/stats.py` to log and report the effective sample size (`n_samples`) for each frequency‑material bin in `artifacts/statistical_results.json`.
- [X] T058 [P] [Polish] Add unit test `test_sample_size_reporting` verifying that `n_samples` in `statistical_results.json` matches the actual row count per bin in `energy_samples.csv`.
- [X] T059 [P] [Polish] Implement `code/regression.py` function to generate a diagnostic plot (`artifacts/regression_diagnostic.png`) showing the fitted line, residuals, and 95 % confidence intervals for deviation vs. frequency.

---

## Revision Tasks: Addressing Review Concerns

**Purpose**: New tasks to resolve specific issues raised during the analysis phase, ensuring data integrity, statistical rigor, and reproducibility.

**⚠️ Note**: These tasks depend on T019b being completed successfully. If T019b fails, these tasks cannot run.

- [ ] T019b [US1] **Repair Energy Calculation**: Re-implement `code/ingestion.py` energy calculation logic to ensure `data/derived/energy_samples.csv` is generated correctly. **Specific Failure Mode**: Fix the truncated logic in function `compute_energy` to handle all rows and ensure E_vib units are Joules (m * var(a) * dt). **Verification**: Verify E_vib column in `energy_samples.csv` has values > 0 and units match Joules. **Constraint**: This task is **blocking** and **sequential**. It MUST invalidate and overwrite the output of T018 if T018 is marked 'Completed' but the output is incorrect. **Dependency**: Requires T018, T018b.
- [X] T063 [P] [US3] Implement `code/ingestion.py` function `verify_chirp_segments` to explicitly count the number of frames excluded due to the `chirp_handling_result.csv` (from T029) and log the percentage of total data lost. If >20% of frames in a specific time window are excluded, raise a `DataExclusionWarning` and flag the bin in `artifacts/exclusion_report.json`. **Constraint**: Aligns with spec Edge Case thresholds (20% of frames in window).
- [X] T064 [P] [US2] Implement `code/stats.py` function `calculate_effective_bins` to dynamically adjust Chi-squared bin counts based on the `n_samples` reported in T057, ensuring no bin has an expected count < 5. If adjustment is needed, log the new bin edges to `artifacts/bin_adjustments.json`.
- [X] T065 [P] [US3] Extend `code/sensitivity.py` to perform a "leave-one-out" cross-validation on the frequency bins to ensure the robustness of the threshold sweep results is not driven by a single outlier bin. Output `artifacts/cv_sensitivity_report.json`.
- [X] T066 [P] [US4] Implement `code/regression.py` function `check_multicollinearity` to calculate the Variance Inflation Factor (VIF) for the frequency and roughness predictors. If VIF > 5, log a warning in `artifacts/regression_diagnostics.json` and flag the model fit as potentially unstable.
- [X] T067 [P] [Polish] Create `docs/data_lineage.md` to explicitly document the flow of data from the raw Zenodo/UCI source through `energy_samples.csv`, `chirp_handling_result.csv`, and `statistical_results.json`, including the specific sampling rule and exclusion criteria used in the current run.
- [X] T068 [P] [Polish] Add a `--dry-run` flag to `code/main.py` that validates all dependencies, file paths, and configuration schemas without executing any heavy computation or data loading, ensuring the environment is ready before a full run.