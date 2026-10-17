# Tasks: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices  

**Inputs**: `specs/001-quantifying-correlations-between-solar-w/spec.md`, `plan.md`, `data-model.md`, `contracts/`  

The following checklist implements the complete end‑to‑end scientific study while satisfying every functional requirement, performance constraint, and verification step described in the specification.  Tasks are ordered to respect data flow; later tasks depend only on the artifacts produced by earlier ones.

---

## Phase 1 – Data acquisition, synchronisation, and first end‑to‑end run  

- [X] **T001** [P] [US1] Create the project layout and a runnable quick‑start command.  
  - Create the directory hierarchy under the project root: `code/data/`, `code/analysis/`, `code/viz/`, `code/tests/`, `data/raw/`, `data/processed/`, `results/`, `figures/`.  
  - Add `specs/001-quantifying-correlations-between-solar-w/quickstart.md` that documents the exact CLI invocation:  

    ```bash
    python -m code.main --stage all
    ```  

  - Verification: running  

    ```bash
    python -c "import pathlib, sys; assert pathlib.Path('code/data').is_dir(); \
    assert pathlib.Path('specs/001-quantifying-correlations-between-solar-w/quickstart.md').exists(); \
    import subprocess; subprocess.run(['python','-m','code.main','--help'], check=True)"
    ```  

    exits with status 0 and the quick‑start file contains the command line above.

- [ ] **T002** [P] [US1] Implement real‑data fetchers in `code/data/fetch_ace.py` and `code/data/fetch_noaa.py`.   <!-- FAILED-IN-EXECUTION: code/data/fetch_ace.py exit=2; code/data/fetch_noaa.py exit=2 -->
  - Functions: `fetch_ace(start_date: str, end_date: str) -> pathlib.Path` and `fetch_noaa(start_date: str, end_date: str) -> pathlib.Path`.  
  - Use the verified URLs:  

    * ACE SWEPAM Level 2 CSV archive: `[UNRESOLVED-CLAIM: https://cdaweb.gsfc.nasa.gov/pub/data/ace/swepam/level2/` — HTTP 404]  
    * ACE SWICS Level 2 CSV archive: `[UNRESOLVED-CLAIM: https://cdaweb.gsfc.nasa.gov/pub/data/ace/swics/level2/` — HTTP 404]  
    * NOAA Kp/Dst archive: `[UNRESOLVED-CLAIM: https://services.swpc.noaa.gov/products/geomagnetic/` — HTTP 404]  

  - Perform streaming downloads with `requests` and exponential‑backoff retries (max 3 attempts).  
  - On any HTTP or network failure raise `ConnectionError`; **do not** fall back to synthetic data.  
  - Write the raw files to `data/raw/ace_<YYYYMM>.csv` and `data/raw/noaa_<YYYYMM>.csv`.  
  - Verification:  

    ```bash
    python -m code.data.fetch_ace --start 2003-10-01 --end 2003-10-31
    python -m code.data.fetch_noaa --start 2003-10-01 --end 2003-10-31
    ```  

    creates CSVs whose headers contain `N_p`, `T_p`, `He2+_ratio` (ACE) and `Kp`, `Dst` (NOAA).  A forced network outage (e.g., disconnecting internet) causes the command to raise `ConnectionError`.

- [ ] **T003** [P] [US1] Synchronise and resample the two data streams in `code/data/sync.py`.  
  - Load the raw ACE and NOAA CSVs, verify the presence of required variables (`N_p`, `T_p`, `He2+_ratio`, `Kp`, `Dst`). Abort with a clear error message if any are missing (FR‑006, SC‑002).  
  - Convert timestamps to UTC, resample both series to a **1‑hour** grid.  
  - Interpolate linearly over gaps **≤ 6 h**; for each interpolated interval log a warning and set `interpolated_flag = True`.  
  - Gaps **> 6 h** are dropped from the synchronized dataset (rows removed).  
  - Rename variables to the canonical names `proton_density`, `temperature`, `helium_abundance`, `Kp`, `Dst`.  
  - Write the aligned dataset to `data/processed/synced.csv` containing exactly the fields defined in `contracts/dataset.schema.yaml` (`timestamp, proton_density, temperature, helium_abundance, Kp, Dst, interpolated_flag`). No `gap_excluded` column is produced and the CSV contains **no NaNs** after imputation.  
  - Verification: running the pipeline for a representative month (e.g., 2003‑10) and executing `pytest code/tests/test_sync.py::test_sync_monthly` passes; the resulting CSV conforms to `contracts/dataset.schema.yaml` and has zero missing entries.

- [ ] **T004** [P] [US2] Compute lagged correlations on the **full 1998‑2020** series in `code/analysis/correlation.py`.  
  - For each composition parameter (3) × each geomagnetic index (2) × each lag ∈ {0,1,2,3,6 h} (30 tests):  
    1. Shift the composition series by the lag, drop rows where `interpolated_flag` is `True` only if they originated from a gap > 6 h (these rows have been removed in T003).  
    2. Compute Pearson *r* and Spearman *ρ* using `scipy.stats`.  
    3. Estimate the effective sample size *Neff* using the **lag‑1 autocorrelation** method of **Pyper & Peterman** applied to each series; derive a two‑sided *p*‑value from the t‑distribution with `df = Neff‑2`.  
    4. Apply a **Bonferroni correction** (α = 0.05 / 30) to each raw *p*‑value and store the corrected value in the field `p_holm_bonferroni` (the schema‑required name, now holding Bonferroni‑corrected values).  
    5. Set `significance_flag = (p_holm_bonferroni < 0.05)` and `effect_size_flag = (abs(pearson_r) > 0.5)`.  
  - Write `results/correlations.csv` (30 rows) that conforms to `contracts/analysis_schema.schema.yaml`.  
  - Verification: `python -m code.main --stage analyze` produces the CSV; `pytest code/tests/test_correlation.py::test_full_correlation_output` passes; a schema validator (`jsonschema.validate`) confirms full compliance.

- [ ] **T005** [P] [US3] Validate on the held‑out 2018‑2020 period in `code/analysis/validation.py`.  
  - Subset `synced.csv` to timestamps between 2018‑01‑01 and 2020‑12‑31.  
  - Repeat the exact correlation workflow of T004 on this subset, producing `results/validation_correlations.csv`.  
  - Flag rows where `|pearson_r| > 0.5` **and** `p_holm_bonferroni < 0.05`; write a Boolean column `validation_significant`.  
  - Generate a concise Markdown report `results/validation_report.md` that lists every flagged pair in the form:  

    ```
    Helium abundance vs. Dst at 3 h lag: r = 0.54 (significant)
    ```  

    and, if no pair meets the criteria, explicitly state “No composition parameter achieved the pre‑registered effect‑size threshold; composition does not add predictive value beyond dynamic pressure.”  
  - Verification: `python -m code.main --stage validate` creates both files; `pytest code/tests/test_validation.py::test_report_contents` confirms the report matches the CSV values.

- [ ] **T006** [P] [US3] Generate visual artefacts in `code/viz/plots.py`.  
  - From `results/correlations.csv` and `results/validation_correlations.csv` produce:  
    1. Time‑series overlay plots (composition vs. index) for each lag in the validation period.  
    2. Heatmaps of correlation magnitude (rows = composition parameters, columns = lags) for the full series and for validation.  
  - Save all PNGs under `figures/` with filenames `ts_overlay_<param>_lag<h>.png` and `heatmap_full.png`, `heatmap_validation.png`.  
  - Ensure each PNG ≤ 5 MB.  
  - Verification: `pytest code/tests/test_viz.py::test_png_sizes` passes; a manual checksum confirms files exist.

---

## Phase 2 – Additional scientific checks, performance, and reproducibility  

- [ ] **T008** [P] [US1] Benchmark the synchronisation pipeline.  
  - Instrument `code/data/sync.py` with `psutil` to record peak RAM usage and total runtime when processing the full 1998‑2020 interval.  
  - Write `results/performance_sync.json` containing `runtime_seconds` and `peak_ram_gb`.  
  - Verification: `pytest code/tests/test_sync_performance.py::test_sync_limits` asserts `runtime_seconds ≤ 1800` (30 min) and `peak_ram_gb ≤ 4`.

- [ ] **T010** [P] [US2] Run the complete pipeline from scratch and produce the paper‑stage handoff.  
  - Execute the command documented in `quickstart.md`:  

    ```bash
    python -m code.main --stage all
    ```  

  - Confirm that **all** pytest suites (`pytest code/tests/`) pass, that the following artefacts exist and conform to their schemas:  

    * `data/processed/synced.csv` → `dataset.schema.yaml`  
    * `results/correlations.csv` → `analysis_schema.schema.yaml`  
    * `results/validation_correlations.csv` → `analysis_schema.schema.yaml`  

  - Generate `results/paper_handoff.md` that lists:  

    * Paths to all figures (`figures/*.png`)  
    * Paths to result tables (`results/correlations.csv`, `results/validation_correlations.csv`)  
    * A short bullet‑point summary of the main findings (significant pairs, effect‑size outcomes).  

  - Verification: a script `python -c "import pathlib, json, jsonschema; ..."` confirms schema compliance; the handoff file contains valid relative links to each artifact.

- [ ] **T011** [P] [US2] Benchmark the full‑run correlation analysis (SC‑001).  
  - Instrument the correlation module (`code/analysis/correlation.py`) to record total wall‑clock time and peak RAM usage when analyzing the entire 1998‑2020 synchronized dataset.  
  - Write `results/performance_correlation.json` with keys `runtime_seconds` and `peak_ram_gb`.  
  - Verification: `pytest code/tests/test_correlation_performance.py::test_correlation_limits` asserts `runtime_seconds ≤ 21600` (6 h) and `peak_ram_gb ≤ 7`.

- [ ] **T012** [P] [US1] Update the repository README to point users to the quick‑start guide, the data‑model description, and the location of the final research narrative.  
  - Verification: `README.md` contains the bullet list with correct relative paths; a CI step runs `markdownlint` with no errors.

---

*All tasks above are unchecked (`- [ ]`) to indicate they still need to be executed.  Once a task completes and its verification step passes, the corresponding checkbox should be ticked.*  