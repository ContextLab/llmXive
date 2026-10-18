# Tasks: Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas

**Inputs**: `specs/001-investigating-the-potential-benefits-of/spec.md`, `plan.md`, `data-model.md`, contracts.  
**Scope**: Observational study (no causal claims) of ecotourism association with NDVI recovery rates, 2000‑2023, ≤30 paired sites, CPU‑only, RAM < 7 GB, real data only.

## Phase 1 – Data acquisition, preprocessing, and first end‑to‑end run  

- [ ] T001 [US1] Verify core specification clauses and log failures.  
  - Open `specs/001-investigating-the-potential-benefits-of/spec.md`.  
  - Confirm that **SC‑001** contains the phrase “up to 30 valid sites”.  
  - Confirm that **FR‑002** includes the note about the linear‑slope fallback.  
  - If either check fails, write a descriptive error entry to `state/spec_validation.log` and raise `RuntimeError` to halt the pipeline.  
  - Verification: `grep -q "up to 30 valid sites" spec.md && grep -q "linear slope fallback" spec.md` succeeds; `state/spec_validation.log` is non‑empty only on failure.

- [ ] T002 Create required project directory hierarchy with placeholder files.  
  - Make the following directories (if they do not exist): `data/raw/landsat/`, `data/processed/`, `data/ecotourism/`, `data/results/`, `figures/`.  
  - Add an empty `.gitkeep` file in each directory to guarantee its presence in version control.  
  - Verification: `find data -type d -exec test -e {}/.gitkeep \; -print` lists all created folders.

- [ ] T003 [US1] Retrieve protected‑area metadata (WDPA) and produce site metadata.  
  - Download the canonical WDPA CSV from `[UNRESOLVED-CLAIM: https://d1gam3xoknrgr2.cloudfront.net/current/WDPA_WDOECM_csv.zip` — HTTP 404].  
  - Stream the zip, filter for candidate sites, and write `data/processed/site_metadata.csv` with columns `site_id,site_type,latitude,longitude,biome,protection_status,pairing_id`.  
  - Log the exact request URL, HTTP status, and timestamp to `data/raw/query_log.json`.  
  - On any network or schema error, raise `RuntimeError` and write details to `data/raw/fetch_error.log`.  
  - Verification: `csvstat data/processed/site_metadata.csv` shows ≥ 2 rows; `data/raw/query_log.json` contains a non‑empty entry.

- [ ] T004 [US1] Acquire ecotourism economic records and generate metadata.  
  - Download revenue and visitor‑count CSVs from the URLs listed in the plan’s verified report list (e.g., `[UNRESOLVED-CLAIM: https://example.org/ecotourism/revenue.csv` — HTTP 404]).  
  - Store raw files under `data/ecotourism/`.  
  - Create `data/ecotourism/metadata.json` listing, for each site, `source_name`, `retrieval_date`, and `preprocessing_steps`.  
  - If a site lacks a revenue value, substitute the visitor count as the proxy variable and record `"proxy_used": "visitor_count"` in the JSON entry.  
  - Verification: `jq . data/ecotourism/metadata.json` shows entries for all sites; no site entry has both `revenue` and `proxy_used` missing.

- [ ] T005 [US1] Download Landsat Level‑2 Surface Reflectance scenes in RAM‑safe batches.  
  - Read `data/processed/site_metadata.csv` to obtain site coordinates.  
  - Use `landsatxplore` to query the USGS API for scenes covering 2000‑2023 for each site.  
  - Process scenes in chunked batches; monitor memory via `psutil`. If RAM usage exceeds 7 GB, raise `MemoryError` and abort the current batch.  
  - Save each scene under `data/raw/landsat/` preserving the original filename.  
  - After each successful download, compute a SHA‑256 checksum and append `{scene_id: checksum}` to `data/raw/landsat/checksums.json`.  
  - On any download failure, raise `RuntimeError` and log to `data/raw/fetch_error.log`.  
  - Verification: At least two `.tif` files exist in `data/raw/landsat/`; `checksums.json` contains a matching entry for each; a simulated OOM triggers a `MemoryError`.

- [ ] T006 [US1] Compute NDVI time series with quality control and schema validation.  
  - For each downloaded scene, apply cloud masking (retain pixels with `cloud_cover ≤ 20 %`).  
  - For Landsat 7 SLC‑off scenes, apply gap‑masking before NDVI calculation.  
  - Compute NDVI = (NIR‑Red) / (NIR + Red) and emit per‑pixel records: `site_id, date, ndvi, scene_id, cloud_cover, qa_pixel, qa_radsat, is_valid`.  
  - Store the aggregated per‑site series as `data/processed/ndvi_timeseries.parquet`.  
  - Validate every record against `specs/001-investigating-the-potential-benefits-of/contracts/timeseries.schema.yaml` (using the generated Pydantic model). Ensure no nulls in `site_id`, `date`, `ndvi`.  
  - Include unit tests in `code/tests/test_preprocessing.py` for cloud masking and NDVI formula.  
  - Verification: `pytest code/tests/test_preprocessing.py` passes; parquet file contains ≥ 2 sites; schema validation succeeds.

## Phase 2 – Modeling, sensitivity, and final reporting  

- [ ] T007 [US2] Fetch climate covariates (CHIRPS precipitation & MODIS LST) and store them.  
  - For each site‑year, query the CHIRPS point API (`[UNRESOLVED-CLAIM: https://data.chc.ucsb.edu/products/CHIRPS-2.0/` — HTTP 404]) to obtain monthly precipitation totals.  
  - Query the NASA POWER API (`[UNRESOLVED-CLAIM: https://power.larc.nasa.gov/api/temporal/monthly/point` — HTTP 404]) for monthly land‑surface temperature.  
  - Stream responses to avoid loading the entire dataset in memory; write rows `site_id, year, month, precip_mm, temp_c` to `data/processed/climate_covariates.parquet`.  
  - Log every HTTP request (URL, status, timestamp) to `data/raw/query_log.json`.  
  - **Verification**: Ensure **both** precipitation and temperature are present for every site‑year combination; raise `RuntimeError` if any pair is missing. Also confirm that the `year` column contains no nulls.  
  - On any API error, raise `RuntimeError` and record details in `data/raw/fetch_error.log`.  
  - Verification: Parquet contains > 0 rows; `query_log.json` has entries for both APIs; a forced 404 aborts with a logged error.

- [ ] T008 [US2] Pair ecotourism sites with control sites and merge economic data.  
  - Using `data/processed/site_metadata.csv`, match each ecotourism site to a control site in the same biome and with initial NDVI severity difference ≤ 10 %.  
  - Write the pairing table to `data/processed/site_pairs.csv` (columns `ecotourism_site_id, control_site_id`).  
  - Merge the economic dataframe (`data/ecotourism/`) using the proxy logic from T004 and output `data/processed/ecotourism_data.csv`.  
  - **Verification**: Confirm that every pair satisfies the biome‑match and severity‑difference criteria; abort with `RuntimeError` if any pair violates the ≤ 10 % rule. Also verify equal numbers of ecotourism and control rows and no missing proxy values.  
  - Verification: `site_pairs.csv` has equal numbers of ecotourism and control rows; `ecotourism_data.csv` contains no missing values in the proxy column.

- [ ] T009 [US2] Detect deforestation events and fit recovery‑trajectory models.  
  - Scan `ndvi_timeseries.parquet` for each site to locate break‑points where NDVI drops ≥ 0.30 and remains below that threshold for ≥ 2 years.  
  - For each detected event, fit a non‑linear asymptotic model (logistic or Gompertz) using `scipy.optimize.curve_fit`. Compute R².  
  - If R² < 0.95, fall back to a linear slope fitted over the recovery window (per FR‑002).  
  - Write results to `data/processed/recovery_trajectories.parquet` with fields `site_id, event_start, event_end, severity, trajectory_params, model_type, r_squared`.  
  - **Verification**: Assert that every recorded event meets the ≥ 0.30 NDVI drop and ≥ 2‑year duration thresholds; raise `RuntimeError` otherwise.  
  - Include unit tests in `code/tests/test_detection.py` for breakpoint detection and fallback logic.  
  - Verification: `pytest code/tests/test_detection.py` passes; parquet contains no nulls in `model_type` or `r_squared`.

- [ ] T010 [US3] Fit the Linear Mixed‑Effects Model, apply multiple‑comparison correction, and perform sensitivity sweeps.  
  - Using `statsmodels`’ `MixedLM`, model the recovery slope (or linear fallback slope) as the outcome with fixed effects: `ecotourism_status`, `precipitation`, `temperature`, `initial_severity`. Include a random intercept for each ecotourism‑control pair.  
  - Apply Holm correction to raw p‑values (fallback to Bonferroni if Holm fails).  
  - Count converged fits; require ≥ 90 % of site‑pairs to converge. Abort with error if the threshold is not met.  
  - Sensitivity analysis: sweep three revenue thresholds (1 000, 10 000, 50 000 USD) and both proxy variables (`revenue_usd`, `visitor_count`). For each configuration, refit the model and record `r_squared`, `AIC`, `convergence`.  
  - Write primary model output to `data/results/lmm_results.json` (coefficients, SE, 95 % CI, raw & corrected p‑values).  
  - Write the full sensitivity table to `data/results/sensitivity_analysis.csv` respecting the `SensitivityArtifact` contract.  
  - **Verification**: Confirm that the corrected p‑values were produced using Holm (or Bonferroni) and that the correction method is recorded in the results metadata.  
  - Unit tests in `code/tests/test_modeling.py` verify convergence counting and correction implementation.  
  - Verification: `pytest code/tests/test_modeling.py` passes; `convergence_check.json` reports ≥ 90 % converged; `sensitivity_analysis.csv` has 6 rows (3 thresholds × 2 proxies).

- [ ] T015 Extend the `FinalReport` contract to include confidence‑interval fields and add a validation test.  
  - Edit `specs/001-investigating-the-potential-benefits-of/contracts/output.schema.yaml` so that each entry in `regression_coefficients` is an object with keys `estimate`, `ci_lower`, `ci_upper` (all floats).  
  - Regenerate the Pydantic model via `code/utils/schema_loader.py`.  
  - Add `code/tests/test_output_schema.py` that loads a sample JSON containing CI fields and asserts successful validation.  
  - Verification: `pytest code/tests/test_output_schema.py` passes; downstream tasks (T011) validate against the updated schema without error.

- [ ] T011 [FR‑006] Generate final reports (CSV + JSON) compliant with the updated `FinalReport` schema.  
  - Assemble regression coefficients (including `estimate`, `ci_lower`, `ci_upper`) from `lmm_results.json`.  
  - Embed the full sensitivity list (from T010) and any data‑quality flags (e.g., low‑R² recoveries, proxy substitutions) into a JSON object matching `specs/001-investigating-the-potential-benefits-of/contracts/output.schema.yaml`.  
  - Write `data/results/final_report.json` and copy it to `data/processed/final_report.json`.  
  - Also produce a CSV version `data/processed/final_report.csv` with columns `variable, estimate, ci_lower, ci_upper, p_value, corrected_p_value`.  
  - Run a schema validation step (`pydantic` loader) to ensure the JSON conforms; abort with error if validation fails.  
  - **Verification**: Ensure that every coefficient entry includes non‑null `ci_lower` and `ci_upper` fields before validation.  
  - Verification: `python -m code.report --validate` exits with status 0; both JSON and CSV files exist and contain the required fields.

- [ ] T012 Write a deterministic research narrative (`research.md`).  
  - Create `specs/001-investigating-the-potential-benefits-of/research.md`.  
  - The script `code/utils/render_report.py` reads `final_report.json` and `sensitivity_analysis.csv` and injects all numeric results via Jinja2 placeholders, guaranteeing no hand‑typed numbers.  
  - Include sections: Methods (data sources, preprocessing, detection, modeling), Results (effect sizes, confidence intervals, corrected p‑values), Sensitivity (tables), Limitations (e.g., sites excluded, proxy substitution).  
  - **Verification**: After rendering, confirm that no Jinja2 placeholder tokens remain (`{{` or `}}`) **and** that a predefined list of required statistics (e.g., `ecotourism_effect`, `precipitation_coeff`) appears in the document; raise `RuntimeError` if any are missing.  
  - Verification: `grep -q "{{" research.md && echo "placeholders remain"` returns non‑zero; script runs without error; required stats present.

- [ ] T013 Execute a clean re‑run from the documented quick‑start command and produce the paper handoff.  
  - Follow the command documented in `quickstart.md` on a fresh runner.  
  - Ensure all `pytest` suites pass, all schema validations succeed, and the final artifacts (`final_report.json`, `figures/`, `tables/`) are regenerated.  
  - Generate `specs/001-investigating-the-potential-benefits-of/paper_handoff.md` listing exact repository paths for all deliverables, summarising effect sizes and corrected p‑values.  
  - Verification: Fresh run ends with exit code 0; `paper_handoff.md` exists and references existing files.

## Phase 3 – Reproducibility, compliance, and contract updates  

- [ ] T014 Consolidate all file checksums into a manifest and update project state.  
  - Merge `data/raw/landsat/checksums.json` with any additional checksum files into `data/raw/checksums_manifest.json`.  
  - Run `code/utils/update_state_hashes.py` to write the manifest entries into `state/projects/PROJ-555-investigating-the-potential-benefits-of-.yaml` under `artifact_hashes`.  
  - Verification: The state YAML contains a hash entry for every file under `data/`; mismatches raise `RuntimeError`.

- [ ] T016 Validate ecotourism metadata completeness.  
  - Load `data/ecotourism/metadata.json` and confirm that every entry contains the keys `source_name`, `retrieval_date`, and `preprocessing_steps`.  
  - Raise `RuntimeError` if any entry is missing a required field.  
  - Verification: Script exits with status 0 only when all entries are complete.

- [ ] T017 Validate absence of nulls in critical ‘year’ fields across all output datasets.  
  - Scan `data/processed/climate_covariates.parquet`, `data/processed/site_pairs.csv`, and any other tables for null values in the `year` column.  
  - Raise `RuntimeError` if any nulls are found.  
  - Verification: Passes only when all year fields are populated.

- [ ] T018 Verify pairing criteria adherence.  
  - Re‑evaluate the `site_pairs.csv` to ensure each ecotourism‑control pair shares the same `biome` and that the absolute difference in `initial_ndvi` ≤ 0.10.  
  - Abort with `RuntimeError` on any violation.  
  - Verification: Successful only when all pairs meet the criteria.

- [ ] T019 Verify multiple‑comparison correction application.  
  - Inspect `data/results/lmm_results.json` to confirm that corrected p‑values were derived using Holm correction (or Bonferroni fallback) and that the method used is recorded in the result metadata.  
  - Raise `RuntimeError` if correction is absent or method not recorded.  
  - Verification: Passes when correction metadata is present and correct.

- [ ] T020 Verify detection thresholds compliance.  
  - Re‑run a lightweight check on `recovery_trajectories.parquet` to ensure every recorded event satisfies NDVI drop ≥ 0.30 and duration ≥ 2 years.  
  - Raise `RuntimeError` on any breach.  
  - Verification: Passes only when all events meet thresholds.

- [ ] T021 Full end‑to‑end pipeline verification on maximum load.  
  - Execute the complete pipeline (T003‑T020) on a curated set of 30 valid sites using streaming/chunked processing.  
  - Monitor peak RAM usage; assert it stays below 7 GB.  
  - After completion, confirm that all previous verification tasks (T014‑T020) succeed.  
  - Verification: Pipeline finishes without memory error and all downstream checks pass.

- [ ] T022 Run Reference‑Validator Agent to verify all external citations meet Constitution Principle II.  
  - Invoke the platform’s citation‑validation utility on the repository.  
  - Abort with `RuntimeError` if any citation fails the Verified Accuracy check.  
  - Verification: Successful only when all citations are validated.

- [ ] T023 Update the FinalReport schema with CI fields **before** any consumer tasks (already handled by T015).  
  - No additional action; placeholder to document ordering compliance.

- [ ] T024 Ensure final report JSON includes CI fields (handled in T011 verification).  
  - No additional action; placeholder to document compliance.

- [ ] T025 Confirm research narrative injection completeness (handled in T012 verification).  
  - No additional action; placeholder to document compliance.
