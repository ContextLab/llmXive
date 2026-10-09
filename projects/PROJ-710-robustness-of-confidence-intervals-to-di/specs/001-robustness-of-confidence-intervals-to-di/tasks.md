# Tasks: Robustness of Confidence Intervals to Differential Privacy Noise

**Input**: `spec.md`, `plan.md`, research idea, existing artifacts, and reviewer feedback.  
**Tests**: Unit, integration, and end‑to‑end tests are defined in `code/tests/`. Tests run **after** the implementation tasks they depend on.

## Phase 1 – Setup & Quickstart (shared infrastructure)

- [ ] T001a [P] Create `code/utils/init_dirs.py` – atomically creates required directories: `code/`, `code/data/`, `code/analysis/`, `code/utils/`, `code/tests/`, `artifacts/`. **Verification**: script exits with status 0 and the directory tree exists.  
- [ ] T001b [P] Add empty `__init__.py` files to each package directory (`code/`, `code/data/`, `code/analysis/`, `code/utils/`, `code/tests/`). **Verification**: `python -c "import code"` succeeds.  
- [ ] T001c [P] Scaffold `code/config.py` with placeholders for hyper‑parameters, random seeds, and artifact paths.  
- [ ] T001d [P] Create `requirements.txt` pinned to stable CPU‑only versions of `numpy`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `pytest`, `ruff`, `black`.  
- [ ] T001e [P] Add `pyproject.toml` configuring `ruff` and `black` to match the pinned versions.  

## Phase 2 – Foundational (blocking prerequisites)

- [ ] T002 [P] Populate `code/config.py` with concrete hyper‑parameters (`N_sim = 1000`, `B = 1000`, `nominal_coverage_target = 0.95`), random seeds, and paths to ground‑truth parameters.  
- [ ] T003 [P] Implement `code/data/synthetic_pop.py` to generate three synthetic populations (Adult, Iris, Wine) each with **N = 1 000 000** rows. Save raw populations under `data/synthetic_populations/` and write the true means & OLS coefficients into `code/config.py` as `GROUND_TRUTH`.  
- [ ] T003b [P] Implement `code/data/synthetic_sampler.py` that draws i.i.d. samples from the synthetic populations defined in T003. Used by validation tasks.  
- [ ] T004 [P] Implement `code/data/dp_noise.py` exposing `add_laplace_noise(arr, epsilon, sensitivity)` and `add_gaussian_noise(arr, epsilon, sensitivity)`; both operate on CPU‑only `numpy` arrays.  
- [ ] T005 [P] Implement `code/utils/update_state.py` – computes SHA‑256 hashes of all files in `artifacts/` and writes a summary YAML under `state/`.  
- [ ] T006 [P] Add minimal package initializers `code/data/__init__.py` and `code/utils/__init__.py`.  
- [ ] T039 [P] Implement `code/data/download_utils.py` with **real, versioned URLs** for the UCI Adult, Iris, and Wine Quality CSVs (e.g., `[UNRESOLVED-CLAIM: https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data` — HTTP 404]). The script downloads each file into `data/raw/` and raises `DataFetchError` on any failure.  
- [ ] T040 [P] Refactor `code/data/download_utils.py` to **remove all fallback‑to‑synthetic logic**; the function now fails loudly if a download cannot be completed.  

## Phase 3 – User Story 1: Empirical Coverage Estimation (P1)

- [ ] T014b [US1] Create `code/analysis/edge_cases.py` with:
  - `clamp_noise_scale(noise_scale, data_range)` – clamps or logs a warning.
  - `enforce_min_sample_size(n, min_n=10)` – raises `ValueError` if `n < min_n`.
  - `detect_collinearity(X)` – drops one perfectly collinear predictor and logs the action.  
- [ ] T013a [US1] Implement outer‑loop simulation in `code/main.py`:
  1. Load **real** UCI datasets via `download_utils.py`.
  2. For each `(dataset, ε, noise_type)` condition, draw `N_sim = 1000` independent samples, add DP noise using `dp_noise.py`, then call the inner‑loop (T013b).  
  3. Compare each CI to the **ground‑truth** parameters from `code/config.py`.  
  4. Record per‑condition results.  
- [ ] T013b [US1] Implement inner‑loop in `code/analysis/ci_builder.py`:
  1. Receive a noisy sample.
  2. (Optionally) apply bias/variance adjustments (T020a).
  3. Perform `B = 1000` bootstrap resamples, compute the 95 % percentile CI for the statistic (mean or regression coefficient).  
  4. Return a boolean indicating coverage of the ground truth.  
- [ ] T013c [US1] Implement `code/analysis/result_writer.py` to atomically write rows to `artifacts/coverage_results.csv`. Schema: `dataset,epsilon,noise_type,statistic,coverage_rate,adjusted_coverage,adjustment_method,improvement_delta,seed_count`. The writer validates that a partially‑written CSV is not left on crash.  
- [ ] T015 [US1] Add unit test `code/tests/test_dp_noise.py` checking that Laplace and Gaussian scales match the theoretical calibration for several ε values.  
- [ ] T016 [US1] Add unit test `code/tests/test_ci_builder.py` verifying the percentile CI construction on a known distribution.  
- [ ] T017 [US1] Add integration test `code/tests/test_coverage_pipeline.py` that runs the outer‑loop for a single dataset/ε/noise_type and asserts that `artifacts/coverage_results.csv` contains a row with a coverage rate between 0 and 1.  

## Phase 4 – User Story 2: Bias‑Correction & Variance‑Inflation (P2)

- [ ] T020a [US2] Implement `code/analysis/adjustments.py`:
  - `bias_correction(point_estimate, noise_params)` – formula from Covington et al. 2021.  
  - `variance_inflation(se, noise_params, n)` – formula from Karwa & Vadhan 2017.  
  - Export `apply_adjustments(point_estimate, se, statistic_type, noise_params, n)` that dispatches the appropriate correction.  
- [ ] T021b [US2] Modify `ci_builder.py` to invoke `apply_adjustments` **after** noise injection and **before** bootstrap resampling.  
- [ ] T023 [US2] Unit test `code/tests/test_adjustments.py` for the bias‑correction implementation (compare against hand‑computed values).  
- [ ] T024 [US2] Unit test `code/tests/test_adjustments.py` for the variance‑inflation implementation.  

## Phase 5 – User Story 3: GLM Comparison & Visualization (P3)

- [ ] T026 [US3] Implement `code/analysis/glm_analysis.py`:
  - Load `artifacts/coverage_results.csv`.
  - Fit a binomial GLM: `covered ~ epsilon + noise_type + epsilon:noise_type` using `statsmodels`.  
  - Save raw model output to `artifacts/glm_raw.pkl`.  
- [ ] T027 [US3] Extract p‑values & coefficients from the GLM and write a concise JSON summary to `artifacts/glm_summary.json` (keys: `p_value_epsilon`, `p_value_noise_type`, `p_value_interaction`, `coefficients`, `deviance_residuals`).  
- [ ] T028 [US3] Create `code/analysis/plotting.py` that produces `artifacts/coverage_vs_epsilon.png` – line plot of coverage vs. ε for Laplace and Gaussian, with error bars (standard error). Uses `matplotlib`.  
- [ ] T029 [US3] Generate `artifacts/coverage_summary.md` – a Markdown table listing `dataset, statistic, ε, noise_type, coverage_rate, adjusted_coverage`.  
- [ ] T030 [US3] Add a validation step in `glm_analysis.py` that checks the response variable is binary and raises a clear error if the GLM fails to converge.  
- [ ] T031 [US3] Implement `code/analysis/sensitivity_analysis.py`:
  - Sweep coverage‑threshold values (e.g., 0.90, 0.93, 0.95, 0.97).
  - For each threshold, count how many datasets pass (mean coverage > threshold).  
  - Write `artifacts/sensitivity_analysis.csv` with columns `threshold,datasets_passing,count,delta_count`.  
- [ ] T032 [US3] Unit test `code/tests/test_glm_analysis.py` confirming that the GLM fits without warnings on a tiny synthetic subset.  

## Phase 6 – Polish & Cross‑Cutting Optimizations

- [ ] T033 [P] Implement `code/analysis/convergence_check.py` that runs the full outer‑loop with three different random seeds and asserts that the standard error of coverage across seeds is ≤ 0.5 %.  
- [ ] T034a [P] Refactor the outer‑loop in `code/main.py` to use a generator that yields one noisy sample at a time, limiting peak memory. Verify with `tracemalloc` that peak RAM < 7 GB.  
- [ ] T034b [P] Implement batched bootstrap resampling in `ci_builder.py`; benchmark with `tracemalloc` to keep RAM < 7 GB.  
- [ ] [ ] T035 [P] Integrate the batched resampling function from T034b into `code/main.py` so the outer‑loop streams samples directly into the batched bootstrap routine.  
- [ ] T036 [P] Update `projects/PROJ-710-robustness-of-confidence-intervals-to-di/README.md` with sections *Simulation Pipeline*, *Adjustment Methods*, and *Data Sources* (including the concrete URLs from T039).  
- [ ] T041 [P] Create `quickstart.md` (if missing) with a step‑by‑step guide: install dependencies, run `download_utils.py`, execute `code/main.py`, then run analysis scripts.  
- [ ] T043 [P] Add `code/utils/feasibility_check.py` that runs a micro‑benchmark (e.g., 10 % of `N_sim` with `B=100`) and estimates total runtime & memory. If projected runtime > 5.5 h or memory > 6.5 GB, exit with a clear warning.  

## Phase 7 – Execution Gate & Full Run

- [ ] T042a [P] Add a gate in `code/main.py` that imports `feasibility_check.py`; aborts execution with exit‑code 1 if the feasibility check fails.  
- [ ] T042 [P] Run the **full** simulation (`N_sim = 1000`, `B = 1000`) after the gate passes, producing the complete `artifacts/coverage_results.csv`.  

## Phase 8 – Verification, Reporting & Handoff

- [ ] T050 [P] Validate all artifact files (`coverage_results.csv`, `glm_summary.json`, `sensitivity_analysis.csv`, `coverage_summary.md`) against the JSON/YAML schemas in `contracts/`.  
- [ ] T051 [P] Execute an end‑to‑end run on a single ε (e.g., ε = 1.0) for the Adult dataset and verify that all intermediate CSV/JSON files are produced and contain plausible values.  
- [ ] T052 [P] Write `projects/PROJ-710-robustness-of-confidence-intervals-to-di/research_results.md` summarizing methods, key quantitative findings, and limitations.  
- [ ] T053 [P] Archive all generated artifacts into `artifacts/archive/` (timestamped zip) and push the archive to the repository.  
- [ ] T054 [P] Perform a reproducibility check: delete `artifacts/`, re‑run `quickstart.md` from a fresh clone, and confirm that the final `research_results.md` is identical (byte‑for‑byte) to the previous version.  

## Dependencies & Execution Order

| Phase | Prerequisite Tasks | Dependent Tasks |
|------|-------------------|-----------------|
| 1 – Setup | – | T001a → T001b → T001c → T001d → T001e |
| 2 – Foundational | T001a‑e | T002 → T003 → T003b → T004 → T005 → T006 → T039 → T040 |
| 3 – US 1 | Phase 2 | T014b → T013a → T013b → T013c → T015‑T017 |
| 4 – US 2 | Phase 2 (and T013b) | T020a → T021b → T023, T024 |
| 5 – US 3 | Phase 2 (and T013c) | T026 → T027 → T028 → T029 → T030 → T031 → T032 |
| 6 – Polish | Phases 1‑5 | T033 → T034a → T034b → T035 → T036 → T041 → T043 |
| 7 – Gate & Full Run | Phase 6 | T042a → T042 |
| 8 – Handoff | All prior phases | T050 → T051 → T052 → T053 → T054 |

*All `[X]` tasks are already verified. Unchecked tasks must be completed to achieve a fully reproducible end‑to‑end study.*
