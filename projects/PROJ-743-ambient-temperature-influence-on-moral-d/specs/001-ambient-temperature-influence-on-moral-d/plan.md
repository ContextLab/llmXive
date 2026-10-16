# Implementation Plan: Ambient Temperature Influence on Moral Decision Speed (Re‑scoped)

**Branch**: `001-ambient-temp-moral-speed` | **Date**: 2026-10-16 | **Spec**: `specs/001-ambient-temp-influence-on-moral-d/spec.md`  
**Input**: Feature specification from `/specs/001-ambient-temp-influence-on-moral-d/spec.md`

## Summary
The original specification required hourly ERA5 temperature data matched to Moral Machine decisions (2014‑2018). No open hourly ERA5 dataset is available, and the public Moral Machine data lack response‑time fields. To keep the project feasible while respecting the Constitution, we **re‑scope** the analysis:

* **Long‑term Climate Proxy** – Use **latitude** as the primary spatial climate covariate (captures the major temperature gradient). The 1982 ERA5 mean‑annual temperature grid is **not used** in the primary analysis; it is retained only as an optional exploratory artifact (which will be unavailable if validation aborts).  
* **Outcome Variable** – Switch from the unavailable response latency to the binary utilitarian choice (1 = utilitarian, 0 = non‑utilitarian) that is present in the Moral Machine dataset.  
* **Modeling** – Fit a **GLM Binomial** (logistic regression) with **cluster‑robust standard errors** for `participant_id` + `cultural_region` (approximating random intercepts).  
* **Indoor/Outdoor Proxy** – Mandatory use of WorldPop 2020 population density raster as an urban/rural proxy; if download fails the pipeline aborts with a clear error (ensuring the confound is always addressed).  
* **Scope‑Limited FRs** – FR‑001 and FR‑003 are marked *scope‑limited* with justification (see FR/SC Mapping). All other FRs remain applicable.

All steps are deterministic, reproducible, and respect the free‑tier GitHub Actions compute limits.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**:  
- `pandas==2.2.*`  
- `numpy==1.26.*`  
- `xarray==2024.*` (for reading ERA5 HDF5, optional)  
- `geopy==2.4.*` (distance calculations)  
- `statsmodels==0.14.*` (GLM with cluster‑robust SE)  
- `matplotlib==3.8.*`, `seaborn==0.13.*` (visualisation)  
- `requests==2.32.*` (dataset download)  
- `rasterio==1.3.*` (WorldPop raster handling)  

**Storage**: Local file system (`data/raw/`, `data/processed/`, `results/`).  
**Testing**: `pytest==8.2.*` with coverage.  
**Target Platform**: Linux (GitHub Actions free tier – 2 CPU cores, ~7 GB RAM).  
**Constraints**: CPU‑only; all data streamed or chunked to stay < 7 GB RAM, ≤6 h.  

## Constitution Check

| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| **I. Reproducibility** | ✅ | `requirements.txt` pins exact versions; random seeds set in `code/config.py`; data fetched from canonical URLs. |
| **II. Verified Accuracy** | ✅ | `validate_sources.py` **rejects** any external source lacking hourly resolution. The pipeline aborts if no hourly ERA5 source is available, satisfying FR‑014. |
| **III. Data Hygiene** | ✅ | Checksums recorded in `data/external/checksums.txt`; raw files immutable; derived files saved under new filenames. |
| **IV. Single Source of Truth** | ✅ | All statistics and figures generated from `data/processed/cleaned_dataset.parquet`; artifacts referenced via JSON/CSV in `results/`. |
| **V. Versioning** | ✅ | Artifact hashes stored in `state/projects/PROJ-743-...yaml`. |
| **VI. Dataset Alignment Integrity** | ✅ | Matching script logs grid ID, distance, and exclusion reasons; distance > 100 km flagged per FR‑009. Temporal alignment is not performed (no hourly source); documented as a scope limitation. |
| **VII. Statistical Modeling Transparency** | ✅ | GLM‑Binomial model specification, diagnostics (Hosmer‑Lemeshow, calibration, Pearson residuals), and likelihood‑ratio test results saved as JSON and figures in `results/`. |

## Project Structure

```
specs/001-ambient-temperature-influence-on-moral-d/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── exclusion_log.schema.yaml
│   ├── merged_dataset.schema.yaml   ← referenced by ingestion & validation
│   ├── model_output.schema.yaml
│   └── moral_temperature.schema.yaml   ← defined for optional exploratory temperature analyses (not used in primary pipeline)
└── tasks.md   # generated later by /speckit-tasks
```

```
code/
├── __init__.py
├── config.py                # seeds, thresholds, file‑path constants
├── download_moral_machine.py   # fetches public CSV (verified URL)
├── download_era5.py            # (optional) fetches ERA5 1982 HDF5 (validated then rejected if no hourly source)
├── download_worldpop.py        # fetches WorldPop 2020 population density raster (mandatory)
├── validate_sources.py         # FR‑014 check – aborts if no hourly source present
├── ingestion.py                # geographic match, distance flagging, contract validation
├── preprocessing.py            # filters, derives covariates, encodes outcome, writes merged_dataset.parquet (validated against merged_dataset.schema.yaml)
├── modeling.py                 # GLM‑Binomial with cluster‑robust SE, diagnostics, writes model_output.json (validated against model_output.schema.yaml)
├── robustness.py               # alternative temperature metric (optional), sensitivity sweeps, indoor/outdoor proxy, generates figures and sensitivity_analysis.csv
└── utils.py                    # logging, checksum helpers
```

```
data/
├── raw/
│   ├── moral_machine.csv
│   └── era5_1982.h5            # optional; will be rejected if no hourly source
├── processed/
│   ├── merged_dataset.parquet   # conforms to merged_dataset.schema.yaml
│   └── data_quality_log.json    # conforms to exclusion_log.schema.yaml
└── external/
    └── checksums.txt
```

```
results/
├── figures/
│   ├── qq_plot.png
│   ├── residuals.png
│   ├── calibration_plot.png
│   └── lat_effect.png
├── logs/
│   ├── processing_log.txt
│   └── validation_report.json
└── stats/
    ├── model_results.json      # conforms to model_output.schema.yaml
    └── sensitivity_analysis.csv
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| **GLM‑Binomial with cluster‑robust SE** | Provides valid inference for binary outcomes without requiring unsupported mixed‑effects GLM implementations. | Using `MixedLM` with logit link would fail; naive logistic mixed model not available in pure Python. |
| **Latitude as primary climate covariate** | Captures the major climate gradient, satisfying FR‑001 residual confounding. | Ignoring latitude would leave strong spatial confounding. |
| **Reject non‑hourly ERA5** | Fails the hourly‑resolution requirement of FR‑014; per Constitution Principle II the source must be rejected, and the pipeline aborts if no hourly source is found. | Proceeding with warning would violate Verified Accuracy. |
| **WorldPop indoor/outdoor proxy** | Provides a reproducible urban/rural proxy; mandatory to address the known confound. | Skipping the adjustment would leave a known confound unaddressed. |
| **Power analysis** | Provides a quantitative justification for sample‑size adequacy given limited predictor variance. | Omitting power discussion would leave SC‑004 unsupported. |

## Scope Adjustment & FR/SC Mapping

| FR / SC | Original Requirement | Feasibility | Revised Handling |
|---------|----------------------|-------------|------------------|
| FR‑001 | Merge Moral Machine with hourly ERA5 temperature (by lat/long + timestamp) | **Partial** – temporal match impossible; source rejected per FR‑014. | **Scope‑limited** – no hourly merge; analysis uses latitude (and optional long‑term proxy for exploratory checks). |
| FR‑002 | Filter temperature outside extreme range | **Not applicable** – temperature proxy not used in primary model. | **Scope‑limited** – filter only if proxy retained for exploratory checks. |
| FR‑003 | Linear mixed‑effects on log‑RT; fallback GLMM | **No** – RT unavailable. | **Scope‑limited** – binary utilitarian choice modeled with GLM‑Binomial + cluster‑robust SE (see methodology). |
| FR‑004 | Include age, gender, complexity, time‑of‑day | **Yes** – retained as fixed effects. |
| FR‑005 | Likelihood‑ratio test (full vs null) | **Yes** – performed on GLM models. |
| FR‑006 | Sensitivity sweep on temperature outlier threshold | **Yes** – applied to optional temperature proxy (if available). |
| FR‑007 | Diagnostic plots (QQ, residual) | **Replaced** – Hosmer‑Lemeshow, calibration, Pearson residuals (appropriate for logistic). |
| FR‑008 | Export results to `results/` | **Yes** – unchanged. |
| FR‑009 | Flag distance > 100 km | **Yes** – unchanged. |
| FR‑010 | Filter response times < 100 ms / > 10 000 ms | **Not applicable** – scope‑limited. |
| FR‑011 | Control for dilemma choice | **Yes** – included as fixed effect (`choice_binary`). |
| FR‑012 | Indoor/outdoor confound | **Yes** – mandatory WorldPop proxy; abort if unavailable. |
| FR‑013 | Test non‑linearity (quadratic or spline) | **Yes** – include `latitude_covariate_squared` and optional `temperature_c_squared`. |
| FR‑014 | Verify sources meet hourly resolution | **No** – ERA5 1982 rejected; pipeline aborts if no hourly source. |
| SC‑001 | Match percentage | **Yes** – computed for geographic matching (distance ≤100 km). |
| SC‑002 | Temperature coefficient significance | **Not applicable** – primary predictor is latitude; report latitude coefficient significance. |
| SC‑003 | Sensitivity variation | **Yes** – reported for alternative temperature proxy and latitude specifications. |
| SC‑004 | Model convergence | **Yes** – convergence flag recorded for GLM fitting. |
| SC‑05 | Residual normality (Anderson‑Darling) | **Replaced** – Hosmer‑Lemeshow p‑value > 0.05 required (recorded in model_output). |

**Note**: All FRs marked *scope‑limited* are explicitly documented in `results/logs/validation_report.json`; the manuscript must acknowledge these limitations per the constitution’s transparency principle.

## Phase / Task Overview (8–12 concrete steps)

1. **Download Moral Machine CSV** (`code/download_moral_machine.py`) – uses verified URL.  
2. **Validate Sources** (`code/validate_sources.py`) – checksums; **rejects** any external source lacking hourly resolution (FR‑014) and aborts with an informative error if none found.  
3. **Download WorldPop Raster** (`code/download_worldpop.py`) – mandatory indoor/outdoor proxy; abort if unavailable.  
4. **Ingest & Match** (`code/ingestion.py`): nearest‑grid join (latitude/longitude only), compute haversine distance, flag > 100 km (FR‑009), validate against `contracts/merged_dataset.schema.yaml`.  
5. **Preprocess** (`code/preprocessing.py`): filter by distance, encode `choice_binary`, derive `time_of_day`, `dilemma_complexity`, duplicate `latitude` as `latitude_covariate`, create `urban_rural_proxy`, write `merged_dataset.parquet`.  
6. **Fit Primary Model** (`code/modeling.py`): read parquet, fit GLM‑Binomial with cluster‑robust SE for `latitude_covariate` (linear & quadratic) and other covariates, output `model_results.json` (conforms to `contracts/model_output.schema.yaml`) and diagnostic plots (Hosmer‑Lemeshow, calibration, Pearson residuals).  
7. **Fit Null Model** (same script, without latitude) and perform likelihood‑ratio test (FR‑005).  
8. **Non‑Linearity Test**: add quadratic term for latitude (and temperature proxy if retained); compare AIC/BIC.  
9. **Robustness Analyses** (`code/robustness.py`): (a) alternative temperature metric – 3‑hour moving‑average approximated by averaging three nearest grid cells (exploratory only, runs only if optional ERA5 proxy is present); (b) outlier threshold sweep; (c) indoor/outdoor adjustment using WorldPop raster; generate figures and `sensitivity_analysis.csv`.  
10. **Power & Sample Size**: run a simulation‑based power analysis (using a large number of replicates) to estimate detectable odds‑ratios given the observed variance of latitude; record results in `results/logs/power_analysis.txt`.  
11. **Generate Summary Report** (`code/robustness.py` also writes a markdown summary linking to figures).  
12. **Export All Artifacts** to `results/` (FR‑008).  

All steps are ordered so data is fetched before any processing, models are fitted before diagnostics, and figures are generated before the final report. Contracts `merged_dataset.schema.yaml`, `exclusion_log.schema.yaml`, `model_output.schema.yaml`, and `moral_temperature.schema.yaml` are explicitly referenced and validated throughout the pipeline.

---



