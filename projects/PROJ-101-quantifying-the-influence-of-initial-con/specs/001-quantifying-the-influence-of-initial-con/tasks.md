# Tasks: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and any existing source files.  
All tasks are written as checklist items; unchecked items indicate work that still needs to be produced or verified.

---

## Phase 1 – Project bootstrap & reproducible environment  

- [ ] T001 Create the required top‑level directory layout and record it.  
  - **Paths**: `code/`, `code/simulation/`, `code/analysis/`, `code/utils/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `state/`  
  - **Verification**: Run `tree -L 2` and commit the generated file list (`dir_structure.txt`) under `state/`; CI checks that the file exists and contains all nine directories.

- [X] T002 [P] Add minimal package initialisation files so the Python package is importable.  
  - **Files**: `code/__init__.py`, `code/simulation/__init__.py`, `code/analysis/__init__.py`, `code/utils/__init__.py`, `tests/__init__.py`  
  - **Verification**: `python -c "import code"` runs without `ImportError`; CI runs a sanity test importing each sub‑module.

- [X] T003 [P] Configure pytest with a fixture suite that pins the random seed and provides a temporary directory for each test.  
  - **File**: `tests/conftest.py` containing `seed` fixture (value 42) and `tmp_path` fixture usage.  
  - **Verification**: `pytest -q` passes a dummy test that asserts `np.random.RandomState(42).rand()` is reproducible.

- [X] T004 [P] Write `quickstart.md` that documents the CLI entry point, the `--noise-levels` and `--N-values` arguments, and a minimal “run‑the‑pipeline” example.  
  - **Path**: `quickstart.md`  
  - **Verification**: CI renders the markdown to HTML and checks that the two argument names appear in the file.

- [X] T005 [P] Update `README.md` with full pipeline instructions (environment setup, data generation, baseline computation, FTLE sweep, regression, visualisation, and final report).  
  - **Path**: `README.md`  
  - **Verification**: CI runs `make docs` (or equivalent) and confirms that the README contains the section headings “Step 1 – Generate trajectories”, “Step 2 – Compute baseline”, etc.

---

## Phase 2 – Synthetic trajectory generation (User Story 1, P1)  

- [ ] T006 [P] Implement the coupled Lorenz system and a trajectory generator that uses `scipy.integrate.solve_ivp` with method **'DOP853'**, `rtol=1e-9`, `atol=1e-12`, and injects additive Gaussian noise of user‑specified standard deviation `σ_noise`.  
  - **File**: `code/simulation/generator.py` (functions `lorenz_ode`, `generate_trajectory`).  
  - **Verification**: Unit tests in `tests/unit/test_generator.py` check (a) that the empirical noise standard deviation matches the injected `σ_noise` within 5 %; (b) that a noise‑free trajectory matches a reference integration to < 1e‑9 absolute error.

- [ ] T007 [P] Add a boundedness / unphysical‑trajectory guard that raises `UnphysicalTrajectoryError` if any state norm exceeds **20.0** and a warning `HighNoiseWarning` if `σ_noise > 0.1`. The guard lives in `code/utils/stability.py`.  
  - **File**: `code/utils/stability.py` (functions `check_boundedness`, `raise_if_unphysical`).  
  - **Verification**: Tests in `tests/unit/test_generator.py` assert that trajectories with `σ_noise=1.5` raise the appropriate error.

- [ ] T008 [P] Implement the generation loop in `code/main.py` (CLI entry point). It must accept `--N-values` and `--noise-levels`, iterate over `N ∈ {3, 5}` and the **noise list limited to the specification maximum σ ≤ 1.0** (`[0.0001, 0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 0.8, 1.0]`), and for each combination run **k** trials (`k=50` if `σ_noise < 0.01` else `k=30`).  
  - **Output**: Immutable `.npz` files saved as `data/raw/trajectory_N{N}_sigma{sigma}_trial{t}.npz`.  
  - **Verification**: Integration test `tests/integration/test_generation.py` runs the CLI with a reduced set (`N=3`, two noise levels, `k=2`) and checks that the expected number of files appear in `data/raw/`.

---

## Phase 3 – Baseline computation & FTLE sweep (User Story 2, P2)  

- [ ] T009 [P] Implement `code/analysis/baseline.py` that computes the asymptotic Lyapunov exponent for a clean system using Rosenstein’s algorithm on a long trajectory (≥ 50 000 steps). Convergence is declared when the relative change between successive estimates at `T=5000` is < 5 %. Abort with `NonChaoticSystemError` if the resulting exponent ≤ 0.  
  - **Output**: `data/processed/baseline_{N}.json` conforming to `baseline.schema.yaml`.  
  - **Verification**: Unit test `tests/unit/test_baseline.py` checks that (i) the JSON file exists, (ii) `status == "valid"`, and (iii) `lambda_max > 0`.

- [ ] T011 [P] Add a gating step in `code/main.py` that loads the baseline JSON, verifies `status == "valid"` and that the system is chaotic before any noisy FTLE computation is launched. If the gate fails, the pipeline aborts with a clear error message.  
  - **Verification**: CI runs the pipeline with a deliberately non‑chaotic parameter set (e.g., `rho = 20`) and checks that the process exits with exit code 1 and prints the expected error.

- [ ] T017 [P] Compute a clean finite‑time baseline for each window size `T` used in FTLE analysis (e.g., 500, 1000, 5000). Store results in `data/processed/baseline_per_window_{N}.json`, an array of objects each containing `window_size`, `lambda_max`, and `convergence_error`. Verify that the baseline for every `T` satisfies the < 5 % error criterion.  
  - **Verification**: Unit test `tests/unit/test_per_window_baseline.py` checks that the JSON file contains entries for all required windows and that each entry has `status == "valid"`.

- [ ] T010 [P] Implement `code/analysis/ftle.py` that (a) loads each raw trajectory, (b) propagates the tangent linear model with QR re‑orthonormalisation, (c) evaluates FTLE over sliding windows `T ∈ {500, 1000, 5000}` while enforcing `T < total_length - 10`, and (d) records a `status` flag (`valid`, `unphysical`, `non‑chaotic`).  
  - **Output**: Aggregated results written to `data/processed/ftle_results.json` (schema `ftle_results.schema.yaml`).  
  - **Verification**: Unit test `tests/unit/test_ftle.py` confirms that (i) the JSON file is non‑empty, (ii) for a clean trajectory the FTLE at `T=5000` is within 5 % of the baseline, and (iii) no `NaN`/`Inf` values appear.

---

## Phase 4 – Statistical modelling, regression and visualisation (User Story 3, P3)  

- [ ] T012 [P] Implement `code/analysis/regression.py` that (a) merges `ftle_results.json` with the appropriate baseline (using per‑window baseline from T017), (b) computes the deviation Δλ = λ_FTLE − λ_baseline for every **bounded** trial, (c) fits a mixed‑effects Multiple Linear Regression  
  ```
  Δλ  ~  σ_noise + N + σ_noise·N + 1/T  + (1|trial_id)
  ```  
  using `statsmodels`. It must (d) apply the Benjamini‑Hochberg FDR correction (q ≤ 0.05) to all coefficients, (e) run the Durbin‑Watson test on each FTLE time‑series and, if autocorrelation is detected (p < 0.05), recompute standard errors with Newey‑West HAC, and (f) always fit a Tobit censored regression on the full dataset (including unphysical points) to estimate the latent bias.  
  - **Outputs**: `data/processed/regression_results.json` (schema `regression_results.schema.yaml`) and an augmented `data/processed/results.json` that includes the primary regression coefficients, their p‑values, q‑values, effect size, `newey_west_used` flag, and `escape_probability` mapping.  
  - **Verification**: Unit test `tests/unit/test_regression.py` generates a synthetic dataset with a known σ_noise effect, runs the module, and asserts that (i) the σ_noise coefficient is significant (p < 0.05), (ii) its q‑value ≤ 0.05, and (iii) the scaling exponent for system dimension is present and finite.

- [ ] T013 [P] Implement `code/analysis/plotting.py` that produces three PNG figures:  
  1. **Convergence plot** – FTFT λ vs. window size T for three representative noise levels (σ = 0, 0.01, 0.1).  
  2. **Bias‑scaling plot** – Δλ vs. σ_noise with error bars (standard error of the mean).  
  3. **Dimension‑scaling plot** – Δλ vs. system dimension N, annotated with the fitted scaling exponent.  
  - **Paths**: `data/processed/plots/convergence.png`, `data/processed/plots/bias_scaling.png`, `data/processed/plots/dimension_scaling.png`.  
  - **Verification**: Integration test `tests/integration/test_plotting.py` runs the full pipeline on a tiny dataset and checks that each PNG file exists and has non‑zero file size.

---

## Phase 5 – Performance optimisation, manifest & final report  

- [ ] T014 [P] Parallelise (a) the trajectory generation loop (Task T008) and (b) the FTLE sweep (Task T010) using `multiprocessing.Pool` with `max_workers=4`. Record a benchmark log (`benchmark.log`) showing wall‑clock time before and after optimisation for the full configuration (`N=5`, all noise levels).  
  - **Verification**: CI parses `benchmark.log` and asserts that the “after” runtime is ≤ 80 % of the “before” runtime.

- [ ] T015 [P] Create a manifest file `state/artifacts/manifest.yaml` that records the SHA‑256 checksum of every file under `data/` (raw trajectories, processed JSONs, PNGs). Add a CI test `tests/unit/test_manifest.py` that recomputes the checksums and fails if any mismatch is found.  
  - **Verification**: CI runs the test and passes on the committed repository.

- [ ] T018 [P] Run the full pipeline on a representative configuration (e.g., N=5, σ_noise ∈ {0.01,0.1,0.5}, 10 trials each), record total wall‑clock time, and fail the task if the runtime exceeds 45 minutes. Store the timing report in `data/processed/runtime_report.json`. This task directly verifies **SC‑004**.  
  - **Verification**: CI checks that `runtime_report.json` contains a `total_seconds` field ≤ 2700 (45 min) and fails otherwise.

- [ ] T016 [P] Write the final scientific report `data/processed/final_report.md`. It must contain four mandatory sections:  
  1. **Convergence validation (SC‑001)** – summarise baseline convergence statistics.  
  2. **Bias‑scaling relationship (SC‑002)** – present regression coefficients, scaling law, and plots.  
  3. **Statistical significance (SC‑003)** – list p‑values, effect sizes, and FDR‑adjusted q‑values.  
  4. **Dimension scaling (US‑3 Scenario 3)** – report the exponent linking system dimension to bias magnitude.  
  The report should also embed the artifact checksums from the manifest.  
  - **Verification**: A CI step runs a simple script that extracts the four section headers from the markdown and fails if any are missing.

---

### Dependency & execution order summary  

| Task | Depends on |
|------|------------|
| T001‑T005 | – (bootstrap) |
| T006‑T008 | T001‑T005 |
| T009‑T011 | T006‑T008 |
| T017 | T009 (needs clean baseline) |
| T010 | T011 (gating) |
| T012‑T013 | T009‑T011, T017 |
| T014 | T006‑T010 (generation & FTLE) |
| T015 | All previous data‑producing tasks (T008, T010, T012, T013) |
| T018 | T014‑T015 (optimisation, manifest, analysis) |
| T016 | T012‑T015 (analysis, manifest, plots) |

Running `python -m code.main --run-all` (as documented in `quickstart.md`) will execute the tasks in the correct order, respecting the gating logic and parallelisation.
