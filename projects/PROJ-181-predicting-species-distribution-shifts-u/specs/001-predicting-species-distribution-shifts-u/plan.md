# Implementation Plan: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Branch**: `001-predicting-species-distribution-shifts` | **Date**: 2024-10-23 | **Spec**: `specs/001-predicting-species-distribution-shifts/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-species-distribution-shifts/spec.md`

## Summary
Build a fully reproducible, CPU‑only pipeline that (1) downloads open North‑American bird occurrence records (historical 1970‑2000 and recent 2005‑2020) via the GBIF/eBird API, (2) downloads WorldClim v2 climate rasters (historical) and WorldClim CMIP6 rasters (future 2050 SSP2‑4.5), (3) preprocesses the data (breeding‑season filter, duplicate removal, spatial thinning ≥ 10 km or dynamic 95 th‑percentile, bias‑layer creation for both historic and recent periods, VIF‑based collinearity removal, climate extraction, simulation‑based power analysis), (4) trains three SDM algorithms (Random Forest, Bioclim, MaxEnt‑style surrogate) using spatial block cross‑validation (K = 5), (5) evaluates models on an independent recent test set with period‑specific bias‑corrected background sampling, (6) projects models onto the 2050 climate scenario, (7) quantifies niche stability via ΔAUC/TSS **between historic CV performance** and the recent test‑set performance and a Multivariate Environmental Similarity Surface (MESS) index, (8) performs a hierarchical bootstrap (≤ 500 iterations) and Benjamini‑Hochberg correction across five probability thresholds, and (9) generates a markdown report containing all tables, figures, and the required disclaimer. All artifacts are validated against JSON/YAML contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scikit-learn==1.5.0`, `geopandas==0.14.2`, `rasterio==1.3.9`, `pandas==2.2.2`, `numpy==1.26.4`, `pygbif==0.13.0`, `tqdm==4.66.2`, `statsmodels==0.14.2`, `matplotlib==3.8.4`, `seaborn==0.13.2`, `requests==2.32.3`, `pyyaml==6.0.1`  
- **Storage**: Local filesystem (`data/`, `models/`, `metrics/`, `logs/`)  
- **Testing**: `pytest` with schema‑validation fixtures  
- **Target Platform**: GitHub Actions free‑tier Linux runner (Multiple CPU cores., ~7 GB RAM, ≤ 6 h)  
- **Constraints**: CPU‑only execution; all external data must be openly downloadable; total runtime ≤ 6 h; no GPU dependencies.

## Phase 0 – Data‑Source Verification (Constitution II)
1. Run the Reference‑Validator Agent on every external URL (GBIF API docs, WorldClim download pages).  
2. Record verification outcomes in `data/manifest.json`.  
3. Abort the pipeline if any URL fails verification.  

*Addresses FR‑016 (checksum verification) and satisfies Constitution Principle II.*

## Phase 1 – Download (FR‑001, FR‑002, FR‑016)
- **Occurrence data**: Stream historical (1970‑2000) and recent (2005‑2020) records via `pygbif`.  
- **Climate rasters**: Stream WorldClim v2 historical rasters and WorldClim CMIP6 2050 SSP2‑4.5 rasters using `datasets.load_dataset(..., streaming=True)`.  
- **Checksum verification**: For each raster (and any auxiliary files) download the accompanying SHA‑256 checksum file, compute the local checksum, and abort on mismatch (fulfills FR‑016).  
- **Exponential back‑off & retry**: The download script implements exponential back‑off with up to 5 retries to handle GBIF API rate limits and transient network timeouts (addresses T004).  
- **Validation**: Immediately after download, validate each raster’s metadata against `contracts/climate_raster.schema.yaml`.  
- After occurrence CSVs are written, **validate them against `contracts/occurrence.schema.yaml`** (raw GBIF records) and **against `contracts/occurrence_record.schema.yaml`** after preprocessing (see Phase 2).  
- Populate `data/manifest.json` with URLs, timestamps, file sizes, and checksums.  

## Phase 2 – Preprocess (FR‑003, FR‑014, FR‑009, FR‑018, FR‑019, SC‑004)
1. **Breeding‑season filter** using species‑specific month windows (configurable).  
2. **Duplicate removal** (identical lat/long).  
3. **Spatial thinning**: compute nearest‑neighbor distances; use the 95th percentile distance or fallback to the default 10 km (FR‑014). Apply thinning to enforce the minimum distance.  
4. **Bias‑layer creation** (period‑specific):  
   - Generate a kernel‑density raster of observation effort from **historical** records → `data/processed/bias_layer_historic.tif`.  
   - Generate a separate kernel‑density raster from **recent** records → `data/processed/bias_layer_recent.tif`.  
   Both rasters are stored with provenance metadata and validated against `contracts/climate_raster.schema.yaml`.  
5. **Collinearity mitigation**: calculate Variance Inflation Factor (VIF) for all Bioclim variables; drop any with VIF > 10.  
6. **Climate extraction**: sample raster values at occurrence points with `rasterio.sample`; nearest‑neighbor impute missing cells.  
7. **Extraction validation**: each per‑occurrence climate record is validated against `contracts/climate_variable.schema.yaml`.  
8. **Data‑sufficiency & Power analysis** (FR‑018):  
   - Count thinned records per species.  
   - Perform a simulation‑based power analysis: bootstrap AUC **500 times** per species, compute empirical power to detect a ΔAUC ≥ 0.05 at α = 0.05.  
   - Flag species with `<100` records **or** power < 0.8 as `INSUFFICIENT_DATA`. Results saved to `metrics/data_sufficiency.json`.  
9. **Data‑acquisition completeness** (SC‑004): compute (a) proportion of target species with ≥ 100 thinned records and (b) proportion of records with non‑null climate values; write summary to `metrics/data_acquisition_completeness.json`.  
10. **Logging**: All preprocessing steps write a record to `logs/preprocess_counts.yaml`, which is a **YAML list of objects** each matching `contracts/log_counts.schema.yaml` (step name, before_count, after_count). The logging behavior is configured via `logs/logging_config.yaml`.  
11. Log before/after counts for each preprocessing step to `logs/preprocess_counts.yaml` (validated against `contracts/log_counts.schema.yaml`).  

All preprocessing scripts use the logging configuration defined in `logs/logging_config.yaml`.

## Phase 3 – Model Training (FR‑004, FR‑007, FR‑019)
- **CPU‑only enforcement**: `utils/gpu_check.py` aborts if a CUDA device is detected.  
- **Spatial block cross‑validation**: divide the study area into a n × n equidistant grid, rotate the held‑out block to obtain K = 5 folds (FR‑007).  
- **Algorithms**:  
  - Random Forest (`n_estimators=500`).  
  - Bioclim (range‑envelope).  
  - MaxEnt‑style surrogate (logistic regression on VIF‑filtered predictors).  
- Train each algorithm for each of the ≤ 5 species (FR‑019).  
- Save model pickles as `models/<modelID>.pkl` with **metadata exactly matching** `contracts/model_artifact.schema.yaml` (`modelID`, `species`, `algorithm`, `trainPeriod`, `testPeriod`, `auc`, `tss`, `filePath`, `seed`).  
- Validate each model artifact against `contracts/model_artifact.schema.yaml`.  

## Phase 4 – Evaluation & Projection (FR‑009, SC‑001, SC‑002, SC‑004, SC‑005)
1. **Bias‑corrected evaluation** on the recent 2005‑2020 test set: background points are sampled according to the **recent** bias‑layer (`bias_layer_recent.tif`) (FR‑017).  
2. **Calibration check**: compute Brier score; models with Brier ≥ 0.2 are excluded from projection.  
3. **Performance metrics**: compute AUC, TSS, and Brier on recent occurrences; verify that AUC ≥ 0.70 relative to a null model (SC‑001).  
4. **Future projection**: predict suitability on 2050 SSP2‑4.5 rasters.  
5. **MESS analysis**: calculate the Multivariate Environmental Similarity Surface between historical and future climate layers; mask non‑analogous pixels.  
6. **ΔAUC/TSS**: compute the calibrated difference between **historic spatial‑block CV performance** (baseline) and the **recent test‑set performance** (2005‑2020). Store as `delta_auc` and `delta_tss`.  
7. **Composite niche‑stability score**: weighted combination of calibrated ΔAUC/TSS and the MESS‑derived proportion of analog climate space, distinguishing model transferability from genuine niche change.  
8. **Threshold sweep**: evaluate five probability thresholds covering a low to moderate range.; record false‑positive/negative rates.  
9. **Hierarchical bootstrap** (≤ 500 iterations, respecting FR‑019):  
   - Level 1: resample species with replacement (max 5 species).  
   - Level 2: within each species, resample spatial blocks.  
   - Compute confidence intervals for each metric.  
10. **Multiple‑comparison correction**: apply Benjamini‑Hochberg (FDR = 0.05).  
11. **Performance‑metric records**: write individual entries (`performance_metric.json`) for each metric (AUC, TSS, Brier, ΔAUC, MESS) and **validate** them against `contracts/performance_metric.schema.yaml`.  
12. **Model‑metrics JSON**: write `metrics/model_performance.json` containing **all required fields** from `contracts/model_metrics.schema.yaml` (`model_id`, `species`, `algorithm`, `test_set_period`, `auc`, `tss`, `threshold`, `sample_size`, `status`, `delta_auc`, `calibration_brier`, `mop_proportion`, `composite_stability`, `p_value`, `effect_size`, `corrected_p_value`).  
13. Output `results/summary_table.csv` and `logs/evaluate.log`.  

All metric files are validated against `contracts/model_metrics.schema.yaml` and `contracts/performance_metric.schema.yaml`.  

## Phase 5 – Reporting (FR‑001, FR‑002, FR‑009)
- Generate `reports/findings.md` containing tables, ROC curves, calibration plots, MESS maps, bootstrap confidence intervals, and the mandatory disclaimer:  
  > **Findings are associational and assume niche stability**.  

- All numbers are read directly from JSON/YAML artifacts, satisfying Constitution Principle IV (single source of truth).

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic scripts, full pipeline can be re‑run on a fresh runner. |
| II. Verified Accuracy | PASS | Phase 0 runs Reference‑Validator on every external URL; results stored in `data/manifest.json`. |
| III. Data Hygiene | PASS | Raw files immutable; SHA‑256 checksums recorded; each transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | PASS | All figures/tables derived from files in `metrics/`, `results/`, and `reports/`. |
| V. Versioning Discipline | PASS | `code/versioning.py` (not shown) updates the project state after each artifact; hashes recorded in `state/projects/...yaml`. |
| VI. Ecological Data Provenance | PASS | Occurrence CSVs include `source_id`, `download_timestamp`, and `dataset_name`; climate rasters have provenance files. |
| VII. Model Evaluation Transparency | PASS | Metrics JSON includes AUC, TSS, Brier, p‑values, effect sizes, seed, and the script version. |

## Compute Feasibility
- All libraries run on CPU; the most intensive step (hierarchical bootstrap) is limited to **500 iterations** across **≤ 5 species**, estimated < 3 h on the free‑tier runner.  
- Raster streaming keeps RAM ≤ 4 GB.  
- No GPU dependencies; any accidental CUDA detection aborts early.  

---

