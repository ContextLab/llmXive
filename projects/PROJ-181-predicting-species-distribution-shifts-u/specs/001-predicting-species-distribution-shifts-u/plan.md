# Implementation Plan: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Branch**: `001-predicting-species-distribution-shifts` | **Date**: 2024-10-18 | **Spec**: `specs/001-predicting-species-distribution-shifts/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-species-distribution-shifts/spec.md`

## Summary
Build a fully reproducible, CPU‑only pipeline that (1) downloads open North‑American bird occurrence records (historical 1970‑2000 and recent 2005‑2020) via GBIF/eBird APIs and climate rasters from WorldClim v2.1/CMIP6, (2) preprocesses them (breeding‑season filter, duplicate removal, spatial thinning at ≥10 km or dynamic 95 th‑percentile distance, VIF collinearity screening, bias‑layer creation, climate extraction, **simulation‑based power analysis**, and **data‑acquisition completeness** reporting), (3) trains three SDM algorithms (Random Forest, Bioclim, MaxEnt‑style surrogate) using spatial block cross‑validation (5 × 5 grid, K = 5), (4) evaluates models on recent records **with bias‑layer‑corrected background sampling**, (5) projects onto a 2050 SSP2‑4.5 scenario, (6) quantifies niche stability via **ΔAUC after MOP‑only extrapolation masking** and a **composite stability score**, (7) performs a **hierarchical bootstrap (500 iterations)** and Benjamini‑Hochberg correction across the five probability‑threshold sweep {0.40, 0.45, 0.50, 0.55, 0.60}, and (8) generates a markdown report with the required disclaimer. All artifacts are validated against JSON/YAML contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scikit-learn==1.5.0`, `geopandas==0.14.2`, `rasterio==1.3.9`, `pandas==2.2.2`, `numpy==1.26.4`, `pygbif==0.13.0`, `tqdm==4.66.2`, `statsmodels==0.14.2`, `matplotlib==3.8.4`, `seaborn==0.13.2`, `requests==2.32.3`, `pyyaml==6.0.1`  
- **Storage**: Local filesystem (`data/`, `models/`, `metrics/`, `logs/`)  
- **Testing**: `pytest` with schema‑validation fixtures  
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h)  
- **Constraints**: CPU‑only execution; all external data must be openly downloadable; total runtime ≤ 360 min (SC‑002)  

## Phase 0 – Data‑Source Verification (Principle II)
1. Run the **Reference‑Validator Agent** on every external URL (GBIF/eBird API docs, WorldClim download pages).  
2. Record verification outcomes in `data/manifest.json`.  
3. Abort the pipeline if any URL fails verification.  
*This satisfies Constitution Principle II (Verified Accuracy).*

## Phase 1 – Download (FR‑001, FR‑002, T004, T010)
- Stream occurrence records via `pygbif` with exponential back‑off and retry logic.  
- Stream WorldClim v2.1 (historical) and CMIP6 (future) raster tiles using `datasets.load_dataset(..., streaming=True)`.  
- For each raster tile, compute SHA‑256 checksum and compare against the official checksum listed on the WorldClim website; abort on mismatch.  
- Populate `data/manifest.json` with URLs, timestamps, file sizes, and checksums.  

## Phase 2 – Preprocess (FR‑003, FR‑014, FR‑009, FR‑006, FR‑011, FR‑015, SC‑004)
1. **Breeding‑season filter**, duplicate removal.  
2. **Spatial thinning**: compute nearest‑neighbor distances; use the 95th percentile or fallback to 10 km (FR‑014).  
3. **Bias‑layer**: generate a kernel‑density raster of observation effort; store as `data/processed/bias_layer.tif`.  
4. **Collinearity mitigation**: calculate VIF; drop variables with VIF > 10.  
5. **Climate extraction**: sample rasters at occurrence points; nearest‑neighbor impute missing cells.  
6. **Data‑sufficiency & Power analysis**:  
   - Count thinned records per species.  
   - Perform a **simulation‑based power analysis**: bootstrap AUC values **500 times** for each species, compute empirical power to detect a ΔAUC = 0.05 (Cohen’s h = 0.50).  
   - Flag species with `<100` records **or** power < 0.8 as `INSUFFICIENT_DATA` (FR‑006, FR‑011).  
   - Write results to `metrics/data_sufficiency.json`.  
7. **Data‑acquisition completeness (SC‑004)**:  
   - Compute proportion of species with ≥100 thinned records.  
   - Compute proportion of records with non‑null climate values.  
   - Write summary to `metrics/data_acquisition_completeness.json`.  
8. Log before/after counts to `logs/preprocess_counts.yaml` (validated against `contracts/log_counts.schema.yaml`).  

## Phase 3 – Model Training (FR‑004, FR‑007, FR‑008)
- Verify no CUDA devices via `utils/gpu_check.py`; abort if detected.  
- Perform **5‑fold spatial block CV** (equidistant 5 × 5 grid).  
- Train Random Forest (`n_estimators=500`), Bioclim (range envelope), and MaxEnt‑style surrogate (logistic regression on VIF‑filtered predictors).  
- Save models as pickle files under `models/` and validate against `contracts/model_artifact.schema.yaml`.  

## Phase 4 – Evaluation & Projection (FR‑005, FR‑009, FR‑010, SC‑001, SC‑003)
1. **Bias‑corrected evaluation**: use the same bias‑layer for background sampling when evaluating on the recent test set (2005‑2020).  
2. Compute **AUC**, **TSS**, and **Brier score** on recent records; require Brier < 0.2 before projection.  
3. **Future projection**: predict suitability on 2050 SSP2‑4.5 rasters.  
4. **MOP‑only analysis**: calculate the Mobility‑Oriented Parity (MOP) similarity between historical and future climate spaces; mask out non‑analogous pixels.  
5. **ΔAUC after MOP masking**: compute calibrated AUC decline only on analog climate pixels; store as `delta_auc`.  
6. **Composite niche‑stability score**: weighted combination of calibrated ΔAUC and MOP proportion.  
7. **Threshold sweep**: evaluate thresholds {0.40, 0.45, 0.50, 0.55, 0.60}; record false‑positive/negative rates.  
8. **Hierarchical bootstrap**:  
   - Level 1: resample species (multiple species) with replacement.  
   - Level 2: within each species, resample spatial blocks.  
   - Perform **500 iterations** (fits CI budget).  
   - Apply Benjamini‑Hochberg correction (FDR = 0.05) across the five thresholds.  
9. Output `metrics/model_performance.json`, `results/summary_table.csv`, and `logs/evaluate.log`.  

## Phase 5 – Reporting (FR‑008)
- Generate `reports/findings.md` containing tables, ROC curves, calibration plots, MOP maps, bootstrap confidence intervals, and the mandatory disclaimer:  
  > **Findings are associational and assume niche stability**.  
- All numbers are read from JSON/YAML artifacts, satisfying Constitution Principle IV.

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Pin versions, set seeds, deterministic scripts. |
| II. Verified Accuracy | PASS | Phase 0 runs Reference‑Validator on all external URLs; results stored in `data/manifest.json`. |
| III. Data Hygiene | PASS | Raw files immutable; SHA‑256 checksums recorded; transformations produce new files. |
| IV. Single Source of Truth | PASS | All figures/tables derive from `metrics/` and `results/` files. |
| V. Versioning Discipline | PASS | `code/versioning.py` updates project state after each artifact. |
| VI. Ecological Data Provenance | PASS | Occurrence CSVs include provenance columns; climate rasters have provenance file. |
| VII. Model Evaluation Transparency | PASS | Metrics saved with effect size, p‑value, seed, and script version. |

## Compute Feasibility
- All steps use CPU‑only libraries; the most intensive step (hierarchical bootstrap) is limited to **500 iterations** on **8 species** → estimated < 3 h on the free‑tier runner.  
- Streaming raster downloads keep RAM ≤ 4 GB.  

---



