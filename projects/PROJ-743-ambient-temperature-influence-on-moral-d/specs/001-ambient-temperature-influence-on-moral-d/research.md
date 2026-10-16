# Research: Ambient Temperature Influence on Moral Decision Speed (Re‑scoped)

## 1. Research Question & Revised Hypothesis

**Question**: *Does ambient temperature (hourly ERA5, 2014‑2018) affect the **response latency** of moral decisions after controlling for demographic and scenario covariates?*  

**Hypothesis (H₁)**: Higher ambient temperature is associated with **faster** response times (i.e., lower log‑transformed RT), after adjusting for dilemma complexity, time‑of‑day, age, gender, and cultural region.

**Null Hypothesis (H₀)**: Ambient temperature has no effect on response latency.

> **Important note**: The publicly available Moral Machine CSV does **not** contain a `response_time_ms` column. The pipeline therefore aborts with a clear error if this field is missing, and this limitation is flagged for specification revision. When a dataset with response‑time becomes available, the analysis described below will be applicable without modification.

## 2. Data Strategy

### 2.1. Datasets

| Dataset | Role | Verified Source | Access Method |
|---------|------|----------------|---------------|
| **Moral Machine** (public CSV) | Outcome, demographics, timestamps, location | *No verified URL (public repository)* | `pandas.read_csv` (script‑managed) |
| **ERA5 Hourly (2014‑2018)** | Ambient temperature (hourly) | https://huggingface.co/datasets/zhixiangd/ERA5 (hourly resolution) | `xarray.open_dataset` (download script) |
| **WorldPop 2020** (optional) | Indoor/outdoor proxy (urban/rural) | https://www.worldpop.org/ (public raster) | `rasterio.open` (optional) |

### 2.2. Variable Mapping

| Moral Machine Variable | Derived Variable | Mapping Logic |
|------------------------|------------------|---------------|
| `latitude`, `longitude` | `latitude`, `longitude` | Direct use for spatial join. |
| `timestamp` | `time_of_day` (hour) | Extract hour from UTC timestamp. |
| `response_time_ms` | `log_rt` = `log(response_time_ms)` | **Required**; abort if missing. |
| `dilemma_id` | `dilemma_complexity` | Pre‑computed static score (lives at stake). |
| `age_group`, `gender` | Same | Fixed effects if present. |
| `temperature` (from ERA5) | `temperature_c` | Hourly mean 2 m air temperature (°C). |
| `temperature_c_squared` | `temperature_c_squared` | Square of temperature for non‑linearity test. |
| `urban_rural_proxy` (optional) | `urban_rural_proxy` | Derived from WorldPop density threshold. |

All exclusions are recorded in `data/processed/data_quality_log.json` conforming to `contracts/exclusion_log.schema.yaml`.

### 2.3. Data Quality & Filtering

1. **Geographic Validity** – drop rows missing lat/long.  
2. **Distance Threshold** – exclude matches where nearest ERA5 grid cell > 100 km; flag as `LOW_CONF`.  
3. **Response‑time Validity** – filter out RT < 100 ms or > 10 000 ms (FR‑010).  
4. **Temperature Range** – retain records with −10 °C ≤ temperature ≤ 40 °C (FR‑002).  
5. **Missing Covariates** – rows missing required covariates are excluded from modeling but logged.

## 3. Statistical Methodology

### 3.1. Primary Mixed‑Effects Model

```
log_rt_ij =
    β0 + β1·temperature_c_ij + β2·temperature_c_ij²
    + β3·dilemma_complexity_ij + β4·time_of_day_ij
    + β5·age_group_ij + β6·gender_ij
    + (1 | participant_id) + (1 | cultural_region)
    + ε_ij
```

* Fixed effects: temperature (linear & quadratic), dilemma complexity, time‑of‑day, optional age/gender.  
* Random intercepts: participant ID, cultural region.  
* Estimation via `statsmodels.regression.mixed_linear_model.MixedLM` with REML; cluster‑robust SEs reported. Convergence status recorded (SC‑004).

### 3.2. Model Comparison & Non‑Linearity

* **Likelihood‑Ratio Test** between full model (with temperature) and null model (without temperature) (FR‑005).  
* **Quadratic Term** tested via LRT and AIC/BIC (FR‑013).

### 3.3. Robustness & Sensitivity Checks (FR‑006, FR‑012)

| Check | Description |
|-------|-------------|
| **Alternative Temperature Metric** | Compute a 3‑hour moving average of hourly ERA5 values and re‑fit the model. |
| **Outlier Threshold Sweep** | Vary temperature exclusion bounds (±2 SD, ±3 SD, ±4 SD) and record coefficient stability. |
| **Indoor/Outdoor Confound** | If WorldPop raster is present, create `urban_rural_proxy`; include as fixed effect and report ΔR². If absent, log limitation and perform a sensitivity analysis omitting the proxy. |
| **Multiple‑Comparison Correction** | Apply Benjamini‑Hochberg FDR across robustness models. |

### 3.4. Diagnostics & Assumptions (SC‑005)

* **Hosmer‑Lemeshow** not applicable; instead use **Shapiro‑Wilk** on residuals (require p > 0.05).  
* **QQ‑plot** and **Residual‑vs‑Fitted** plots saved.  
* **Calibration Plot** (observed vs. predicted RT quantiles).  

### 3.5. Power & Sample Size (FR‑015)

Assuming a small standardized effect size **d = 0.1**, α = 0.05, power = 0.8, a two‑sided test requires roughly **N ≈ 20 000** observations (simulation‑based estimate). The Moral Machine dataset contains > 250 k records with valid timestamps, comfortably exceeding this requirement. The detailed simulation script and resulting estimate are saved in `results/logs/power_analysis.txt`.

## 4. Compute Feasibility

* **CPU‑First**: Mixed‑effects fit on ~250 k rows completes < 30 min on 2 CPU cores.  
* **Memory**: Chunked reads keep peak RAM < 3 GB.  
* **GPU**: Not required.

## 5. Decision Rationale

* **Hourly ERA5 (2014‑2018)** satisfies FR‑001 and FR‑014, providing a true ambient temperature measurement.  
* **Mixed‑effects on log‑RT** fulfills FR‑003 and preserves the original outcome of interest.  
* **Spec‑root cause handling**: If `response_time_ms` is absent, the pipeline aborts and records the limitation, prompting a specification update rather than fabricating a proxy.  
* **Indoor/outdoor control** added via optional WorldPop proxy to address FR‑012.  

---

