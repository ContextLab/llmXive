---
description: "Task list template for feature implementation"
---

# Tasks: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

**Input**: Design documents from `/specs/001-validity-equipartition-granular/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The spec explicitly requests independent tests for energy accuracy (US1), statistical classification (US2), sensitivity sweeps (US3), and regression fit (US4). Tests are INCLUDED.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must run after previous task)
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

## Phase 1: Setup & Planning (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, test data generation, and real data source setup

- [X] T001a [S] [Setup] Create project structure: Create directories `code/`, `data/raw/`, `data/derived/`, `artifacts/`, `tests/`, `docs/`. Create files: `code/__init__.py` (empty), `tests/__init__.py` (empty).
- [X] T001b [S] [Setup] Create `.gitignore` with specific content: `*.pyc`, `__pycache__/`, `data/`, `artifacts/`, `logs/`, `.env`.
- [X] T002 [S] [Setup] Initialize Python 3.11 project `requirements.txt` with core and testing dependencies: `pandas>=2.0.0,<3.0.0`, `numpy>=1.24.0,<2.0.0`, `scipy>=1.11.0,<2.0.0`, `pyyaml>=6.0.0,<7.0.0`, `tqdm>=4.65.0,<5.0.0`, `datasets>=2.14.0,<3.0.0`, `huggingface_hub>=0.17.0,<1.0.0`, `scikit-learn>=1.3.0,<2.0.0`, `pytest>=7.4.0,<8.0.0`, `pytest-cov>=4.0.0,<5.0.0`, `statsmodels>=0.14.0,<1.0.0`.
- [X] T003 [P] [Setup] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`
- [X] T020a [S] [Setup] Define parameters for synthetic test datasets: Maxwell‑Boltzmann (mean=1.0, scale=0.1) and Pareto (shape=2.0). **Output**: Generate `artifacts/test_params.json` containing these parameters. **Dependency**: Must run before T020b.
- [ ] T020b [S] [Setup] Generate `data/derived/test_thermal_data.csv` (Maxwell-Boltzmann) and `data/derived/test_nonthermal_data.csv` (Pareto) using parameters from T020a. Files are prefixed with `test_` and are **not** used as primary scientific input. **Dependency**: Requires T020a.

**Data Source Validation (Simplified)**
- [X] T060 [P] [Foundational] Create `data/config.yaml` template with minimal required fields: `mass`, `radius`, `material_type`, `frequency_bins`, `default_zenodo_id`. No complex schema validation or automated resolver logic.
- [X] T076 [S] [Foundational] **Implement Real Data Source Loader**: Implement `code/ingestion.py` function `fetch_zenodo_granular` to download the Zenodo dataset. **Input**: Read Zenodo ID from `research.md` if present; **otherwise, use `default_zenodo_id` from `data/config.yaml`**. If both are missing, raise `RuntimeError` with the exact error message "Real data fetch failed: Zenodo ID not found in research.md or data/config.yaml". **Constraint**: Must use `streaming=True` if dataset > 7GB. **Constraint**: Must NOT have a `try/except` block that falls back to synthetic data; if download fails, raise `RuntimeError` with the exact error message "Real data fetch failed: <reason>". **Constraint**: Must verify the downloaded file's cryptographic checksum against the canonical source before processing. **Dependency**: Must be added to `requirements.txt`. **Dependency**: Must be integrated into `T009` (load_and_sample) as the primary source.
- [X] T009 [S] [Foundational] Implement `code/ingestion.py` function `load_and_sample` to accept a `--data-source` CLI argument (local path). **Streaming Algorithm**: If total rows > 1,000,000 OR if `--streaming` flag is set, use `datasets.load_dataset(..., streaming=True)` to process chunks. Must fail loudly on fetch failure, record random seed, sample indices and row count in `artifacts/sampling_metadata.json`. **Dependency**: Requires T076 and T050.
- [X] T050 [P] [Foundational] Implement `code/ingestion.py` function `stream_dataset` using `datasets.load_dataset(..., streaming=True)` for chunked processing of large Zenodo/OpenGranular datasets. Integrate with `load_and_sample` (T009) to sample on‑the‑fly when dataset size > 14 GB. **Dependency**: None (Standalone implementation).
- [X] T077a [S] [Foundational] **Generate Pilot Data for Effect Size**: Generate synthetic `data/derived/pilot_nonthermal_data.csv` using a Pareto distribution (shape=2.0) to simulate a non-thermal state. **Output**: A dataset with known deviation from Maxwell-Boltzmann. **Dependency**: Requires T020a.
- [X] T077 [S] [Foundational] **Implement Sensitivity Sweep for Effect Size**: Implement `code/utils/power_analysis.py` function `calculate_required_samples` to perform a sensitivity sweep over effect size delta (δ) using the pilot data from T077a. **Input**: Effect size (estimated from pilot data generated in T077a, specifically the non-thermal Pareto data), alpha (conventional significance threshold), power (0.8). **Output**: Minimum `n_samples` required per bin, a report of the minimum detectable effect size, and a sweep of rejection rates across δ values. **Constraint**: This is a PLANNING task using SYNTHETIC data. It does NOT require real data loading (T009) or energy calculation (T018). Its output (`artifacts/power_analysis_plan.json`) is an **informative** pre-run that T024 reads if present but does not fail if missing. **Dependency**: Must run before T024 (binning) to inform binning strategy. **Dependency**: Requires T077a (for pilot data estimation).

**Explicit Sample Size Logging (Critical for Reproducibility)**
- [X] T084 [S] [Setup] **Implement Explicit Sample Size Logging**: Add a task to ensure `artifacts/sampling_metadata.json` explicitly records the `total_rows_streamed`, `rows_sampled`, `sampling_seed`, and `sampling_fraction` (if applicable) to satisfy the "State the exact streaming/sampling rule" requirement for auditability. **Constraint**: Must run AFTER T009 and T019 to ensure the file exists. **Dependency**: T009, T019.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

- [X] T006 [P] [Foundational] Create `code/config.py` to load material properties (mass, inertia, roughness proxy) and frequency bins from `data/config.yaml`
- [X] T007 [P] [Foundational] Implement `code/main.py` orchestration script with argument parsing for pipeline stages
- [X] T008 [P] [Foundational] Setup `tests/conftest.py` with fixtures for synthetic data generation and random seed pinning
- [X] T010 [P] [Foundational] Implement `code/ingestion.py` function `validate_metadata` to validate required metadata fields (mass, radius, material type) in the dataset header. If missing, FLAG the dataset as 'incomplete' for those fields. **Constraint**: Raise `DataIngestionError` UNLESS `--allow-incomplete` flag is passed. Do NOT silently proceed.
- [X] T010a [P] [Foundational] Implement `code/ingestion.py` function `handle_kinetic_only_fallback` to process datasets flagged as 'incomplete' (from T010) by calculating only available energy components (translational, rotational) and setting potential/vibrational energy to NaN or 0 with a warning. **Dependency**: Requires T010.
- [X] T011 [P] [Foundational] Implement `code/ingestion.py` function to handle missing z‑axis data by adding a `pot_incomplete` boolean column to the output dataframe and writing a specific warning log entry (Edge Case: missing z‑axis). **Dependency**: Requires T010.

---

## Phase 3: User Story 1 - Data Ingestion and Energy Component Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest particle tracking data and driving logs to compute $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ for every particle/frame.

**Independent Test**: Run ingestion script on a small synthetic CSV subset; verify calculated energies match manual calculations within a high‑precision tolerance.

**Dependency Order**: T014a -> T016 -> T016a -> T017 -> T029 -> T063 -> T018 -> T019.

### Implementation for User Story 1

- [ ] T014a [S] [US1] **Ingest Driving Logs**: Implement `code/ingestion.py` function to **ingest and parse raw driving signal logs** from `data/raw/`. **Constraint**: Output a canonical intermediate file `data/derived/driving_signals.csv` with timestamps aligned to the raw log. **Dependency**: Must be executed before T016, T029, and T019. **Implementation**: Parse CSV/JSON logs, interpolate if necessary, and write to `data/derived/driving_signals.csv`.
- [X] T016 [S] [US1] Implement `code/ingestion.py` function to handle missing frames via linear interpolation or flagging (Edge Case: missing frames). If a gap exceeds the configured threshold, log a warning and set a `gap_flag` column. **Dependency**: Requires T014a. **Implementation**: Interpolate positions/orientations to maintain continuity.
- [X] T016a [S] [US1] **Calculate Tracking Failure Rate**: Implement `code/ingestion.py` function `calculate_tracking_failure_rate` to compute the percentage of missing frames per time window. If the rate > 20%, flag the window for exclusion. **Dependency**: Requires T016. **Constraint**: This exclusion logic must be applied before energy calculation (T018).
- [X] T017 [S] [US1] Implement `code/ingestion.py` function to compute $v$ and $\omega$ via finite differences from positions/orientations. **Dependency**: Requires T016 (interpolated data).
- [ ] T029 [S] [US1] **Handle Non-stationary Signals**: Implement `code/ingestion.py` function to handle non‑stationary (chirped) driving signals: compute instantaneous frequency or exclude non-stationary segments as per spec Edge Cases. **CLI Flag**: `--chirp-handling` with choices `exclude` (default) or `bin`. If `exclude`, generate `artifacts/chirp_handling_result.csv` with strategy='excluded' and value=mask_index. If `bin`, generate `artifacts/chirp_handling_result.csv` with strategy='binned' and value=frequency_bin. **Algorithm**: Use `scipy.signal.hilbert` on the driving signal from `data/derived/driving_signals.csv` (T014a) to compute instantaneous frequency. **Output**: Unified artifact `artifacts/chirp_handling_result.csv` with columns `timestamp`, `strategy`, `value`. **Dependency**: Consumes output of T014a. **Constraint**: Implements both 'exclude' and 'bin' paths via CLI flag. **Dependency**: Must run before T018.
- [ ] T063 [S] [US1] **Verify Chirp Segments**: Implement `code/ingestion.py` function `verify_chirp_segments` to explicitly count the number of frames excluded due to the `chirp_handling_result.csv` (from T029) and log the percentage of total data lost. If >20% of frames in a specific time window are excluded, raise a `DataExclusionWarning`, flag the bin in `artifacts/exclusion_report.json`, and **exclude the window from the final `energy_samples.csv`**. If a frequency bin has < 50 samples after exclusion, flag it as 'insufficient_data' in the report. **Constraint**: Aligns with spec Edge Case thresholds (20% of frames in window). **Dependency**: Requires T029 and must run before T018.
- [ ] T018 [S] [US1] **Calculate Energy Components (Streaming PSD)**: Implement `code/ingestion.py` function to calculate $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ using independent physics formulas.
 - **Formulas**:
 - $E_{trans} = \frac{1}{2} m v^2$
 - $E_{rot} = \frac{1}{2} I \omega^2$
 - $E_{pot} = m g z$
 - $E_{vib} = \text{PSD Integration of driving signal cross-correlation}$ (Calculated via Power Spectral Density integration of the driving signal cross-correlation as mandated by Constitution Principle VI and Plan Methodology Updates). **Units**: All energy values must be in Joules ($kg \cdot m^2/s^2$). **Note**: $E_{vib}$ is included to satisfy FR-002 and Constitution Principle VI. **Implementation Note**: Implement with a rolling window of N frames to compute local PSD. **CRITICAL ALGORITHM**: Integrate the PSD over the window to produce a **SINGLE scalar E_vib value** for the **CENTER FRAME** of that window. Store this scalar for **EVERY FRAME** in the output dataframe (interpolating edges if necessary). Do NOT aggregate across frames for the final output. **Dependency**: Requires T017, T029 (exclusion masks), T063, T060 (config).
- [ ] T019 [S] [US1] **Output Final Energy Data**: Output final `energy_samples.csv` to `data/derived/` with columns: `particle_id`, `timestamp`, `E_trans`, `E_rot`, `E_pot`, `E_vib`, `pot_incomplete`. Apply exclusion masks from T016a, T029, and T063 before writing. Record the random seed and sampling rule (from T009) in `artifacts/sampling_metadata.json`. Compute SHA‑256 hash of the CSV and store in `artifacts/energy_samples.hash`. **Dependency**: Requires T018, T029, T063.

### Tests for User Story 1

- [X] T012a [S] [US1] **Independent Test**: 1) Generate a synthetic dataset with **hardcoded** known ground-truth velocities (e.g., `v=1.0 m/s`, `v=2.0 m/s`) and positions. 2) Calculate expected energies manually using the formulas defined in T018 and save to `artifacts/manual_baseline.csv` via a dedicated script that computes these values from the hardcoded inputs. 3) Run the ingestion pipeline on this data, compare computed energies to `artifacts/manual_baseline.csv`, and output `artifacts/energy_verification_report.json` containing the max absolute error. **Constraint**: If max error > 1e-9, set `repair_needed: true` in the report. **Dependency**: Must run AFTER T019.
- [X] T012 [P] [US1] Unit test for energy formulas in `tests/test_energy.py` (verify $E_{trans}=0.5mv^2$, etc. with known inputs)
- [ ] T013 [P] [US1] Integration test for missing frame interpolation in `tests/test_ingestion.py` (verify linear interpolation logic)
- [ ] T014 [P] [US1] Integration test for material‑specific mass application in `tests/test_ingestion.py` (verify steel vs. polymer constants)

### Additional US1 Tests

- [X] T021 [P] [US1] Unit test for correct handling of the `test_` prefix (ensures synthetic data are ignored by downstream analysis).
- [X] T022 [P] [US1] Verify that `artifacts/sampling_metadata.json` correctly records the seed and sampling rule.
- [ ] T023b [P] [US1] Explicitly link T021/T022 to `test_thermal_data.csv` and `test_nonthermal_data.csv` to resolve cross-phase ambiguity.

---

## Phase 4: User Story 2 - Statistical Deviation Assessment and Hypothesis Testing (Priority: P2)

**Goal**: Compare observed energy distributions against Maxwell‑Boltzmann prediction using KS and Chi‑squared tests.

**Independent Test**: Run analysis on "thermal" vs "non‑thermal" labeled datasets; verify p‑values and rejection flags match expected ground truth.

**Dependency**: Requires `data/derived/energy_samples.csv` (T019) and `artifacts/chirp_handling_result.csv` (T029, optional).

### Entry Gate

- [ ] T054 [S] [US2] Implement `code/main.py` dependency check: verify `data/derived/energy_samples.csv` exists and is valid; if missing, exit with `ERROR: Dependency file data/derived/energy_samples.csv missing. Run US1 first.` **Constraint**: If `chirp_handling_result.csv` exists, verify it is also valid.

### Implementation for User Story 2

- [X] T025a [S] [US2] **Calculate DOF-Normalized Energy Ratio (Primary Metric)**: Implement `code/stats.py` logic to calculate the **Degrees-of-Freedom Normalized Energy Ratio** ($R = \frac{\langle E_{trans} \rangle / DOF_{trans}}{\langle E_{rot} \rangle / DOF_{rot}}$) where $DOF_{trans}=3$ and $DOF_{rot}=2$ (or 3). **Constraint**: This is the primary quantification metric as per Plan Methodology Updates and is linked to SC-002 and FR-003. **Dependency**: Requires T024.
- [ ] T024 [S] [US2] Implement `code/stats.py` function `bin_energy_data` to read `data/derived/energy_samples.csv`, apply the `chirp_handling_result.csv` (if present) to exclude or bin data, and bin by driving frequency (fixed intervals) and material type. **Dependency**: Requires T019. **Constraint**: If `chirp_handling_result.csv` is missing, proceed without it (do not fail). Raise `FileNotFoundError` with the exact message if the file is missing or has a `test_` prefix. **Note**: This task reads `artifacts/power_analysis_plan.json` (from T077) if present to inform binning strategy, but does not fail if it is missing.
- [X] T025b [S] [US2] **Kolmogorov‑Smirnov Test (Theoretical - Primary Validation)**: Implement KS test comparing each binned empirical distribution to the **theoretical** Maxwell‑Boltzmann CDF. **Constraint**: The test MUST be a strict theoretical KS test as per Spec FR-003 and Constitution Principle VII. **CRITICAL**: The temperature parameter ($T$) MUST be read from `data/config.yaml` (external calibration). If $T$ is missing, the task MUST fail with `RuntimeError: Theoretical temperature T not found in data/config.yaml`. **Do NOT estimate T from the sample mean.** **Constraint**: Must explicitly stratify by frequency bins (regular intervals) and material types as per Constitution Principle VII. **Dependency**: Requires T024.
- [X] T025 [S] [US2] **Kolmogorov‑Smirnov Test (Parameterized - Secondary Robustness)**: Implement KS test with Lilliefors correction comparing each binned empirical distribution to the theoretical Maxwell‑Boltzmann CDF where temperature ($T$) is derived from the sample mean. **Constraint**: This is a secondary robustness check, not the primary validation. **Dependency**: Requires T024.
- [X] T071 [P] [US2] Unit test for KS test logic in `tests/test_stats.py` (verify p‑value calculation against known distribution). **Dependency**: Requires synthetic test data from T020b and implementation T025b/T025. **Dependency**: T020b.
- [X] T072 [P] [US2] Unit test for Chi‑squared test logic in `tests/test_stats.py` (verify statistic and rejection boolean). **Dependency**: Requires synthetic test data from T020b and implementation T026. **Dependency**: T020b.
- [X] T022b [P] [US2] Unit test `test_rejects_test_prefix` in `tests/test_stats.py` to verify that `bin_energy_data` explicitly rejects files with `test_` prefix and logs the rejection reason.
- [X] T026 [S] [US2] **Chi‑squared Goodness‑of‑Fit**: Implement Chi‑squared goodness‑of‑fit test using a standard binning algorithm (e.g., Freedman‑Diaconis or Sturges) selected based on data distribution, integrating the Maxwell‑Boltzmann PDF (scale estimated from sample mean) to obtain expected counts. **Constraint**: The null hypothesis explicitly uses the sample mean to define the theoretical distribution parameters. **Dependency**: Requires T024.
- [X] T085 [S] [US2] **Stretched Exponential Goodness-of-Fit**: Implement `code/stats.py` function `fit_stretched_exponential` to perform the secondary test mandated by the Plan ("Stretched Exponential Goodness-of-Fit"). **Formula**: $f(x) = \frac{\beta}{\lambda} (\frac{x}{\lambda})^{\beta-1} e^{-(x/\lambda)^\beta}$. **Parameters**: Estimate shape $\beta$ and scale $\lambda$ using Maximum Likelihood Estimation. **Test Statistic**: Use Likelihood Ratio Test to compare against the Maxwell-Boltzmann null. **Output**: Results to `artifacts/stretched_exponential_results.json`. **Dependency**: Requires T024.
- [X] T027a [S] [US2] **Primary: Benjamini-Hochberg (BH) FDR Correction**: Implement BH correction across all frequency‑material bins as the PRIMARY default method per FR-006. **Algorithm**: Sort p-values, compare to $\frac{i}{m} \alpha$, find largest $k$ such that $p_{(k)} \le \frac{k}{m} \alpha$. **Constraint**: This is the primary correction method. **Dependency**: Requires T025b, T025, T026, T085.
- [X] T027 [S] [US2] **Secondary: Permutation-based FDR Correction**: Implement permutation-based FDR correction across all frequency‑material bins to account for dependent bins as a sensitivity check (Plan 'Complexity Tracking'). **Algorithm**: Shuffle labels across bins N=1000 times to generate a null distribution of p-values, then correct observed p-values based on this empirical distribution. **Constraint**: This is a secondary/sensitivity check, not the primary method. **Output**: Results to `artifacts/fdr_permutation_results.json`. **Dependency**: Requires T025b, T025, T026, T085.
- [X] T028 [S] [US2] Generate `artifacts/statistical_results.json` containing test type, statistic, raw p‑value, corrected p‑value (from T027a), rejection flag, and `n_samples` per bin. Also log the effective sample size for each bin (see T057). **Dependency**: Requires T027a.
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

- [X] T032 [S] [US3] Implement `code/sensitivity.py` function `sweep_alpha` to iterate over the specified $\alpha$ values, count rejections per bin, and store results. **Dependency**: Requires T028.
- [X] T033a [S] [US3] **Sweep Discrepancy Boundaries for Rejection Robustness**: Implement `code/sensitivity.py` function `sweep_discrepancy_boundary` to iterate over energy‑discrepancy boundaries **{, 0.05, 0.10}** (fractional deviation from equipartition) and record the **binary rejection decision (True/False)** for the null hypothesis for each bin. **Constraint**: This explicitly measures the robustness of the rejection decision as required by FR-005 and SC-003. **Dependency**: Requires T028.
- [X] T033 [S] [US3] **Sweep Quasi-Thermal Classification Stability**: Implement `code/sensitivity.py` function `sweep_quasi_thermal_boundary` to iterate over energy‑ratio boundaries and record classification rates (secondary check). **Dependency**: Requires T028.
- [X] T034 [S] [US3] Generate `artifacts/sensitivity_analysis_report.json` containing threshold vs. rejection‑rate data and discrepancy boundary vs. rejection-decision data.
- [ ] T035a [S] [US3] **Document Design Decision: Primary Frequency Bin**: Create `docs/design_decisions.md` entry explaining the choice of the "median of unique frequency bin values in `energy_samples.csv`" as the "primary frequency bin" for SC-003 verification. **Constraint**: This provides the traceable justification required by the spec. **Dependency**: None.
- [X] T035 [S] [US3] **Verify Robustness (SC-003)**: Verify that the rejection decision for the **primary frequency bin** remains identical across $\alpha \in \{0.01,0.05,0.10\}$ and discrepancy boundaries.
 - **Definition**: The "primary frequency bin" is defined as the **median of the unique frequency bin values present in `data/derived/energy_samples.csv`** (see `docs/design_decisions.md` for justification).
 - **Output**: `artifacts/stability_check.json` with a boolean `stable_across_thresholds` and per‑threshold decisions for the primary bin only.
 - **Constraint**: Must explicitly measure and report the boolean decision stability as per SC-003. **Dependency**: Requires T028, T035a, T033a.

---

## Phase 6: User Story 4 - Regression Analysis of Deviation Drivers (Priority: P3)

**Goal**: Perform linear regression to relate deviation magnitude to driving frequency and material roughness, and test significance.

**Independent Test**: Run regression on synthetic dataset with known slope/intercept; verify calculated coefficients match within 1 % tolerance.

**Dependency**: Reads `artifacts/statistical_results.json` from T028.

### Tests for User Story 4

- [X] T036 [P] [US4] Unit test for linear regression fit in `tests/test_regression.py` (verify slope/intercept calculation)
- [X] T037 [P] [US4] Unit test for t‑test significance in `tests/test_regression.py` (verify p‑value calculation for slope)

### Implementation for User Story 4

- [X] T078a [S] [US4] **Calculate Equipartition Deviation Metric**: Implement `code/regression.py` function `calculate_deviation_metric` to explicitly compute the **Equipartition Deviation Metric** ($|\langle E_{trans} \rangle - \langle E_{rot} \rangle| / \langle E_{total} \rangle$) as the dependent variable. **Constraint**: $\langle E_{total} \rangle$ must include $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ as per Spec FR-002 and Plan Principle VI. **Dependency**: Requires T028.
- [X] T038 [S] [US4] Implement `code/regression.py` function `prepare_predictors` to map material type to roughness proxy (from `data/config.yaml`) and assemble predictor matrix (frequency, roughness) and target vector (deviation magnitude from T078a). **Dependency**: Requires T028 and T078a.
- [X] T039 [S] [US4] Fit ordinary least‑squares linear model, compute slope, intercept, $R^2$, and store in `artifacts/regression_results.json`.
- [X] T040 [S] [US4] Perform t‑tests on regression coefficients, report p‑values (especially for the slope relating deviation to driving frequency).
- [X] T041 [S] [US4] Persist results (coefficients, statistics, p‑values) in `artifacts/regression_results.json`.
- [X] T042 [S] [US4] **Verify Regression Validity**: Implement logic to calculate the t-statistic and p-value for the slope coefficient. Output `artifacts/regression_validity_check.json` containing the slope p-value and a boolean `is_significant` (True if p < 0.05). **Constraint**: Do NOT assert a pass/fail; report the metric for SC-005 verification. **Dependency**: Requires T028, T078a, T039, T040.
- [X] T042b [S] [US4] **Verify SC-005**: Explicitly verify SC-005 by checking that `artifacts/regression_validity_check.json` exists and contains the required fields. **Constraint**: The verification logic MUST explicitly check that the numeric value of `slope_p_value` is strictly less than a predefined significance threshold. and output a boolean `sc005_verified` to `artifacts/sc005_check.json`. **Note**: This task reports the metric; it does NOT exit with an error code if the condition is not met, preserving the observational nature of the research. **Dependency**: Requires T042.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T043 [P] Documentation updates in `README.md` and `docs/`
- [X] T044 [P] Run `ruff check --fix` on all code files to remove unused imports and fix formatting
- [ ] T045 [P] Refactor loops in `code/ingestion.py` to use vectorized NumPy operations for performance
- [X] T046 [P] Add unit test `test_large_dataset_memory` in `tests/unit/` to verify memory usage stays within acceptable limits with large inputs
- [X] T047 [P] Add unit test `test_empty_bin_handling` in `tests/unit/` to verify graceful handling of empty frequency bins
- [X] T048 [P] Run `quickstart.md` validation to ensure end‑to‑end pipeline execution
- [X] T051 [P] [Polish] Extend `artifacts/sampling_metadata.json` with a `sampling_rule` object describing split, chunking, and row count used for any real sample taken.
- [X] T052 [P] [Polish] Add unit test `test_loader_fail_loudly` verifying that the data loader raises a `RuntimeError` immediately upon fetch failure, with no silent synthetic fallback.
- [X] T057 [P] [Polish] Extend `code/stats.py` to log and report the effective sample size (`n_samples`) for each frequency‑material bin in `artifacts/statistical_results.json`.
- [ ] T058 [P] [Polish] Add unit test `test_sample_size_reporting` verifying that `n_samples` in `statistical_results.json` matches the actual row count per bin in `energy_samples.csv`.
- [X] T059 [P] [Polish] Implement `code/regression.py` function to generate a diagnostic plot (`artifacts/regression_diagnostic.png`) showing the fitted line, residuals, and 95 % confidence intervals for deviation vs. frequency.
- [X] T064 [P] [US2] Implement `code/stats.py` function `calculate_effective_bins` to dynamically adjust Chi-squared bin counts based on the `n_samples` reported in T057, ensuring no bin has an expected count < 5. If adjustment is needed, log the new bin edges to `artifacts/bin_adjustments.json`.
- [X] T065 [P] [US3] Extend `code/sensitivity.py` to perform a "leave-one-out" cross-validation on the frequency bins to ensure the robustness of the threshold sweep results is not driven by a single outlier bin. Output `artifacts/cv_sensitivity_report.json`.
- [X] T066 [P] [US4] Implement `code/regression.py` function `check_multicollinearity` to calculate the Variance Inflation Factor (VIF) for the frequency and roughness predictors. If VIF > 5, log a warning in `artifacts/regression_diagnostics.json` and flag the model fit as potentially unstable.
- [ ] T067 [P] [Polish] Create `docs/data_lineage.md` to explicitly document the flow of data from the raw Zenodo/UCI source through `energy_samples.csv`, `chirp_handling_result.csv`, and `statistical_results.json`, including the specific sampling rule and exclusion criteria used in the current run.
- [ ] T068 [P] [Polish] Add a `--dry-run` flag to `code/main.py` that validates all dependencies, file paths, and configuration schemas without executing any heavy computation or data loading, ensuring the environment is ready before a full run.
- [ ] T069 [P] [Polish] Implement `code/ingestion.py` function `calculate_energy_ratios` to compute the ratio $E_{rot}/E_{trans}$ for every particle and store it in `data/derived/energy_ratios.csv` for direct inspection and plotting.
- [ ] T070 [P] [Polish] Add a `--plot-results` flag to `code/main.py` that generates standard plots (energy distribution histograms, p-value heatmaps, regression lines) and saves them to `artifacts/plots/` without re-running the full analysis if artifacts exist.
- [X] T073 [P] [Polish] Implement `code/config.py` to validate that `frequency_bins` in `data/config.yaml` are strictly increasing and non-overlapping, raising a `ConfigurationError` if invalid.
- [ ] T074 [P] [Polish] Add a `--verbose` flag to `code/main.py` to enable detailed logging of intermediate steps (e.g., binning counts, interpolation gaps) to `logs/pipeline.log`.
- [ ] T075 [P] [Polish] Create `docs/api_reference.md` documenting all public functions in `code/ingestion.py`, `code/stats.py`, `code/regression.py`, and `code/sensitivity.py` with usage examples.

---

## Phase Revision: Addressing Review Concerns

**Purpose**: Add missing tasks to address specific review concerns regarding data sourcing, power analysis, regression target definition, and compute feasibility.

- [ ] T079 [P] [US2] **Add Ground Truth Verification Test**: Implement `tests/test_stats.py` function `test_ground_truth_rejection` to verify that the KS test with Lilliefors correction correctly rejects the null hypothesis for the `test_nonthermal_data.csv` (Pareto distribution) and accepts it for `test_thermal_data.csv` (Maxwell-Boltzmann) at a high confidence level. **Constraint**: This test must pass before the analysis phase is considered valid.
- [X] T080 [P] [Polish] **Update Documentation**: Update `docs/data_lineage.md` and `README.md` to explicitly document the new Power Analysis step (T077) and the specific Zenodo dataset ID used (resolved from research.md or config.yaml).
- [X] T083 [S] [US4] **Add Robust Regression (RANSAC)**: Implement `code/regression.py` function `fit_robust_regression` using RANSAC (Random Sample Consensus) to handle potential outliers in the deviation data. Compare results with OLS (T039) and report the difference in `artifacts/regression_robustness.json`. **Constraint**: This addresses the concern that linear regression might be skewed by non-thermal outliers, ensuring the "real data" analysis is robust.
- [X] T086 [S] [US4] **Verify Material Roughness Proxy Validity**: Implement `code/regression.py` function `validate_roughness_proxy` to check if the material-to-roughness mapping in `data/config.yaml` is supported by literature references or if it is a placeholder. If placeholder, flag the regression result with a `proxy_limitation_warning` in `artifacts/regression_results.json`. **Dependency**: Requires T038.
- [X] T087 [P] [US2] **Add Multiple Comparison Correction Visualization**: Generate `artifacts/fdr_correction_plot.png` visualizing the raw vs. corrected p-values across all frequency bins to provide a graphical representation of the FDR impact (T027a). **Dependency**: Requires T028.
