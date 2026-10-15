# Tasks: Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, reviewer feedback, and prior verification failures.  
**Goal**: A reproducible end‑to‑end pipeline that (1) obtains real 30 m NLCD land cover data via the USGS EarthExplorer API, (2) aggregates it to coarser resolutions with nearest‑neighbor resampling, (3) transforms it to binary class indicators, (4) runs Moran's I permutation tests and H1 simulations, (5) estimates statistical power per resolution, (6) visualizes the power curve (JSON) and identifies the resolution where power < 0.80, and (7) validates all result artifacts against the declared schemas.

**Re‑plan notes**: The prior task list contained a duplicate identity (T010), a platform‑owned directory‑creation task, linting‑configuration tasks, a CI‑workflow task, and several tasks whose declared artifacts were missing or written to inconsistent paths. This revision consolidates the work into 16 substantive tasks with canonical IDs, consistent relative paths (`code/`, `data/`, `tests/` under the project root), and no synthetic‑fallback data loading. Directory creation is handled on demand by `llmxive_toolkit.paths`; no task is spent on it.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 Implement real NLCD data ingestion in `code/data_ingestion.py` (FR‑001).   <!-- FAILED-IN-EXECUTION: code/data_ingestion.py exit=1 -->
  - Use the USGS EarthExplorer API (official Python client) with a valid API key to download the 30 m NLCD Land Cover tile for Colorado, applying the user‑specified bounding box.  
  - Perform windowed reads with `rasterio` to crop the CONUS raster to the bounding box and write `data/raw/nlcd_30m_co.tif`.  
  - Retry up to 3 times with exponential back‑off; on final failure **RAISE** a clear error (no synthetic fallback).  
  - Record source URL, CRS, pixel size, dtype, class list, and SHA‑256 checksum in `data/raw/nlcd_30m_co_meta.json` (conforms to `dataset.schema.yaml`).  
  - Verification: `tests/test_ingestion.py` asserts file existence, CRS = EPSG:5070, pixel size = 30 m, integer dtype, and non‑empty class list.

- [ ] T002 Implement nearest‑neighbor resolution aggregation in `code/resampling.py` (FR‑002, Constitution VII).  
  - `generate_resolution(input_path, target_resolution_m) -> Path` uses `rasterio.warp.reproject` with `Resampling.nearest`, processing the source in ≤2000×2000‑pixel windows.  
  - Generate `data/derived/nlcd_{60,120,240,480}m_co.tif` from the 30 m source; skip resolutions that would exceed raster bounds with a logged warning.  
  - **Dependency**: requires output of T001 (`data/raw/nlcd_30m_co.tif`).  
  - Verification: `tests/test_resampling.py` asserts each output’s pixel size, integer dtype, and that unique class values are a subset of the source (no new interpolated values).

- [ ] T003 Implement binary indicator transformation in `code/binary_indicator.py` (FR‑003).  
  - `make_binary(raster_path, class_id, output_path)` writes 1 where the class occurs, 0 elsewhere, dtype uint8, honoring nodata.  
  - Produce `data/derived/binary_forest_{res}m_co.tif` (Forest = 41) and `data/derived/binary_urban_{res}m_co.tif` (Developed = 12) for all five resolutions.  
  - Verification: `tests/test_binary.py` asserts the count of 1‑pixels matches the source class count and that values are exactly {0, 1}.

- [ ] T004 Implement the Moran's I analysis core in `code/analysis.py` (FR‑004, FR‑006).  
  - `compute_morans_i(binary_path) -> (I, p)` uses `esda.moran.Moran` with exactly 1,000 permutations, weights from `libpysal` (queen contiguity on a subsampled grid if needed).  
  - Run a thin end‑to‑end case: compute Moran's I and p‑value for the 30 m forest binary and write a first result row to `data/results/morans_i_results.csv` conforming to `results.schema.yaml`.  
  - Verification: `tests/test_analysis.py` asserts permutation count = 1,000, I ∈ [‑1, 1], p ∈ [0, 1], and CSV schema compliance.

- [ ] T005 Implement lambda calibration in `code/calibration.py` (Phase 0).  
  - From the 30 m forest binary (produced by **T003**), take a fixed‑seed random sample of contiguous grid windows (sample size documented in output).  
  - Estimate the spatial lag parameter λ of a binary spatial autoregressive process by grid‑searching λ to match the observed Moran's I of simulated surfaces.  
  - Write `data/results/calibration.json` with keys `lambda`, `sample_size`, `observed_morans_i`, `simulated_morans_i`, `fit_error_pct`; require `fit_error_pct ≤ 5 %`.  
  - Verification: `tests/test_calibration.py` asserts λ ∈ (0, 1) and error ≤ 5 %.

- [ ] T006 Implement H1 simulation and power estimation in `code/analysis.py` (FR‑005).  
  - `simulate_h1(binary_path, lambda_val, n=1000)` generates 1,000 synthetic binary surfaces per resolution via a Gibbs sampler for a binary spatial autoregressive process with the calibrated λ.  
  - `estimate_power(h0_dist, h1_dist, alpha=0.05)` returns the proportion of H1 simulations whose Moran's I exceeds the (1 ‑ α) quantile of the H0 permutation distribution.  
  - Verification: `tests/test_power.py` asserts both distributions have length 1,000, power ∈ [0, 1], and matches a hand‑computed example.

- [ ] T007 Run the full resolution × class sweep (SC‑001, SC‑002).   <!-- FAILED-IN-EXECUTION: code/full_sweep.py exit=1 -->
  - For each resolution [30, 60, 120, 240, 480] m and class (Forest, Urban): compute observed Moran's I, permutation p‑value, H1 power estimate, and **record** `n_simulations` = 1,000.  
  - Apply Benjamini‑Hochberg correction across all class tests; store both raw and corrected p‑values.  
  - Write **10 rows** to `data/results/morans_i_results.csv` with columns `resolution_m`, `observed_morans_i`, `p_value`, `n_permutations` (always 1,000), `n_simulations` (always 1,000), `power_estimate`, `is_below_threshold` (true when power < 0.80).  
  - Verification: a check script confirms 10 rows, required fields, and JSON‑schema validation against `results.schema.yaml`.

- [ ] T008 Generate the power curve and threshold identification in `code/visualization.py` (FR‑007, SC‑001).  
  - Read `morans_i_results.csv`, compute per‑resolution power per class, and write **`data/results/power_curve.json`** matching `power_curve.schema.yaml` (object with `curve_data` array and `summary` object).  
  - Plot power vs. resolution per class with the 0.80 line and threshold annotation; save `data/results/power_curve_forest.png` and `data/results/power_curve_urban.png`.  
  - Write `data/results/threshold_report.txt` naming the resolution where power first falls below 0.80 for each class and the Type II error increase relative to the 30 m baseline.  
  - Verification: `tests/test_visualization.py` asserts the JSON validates against the schema, that **zero or one** `threshold_flag == true` rows exist per class (allowing a flat curve), and that PNG/report files are non‑empty.

- [ ] T009 Perform the ±10 % sensitivity sweep (SC‑004).  
  - Around the identified threshold resolution, generate perturbed rasters at 0.9× and 1.1× the nominal resolution (rounded to integer meters) via `resampling.generate_resolution` into `data/derived/sensitivity/`.  
  - Re‑run the full analysis (binary transform, Moran's I, H1 power) on the perturbed rasters and append rows tagged `sensitivity` to `morans_i_results.csv`.  
  - Write `data/results/sensitivity_report.md` stating whether the threshold moves by more than one resolution step (± 60 m) and flag any p‑value exactly = 0.05.  
  - Verification: the sensitivity directory contains at least two rasters; the report contains an explicit threshold‑variation statement.

- [ ] T010 Runtime, memory, and disk‑usage validation (SC‑003, FR‑006).  
  - Instrument `code/main.py` to record wall‑clock time, peak RSS, and peak disk usage (via `psutil` and `shutil.disk_usage`) per phase into `data/results/runtime_report.json`.  
  - Confirm the full sweep completes **CPU‑only** within 6 h, < 7 GB RAM, and < 14 GB disk. If the full grid exceeds limits, fall back to a documented fixed‑seed spatial subsample (rule and power limitation noted in the report).  
  - Verification: the runtime report shows total time < 6 h, peak memory < 7 GB, peak disk < 14 GB, and includes a flag confirming no GPU devices were detected.

- [ ] T011 Write the methods and results account in `data/results/final_report.md`.  
  - State the resolution where power first drops below 0.80 for each class, the Type II error delta vs. the 30 m baseline, the calibrated λ and fit error, the sensitivity conclusion, the runtime/memory figures, and honest limitations.  
  - Link every numeric claim to the actual CSV/JSON artifact; no hand‑typed values.  
  - Verification: the report contains the required sections and every cited value is traceable to a file under `data/results/`.

- [ ] T012 Re‑run the documented workflow end‑to‑end and record the paper‑stage handoff.  
  - Update `specs/001-assessing-the-impact-of-data-resolution/quickstart.md` with exact runnable commands, pinned seeds, and the USGS EarthExplorer data‑source recipe.  
  - Re‑execute the full pipeline from `data/raw/`, confirm `pytest tests/` passes and all schema validations succeed, and write `data/results/handoff.md` summarising the artifacts the paper stage receives (results CSVs, power‑curve JSON/PNG, threshold and sensitivity reports, final report).  
  - Verification: a clean re‑run reproduces `morans_i_results.csv`, `power_curve.json`, and the threshold report with identical values under the pinned seeds.

## Phase 2: Reproducibility, verification, and hygiene

- [ ] T013 Record and pin all random seeds in `code/config.py` and verify that a fresh checkout can execute the full pipeline end‑to‑end without manual intervention (Constitution I).  
  - `config.py` defines `SEED_NP`, `SEED_PYSA`, etc.; tasks import these seeds.  
  - A verification script runs the complete pipeline on a clean environment and asserts identical outputs to a stored fingerprint.  
  - Verification: `tests/test_seeds.py` checks that the fingerprint matches the reference.

- [ ] T014 Run the Reference‑Validator Agent to confirm every external citation (NLCD URL, literature references) is reachable and matches the primary source before research completion (Constitution II).  
  - The task aborts the pipeline if any citation fails validation.  
  - Verification: the agent’s log contains “All citations verified”.

- [ ] T015 Write SHA‑256 checksums of all data artifacts into the project’s `state/projects/PROJ-421‑...yaml` manifest and validate the manifest (Constitution III).  
  - After each data‑generation task, the checksum is added to the `artifact_hashes` map.  
  - Verification: `tests/test_state_checksums.py` confirms the manifest entries match the actual file hashes.

- [ ] T016 Assert CPU‑only execution environment (FR‑006).  
  - The task checks `torch.cuda.is_available()` (if torch is installed) and that no CUDA‑enabled libraries are imported; it fails if a GPU is present.  
  - Verification: `tests/test_gpu_absence.py` passes on the GitHub Actions runner.

## Dependencies and ordering

- Execution order (respecting data flow):  
  T001 → T002 → T003 → (T004, T005) → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016.  
- Parallel‑safe tasks: none are marked `[P]`; all dependencies are explicit.  

## Dependencies and requirement coverage

- FR‑001 → T001 (USGS EarthExplorer download)  
- FR‑002 → T002  
- FR‑003 → T003  
- FR‑004 → T004, T007  
- FR‑005 → T005, T006  
- FR‑006 → T010, T016  
- FR‑007 → T008  
- SC‑001 → T007, T008  
- SC‑002 → T008  
- SC‑003 → T010  
- SC‑004 → T009  

All tasks are unchecked; they will be completed and verified according to the updated specifications.  