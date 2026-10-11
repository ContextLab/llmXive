# Tasks: Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

**Input**: Design documents from `/specs/001-quantify-artifact-bias/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by research phase and by user story to enable independent implementation and testing.

---

## Phase 1: Setup and First End‑to‑End Analysis  

**Goal**: Establish project scaffolding, verify that the pipeline can run on a tiny synthetic example, and produce a reproducible end‑to‑end result.

| ID | Status | Description |
|----|--------|-------------|
- [ ] T001a1 [P] Create `code/` directory and sub‑directories: `synthetic`, `metrics`, `analysis`, `io`  
  - **Verification**: Directory tree exists and is tracked in Git.  
- [ ] T001a2 [P] Create `data/` directory and sub‑directories: `raw`, `synthetic`, `processed`, `validation`  
  - **Verification**: Directory tree exists.  
- [ ] T001a3 [P] Create `tests/` directory and sub‑directories: `unit`, `contract`, `integration`  
  - **Verification**: Directory tree exists.  
- [ ] T001a4 [P] Create `logs/` directory  
  - **Verification**: Directory exists.  
- [ ] T001b [P] Initialise `.gitignore` (exclude `data/`, `__pycache__/`, `*.pyc`, `logs/`, `*.log`)  
  - **Verification**: `.gitignore` contains the listed patterns.  
- [ ] T001c [P] Initialise `README.md` with a brief project overview and quick‑start instructions  
  - **Verification**: `README.md` exists and contains a “Quick‑start” section.  
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools via `pyproject.toml`  
  - **Verification**: `pyproject.toml` includes `[tool.ruff]` and `[tool.black]` sections.  
- [ ] T002 [P] Initialise Python 3.11 project with `requirements.txt` (numpy, scikit‑image, astropy, scipy, statsmodels, pandas, matplotlib, pytest)  
  - **Verification**: `requirements.txt` lists the exact packages and versions.  
- [ ] T004 [P] Create `code/config.py` with pinned random seeds, default paths, and concrete artifact parameters (noise levels `{0.01,0.05,0.10}`, saturation range `0.0–0.5` in `0.05` steps)  
  - **Verification**: `code/config.py` defines `DEFAULT_NOISE_LEVELS` and `DEFAULT_SATURATION_FRACTIONS`.  
- [ ] T007 [P] Implement `code/io/writer.py` to save generated images and logs with SHA‑256 checksums for reproducibility (FR‑008)  
  - **Verification**: `writer.save_with_checksum()` creates a `.sha256` file beside each artifact.  
- [ ] T008 [P] Setup `tests/unit/` structure and a minimal `pytest.ini` configuration  
  - **Verification**: `tests/unit/` exists and `pytest -q` discovers at least one test.  
- [ ] T046a [P] Create CLI stub `code/main.py` with a `--run-all` flag and basic argument parsing (no pipeline logic yet)  
  - **Verification**: Running `python -m code.main --help` prints usage information.  

**Checkpoint**: The repository now contains a valid Python package layout, configuration, and a runnable CLI stub.

---

## Phase 2: Core Infrastructure and Synthetic Data Generation  

**Goal**: Provide real (synthetic) input data, verify metadata handling, and make the pipeline ready for scientific tasks.

- [ ] T006a [S] Implement `code/synthetic/generator.py` to generate **N = 50** synthetic planetary‑nebula FITS images with known ground‑truth ellipticity and asymmetry (CPU‑only)  
  - **Output**: `data/synthetic/synth_{id:03d}.fits` (50 files).  
  - **Verification**: Each FITS header contains `TRUE_ELLIP` and `TRUE_ASYM` keywords.  
- [ ] T006b [S] Run the generator script to populate `data/synthetic/`  
  - **Verification**: Count of FITS files equals 50.  
- [ ] T006c [S] Generate `data/synthetic/gt_metadata.json` containing ground‑truth values for every synthetic image (schema matches `MorphologyMetrics` requirements)  
  - **Verification**: JSON file validates against a generated schema test.  
- [ ] T009 [S] Acquire 2–5 real, flux‑calibrated HST FITS images (e.g., NGC 7009, NGC 6543) via `astroquery.mast`, verify checksums, and store in `data/validation/` together with `validation_manifest.json` and a short `validation_report.md` (qualitative only, Constitution VII)  
  - **Verification**: Manifest lists at least two images; report references file paths and includes WCS checks.  
- [ ] T046b [P] Implement `validate_pipeline_state()` in `code/main.py` to abort with clear errors if `gt_metadata.json` or `validation_manifest.json` are missing  
  - **Verification**: Running the CLI without those files exits with status 1 and prints the expected message.  

**Checkpoint**: Synthetic data, real‑data manifest, and validation logic are in place; the pipeline can now be exercised on known inputs.

---

## Phase 3: User Story 1 – Noise‑Induced Bias on Ellipticity (Priority P1)

**Goal**: Quantify how Gaussian noise (σ = 0.01, 0.05, 0.10 × median) biases ellipticity measurements.

- [ ] T010 [P] Contract test `tests/unit/test_loader.py::test_loader_raises_on_missing_wcs` (FR‑009)  
  - **Verification**: Test fails before implementation.  
- [ ] T011 [P] Unit test `tests/unit/test_artifacts.py::test_noise_injection_sigma` (FR‑002)  
  - **Verification**: Test fails before implementation.  
- [ ] T012 [P] Unit test `tests/unit/test_ellipticity.py::test_ellipticity_calculation` (FR‑004)  
  - **Verification**: Test fails before implementation.  
- [ ] T013 [P] Implement `code/metrics/ellipticity.py` using second‑order moments (FR‑004)  
  - **Verification**: Function `measure_ellipticity(image)` returns a float in [0, 1].  
- [ ] T014 [S] Implement `code/synthetic/artifacts.py::inject_noise(image, sigma)` to create three noisy versions per image and write a sweep CSV `data/processed/noise_sweep_data.csv` (columns: image_id, sigma, measured_ellipticity, ground_truth_ellipticity, bias) (FR‑002, SC‑003)  
  - **Verification**: CSV contains 150 rows (50 images × 3 sigma levels).  
- [ ] T016 [S] Implement `code/analysis/statistics.py::run_noise_regression()` performing linear regression of bias vs. σ with Bonferroni correction; output `data/processed/noise_stats.csv` (FR‑005, SC‑003)  
  - **Verification**: CSV includes columns `sigma`, `mean_bias`, `p_value`, `significant`, `slope`, `intercept`.  
- [ ] T015a [S] Add `run_us1_orchestration()` in `code/main.py` to orchestrate loading, noise injection, ellipticity measurement, and bias recording (FR‑001, FR‑008)  
  - **Verification**: CLI flag `--run-us1` executes the full US1 workflow without error.  
- [ ] T015b [S] Add `compute_noise_bias()` in `code/main.py` that calls `run_noise_regression()` and logs results to `logs/noise_bias.log`  
  - **Verification**: Log file contains a line “Noise bias regression completed”.  
- [ ] T017 [P] Add detailed logging of noise parameters, random seeds, and regression outcomes to `logs/research.log` (FR‑008)  
  - **Verification**: Log entries include timestamp, `sigma`, and regression coefficients.  

**Checkpoint**: US1 can be executed independently; all unit tests now pass.

---

## Phase 4: User Story 2 – Saturation‑Induced Bias on Asymmetry (Priority P2)

**Goal**: Determine whether clipping the brightest pixels (saturation fractions 0.0–0.5 in 0.05 steps) inflates the asymmetry index.

- [ ] T018 [P] Unit test `tests/unit/test_artifacts.py::test_saturation_clipping` (FR‑003)  
  - **Verification**: Test fails before implementation.  
- [ ] T019 [P] Unit test `tests/unit/test_asymmetry.py::test_asymmetry_conselice` (FR‑004)  
  - **Verification**: Test fails before implementation.  
- [ ] T020 [P] Implement `code/metrics/asymmetry.py` using the Conselice (2003) definition with robust centering (FR‑004)  
  - **Verification**: Function `measure_asymmetry(image)` returns a float in [0, 1].  
- [ ] T021 [S] Extend `code/synthetic/artifacts.py::apply_saturation(image, fraction)` to produce FITS files `data/processed/sat_{fraction:.2f}_{id:03d}.fits` for each fraction (0.0–0.5 step 0.05) and flag unusable images (zero signal) in metadata  
  - **Verification**: Directory contains 11 × 50 = 550 FITS files; each header includes `SAT_FRACTION`.  
- [ ] T024 [S] Implement sweep aggregation `code/analysis/saturation_sweep.py` that reads all saturated images, measures asymmetry, and writes `data/processed/saturation_sweep.csv` (columns: saturation_fraction, measured_asymmetry, ground_truth_asymmetry, bias_mean, bias_std, valid) (SC‑003)  
  - **Verification**: CSV has 550 rows with a `valid` flag.  
- [ ] T023 [S] Implement `code/analysis/statistics.py::run_saturation_regression()` performing linear regression of bias vs. saturation fraction with Bonferroni correction; output `data/processed/saturation_stats.csv` (FR‑005, SC‑003)  
  - **Verification**: CSV includes `saturation_fraction`, `mean_bias`, `p_value`, `significant`, `slope`, `intercept`.  
- [ ] T022a [S] Add `run_us2_orchestration()` in `code/main.py` to drive loading, saturation, asymmetry measurement, and bias recording (FR‑001, FR‑008)  
  - **Verification**: CLI flag `--run-us2` completes without error.  
- [ ] T022b [S] Add `compute_saturation_bias()` in `code/main.py` that calls `run_saturation_regression()` and logs to `logs/saturation_bias.log`  
  - **Verification**: Log file contains “Saturation bias regression completed”.  

**Checkpoint**: US2 runs independently; all associated unit tests now pass.

---

## Phase 5: User Story 3 – Calibration Functions (Priority P3)

**Goal**: Fit regression models linking artifact intensity to bias, derive inverse correction functions, and validate them on held‑out synthetic data.

- [ ] T025 [P] Contract test `tests/contract/test_regression.py` verifying the schema of `data/processed/calibration_functions.json` (FR‑006)  
  - **Verification**: Test fails before implementation.  
- [ ] T026 [P] Unit test `tests/unit/test_validation.py::test_correction_application` ensuring that applying the inverse correction yields residual bias within the required tolerance (FR‑007)  
  - **Verification**: Test fails before implementation.  
- [ ] T027 [P] Implement `code/analysis/regression.py` to fit linear or polynomial models (auto‑select via AIC) for each metric‑artifact pair and store the chosen model parameters in `data/processed/calibration_functions.json` (FR‑005, FR‑006)  
  - **Verification**: JSON file contains keys `ellipticity_model` and `asymmetry_model` with `coefficients`, `model_type`, `r_squared`, `p_value`.  
- [ ] T041 [S] Implement `code/analysis/validation.py::aggregate_bias_data()` to merge `noise_sweep_data.csv` and `saturation_sweep.csv` into `data/processed/aggregated_bias.csv` (FR‑007)  
  - **Verification**: Aggregated CSV contains 700 rows (150 noise + 550 saturation).  
- [ ] T028 [S] Extend `code/analysis/validation.py::apply_corrections()` to use the calibration functions on a held‑out subset (20 % of synthetic images), compute residual bias statistics, and write `data/processed/validation_results.csv` (FR‑007)  
  - **Verification**: CSV includes `metric`, `residual_bias_mean`, `p_value`.  
- [ ] T029a [S] Add `run_us3_orchestration()` in `code/main.py` that calls aggregation, regression, and validation steps in sequence (FR‑001, FR‑008)  
  - **Verification**: CLI flag `--run-us3` completes and prints a summary.  
- [ ] T029b [S] Implement `apply_correction()` helper returning a dict with residual statistics (FR‑006, FR‑007)  
  - **Verification**: Function returns keys `residual_mean`, `residual_std`.  
- [ ] T030 [S] Implement `code/analysis/power_analysis.py` to compute post‑hoc power (≥ 80 % for n = 50) using observed effect size; write `data/validation/power_analysis_report.md` documenting observed effect size, calculated power, MDES, and any limitation (SC‑004)  
  - **Verification**: Report contains the required fields; if power < 80 % a “Limitation” paragraph is present.  
- [ ] T031 [S] Save final calibration functions to `data/processed/calibration_functions.json` and generate a short validation summary `data/processed/calibration_summary.md` linking to the regression and validation CSVs (SC‑002)  
  - **Verification**: JSON and markdown files exist and reference the correct CSVs.  

**Checkpoint**: All calibration steps are automated; regression models are persisted and validated on held‑out data.

---

## Phase N: Polish & Cross‑Cutting Concerns  

**Goal**: Improve documentation, code quality, and overall robustness.

- [ ] T032a [P] Update `quickstart.md` with sections on data generation, artifact injection, metric calculation, and how to run each user story via the CLI  
  - **Verification**: `quickstart.md` contains headings “Synthetic Data Generation”, “Inject Noise”, “Run US1”, etc.  
- [ ] T032b [P] Update `research.md` to include results tables, bias trend plots, and calibration performance discussion  
  - **Verification**: `research.md` contains a “Results” section with references to `figures/` files.  
- [ ] T033 [P] Refactor `code/main.py` into modular sub‑commands (`run-us1`, `run-us2`, `run-us3`) while preserving the `--run-all` convenience flag  
  - **Verification**: `python -m code.main run-us1` works and prints progress.  
- [ ] T034 [P] Optimise the full sensitivity sweep to finish < 4 h on 2 CPU cores (e.g., batch processing, memory‑mapped I/O)  
  - **Verification**: CI timing log shows total sweep < 4 h.  
- [ ] T035 [P] Add integration test `tests/integration/test_pipeline.py` that executes the complete pipeline (`--run-all`) on a fresh virtual environment and checks that the final calibration JSON exists and contains non‑empty coefficients  
  - **Verification**: `pytest -q tests/integration/test_pipeline.py` passes.  
- [ ] T038 [US2] Add a validation guard in `code/synthetic/artifacts.py` saturation logic that raises `ValueError` if clipping fraction exceeds 0.5 or results in zero total signal, preventing silent generation of unusable artifacts  
  - **Verification**: Unit test confirms the exception is raised for `fraction=0.6`.  
- [ ] T039 [US3] Enforce a zero‑intercept constraint in `code/analysis/regression.py` when artifact intensity = 0, ensuring baseline bias equals zero  
  - **Verification**: Model coefficients include `intercept = 0.0` (within tolerance).  
- [ ] T042 [US1] Refactor noise injection in `code/synthetic/artifacts.py` to validate that the measured σ matches the target within 1 % tolerance; raise `ValueError` otherwise (FR‑002)  
  - **Verification**: Test `test_noise_injection_sigma` now passes.  
- [ ] T043 [US2] Update saturation logic to log a warning and skip metric calculation for extreme levels (> 0.5) as defined in the Edge Cases (no crash, no NaNs) (FR‑003)  
  - **Verification**: Log contains “Saturation fraction 0.55 exceeds allowed maximum; skipping”.  
- [ ] T044 [US3] Enhance `code/analysis/regression.py` to automatically select between linear and quadratic models based on AIC (FR‑005)  
  - **Verification**: Regression JSON includes `"model_type": "quadratic"` when AIC favours it.  
- [ ] T045 [US3] Implement cross‑validation loop in `code/analysis/validation.py` to test calibration functions on a held‑out subset, reporting mean residual bias and confidence intervals (FR‑007)  
  - **Verification**: `validation_results.csv` contains columns `cv_fold`, `residual_mean`, `residual_ci_lower`, `residual_ci_upper`.  
- [ ] T046c [P] Wire full orchestration in `code/main.py`: `--run-all` executes US1 → US2 → US3 in order, aborting on any failure (FR‑001, FR‑008)  
  - **Verification**: CLI `--run-all` completes and prints “Pipeline completed successfully”.  

---

## Phase N+1: Review‑Resolution & Robustness Enhancements  

**Goal**: Address specific reviewer concerns about data flow, edge cases, and statistical rigor.

- [ ] T051 [S] Implement `validate_inputs()` in `code/main.py` that checks for `gt_metadata.json` before any US1/US2 execution; raise `FileNotFoundError` with a clear message if missing (replaces cancelled T047)  
  - **Verification**: Missing file triggers the expected exception.  
- [ ] T052 [S] Extend `code/analysis/power_analysis.py` to compute and report the Minimum Detectable Effect Size (MDES) in `power_analysis_report.md` (replaces cancelled T049)  
  - **Verification**: Report includes a line “Minimum Detectable Effect Size: …”.  
- [ ] T053 [S] Extend `code/io/writer.py` to generate `data/processed/run_manifest.json` capturing git commit, environment variables, artifact parameters, and timestamp (replaces cancelled T050)  
  - **Verification**: Manifest file exists and contains the required keys.  
- [ ] T054 [S] Update noise injection to detect “extreme” σ > 0.10, log a warning, and skip metric calculation for that image (replaces cancelled T048 part 1)  
  - **Verification**: Log entry “Noise σ = 0.12 exceeds maximum; skipping image …”.  
- [ ] T055 [S] Update saturation logic to detect “extreme” fraction > 0.5, log a warning, and skip metric calculation (replaces cancelled T048 part 2)  
  - **Verification**: Log entry as described in T043.  

---

## Phase N+2: Final Integration & Reporting  

**Goal**: Produce the final reproducible research artefacts and verify the entire pipeline end‑to‑end.

- [ ] T056 [S] Generate `docs/reports/001-final-bias-analysis.md` synthesising plots of bias vs. artifact intensity, regression tables, calibration functions, power‑analysis limitations, and qualitative HST validation results (SC‑001 – SC‑004)  
  - **Verification**: Report contains at least one figure (`figures/bias_vs_noise.png`) and references `calibration_functions.json`.  
- [ ] T057 [P] **Run code quality audit**: execute `ruff check .` and `black --check .`, capture the full textual reports in `logs/ruff_report.txt` and `logs/black_report.txt`, fix any reported issues, and commit the cleaned code (FR‑008)  
  - **Verification**: Both log files exist and contain “No issues found”.  
- [ ] T058 [P] **Refresh project documentation**: update `README.md`, `quickstart.md`, and `research.md` to reflect the latest implementation details, file locations, and CLI usage; ensure each file contains a “Generated on <date>” footer and cross‑references to the relevant code modules (FR‑008)  
  - **Verification**: Each markdown file includes the updated sections and the footer line.  
- [ ] T059 [P] Execute the full pipeline (`python -m code.main --run-all`) in a clean virtual environment and verify that it completes without manual intervention, producing all expected artefacts (calibration JSON, validation CSVs, reports, logs) (Constitution I)  
  - **Verification**: CI run logs show “Pipeline completed successfully” and all expected files are present.  

---

## Dependencies & Execution Order  

- **Setup (Phase 1)** → **Core Infrastructure (Phase 2)** → **User Stories (Phases 3‑5)** → **Polish (Phase N)** → **Review‑Resolution (Phase N+1)** → **Final Integration (Phase N+2)**.  
- Within each phase, tasks marked `[P]` may run in parallel; tasks marked `[S]` must respect the indicated predecessor order.  
- All scientific requirements (FR‑001 – FR‑009, SC‑001 – SC‑004) are satisfied by the tasks above.  

---  

*End of tasks.md*
