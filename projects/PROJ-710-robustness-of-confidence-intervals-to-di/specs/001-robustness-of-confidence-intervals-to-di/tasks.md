# Tasks: Robustness of Confidence Intervals to Differential Privacy Noise

**Inputs**: `spec.md`, `plan.md`, research idea, existing artifacts, and reviewer feedback.  
**Tests**: Unit and integration tests live in `code/tests/` and run after the tasks that implement the code they test.

This revision consolidates the prior 40+ task list into a bounded study and resolves all panel concerns.

## Phase 1: Setup and first end‑to‑end analysis

**Goal**: Fetch the real datasets, build the ground‑truth populations, and run one small end‑to‑end coverage measurement on real inputs early.

- [ ] T000 [P] Create a pinned `requirements.txt` (or `pyproject.toml`) in `code/` listing exact versions of all dependencies: `numpy`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `ucimlrepo`, and any other packages used. This satisfies the Constitution’s reproducibility requirement.

- [ ] T001 [P] Implement `code/config.py` with all study hyper‑parameters and seeds, and `code/data/fetch_real.py` that downloads the UCI Adult, Iris, and Wine Quality datasets using the `ucimlrepo` package (`fetch = ucimlrepo.fetch_ucirepo(id=…)` with Adult id=2, Iris id=53, Wine id=186). Files are saved under `data/raw/`. The fetch must raise `RuntimeError` on any failure (no synthetic fallback). **Verification**: `python -m code.data.fetch_real` exits 0 and `data/raw/` contains three CSV files with the expected column counts; a forced offline run raises an error. (FR‑001, Assumptions)

- [ ] T014 [P] After fetching, compute SHA‑256 checksums for each file in `data/raw/` and write them to `artifacts/checksums.txt`. This implements Principle III (Data Hygiene). **Verification**: checksum file exists and contains a line per raw file.

- [ ] T002 [P] Implement `code/data/synthetic_pop.py` that fits multivariate normal (or appropriate) parameters to the numeric columns of each real dataset from T001, then generates a synthetic population of `N = 1_000_000` rows on demand (streamed). Analytically compute the **true mean** of the target variable for each dataset and store the scalar value and the population size (`sample_size`) in a JSON file `artifacts/ground_truth_means.json` that conforms to `specs/001-robustness-of-confidence-intervals-to-di/contracts/dataset.schema.yaml`. Regression coefficients are stored as constants in `code/config.py` (not part of the schema). **Verification**: unit test `code/tests/test_synthetic_pop.py` checks that the `true_mean` matches the analytic mean within 0.01 SD and that the JSON validates against the schema.

- [ ] T003 [P] Implement `code/data/dp_noise.py` with `add_laplace_noise(arr, epsilon, sensitivity)` and `add_gaussian_noise(arr, epsilon, sensitivity)` using double‑precision NumPy. Laplace scale = sensitivity/ε; Gaussian σ = sensitivity·√(2·ln(1.25/δ))/ε with δ = 1e‑5. Clamp/log a warning if the scale exceeds the attribute range; reject ε ≤ 0 with a `ValueError`. **Verification**: `code/tests/test_dp_noise.py` validates calibration and error handling. (FR‑001, Edge Cases)

- [ ] T004 [P] Implement `code/analysis/ci_builder.py` (inner loop) and `code/main.py` (outer loop). Run a **pilot** for a single dataset (Adult‑synthetic), ε = 1.0, Laplace noise, statistic = Mean, with reduced `N_SIM = 50` and `B_BOOTSTRAP = 200`. The pilot writes its rows to `artifacts/pilot_coverage_results.csv` (schema‑conformant). Edge‑case handling: enforce `n ≥ 10` (raise otherwise) and drop perfectly collinear predictors with a logged warning. **Verification**: `code/tests/test_ci_builder.py` checks percentile bootstrap CI on a known Normal; `code/tests/test_coverage_pipeline.py` runs the pilot and asserts the CSV exists, validates schema, and that coverage rates lie in [0, 1]. Document the pilot command in `quickstart.md`. (FR‑003, US‑1, Edge Cases)

## Phase 2: Complete the study and validate its evidence

**Goal**: Full parameter sweep, adjustments, GLM analysis, sensitivity, and convergence checks.

- [ ] T005 [P] Implement `code/analysis/adjustments.py` providing `bias_correction` and `variance_inflation` derived from Covington et al. 2021 (arXiv:2110.14465) and Karwa & Vadhan 2017 (arXiv:1711.03908) for both mean and OLS settings. Expose `apply_adjustments(point_estimate, se, statistic_type, noise_params, n)`. Wire this into `ci_builder.py` so adjusted intervals are computed when requested. **Verification**: `code/tests/test_adjustments.py` checks both corrections against hand‑computed examples. (FR‑004, US‑2, SC‑002)

- [ ] T006 [P] Extend `code/main.py` to run the **full simulation grid**: all three datasets × 5 ε values × 2 noise types × 2 statistics (Mean, Regression) × 3 adjustment methods (None, BiasCorrected, VarianceInflated). Use `N_SIM = 1_000` and `B_BOOTSTRAP = 1_000`. Implement batched, vectorised resampling and process one condition at a time to keep peak RAM ≤ 7 GB. If runtime exceeds 6 h, automatically reduce `N_SIM` uniformly (not below the value giving SE ≤ 0.5 %) and record the reduction in the runtime log. All rows are written to `artifacts/coverage_results.csv` (schema‑conformant). **Verification**: run completes; row count equals `3 datasets × 5 ε × 2 noise × 2 stat × 3 adj × N_SIM`. A `artifacts/runtime_log.txt` records wall‑time and peak RSS. (FR‑001, FR‑003, FR‑007, SC‑004)

- [ ] T007 [P] Implement `code/analysis/glm_analysis.py`: load `artifacts/coverage_results.csv`, fit a binomial GLM `covered ~ epsilon + noise_type + epsilon:noise_type` using `statsmodels`. Raise a clear error if convergence fails. Write summary to `artifacts/glm_summary.json` conforming to `specs/001-robustness-of-confidence-intervals-to-di/contracts/glm_result.schema.yaml`. **Verification**: `code/tests/test_glm_analysis.py` fits the GLM on a synthetic subset and asserts convergence and valid p‑values; the real run produces the JSON with all required keys. (FR‑005, US‑3, SC‑003)

- [ ] T008 [P] Implement `code/analysis/sensitivity_analysis.py` that sweeps **exactly** the thresholds `{0.90, 0.93, 0.95}` (matching the spec) and counts, for each threshold, how many (dataset, statistic, ε, noise_type, adjustment) combinations achieve coverage ≥ threshold. Write results to `artifacts/sensitivity_analysis.csv`. Also implement `code/analysis/plotting.py` to generate `figures/coverage_vs_epsilon.png` (lines per noise type, error bars = binomial SE, panels per dataset/statistic) and `artifacts/coverage_summary.md` summarising coverage rates for every combination. **Verification**: plots/tables are produced directly from `coverage_results.csv`; the sweep output matches the three‑threshold grid. (FR‑006, US‑3, SC‑001, SC‑005)

- [ ] T009 [P] Implement `code/analysis/convergence_check.py` (no parallel‑safe tag). Re‑run a representative subset (all ε, both noise types, one dataset) with ≥ 3 different seeds, record the per‑condition standard error of coverage in `artifacts/convergence_check.csv`, and flag any condition with SE > 0.5 %. If flagged, increase `N_SIM` for that condition and re‑run automatically. **Verification**: CSV exists, all SE ≤ 0.5 % after any necessary re‑runs. (Constitution Principle VII)

- [ ] T012 [P] Add `specs/001-robustness-of-confidence-intervals-to-di/contracts/sensitivity_result.schema.yaml` defining the columns of `sensitivity_analysis.csv` (`threshold`, `passing_cases`, `variance`).  

- [ ] T013 [P] Add `specs/001-robustness-of-confidence-intervals-to-di/contracts/convergence_result.schema.yaml` defining the columns of `convergence_check.csv` (`dataset_name`, `epsilon`, `noise_type`, `statistic_type`, `adjustment_method`, `coverage_se`).  

- [ ] T010 [P] Implement `code/analysis/validate_artifacts.py` that validates **all** result artifacts (`ground_truth_means.json`, `coverage_results.csv`, `glm_summary.json`, `sensitivity_analysis.csv`, `convergence_check.csv`) against their respective JSON‑Schema files (including the two new schemas). Exit 0 on success. **Verification**: script returns 0; any schema violation raises an error. (Plan Phase 4, now fully executable)

- [ ] T011 [ ] Write `artifacts/research_results.md` summarising methods, coverage degradation versus ε, adjustment improvements, GLM p‑values, sensitivity‑sweep robustness, convergence evidence, and limitations. Every quantitative claim must cite a concrete artifact path (e.g., `artifacts/coverage_results.csv`, `artifacts/glm_summary.json`, `figures/coverage_vs_epsilon.png`). **Verification**: a lint script checks that every number is accompanied by a file reference and that all referenced files exist. (SC‑001 – SC‑005)

## Phase 3: Reproducible results and paper handoff

- Execution order (respecting data flow):  
  T000 → T001 → T014 → T002 → T003 → T004 (pilot) → T005 → T006 (full run) → T007 → T008 → T009 → T012 → T013 → T010 → T011.

- All computational work runs on CPU‑only hardware; no GPU code is present.

- Platform‑owned artifact hashing is handled automatically by the advancement‑evaluator; no project‑level script is needed.