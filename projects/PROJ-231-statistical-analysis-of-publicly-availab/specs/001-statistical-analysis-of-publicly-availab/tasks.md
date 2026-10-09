# Tasks: Statistical Analysis of Publicly Available Climate Model Output Ensembles  

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, and reviewer feedback.  
**Goal**: Implement a reproducible end‑to‑end pipeline that ingests CMIP6 temperature & precipitation data, converts each ensemble member to a smooth functional representation, extracts dominant spatiotemporal modes via functional PCA, and assesses their robustness with **bootstrap resampling (≥ 100 iterations)**. All artefacts must be real (no synthetic stand‑ins) and verifiable by automated tests.

---

## Phase 0 – Project scaffolding (must exist before any scientific work)

- [ ] **T001** Create project‑root `projects/PROJ-231-statistical-analysis-of-publicly-availab/` with the following sub‑directories and placeholder files:  
  - `code/__init__.py`  
  - `data/raw/.gitkeep`  
  - `data/processed/.gitkeep`  
  - `data/artifacts/.gitkeep`  
  - `tests/unit/.gitkeep`  
  - `tests/contract/.gitkeep`  
  - `contracts/` (empty for now)  
  *Verification*: `tree -L 3 projects/PROJ-231-statistical-analysis-of-publicly-availab/` lists all directories and `.gitkeep` files.

- [ ] **T002** Add a project‑level `.gitignore` that excludes `data/raw/`, `data/processed/`, `data/artifacts/`, compiled artefacts, and Python caches.  
  *Verification*: `git check-ignore -v data/raw/*` returns a matching rule.

- [ ] **T003** Initialise `requirements.txt` with exact versions (pinned) for: `pandas`, `numpy`, `scipy`, `xarray`, `datasets`, `scikit-learn`, `scikit-fda`, `matplotlib`, `seaborn`, `pyyaml`, `black`, `ruff`, `pytest`.  
  *Verification*: `pip install -r requirements.txt` succeeds on a fresh environment.

- [ ] **T004** Write `quickstart.md` that documents a single command to run the full pipeline on a tiny test subset (e.g., three models) and points to the expected output directories.  
  *Verification*: Executing the command in a fresh clone produces `data/artifacts/end_to_end_demo/` with at least one PNG plot and a JSON summary.

---

## Phase 1 – Foundational utilities (blocking prerequisite for all user stories)

- [ ] **T005** Create `code/config.py` containing:  
  - Global random seed (`SEED = 42`)  
  - Paths (`RAW_DIR`, `PROCESSED_DIR`, `ARTIFACTS_DIR`)  
  - Hyper‑parameters (`B_SPLINE_K_RANGE = (10, 20)`, `VARIANCE_THRESHOLD = 0.80`, `STABLE_CORR_THRESHOLD = 0.95`, `BOOTSTRAP_ITER = 100`)  
  *Verification*: Importing `config` yields the expected attributes.

- [ ] **T006** Implement `code/update_state.py` that:  
  1. Recursively hashes every file in `data/processed/` and `data/artifacts/` (SHA‑256).  
  2. Writes a YAML state file `state/projects/PROJ-231-statistical-analysis-of-publicly-availab.yaml` with a mapping `artifact_hashes:` and a timestamp `updated_at:`.  
  *Verification*: After running the script, the state file exists and the hash values change when any artefact is modified.

- [ ] **T007** Add `code/logging_config.py` that configures a JSON‑formatted logger (INFO, DEBUG, ERROR) writing to `logs/pipeline.log`.  
  *Verification*: Importing the logger and emitting a test record creates a valid JSON line in the log file.

- [ ] **T008** Define JSON‑schema files in `contracts/`:  
  - `dataset.schema.yaml` (raw CMIP6 schema)  
  - `output.schema.yaml` (processed coefficients & FPCA outputs)  
  Implement `tests/contract/test_schemas.py` that validates files against these schemas using `jsonschema`.  
  *Verification*: Running `pytest tests/contract/test_schemas.py` passes on the reference artefacts.

---

## Phase 2 – User Story 1: Data ingestion & functional representation (Priority P1)

- [ ] **T009** Implement `code/ingestion.py` to:  
  1. Download CMIP6 temperature & precipitation files via the HuggingFace `datasets` library (`sungduk/wip_cmip6`).  
  2. Stream data (`streaming=True`) when the total size exceeds 7 GB, writing each model’s raw NetCDF to `data/raw/{model}.nc`.  
  *Verification*: After execution, `data/raw/` contains at least one `.nc` file and a log entry confirming successful download.

- [ ] **T010** Within `ingestion.py`, add spline‑based missing‑value imputation:  
  - Use `scipy.interpolate.CubicSpline` on each time series (per grid point).  
  - If `CubicSpline` raises, fall back to `interp1d(kind='linear')`.  
  - Log any model‑time‑step pairs that required the linear fallback.  
  *Verification*: The log file `logs/pipeline.log` contains entries with the phrase “linear fallback”.

- [ ] **T011** Standardise spatial resolution to a 1° × 1° grid using `xarray` bilinear interpolation; write the harmonised dataset to `data/processed/standardized_{model}.parquet`.  
  *Verification*: The parquet file can be opened with `pandas.read_parquet` and contains the expected coordinates.

- [ ] **T012** Implement `code/basis.py`:  
  1. Pilot GCV/AIC over the candidate range `K = 10…20` on a **global** pilot series (one representative grid point).  
  2. If optimisation fails, default to `K = 15`.  
  3. Perform B‑spline expansion for every processed model, saving coefficients as `data/processed/coeffs_{model}.npz`.  
  *Verification*: Each `.npz` file contains arrays `knots`, `coeffs`, and the chosen `K`.

- [ ] **T013** Verify reconstruction quality: for each model, reconstruct the time series from its coefficients, compute MSE against the standardized data, and assert `MSE ≤ 0.01`. Write a summary CSV `data/artifacts/reconstruction_errors.csv`.  
  *Verification*: The CSV exists and all rows have `mse <= 0.01`.

- [ ] **T014** After all coefficient files are written, invoke `code/update_state.py` to record the new hashes.  
  *Verification*: The state YAML’s `artifact_hashes` entry includes the hashes of all `coeffs_*.npz` files.

- [ ] **T015** Write unit tests in `tests/unit/test_ingestion.py` that (a) mock a tiny NetCDF with missing timestamps, (b) assert the imputation fallback logs correctly, and (c) fail before the actual implementation is present.  
  *Verification*: Running `pytest tests/unit/test_ingestion.py` results in at least one failing test.

---

## Phase 3 – User Story 2: Dominant mode extraction via fPCA (Priority P2)

- [ ] **T016** Implement `code/fpca.py` to:  
  1. Load all `coeffs_*.npz` files.  
  2. Stack them into a functional data matrix compatible with `scikit‑fda`.  
  3. Run `skfda.exploratory.fpca.FPCA` and obtain eigenvalues, eigenfunctions, and component scores.  
  *Verification*: The script prints the first five eigenvalues and saves intermediate objects.

- [ ] **T017** Compute cumulative variance explained; stop adding components once the cumulative sum reaches **≥ 80 %** (or the user‑defined `VARIANCE_THRESHOLD`). Write `data/processed/variance_metrics.json` with keys: `components`, `cumulative_variance`, `threshold_used`, `stopped_early`.  
  *Verification*: The JSON file exists and `cumulative_variance[-1] >= 0.80`.

- [ ] **T018** Persist results:  
  - `data/processed/eigenvalues.npy` (1‑D array)  
  - `data/processed/eigenfunctions.npy` (3‑D array: component × grid × time)  
  - `data/processed/component_scores.npy` (ensemble × component)  
  *Verification*: Each `.npy` file loads without error and dimensions match expectations.

- [ ] **T019** Add unit tests in `tests/unit/test_fpca.py` that (a) load a tiny synthetic coefficient set, (b) run `fpca.py`, and (c) check that the variance JSON contains the `stopped_early` flag. Tests must initially fail.  
  *Verification*: `pytest tests/unit/test_fpca.py` reports failing tests before implementation.

- [ ] **T020** Create visualisations of the top three eigenfunctions (spatiotemporal patterns) in `code/visualize.py`; save PNGs to `data/artifacts/mode_{i}.png` and a combined PDF `data/artifacts/modes_summary.pdf`. Include **bootstrap‑derived uncertainty bands** (computed later).  
  *Verification*: The PNG files open and display a heat‑map with a color bar; the PDF contains three pages.

---

## Phase 4 – User Story 3: Robustness assessment via **Bootstrap** resampling (Priority P3)

- [ ] **T021** Implement `code/robustness.py` – **Bootstrap baseline**: run `fpca.py` on the full ensemble and store eigenfunctions as `data/artifacts/baseline_eigenfunctions.npy`.  
  *Verification*: The baseline file exists and matches the eigenfunctions from Phase 3.

- [ ] **T022** Implement the **bootstrap loop**: for `i` in `1 … BOOTSTRAP_ITER` (≥ 100), randomly sample **with replacement** a subset of ensemble members (same size as the full ensemble), recompute fPCA, align eigenfunctions to the baseline via Procrustes (`scipy.linalg.orthogonal_procrustes`), and store loading correlations per component.  
  *Verification*: After execution, log entries `Bootstrap iteration {i} completed` appear for all iterations.

- [ ] **T023** Validate iteration count: automatically compare the number of bootstrap iterations recorded in `logs/pipeline.log` to the required `BOOTSTRAP_ITER`. Write a short report `data/artifacts/bootstrap_iteration_report.txt` stating “Expected = BOOTSTRAP_ITER, Observed = M”.  
  *Verification*: The report file exists and `Expected == Observed`.

- [ ] **T024** Aggregate stability metrics: for each component, compute the mean and standard deviation of loading correlations across all bootstrap runs. Save `data/artifacts/stability_metrics.json` with fields `component`, `mean_corr`, `std_corr`.  
  *Verification*: JSON file loads and `std_corr` is a numeric value.

- [ ] **T025** Flag unstable modes: any component with `mean_corr < STABLE_CORR_THRESHOLD` (0.95) is written to `data/artifacts/unstable_modes.json` as a list of objects `{ "component": i, "mean_corr": v }`.  
  *Verification*: The file exists and contains at least one entry when instability occurs.

- [ ] **T026** Produce a histogram of the per‑model loading correlations (including bootstrap‑derived uncertainty bands) and save as `data/artifacts/stability_histogram.png`.  
  *Verification*: The PNG opens and shows a histogram with a shaded ±1 σ band.

- [ ] **T027** After all bootstrap artefacts are written, run `code/update_state.py` to hash the new files.  
  *Verification*: The state YAML now contains hashes for `stability_metrics.json`, `unstable_modes.json`, and the histogram image.

- [ ] **T028** Add unit tests in `tests/unit/test_robustness.py` that (a) mock a tiny ensemble of three models, (b) run the bootstrap routine with a reduced `BOOTSTRAP_ITER` (e.g., 10), and (c) assert that the number of iterations equals the mocked count. Tests must initially fail.  
  *Verification*: `pytest tests/unit/test_robustness.py` reports failing tests before implementation.

---

## Phase 5 – Documentation, polishing, and compliance

- [ ] **T029** Create `specs/001-statistical-analysis-of-publicly-availab/research.md` with a concise methodological justification for the **bootstrap** robustness protocol, citing Constitution Principle VI and the robustness goals.  
  *Verification*: The file contains a section titled “Robustness via Bootstrap Resampling”.

- [ ] **T030** Perform code cleanup: run `black .` and `ruff` to fix formatting and linting issues; commit the cleaned files.  
  *Verification*: CI lint step passes without warnings.

- [ ] **T031** Instrument `code/main.py` (the pipeline entry point) to record wall‑clock time and peak memory usage (using `time` and `psutil`). Write a compliance report `data/artifacts/performance_compliance_report.md` with a table **Metric | Value | Limit | Status** confirming runtime < 6 h and memory < 7 GB.  
  *Verification*: The markdown report exists and all status fields read “PASS”.

- [ ] **T032** Add additional edge‑case unit tests (under `tests/unit/`) covering:  
  - >10 % missing time steps triggers a warning but does not crash.  
  - Ensemble size < 10 models aborts with a clear error message.  
  *Verification*: Running the full test suite (`pytest`) passes for all implemented edge cases.

- [ ] **T033** Validate the end‑to‑end command documented in `quickstart.md` on the minimal three‑model subset: the command must complete, produce the artefacts listed in Phase 5, and exit with status 0. Record the console output in `data/artifacts/end_to_end_demo/log.txt`.  
  *Verification*: The log file ends with “Pipeline completed successfully”.