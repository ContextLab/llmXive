# Implementation Plan: Ambient Temperature Influence on Moral Decision Speed

**Branch**: `001-ambient-temp-moral-speed` | **Date**: 2026-10-16 | **Spec**: `specs/001-ambient-temp-influence-on-moral-d/spec.md`  
**Input**: Feature specification from `/specs/001-ambient-temp-influence-on-moral-d/spec.md`

## Summary
The study will test whether ambient temperature influences **response latency** in moral decisions, using the **hourly ERA5 reanalysis** (2014‑2018) merged with the Moral Machine dataset. When a dataset with `response_time_ms` becomes available, the full mixed‑effects analysis will run as described below.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**:
- `pandas==2.2.*`
- `numpy==1.26.*`
- `xarray==2024.*` (for ERA5 hourly data)
- `geopy==2.4.*`
- `statsmodels==0.14.*`
- `matplotlib==3.8.*`, `seaborn==0.13.*`
- `requests==2.32.*`
- `rasterio==1.3.*` (WorldPop raster for indoor/outdoor proxy)
- `llmxive_toolkit` (project utilities)

**Storage**: `data/raw/`, `data/processed/`, `results/`.  
**Compute**: CPU‑first on GitHub Actions free tier (2 CPU cores, ≤7 GB RAM, ≤6 h). No GPU required.

## Constitution Check

| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| I. Reproducibility | ✅ | `requirements.txt` pins exact versions; random seeds in `code/config.py`; deterministic data fetching. |
| II. Verified Accuracy | ✅ | `validate_sources.py` enforces hourly ERA5 (2014‑2018) and aborts otherwise (FR‑014). |
| III. Data Hygiene | ✅ | Checksums recorded; raw files immutable; derived files have new filenames. |
| IV. Single Source of Truth | ✅ | All downstream artifacts trace back to `data/processed/merged_dataset.parquet`. |
| V. Versioning | ✅ | Artifact hashes stored in project state YAML. |
| VI. Dataset Alignment Integrity | ✅ | Geographic matching logs distance, flags > 100 km (FR‑009). Temporal alignment uses hourly ERA5 (2014‑2018). |
| VII. Statistical Modeling Transparency | ✅ | Mixed‑effects model specification, diagnostics, and LRT results saved as JSON; scripts committed. |

## Project Structure
```
specs/001-ambient-temperature-influence-on-moral-d/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── exclusion_log.schema.yaml
│   ├── merged_dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── moral_temperature.schema.yaml
└── tasks.md   # generated later
```

```
code/
├── __init__.py
├── config.py                # seeds, thresholds, paths
├── download_moral_machine.py   # fetches public CSV
├── download_era5.py            # fetches hourly ERA5 (2014‑2018) from verified HF URL
├── download_worldpop.py        # optional indoor/outdoor proxy
├── validate_sources.py         # FR‑014 enforcement
├── ingestion.py                # geographic join, distance flagging, hourly temp merge
├── preprocessing.py            # filtering, response‑time check, feature engineering
├── modeling.py                 # MixedLM on log‑RT with cluster‑robust SE
├── robustness.py               # alternative specs, sensitivity sweeps, indoor/outdoor analysis
└── utils.py                    # logging, checksum helpers
```

```
data/
├── raw/
│   ├── moral_machine.csv
│   └── era5_2014_2018.h5            # hourly ERA5 (2014‑2018)
├── processed/
│   └── merged_dataset.parquet
└── external/
    └── checksums.txt
```

```
results/
├── figures/
│   ├── qq_plot.png
│   ├── residuals.png
│   ├── calibration_plot.png
│   └── temperature_effect.png
├── logs/
│   ├── processing_log.txt
│   └── validation_report.json
└── stats/
    ├── model_results.json
    └── sensitivity_analysis.csv
```

## Phase / Task Overview (8–12 steps)

1. **Download Moral Machine CSV** (`code/download_moral_machine.py`).  
2. **Download Hourly ERA5 (2014‑2018)** (`code/download_era5.py`).  
3. **Validate Sources** (`code/validate_sources.py`) – aborts if ERA5 is not hourly (FR‑014).  
4. **(Optional) Download WorldPop raster** (`code/download_worldpop.py`) for indoor/outdoor proxy.  
5. **Ingest & Match** (`code/ingestion.py`): nearest‑grid join (lat/long), compute haversine distance, flag > 100 km (FR‑009), merge hourly temperature.  
   - **Validate** the raw merged file against `contracts/moral_temperature.schema.yaml`.  
6. **Preprocess** (`code/preprocessing.py`):  
   - Verify presence of `response_time_ms`; abort with informative error if missing (FR‑003, FR‑010).  
   - Filter implausible RTs (<100 ms or >10 000 ms) (FR‑010).  
   - Encode `choice_binary`, derive `dilemma_complexity`, `time_of_day`, etc.  
   - **Validate** the processed file against `contracts/merged_dataset.schema.yaml`.  
   - Write `data/processed/merged_dataset.parquet`.  
7. **Fit Primary Mixed‑Effects Model** (`code/modeling.py`):  
   - Dependent: `log(response_time_ms)`.  
   - Fixed effects: `temperature_c`, `temperature_c_squared`, dilemma complexity, time‑of‑day, age, gender.  
   - Random intercepts: `participant_id`, `cultural_region`.  
   - Cluster‑robust SE, convergence check (SC‑004).  
8. **Likelihood‑Ratio Test** against null model without temperature (FR‑005).  
9. **Non‑Linearity Test** (quadratic temperature term) and compare AIC/BIC (FR‑013).  
10. **Robustness & Sensitivity Analyses** (`code/robustness.py`):  
    - Alternative temperature metric (3‑hour moving average).  
    - Temperature outlier thresholds (2, 3, 4 SD) sweep (FR‑006).  
    - Indoor/outdoor confound: include WorldPop urban/rural proxy when available; otherwise log limitation and perform sensitivity (FR‑012).  
    - Multiple‑comparison correction (Benjamini‑Hochberg).  
11. **Power & Sample Size** (`code/power_analysis.py`): simulation‑based a‑priori power analysis (α = 0.05, d ≈ 0.1, target = 0.8) → required N ≈ 20 000; write `results/logs/power_analysis.txt` (FR‑015).  
12. **Export All Artifacts** (`results/`): model coefficients, p‑values, diagnostic plots, LRT statistics, robustness tables (FR‑008).

All steps respect ordering (download → validation → ingestion → preprocessing → modeling → diagnostics → reporting).  

---

