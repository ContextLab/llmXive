# Tasks: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Inputs**: `spec.md`, `plan.md`, `research.md`, data‑model, contracts, and any existing source files.  
All tasks are written as checklist items; unchecked items indicate work that still needs to be produced or verified.

---

## Phase 1 – Project bootstrap & reproducible environment  

- [ ] T001 Create the required top‑level directory layout **under project‑owned paths only** (`code/`, `data/`, `tests/`). Write a plain‑text manifest of the layout (`data/dir_structure.txt`) and verify it with a CI step that runs `tree -L 2` and checks that the file exists and contains the nine expected directories.  
  - **Paths**: `code/`, `code/simulation/`, `code/analysis/`, `code/utils/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `data/processed/plots/`  
  - **Verification**: CI runs `cat data/dir_structure.txt` and asserts each directory name appears.

- [ ] T002 [P] Add minimal package initialisation files so the Python package is importable.  
  - **Files**: `code/__init__.py`, `code/simulation/__init__.py`, `code/analysis/__init__.py`, `code/utils/__init__.py`, `tests/__init__.py`  
  - **Verification**: `python -c "import code"` runs without `ImportError`; CI imports each sub‑module.

- [ ] T003 [P] Configure pytest with a fixture suite that pins the random seed and provides a temporary directory for each test.  
  - **File**: `tests/conftest.py` containing a `seed` fixture (value 42) and using the built‑in `tmp_path` fixture.  
  - **Verification**: `pytest -q` passes a dummy test that asserts reproducibility of `np.random.RandomState(42).rand()`.

- [ ] T004 [P] Write `quickstart.md` that documents the CLI entry point, the `--noise-levels` and `--N-values` arguments, and a minimal “run‑the‑pipeline” example.  
  - **Path**: `quickstart.md`  
  - **Verification**: CI renders the markdown and checks that the two argument names appear in the file.

- [ ] T005 [P] Update `README.md` with full pipeline instructions (environment setup, data generation, baseline computation, FTLE sweep, regression, visualisation, and final report).  
  - **Path**: `README.md`  
  - **Verification**: CI runs a documentation lint step that confirms the presence of the section headings “Step 1 – Generate trajectories”, “Step 2 – Compute baseline”, “Step 3 – FTLE sweep”, “Step 4 – Statistical analysis”, and “Step 5 – Figures”.

---

## Phase 2 – Synthetic trajectory generation (User Story 1, P1)  

- [ ] T006 [P] Implement the coupled Lorenz system and a trajectory generator (`code/simulation/generator.py`) that uses `scipy.integrate.solve_ivp` with method **'DOP853'**, `rtol=1e-9`, `atol=1e-12`; inject additive Gaussian noise with user‑specified `sigma_noise`; **emit a `HighNoiseWarning` when `sigma_noise > 0.1`**; **raise `UnphysicalTrajectoryError` when any state norm exceeds 20.0**.  
  - **Verification**: Unit tests in `tests/unit/test_generator.py` (a) compare empirical noise std‑dev to the injected `sigma_noise` within 5 %; (b) confirm a noise‑free trajectory matches a reference integration to < 1e‑9 absolute error; (c) check that `HighNoiseWarning` is raised for `sigma_noise = 0.2`; (d) check that `UnphysicalTrajectoryError` is raised for `sigma_noise = 1.5`.

- [ ] T007 [P] Wire the stability guard from `code/utils/stability.py` into the generation pipeline so that `raise_if_unphysical` is called after integration and `check_noise_level` triggers the warning. Update `code/simulation/generator.py` to import and use these helpers.  
  - **Verification**: The same unit tests as T006 must pass, demonstrating that the guard is exercised during trajectory creation.

- [ ] T008 [P] Implement the CLI generation loop in `code/main.py` (exposed as `python -m code.main`). It must accept `--N-values` and `--noise-levels`, iterate over the grid `N ∈ {3,5,7}` and `sigma_noise ∈ {0.0001,0.001,0.01,0.05,0.1,0.2,0.5,0.8,1.0}`, run `k` trials (`k=50` for `sigma_noise < 0.01`, otherwise `k=30`), and **write each trajectory as an immutable `.npz` file under `data/raw/trajectory_N{N}_sigma{sigma}_trial{t}.npz`**.  
  - **Verification**: Add an integration test `tests/integration/test_generation.py` that invokes the CLI with a reduced configuration (`N=3`, two noise levels, `k=2`) and asserts that the expected number of `.npz` files appear in `data/raw/` and that each file validates against `contracts/trajectory.schema.yaml`.

---

## Phase 3 – Baseline computation (User Story 2, P2)  

- [ ] T009 [P] Implement `code/analysis/baseline.py` to (a) generate **≥ 5** noise‑free trajectories of length **≥ 50 000** steps for each system dimension `N`; (b) compute the asymptotic Lyapunov exponent using Rosenstein’s method; (c) **declare the baseline `valid` only when the relative error between estimates at `T=5000` and `T=20 000` is ≤ 1 % and the 95 % CI width ≤ 0.01**; (d) **run an independent RK45 integration (`rtol=1e-10`, `atol=1e-13`) to cross‑validate the Rosenstein result**; (e) abort with `NonChaoticSystemError` if the resulting exponent ≤ 0.  
  - **Outputs**:  
    - `data/processed/baseline_{N}.json` (single asymptotic exponent, `status: "valid"`).  
    - `data/processed/baseline_per_window_{N}.json` – JSON array with entries for **all FTLE windows used later** (`{500, 1000, 5000}`), each object containing `{window_size, lambda_mean, lambda_std, convergence_error}`.  
    - `data/processed/baseline_rk45_{N}.json` (RK45 cross‑validation result, for internal verification only).  
  - **Verification**: Unit tests `tests/unit/test_baseline.py` check that (i) the JSON files exist, (ii) `status == "valid"`, (iii) `lambda_max > 0`, (iv) each per‑window entry satisfies `convergence_error ≤ 1`, and (v) the RK45 baseline is within 0.5 % of the Rosenstein baseline.

---

## Phase 4 – FTLE computation (User Story 2, P2)  

- [ ] T011 [P] Implement `code/analysis/ftle.py` that (a) loads each raw trajectory, (b) propagates the tangent linear system alongside the state, (c) performs **QR re‑orthonormalisation** at every integration step, (d) evaluates FTLE over sliding windows `T ∈ {500, 1000, 5000}` while enforcing `T < total_length – 10`, (e) records a `status` field (`"valid"`, `"unphysical"`, `"non‑chaotic"`), (f) computes a Durbin‑Watson p‑value for the FTLE time‑series, (g) **writes an aggregated file `data/processed/ftle_results.json` conforming to `contracts/ftle_results.schema.yaml`**.  
  - **Verification**: Unit tests `tests/unit/test_ftle.py` assert that (i) the JSON file is non‑empty, (ii) for a clean trajectory the FTLE at `T=5000` is within 5 % of the asymptotic baseline, (iii) no `NaN`/`Inf` values appear, (iv) each entry includes the required fields (`trial_id`, `system_dimension`, `noise_level`, `window_size`, `lambda_max`, `deviation`, `status`, `timestamp`, `durbin_watson_p`), and (v) the status field matches the `"valid"` baseline status.

---

## Phase 5 – Statistical modelling & visualisation (User Story 3, P3)  

- [ ] T012 [P] Implement `code/analysis/regression.py` that (a) merges `ftle_results.json` with the appropriate per‑window baseline, (b) computes the deviation Δλ = λ_FTLE – λ_baseline for every **bounded** trial, (c) **fits a mixed‑effects linear model** on the bounded subset (`Δλ ~ sigma_noise + N + sigma_noise:N + 1/T + (1|trial_id)`) using `statsmodels.MixedLM`, (d) **computes the Pearson correlation** between absolute Δλ and `sigma_noise` and **asserts r ≥ 0.8 with p < 0.05** (this satisfies SC‑002), (e) applies the Benjamini‑Hochberg FDR correction (`q ≤ 0.05`) to all fixed‑effect p‑values, (f) runs the Durbin‑Watson test on each FTLE series and, if `p < 0.05`, recomputes standard errors with Newey‑West HAC, (g) incorporates baseline variance (`lambda_std`) as observation‑level weights, and (h) records the escape probability per noise level.  
  - **Outputs**:  
    - `data/processed/regression_results.json` (conforms to `contracts/regression_results.schema.yaml`).  
    - `data/processed/regression_stats.json` (conforms to `contracts/regression_stats.schema.yaml`).  
    - Updated `data/processed/results.json` bundling all artifacts.  
  - **Verification**: Unit test `tests/unit/test_regression.py` generates a synthetic dataset with a known σ_noise effect, runs the module, and checks that (i) the σ_noise coefficient is significant (`p < 0.05`), (ii) its BH‑adjusted q‑value ≤ 0.05, (iii) the Pearson correlation assertion passes, (iv) the `newey_west_used` flag is set correctly when autocorrelation is detected, and (v) `regression_stats.json` validates against its schema.

- [ ] T012a [P] (sub‑task of T012) Compute Pearson correlation `r` between `|Δλ|` and `sigma_noise` and assert `r ≥ 0.8` with `p < 0.05`. Fail the pipeline if the condition is not met.  
  - **Verification**: Included in `tests/unit/test_regression.py`.

- [ ] T012b [P] Serialize regression summary statistics to `data/processed/regression_stats.json` matching `regression_stats.schema.yaml`.  
  - **Verification**: CI validates the JSON against the schema.

- [ ] T013 [P] Implement `code/analysis/plotting.py` that creates three PNG figures saved under `data/processed/plots/`:  
  1. **Convergence plot** – λ vs. window size `T` for three noise levels (σ = 0, 0.01, 0.1).  
  2. **Bias‑scaling plot** – Δλ vs. σ_noise with error bars representing the standard error of the mean.  
  3. **Dimension‑scaling plot** – Δλ vs. system dimension `N` on log‑log axes, annotated with the fitted power‑law exponent.  
  - **Verification**: Integration test `tests/integration/test_plotting.py` runs the full pipeline on a tiny dataset and asserts that each PNG file exists, is readable, and has non‑zero file size.

---

## Phase 6 – Performance optimisation & runtime validation  

- [ ] T014 [P] Parallelise (a) the trajectory‑generation loop (Task T008) and (b) the FTLE sweep (Task T011) using `multiprocessing.Pool` (max 4 workers). Record a benchmark log `data/processed/benchmark.log` that shows wall‑clock time before and after optimisation for the full configuration (`N=5`, all noise levels, `k=30`). Then run the complete pipeline once more and produce `data/processed/runtime_report.json` containing the total elapsed seconds; the CI must assert that this value is **≤ 2700 s** (45 min) to satisfy **SC‑004**.  
  - **Verification**: CI parses `benchmark.log` to confirm the “after” runtime is ≤ 80 % of the “before” runtime, and checks `runtime_report.json.total_seconds ≤ 2700`.

---

## Phase 7 – Final scientific report & hand‑off  

- [ ] T015 [P] Write the final scientific report `data/processed/final_report.md`. It must contain the four mandatory sections required by the success criteria:  
  1. **Convergence validation (SC‑001)** – summary of baseline convergence statistics and RK45 cross‑validation.  
  2. **Bias‑scaling relationship (SC‑002)** – regression coefficients, Pearson‑r assertion, scaling law, and relevant plots.  
  3. **Statistical significance (SC‑003)** – p‑values, effect sizes, BH‑adjusted q‑values, and Newey‑West usage flag.  
  4. **Dimension scaling (US‑3 Scenario 3)** – exponent linking system dimension to bias magnitude.  
  The report should also embed the SHA‑256 checksums of all result artifacts (taken from the platform‑generated manifest) and a brief methods description linking each analysis step to the corresponding task IDs.  
  - **Verification**: CI runs a lightweight script that extracts the four section headers from the markdown and fails if any are missing; it also checks that the checksum table contains an entry for each file in `data/processed/`.

---  

### Dependency & execution order summary  

| Task | Depends on |
|------|------------|
| T001‑T005 | – (bootstrap) |
| T006‑T008 | T001‑T005 |
| T009 | T006‑T008 |
| T011 | T009 (baseline availability) |
| T012, T012a, T012b, T013 | T009, T011 |
| T014 | T006‑T011 (generation & FTLE) |
| T015 | T012‑T014 (analysis, benchmark, runtime) |

Running the full pipeline with the documented command  

```bash
python -m code.main --run-all
```  

will execute the tasks in the correct order, respecting gating logic, parallelisation, and verification checkpoints.  
