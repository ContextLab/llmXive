# Research: Ambient Temperature Influence on Moral Decision Speed (Re‑scoped)

## 1. Research Question & Revised Hypothesis

**Re‑scoped Question**: *Does the long‑term climatic gradient (proxied by geographic latitude) predict the likelihood of making a utilitarian moral choice (e.g., “save many”) after controlling for dilemma complexity, time‑of‑day, and demographic covariates?*  

**Hypothesis (H₁)**: Higher latitude (i.e., cooler climates) is associated with a lower probability of selecting the utilitarian option, after adjusting for covariates.

**Null Hypothesis (H₀)**: Latitude has no effect on the utilitarian choice probability.

> The original outcome variable (response latency) is unavailable in the public Moral Machine data; the analysis therefore focuses on the binary choice outcome. Because no open hourly ERA5 dataset is available, we use **latitude** as the primary spatial climate covariate. The 1982 mean‑annual ERA5 temperature grid is **not used** in the primary analysis (and will be unavailable if validation aborts). This limitation is explicitly documented and the manuscript will qualify any inference as correlational, not causal.

## 2. Data Strategy

### 2.1. Datasets

| Dataset | Role | Verified Source | Access Method |
|---------|------|----------------|---------------|
| **Moral Machine** (public CSV) | Outcome (binary choice), demographics, timestamps, location | https://raw.githubusercontent.com/ethanluoyc/Moral-Machine-Data/master/shared_responses.csv | `pandas.read_csv` |
| **WorldPop 2020 Population Density** (GeoTIFF) | Indoor/outdoor proxy (urban vs. rural) | https://worldpop.org/geodata/2020/Population_Density/ | `rasterio.open` |

*Temporal mismatch*: No hourly ERA5 source is available; therefore temperature is not used as a predictor in the primary model.

### 2.2. Variable Mapping

| Moral Machine Variable | Derived Variable | Mapping Logic |
|------------------------|------------------|---------------|
| `latitude`, `longitude` | `latitude` (kept) | Direct use; also used for geographic matching to ERA5 if optional exploratory checks are performed. |
| `timestamp` | `time_of_day` (hour) | Extracted from UTC timestamp. |
| `choice` | `choice_binary` (1 = utilitarian, 0 = non‑utilitarian) | Derived per Moral Machine documentation. |
| `dilemma_id` | `dilemma_complexity` | Static score based on lives at stake, independent of response time. |
| `age_group`, `gender` | Same | Fixed effects if present. |
| `urban_rural_proxy` | `urban_rural_proxy` | Binary “urban”/“rural” derived from WorldPop density threshold (≥300 people/km² = urban). |

All exclusions are recorded in `data/processed/data_quality_log.json` conforming to `contracts/exclusion_log.schema.yaml`.

### 2.3. Data Quality & Filtering

1. **Geographic Validity** – drop rows missing lat/long.  
2. **Distance Threshold** – exclude matches where nearest ERA5 grid cell > 100 km; flag as `LOW_CONF`.  
3. **Outcome Encoding** – map utilitarian vs. non‑utilitarian choice to `choice_binary`.  
4. **Missing Covariates** – rows missing a required covariate are excluded from the model but retained in the quality log.  

## 3. Statistical Methodology

### 3.1. Primary Model (GLM‑Binomial with Cluster‑Robust SE)

```
logit( P(utilitarian_ij) ) = 
    β0 + β1·latitude_covariate_i + β2·latitude_covariate_i²
    + β3·dilemma_complexity_ij + β4·time_of_day_ij
    + β5·age_group_ij + β6·gender_ij
    + β7·urban_rural_proxy_i (optional)
    + ε_ij
```

* **Fixed Effects**: Latitude (linear & quadratic), optional urban/rural proxy, dilemma complexity, time‑of‑day, optional age/gender.  
* **Cluster‑Robust SE**: Standard errors clustered on the concatenated key `participant_id + cultural_region` to approximate random intercepts.  
* **Estimation**: `statsmodels.api.GLM` with `family=Binomial()`, `cov_type='cluster'`. Convergence status recorded (SC‑004).  

### 3.2. Model Comparison & Non‑Linearity

* **Likelihood‑Ratio Test** (FR‑005) between full model (with latitude) and null model (without latitude).  
* **Quadratic Terms** for latitude (and temperature proxy if retained) tested via AIC/BIC and LRT (FR‑013).  

### 3.3. Robustness & Sensitivity Checks (FR‑006, FR‑012)

| Check | Description |
|-------|-------------|
| **Alternative Temperature Metric** | If the optional 1982 ERA5 proxy is retained, compute a 3‑hour moving‑average approximation by averaging the three nearest grid cells (exploratory only). |
| **Outlier Threshold Sweep** | Vary latitude exclusion limits (±1 SD, ±2 SD) and record coefficient stability. |
| **Indoor/Outdoor Proxy** | Use WorldPop raster to create `urban_rural_proxy`; pipeline aborts if raster cannot be downloaded. |

Multiple comparisons across robustness models are corrected with **Benjamini‑Hochberg** (FDR).

### 3.4. Diagnostics & Assumptions (SC‑005)

* **Hosmer‑Lemeshow Goodness‑of‑Fit** – χ² test; require p > 0.05.  
* **Calibration Plot** – observed vs. predicted probabilities.  
* **Pearson / Standardized Residuals** – inspect for outliers and heteroscedasticity.  

### 3.5. Power & Sample Size

A simulation‑based a‑priori power analysis (10 000 replicates) will estimate detectable odds‑ratios for latitude given the observed variance; we assume a modest effect size (odds‑ratio ≈ 1.05) and report the resulting power in `results/logs/power_analysis.txt` (numeric value **[deferred]**).

## 4. Compute Feasibility

* **CPU‑First**: GLM on ~250 k rows with modest covariates runs in < 20 min on 2 CPU cores (empirically verified).  
* **Memory**: Data streamed in 100 k‑row chunks; peak RAM < 3 GB.  
* **GPU**: Not required.  

## 5. Decision Rationale

* **Why latitude as primary proxy?** Latitude captures the major climate gradient (temperature, humidity) and satisfies the need for a spatial covariate when hourly temperature data are unavailable, addressing FR‑001 residual confounding.  
* **Why reject ERA5 1982 for primary analysis?** It fails the hourly‑resolution requirement of FR‑014; per Constitution Principle II the source must be rejected, and the pipeline aborts if no hourly source is found. The long‑term proxy is retained only for optional exploratory checks, clearly marked as scope‑limited.  
* **Why GLM‑Binomial with cluster‑robust SE?** Provides valid inference for binary outcomes without requiring unsupported mixed‑effects GLM implementations, ensuring feasibility on the CI runner.  

---



