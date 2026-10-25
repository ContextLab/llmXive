# Implementation Plan: Ambient Temperature Influence on Moral Decision Speed

**Branch**: `001-ambient-temp-moral-speed` | **Date**: 2026-10-24 | **Spec**: `specs/001-ambient-temperature-influence-on-moral-d/spec.md`  
**Input**: Feature specification from `/specs/001-ambient-temperature-influence-on-moral-d/spec.md`

## Summary
The project will **examine the association** between ambient temperature (hourly ERA5, 2014‑2018) and **response latency** in moral decisions. All interpretations will be framed as *associations* rather than causal effects, reflecting the observational nature of the data.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`):  
  `pandas==2.2.*`, `numpy==1.26.*`, `xarray==2024.*`, `geopy==2.4.*`, `statsmodels==0.14.*`, `matplotlib==3.8.*`, `seaborn==0.13.*`, `requests==2.32.*`, `rasterio==1.3.*` (optional GHSL raster), `llmxive_toolkit` (project utilities).  
- **Storage**: `data/raw/`, `data/processed/`, `results/`.  
- **Compute**: CPU‑first on GitHub Actions free tier (2 CPU cores, ≤7 GB RAM, ≤6 h). No GPU required.  
- **Target Platform**: Linux runner (default CI environment).  

## Constitution Check
| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| I. Reproducibility | ✅ | `requirements.txt` pins versions; random seeds in `code/config.py`; deterministic data fetching. |
| II. Verified Accuracy | ✅ | `validate_sources.py` enforces hourly ERA5 (2014‑2018) and aborts otherwise (FR‑014). |
| III. Data Hygiene | ✅ | Checksums recorded in `data/external/checksums.txt`; raw files immutable; derived files have new filenames. |
| IV. Single Source of Truth | ✅ | All downstream artifacts trace back to `data/processed/merged_dataset.parquet` (FR‑017). |
| V. Versioning | ✅ | Artifact hashes stored in project state YAML (Principle V). |
| VI. Dataset Alignment Integrity | ✅ | Geographic matching logs distance; flags > 100 km (FR‑009). Temporal alignment uses hourly ERA5 (FR‑001). |
| VII. Statistical Modeling Transparency | ✅ | Mixed‑effects model specification, diagnostics, LRT results saved as JSON; scripts committed (Principle VII). |

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
├── download_moral_machine.py   # fetches public CSV (no verified URL required)
├── download_era5.py            # **downloads a spatially‑filtered ERA5 subset** (see Phase 2)
├── download_ghsl.py            # optional GHSL urban/rural raster (verified URL)
├── validate_sources.py         # FR‑014 enforcement
├── ingestion.py                # geographic join, distance flagging, temperature merge
├── preprocessing.py            # filtering, feature engineering, response‑time check (FR‑016)
├── modeling.py                 # MixedLM on log‑RT with random intercepts
├── robustness.py               # alternative specs, sensitivity sweeps, indoor/outdoor analysis
├── power_analysis.py           # simulation‑based a‑priori power analysis (detailed params)
└── utils.py                    # logging, checksum helpers
```

```
data/
├── raw/
│   ├── moral_machine.csv            # public Moral Machine responses
│   ├── era5_subset.h5               # **spatially‑filtered ERA5 subset** covering only the convex hull of Moral Machine locations (≈ few hundred MB) (verified)
│   └── ghsl_urban_rural.parquet    # optional GHSL classification (verified)
└── processed/
    └── merged_dataset.parquet
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

## Phase / Task Overview (Mapping to FR/SC)

| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|----------------|-----------------|
| **0** | **Setup & Validation** – install env, pin seeds. | – | – |
| **1** | **Download Moral Machine CSV** (`download_moral_machine.py`). | – | – |
| **2** | **Download ERA5 (hourly, 2014‑2018) – spatial subset** (`download_era5.py`). The script first reads the Moral Machine location file, computes the convex hull, and then downloads **only the ERA5 grid cells intersecting that hull** (≈ few hundred MB) via the Copernicus Climate Data Store API. This satisfies compute constraints and respects the hourly‑resolution requirement. | FR‑001, FR‑014 | – |
| **3** | **(Optional) Download GHSL raster** (`download_ghsl.py`). | FR‑012 (indoor/outdoor proxy) | – |
| **4** | **Validate Sources** (`validate_sources.py`). Abort if ERA5 not hourly. | FR‑014 | – |
| **5** | **Ingest & Match** (`ingestion.py`): nearest‑grid join, compute haversine distance, flag > 100 km (FR‑009), merge temperature, compute match % (SC‑001). | FR‑001, FR‑009, FR‑002 | SC‑001 |
| **6** | **Preprocess** (`preprocessing.py`):<br>• **Merge auxiliary latency data by `scenario_id`** (not `response_id`). The file `aux_response_times.csv` must contain `scenario_id` and `mean_response_time_ms`; the script left‑joins to assign each Moral Machine record the *scenario‑level* average latency (FR‑016). If any scenario lacks a latency entry the script aborts with a clear error.<br>• Verify presence of `response_time_ms`; abort if any scenario lacks it.<br>• Filter implausible RTs (<100 ms, >10 000 ms) (FR‑010).<br>• Derive `log_rt`, `dilemma_complexity` (FR‑011), `time_of_day`, age/gender covariates (FR‑004).<br>• Apply temperature range filter (FR‑002).<br>• Write `merged_dataset.parquet`. | FR‑003, FR‑004, FR‑010, FR‑011, FR‑018 | – |
| **7** | **Fit Primary Mixed‑Effects Model** (`modeling.py`): log‑RT ~ temperature (+ quadratic) + covariates, random intercepts for participant & cultural region (FR‑003, FR‑013). Save diagnostics, convergence flag (SC‑004), Shapiro‑Wilk p‑value (SC‑005). | FR‑003, FR‑013, FR‑005 | SC‑004, SC‑005 |
| **8** | **Likelihood‑Ratio Test** (null model without temperature) – records test statistic & p‑value (FR‑005, SC‑002). | FR‑005 | SC‑002 |
| **9** | **Non‑Linearity Decision** – compare AIC/BIC of linear vs. quadratic model; retain lower‑AIC model (FR‑013). | FR‑013 | SC‑002 |
| **10** | **Robustness & Sensitivity Analyses** (`robustness.py`):<br>• Alternative temperature metric (3‑hour moving average).<br>• Temperature outlier thresholds (±2 SD, ±3 SD, ±4 SD) sweep (FR‑006).<br>• Indoor/outdoor confound: include GHSL `urban_rural_proxy` if available; otherwise perform 1 000 bootstrap resamples assigning random urban/rural labels (preserving overall proportions) and report the 95 % CI width of the temperature coefficient (noise impact metric). **Limitation**: Both GHSL and bootstrap are imperfect proxies for actual indoor/outdoor exposure; the temperature coefficient should be interpreted as an association, not a causal effect.<br>• Multiple‑comparison correction (Benjamini‑Hochberg).<br>• Generate comparison table & figures saved in `results/`. (SC‑003) | FR‑006, FR‑012 | SC‑003 |
| **11** | **Power & Sample Size Analysis** (`power_analysis.py`): simulation‑based a‑priori power analysis (α = 0.05, d≈0.1, target = 0.8).<br>**Parameters** (used in the script):<br> - Fixed‑effect variance = 0.02<br> - Random‑effect ICC ≈ 0.05 (participant & region)<br> - Number of cultural regions ≈ 200<br> - Number of simulations = 5 000<br> - Effect size = 0.1 (standardized)<br> - α = 0.05<br>Estimated required N is on the order of **20 000** records; the Moral Machine dataset exceeds this. Results written to `results/logs/power_analysis.txt`. | FR‑015 | – |
| **12** | **Export Artifacts** (`results/`): model coefficients, p‑values, diagnostic plots, LRT stats, robustness tables (FR‑008). | FR‑008 | – |

All steps respect ordering (download → validation → ingestion → preprocessing → modeling → diagnostics → reporting).  

---

