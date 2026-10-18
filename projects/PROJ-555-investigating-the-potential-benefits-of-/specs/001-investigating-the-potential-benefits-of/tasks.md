# Tasks: Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas

**Inputs**: `specs/001-investigating-the-potential-benefits-of/spec.md`, `plan.md`, `data-model.md`, contracts.  
**Scope**: Observational study (no causal claims) of ecotourism association with NDVI recovery rates, 2000–2023, ≤30 paired sites, CPU‑only, RAM <7 GB, real data only.

## Phase 1: Setup, data acquisition & first end‑to‑end analysis

- [ ] T001 [US1] Scaffold project directories, pin dependencies, and **pin random seeds** (e.g., `np.random.seed(42); random.seed(42); torch.manual_seed(42)`) in `code/config.py`. Create empty placeholder directories:
  `data/raw/`, `data/raw/landsat/`, `data/processed/`, `data/ecotourism/`, `data/results/`, `figures/`. Write `requirements.txt` with exact versions. Document usage in `specs/001-investigating-the-potential-benefits-of/quickstart.md`.
  - Verification: `tree` shows all directories; `requirements.txt` exists; `code/config.py` defines `SEED = 42`; running `python -c "import code.config; assert code.config.SEED == 42"` succeeds.

- [ ] T011 [US1] Fetch protected‑area metadata (WDPA) from the **canonical CSV URL** `[UNRESOLVED-CLAIM: https://d1gam3xoknrgr2.cloudfront.net/current/WDPA_WDOECM_csv.zip` — HTTP 404]. Stream, filter to candidate sites, and write **canonical site metadata** to `data/processed/site_metadata.csv` (`site_id, site_type, latitude, longitude, biome, protection_status, pairing_id`). On any network or schema error **raise `RuntimeError`**, write details to `data/raw/fetch_error.log`, and exit with status 1. Log the exact query parameters and timestamps to `data/raw/query_log.json`.
  - Verification: `data/processed/site_metadata.csv` exists with ≥2 rows; `data/raw/query_log.json` is non‑empty; a forced network failure aborts with `RuntimeError` and logs to `fetch_error.log`.

- [ ] T012 [US1] Retrieve ecotourism economic records (revenue and visitor counts) from the URLs listed in the plan’s verified report list. Store raw CSVs under `data/ecotourism/` and generate a **metadata file** `data/ecotourism/metadata.json` containing for each site: `source_name`, `retrieval_date`, `preprocessing_steps`. If a site lacks revenue entirely, **substitute visitor count** as the proxy variable and record the substitution in `metadata.json`. No interpolation is performed.
  - Verification: `data/ecotourism/metadata.json` lists all sites; rows with missing revenue have `proxy_used: visitor_count`; no NaNs in critical fields.

- [ ] T002a [US1] Download Landsat Level‑2 Surface Reflectance scenes for each site in `data/processed/site_metadata.csv` using `landsatxplore`. Process in **chunked batches** monitoring RAM via `psutil`; raise `MemoryError` if usage exceeds 7 GB. Save each scene under `data/raw/landsat/` preserving original filenames. After each successful download, compute a **SHA‑256 checksum** and append an entry to `data/raw/landsat/checksums.json` (`{scene_id: checksum}`). On failure, raise `RuntimeError` and log to `fetch_error.log`.
  - Verification: At least two scene files exist; `checksums.json` contains entries for each; a simulated OOM triggers `MemoryError`.

- [ ] T002b [US1] Compute NDVI time series from the downloaded scenes:
  * Apply cloud masking using QA bands (cloud_cover ≤ 20 %).  
  * For Landsat 7 SLC‑off scenes, apply gap‑masking to avoid false NDVI drops.  
  * Generate per‑site NDVI points and write `data/processed/ndvi_timeseries.parquet`.  
  * Validate each point against the **canonical schema** `specs/001-investigating-the-potential-benefits-of/contracts/timeseries.schema.yaml` (required fields: site_id, date, ndvi, scene_id, cloud_cover, etc.) and ensure no nulls in critical fields (`site_id`, `date`, `ndvi`).  
  * Include unit tests in `code/tests/test_preprocessing.py` for NDVI calculation and cloud masking.
  - Verification: `pytest code/tests/test_preprocessing.py` passes; parquet file contains ≥2 sites; schema validation succeeds.

- [ ] T003a [US1] Fetch climate covariates:
  * CHIRPS precipitation via the NOAA/OpenGeoCHIRPS point API (streamed per site‑year).  
  * MODIS Land Surface Temperature via NASA POWER API (`[UNRESOLVED-CLAIM: https://power.larc.nasa.gov/api/temporal/monthly/point?...` — HTTP 404]).  
  * Write monthly aggregates to `data/processed/climate_covariates.parquet` (`site_id, year, month, precip_mm, temp_c`). Log all queries to `data/raw/query_log.json`.
  - Verification: Parquet exists with >0 rows; query log contains entries for both APIs.

- [ ] T003b [US1] Perform site pairing and economic proxy handling:
  * Pair each ecotourism site with a control site in the same biome and with initial NDVI severity difference ≤ 10 %. Output `data/processed/site_pairs.csv`.  
  * Merge economic data from `data/ecotourism/` (using revenue where present, otherwise visitor count per FR‑007) into `data/processed/ecotourism_data.csv`.  
  - Verification: `site_pairs.csv` has equal numbers of ecotourism and control sites; `ecotourism_data.csv` contains no missing proxy values.

- [ ] T004 [US2] **Deforestation detection & recovery‑trajectory modeling**:
  * Detect deforestation events where NDVI drops ≥ 0.30 and the drop persists for ≥ 2 years.  
  * For each event, fit a **per‑site non‑linear asymptotic model** (logistic or Gompertz) using `scipy.optimize.curve_fit`. Compute R²; if R² < 0.95, fall back to a **linear slope** over the recovery window (as mandated by FR‑002).  
  * Determine temporal flags by comparing `designation_date` (from site metadata) with `deforestation_start_date`.  
  * Output `data/processed/recovery_trajectories.parquet` with columns `site_id, event_start, event_end, severity, trajectory_params, model_type, r_squared, temporal_flag`.  
  * Include unit tests in `code/tests/test_detection.py` for breakpoint detection and fallback logic.
  - Verification: `pytest code/tests/test_detection.py` passes; parquet contains no nulls in `severity` or `model_type`.

- [ ] T005 [US1] **Full‑scale pipeline execution**:
  * Run the entire workflow on up to 30 paired sites (15 ecotourism / 15 control) covering 2000‑2023.  
  * Record peak RAM usage and total runtime in `data/results/run_metrics.json`.  
  * Ensure that the checksum step from T002a has been applied to all downloaded scenes.  
  - Verification: `run_metrics.json` shows `peak_ram_gb < 7`; `data/processed/ndvi_timeseries.parquet` and `recovery_trajectories.parquet` contain ≤ 30 sites; no data loss.

## Phase 2: Modeling, sensitivity, and final reporting

- [ ] T006 [US3] **Linear Mixed‑Effects Modeling**:
  * Fit a MixedLM using `statsmodels` with random intercept for each ecotourism‑control pair and fixed effects for ecotourism status, precipitation, temperature, and initial severity.  
  * Apply **Holm correction** (fallback to Bonferroni if needed) to p‑values (FR‑005).  
  * Verify convergence for **≥ 90 % of site‑pairs** (explicitly count converged pair fits).  
  * Write results to `data/results/lmm_results.json` (including coefficients, standard errors, 95 % CIs, raw and corrected p‑values).  
  * Unit tests in `code/tests/test_modeling.py` check convergence counting and multiple‑comparison correction.
  - Verification: `pytest code/tests/test_modeling.py` passes; `convergence_check.json` reports ≥ 90 % converged pairs.

- [ ] T007 [US3] **Sensitivity analysis**:
  * Sweep **three** revenue thresholds (low = 1 000 USD, medium = 10 000 USD, high = 50 000 USD) and both proxy variables (`revenue_usd`, `visitor_count`).  
  * For each configuration, refit the LMM (using the same seed) and record model metrics (R², AIC, convergence).  
  * Output `data/results/sensitivity_analysis.csv` conforming to the `SensitivityArtifact` contract (`threshold, proxy_variable, model_params, metrics`).  
  - Verification: CSV has 3 × 2 = 6 rows; all metric columns are populated; no nulls.

- [ ] T008a [FR‑006] **Final report – CSV**:
  * Assemble a CSV version of the final report matching `data-model.md` expectations: `data/processed/final_report.csv` containing columns for each regression coefficient, its CI lower/upper bounds, and a flag column for data‑quality issues.
  - Verification: CSV exists; schema validation (via a simple pandas check) passes; column names match data‑model description.

- [ ] T008b [FR‑006] **Final report – JSON**:
  * Generate `data/results/final_report.json` adhering to the **updated** `FinalReport` contract. The `regression_coefficients` dict now contains nested objects with `estimate`, `ci_lower`, and `ci_upper` for each variable, satisfying the confidence‑interval requirement. Include `sensitivity_analysis` list (from T007) and `data_quality_flags` (e.g., low‑R² recoveries, proxy substitutions).  
  * **Copy** the same JSON file to `data/processed/final_report.json` so that the data model’s processed‑data directory also contains the authoritative JSON report.
  - Verification: `python -m code.report --output json` runs without error; both `data/results/final_report.json` and `data/processed/final_report.json` exist; each contains `regression_coefficients` entries with `estimate`, `ci_lower`, `ci_upper`; `pydantic` validation against the **updated** `output.schema.yaml` succeeds.

- [ ] T009 [US3] **Methods & Results write‑up**:
  * Write a deterministic markdown document `specs/001-investigating-the-potential-benefits-of/research.md` that narrates the methodology, references all real data sources (with paths), lists key quantitative findings (drawn directly from `final_report.json` and `sensitivity_analysis.csv`), and discusses limitations (e.g., sites excluded, proxy substitution). No numbers are hand‑typed; they are programmatically inserted via a templating script.
  - Verification: File exists; a quick grep for `{{` placeholders fails, confirming all values were rendered; all cited file paths are valid.

- [ ] T010 [US3] **Re‑run & paper handoff**:
  * Execute the full workflow from the `quickstart.md` command on a fresh runner, ensuring all tests (`pytest`) and schema validations pass.  
  * Produce a handoff markdown `specs/001-investigating-the-potential-benefits-of/paper_handoff.md` that lists required deliverables (figures, tables, JSON/CSV reports) with their exact repository paths, and summarises effect sizes and corrected p‑values.
  - Verification: Clean re‑run reproduces `final_report.json`, `final_report.csv`, all figures, and the handoff file; `pytest` exits with 0; all Pydantic validations succeed.

## Phase 3: Reproducibility & compliance checks

- [ ] T013 [Constitution VII] **Checksum aggregation & state update**:
  * Consolidate all checksums from `data/raw/landsat/checksums.json` and any other `data/` files into a single manifest `data/raw/checksums_manifest.json`.  
  * Run the helper script `code/utils/update_state_hashes.py` which reads the manifest and writes the corresponding entries into the project's state YAML (`state/projects/PROJ-555-investigating-the-potential-benefits-of-.yaml` under `artifact_hashes`). This satisfies Principle VII and the Data Hygiene requirement.
  - Verification: `state/projects/PROJ-555-investigating-the-potential-benefits-of-.yaml` contains hash entries for every file under `data/`; a checksum mismatch triggers a RuntimeError.

- [ ] T014 [FR‑006, contracts] **Extend FinalReport contract to include confidence‑interval fields**:
  * Modify `specs/001-investigating-the-potential-benefits-of/contracts/output.schema.yaml` so that `regression_coefficients` maps each variable name to an object with `estimate`, `ci_lower`, and `ci_upper` (all floats).  
  * Update any generated Pydantic model loader to reflect the new schema.  
  * Add a unit test `code/tests/test_output_schema.py` confirming that a sample JSON with CI fields validates successfully.
  - Verification: Schema file contains the new fields; `pytest code/tests/test_output_schema.py` passes; downstream tasks (T008b) validate against the updated contract without error.