# Tasks: Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets

**Input**: `spec.md`, `plan.md`, `data‑model.md`, contracts, and reviewer feedback.  
**Goal**: Produce a fully reproducible end‑to‑end pipeline that (1) downloads NLCD data, (2) creates coarser rasters, (3) transforms them to binary maps, (4) runs Moran’s I with null/alternative simulations, (5) estimates statistical power, (6) visualises the power curve, (7) identifies the resolution where power < 0.80, and (8) validates everything against the declared schemas.

---

## Phase 0 – Project bootstrap (no scientific dependencies)

- [ ] **T001** [P] Create the canonical project directory tree.  
  `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/`  
  `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/raw/`  
  `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/derived/`  
  `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results/`  
  `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/`  
  *Requirement*: All directories must exist after execution.  
  *Verification*: `tree` output shows the five directories; CI step `test_dir_structure` asserts their presence.

- [ ] **T002** [P] Add a single `pyproject.toml` that (a) pins all runtime dependencies (`rasterio`, `geopandas`, `pysal`, `numpy`, `scipy`, `matplotlib`, `pandas`, `libpysal`), (b) configures **Black** (`[tool.black] line-length = 88`) and **Ruff** (`[tool.ruff] select = ["E", "F", "W"]`).  
  Path: `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/pyproject.toml`  
  *Verification*: `pip install -r <(poetry export -f requirements.txt)` succeeds; `black --check .` and `ruff .` return zero violations.

- [ ] **T003** [P] Implement `code/utils.py` with:  
  * `checksum_file(path) → sha256` (uses `hashlib`),  
  * `validate_url(url) → bool` (HTTP 2xx check with timeout),  
  * `windowed_reader(raster_path, window_size=2000) → generator` (uses `rasterio`),  
  * a basic logger (`logging.getLogger(__name__)`).  
  *Verification*: Unit tests in `tests/test_utils.py` confirm checksum matches a known file, URL validation fails on a 404, and the windowed reader yields the expected number of windows without loading the whole raster.

- [ ] **T004** [P] Define core data structures and static configuration:  
  * `code/models.py` – `ResolutionRaster` and `BinaryIndicatorMap` dataclasses.  
  * `code/config.py` – list `RESOLUTIONS = [30, 60, 120, 240, 480]`, `SEED = 42`, `DATA_DIR = Path(__file__).resolve().parents[2] / "data"`, and a helper `load_lambda()` that reads `state/calibration.yaml`.  
  *Verification*: Importing `models` and `config` in an interactive session raises no errors; `config.load_lambda()` returns a float after calibration.

- [ ] **T005** [P] Implement the **lambda‑calibration** script `code/calibration.py`:  
  * Loads the 30 m binary map (produced later), samples a reproducible 5 % of pixels, fits a binary spatial autoregressive model by maximum‑likelihood to estimate the spatial lag parameter λ, writes `state/calibration.yaml` (`lambda: <value>`).  
  *Requirement*: The file must conform to a simple YAML schema (`lambda: float`).  
  *Verification*: After running `python -m code.calibration`, the YAML exists, parses with `yaml.safe_load`, and the value lies in (0, 1).

---

## Phase 1 – Data acquisition & resolution manipulation (User Story 1, P1)

- [ ] **T006** Implement `code/data_ingestion.py` that:  
  1. Calls the USGS EarthExplorer API (using an environment variable `USGS_API_KEY`) to request the 30 m NLCD tile for Colorado;  
  2. Falls back to the verified HuggingFace mirror `https://huggingface.co/datasets/nlcd-30m/resolve/main/nlcd_2019_colorado_30m.tif` if the API call fails after three exponential‑backoff retries;  
  3. Validates the download with `utils.validate_url` and `utils.checksum_file` against the checksum stored in `specs/.../dataset.schema.yaml`;  
  4. Writes the raster to `data/raw/nlcd_30m_co.tif`.  
  *Verification*: Integration test `tests/test_ingestion.py` asserts file existence, correct CRS (`EPSG:5070`), and that the checksum matches the schema value.

- [ ] **T007** Implement `code/resampling.py` with function `generate_resolution(input_path: Path, factor: int) → Path` that:  
  * Uses `rasterio.warp.reproject` with `Resampling.nearest`;  
  * Processes the source raster in 2000 × 2000‑pixel windows (via `utils.windowed_reader`) to stay ≤ 7 GB RAM;  
  * Skips a target resolution if the resulting raster would exceed the original bounding box (logs a warning);  
  * Writes each output to `data/derived/nlcd_{resolution}m_co.tif` (e.g., `nlcd_60m_co.tif`).  
  *Verification*: Unit test `tests/test_resampling.py` checks that unique class IDs are unchanged after resampling and that the pixel size metadata equals the requested resolution.

- [ ] **T008** Add a thin CLI orchestrator `code/main.py` exposing:  
  * `--download` → runs `data_ingestion`;  
  * `--aggregate` → runs `resampling` for all factors in `config.RESOLUTIONS[1:]`;  
  * `--full-sweep` → sequentially runs download, aggregation, binary conversion, calibration, analysis, visualization, and sensitivity sweep.  
  *Verification*: Running `python -m code.main --full-sweep` completes without error and leaves a non‑empty `data/results/morans_i_results.csv`.

---

## Phase 2 – Binary conversion & lambda estimation (pre‑US2)

- [ ] **T009** Implement `code/binary_indicator.py` containing `make_binary(raster_path: Path, class_id: int, output_path: Path)`.  
  * Converts the categorical NLCD raster to a binary map where the chosen `class_id` (e.g., Forest = 41) becomes 1 and all others 0; writes GeoTIFF with `dtype=uint8`.  
  *Creates two binaries:* `data/derived/binary_forest_30m_co.tif` and `data/derived/binary_urban_30m_co.tif` (Urban = 12).  
  *Verification*: Tests in `tests/test_binary.py` confirm that the sum of 1‑pixels matches the count of the target class in the source raster.

- [ ] **T010** Run the calibration script (`code/calibration.py`) **after** the forest binary is created.  
  *Reads `binary_forest_30m_co.tif`, estimates λ, writes `state/calibration.yaml`.  
  *Verification*: The YAML file exists, contains a single key `lambda`, and the value is printed in the CI log.

---

## Phase 3 – Spatial autocorrelation & power simulation (User Story 2, P2)

- [ ] **T011** Implement `code/analysis.py` with three public functions:  
  1. `compute_morans_i(binary_path: Path) → (float, float)` – returns Moran’s I and its p‑value using `pysal.esda.moran.Moran` with **exactly 1 000** random permutations (FR‑004).  
  2. `simulate_h1(binary_path: Path, lambda_val: float, n: int = 1_000) → List[Path]` – generates `n` synthetic binary rasters via a Gibbs sampler for a binary spatial autoregressive process (FR‑005).  
  3. `estimate_power(observed_i: float, h0_dist: np.ndarray, h1_dist: np.ndarray) → float` – computes the proportion of H1 simulations whose Moran’s I exceeds the 95 % percentile of the H0 distribution (α = 0.05).  
  *All results* are written to `data/results/morans_i_results.csv` adhering to `results.schema.yaml`.  
  *Verification*: `tests/test_analysis.py` checks that (a) the H0 array has length 1 000, (b) the H1 array length 1 000, (c) power lies in [0, 1] and matches a manual calculation on a tiny toy raster.

- [ ] **T012** Extend `analysis.py` to loop over **all** resolutions (`config.RESOLUTIONS`) **and** both land‑cover classes (Forest = 41, Urban = 12).  
  *Each combination* produces a row in the CSV with columns `resolution_m`, `class_id`, `observed_morans_i`, `p_value`, `n_permutations`, `n_simulations`, `power_estimate`, `is_below_threshold`.  
  *Verification*: After `python -m code.main --full-sweep`, the CSV contains 10 rows (5 resolutions × 2 classes) and passes JSON‑schema validation (`code/validate_schemas.py`).

---

## Phase 4 – Power‑curve visualisation & threshold detection (User Story 3, P3)

- [ ] **T013** Implement `code/visualization.py` that:  
  * Reads `morans_i_results.csv`; groups by resolution to compute mean power per resolution; writes `data/results/power_curve.csv` conforming to `power_curve.schema.yaml`.  
  * Plots the power‑vs‑resolution curve (matplotlib), annotates the first point where power < 0.80, saves PNG `data/results/power_curve.png`.  
  * Writes the identified threshold (e.g., `240m`) to `data/results/threshold_report.txt`.  
  *Verification*: Unit test `tests/test_visualization.py` asserts that the CSV contains a `threshold_flag == True` row and that the PNG file size > 0 KB.

- [ ] **T014** Perform a **±10 % sensitivity sweep** around the identified inflection point:  
  * Calls `resampling.generate_resolution` with factors `0.9×` and `1.1×` of the nominal resolution (e.g., 216 m and 264 m approximated to the nearest integer).  
  * Stores perturbed rasters in `data/derived/sensitivity/`.  
  * Re‑runs the full analysis (functions from `analysis.py`) on these rasters, appends results to the CSV, and updates the power curve.  
  * Generates `data/results/sensitivity_report.md` summarising whether the threshold moves by more than one discrete resolution step.  
  *Verification*: The `sensitivity` directory contains at least two new rasters; the report contains a statement like “Threshold variation ≤ 60 m (one step)”.

---

## Phase 5 – End‑to‑end verification, reproducibility & hand‑off

- [ ] **T015** Add a CI workflow (`.github/workflows/pipeline.yml`) that:  
  * Checks out the repo, sets up Python 3.11, installs from `pyproject.toml`, runs `python -m code.main --full-sweep`.  
  * Measures total runtime (must be < 6 h) and peak memory (must be < 7 GB) using the `psutil`‑based monitor in `code/main.py`.  
  * Executes `code/validate_schemas.py` against all result files.  
  * Fails if any check is violated.  
  *Verification*: GitHub Actions badge shows “passed”; local `act` run reproduces the same checks.

- [ ] **T016** Consolidate documentation for the research hand‑off:  
  * Update `README.md` with a “Quickstart” section that mirrors `quickstart.md` (installation, `python -m code.main --full-sweep`, where to find the final report).  
  * Create `data/results/final_report.md` that (a) states the resolution where power first drops below 0.80 for each class, (b) reports the Type II error delta relative to the 30 m baseline, (c) includes the sensitivity analysis conclusion, and (d) links to the generated figures and CSVs.  
  *Verification*: The final report file exists, contains the required headings, and the CI step `check_report` runs a simple grep to confirm the presence of “threshold_resolution_m”.

---

## Dependency & Execution Order Summary

| Task | Blocks | Can run in parallel |
|------|--------|----------------------|
| T001‑T005 (bootstrap) | – | ✔ |
| T006‑T008 (download + aggregate + CLI) | after T001‑T005 | ✔ (T006 & T007 independent) |
| T009 (binary conversion) | after T006 | ✔ |
| T010 (calibration) | after T009 | – |
| T011‑T012 (analysis) | after T010 & T007 | ✔ (different resolutions/classes processed in parallel) |
| T013 (visualisation) | after T011‑T012 | – |
| T014 (sensitivity sweep) | after T013 | – |
| T015 (CI workflow) | after all previous tasks | – |
| T016 (final report) | after T015 | – |

All tasks are unchecked (`[ ]`) to indicate they remain to be implemented. The list respects the scientific workflow, satisfies every functional requirement (FR‑001 – FR‑007), and provides concrete, verifiable artefacts at each stage.
