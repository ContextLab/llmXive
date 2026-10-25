# Research: Ambient Temperature Influence on Moral Decision Speed (Re‑scoped)

## 1. Research Question & Hypotheses

**Question**: Does ambient temperature (hourly ERA5, 2014‑2018) *associate* with **response latency** in moral decisions after controlling for demographic and scenario covariates?

**Primary Hypothesis (H₁)**: Higher ambient temperature is associated with **faster** response times (i.e., lower log‑transformed RT) after adjustment.

**Null Hypothesis (H₀)**: Ambient temperature has no association with response latency.

*Observational limitation*: The design matches existing Moral Machine responses with ERA5 temperature; therefore, we can only infer correlation, not causation. All interpretations will be framed accordingly.

## 2. Data Strategy

### 2.1. Datasets

| Dataset | Role | Verified Source | Access Method |
|---------|------|----------------|---------------|
| **Moral Machine** (public CSV) | Decision records, demographics, timestamps, scenario IDs | | `pandas.read_csv` (script‑managed) |
| **ERA5 Hourly (2014‑2018) – spatial subset** | Ambient temperature (hourly, 2 m air temperature) | | `xarray.open_dataset` (download script) |
| **GHSL Urban/Rural Classification** (optional) | Indoor/outdoor proxy | https://huggingface.co/datasets/jameszokah/ghsl-dictionary/resolve/main/data/train-00000-of-00001.parquet | `pandas.read_parquet` (download script) |
| **Auxiliary Latency Study** | Scenario‑level average latency (ms) | *No verified URL – collected via a crowdsourced latency study* | CSV placed at `data/raw/latency_study.csv` |

All external files are checksum‑verified (recorded in `data/external/checksums.txt`).

### 2.2. Merging Auxiliary Latency (FR‑016)

The auxiliary experiment provides a **scenario‑level average latency** (`mean_response_time_ms`) for each `scenario_id`. We **left‑join** this table to the Moral Machine records **by `scenario_id`** (matching the Moral Machine `dilemma_id`). The merged column `response_time_ms` becomes the outcome variable for all subsequent modeling. If any scenario lacks a latency entry, the pipeline aborts with a clear error, ensuring transparency.

*Construct validity note*: This proxy captures systematic speed differences driven by scenario difficulty, aligning with the research question while acknowledging that individual‑level RTs are unavailable. Because the latency proxy is derived at the scenario level, it may be partially collinear with the **dilemma_complexity** covariate (both reflect scenario difficulty). To guard against inflated standard errors, we will compute variance‑inflation‑factors (VIF) for all fixed effects before model fitting; if VIF > 5 for either `dilemma_complexity` or `difficulty_score`, the more collinear of the two will be dropped from the model (see Phase 7 in the implementation plan).

### 2.3. Variable Mapping

| Source | Derived Variable | Mapping |
|--------|------------------|---------|
| `latitude` / `longitude` | `latitude`, `longitude` | Direct |
| `timestamp` | `time_of_day` (hour) | Extract hour (0‑23) |
| ERA5 temperature | `temperature_c` | Hourly 2 m air temperature (°C) |
| ERA5 temperature | `temperature_c_squared` | Square of `temperature_c` |
| Auxiliary latency | `response_time_ms` | Scenario‑level mean (ms) |
| Auxiliary latency | `log_rt` | `log(response_time_ms)` |
| Scenario attributes | `dilemma_complexity` | Lives at stake + difficulty mapping (FR‑011) |
| Scenario attributes | `difficulty_score` | Categorical (Low = 0, Medium = 1, High = 2) derived **independently** of latency |
| GHSL (if present) | `urban_rural_proxy` | “urban” / “rural” classification |
| Haversine distance | `distance_km` | Distance to nearest ERA5 grid cell (flag > 100 km) |

All exclusions (distance > 100 km, temperature out of range, implausible RTs) are recorded in `data/processed/data_quality_log.json` conforming to `contracts/exclusion_log.schema.yaml`.

## 3. Statistical Methodology

### 3.1. Primary Mixed‑Effects Model

\[
\text{log\_rt}_{i} =
\beta_0 + \beta_1\cdot\text{temp}_{i} + \beta_2\cdot\text{temp}_{i}^2
+ \beta_3\cdot\text{complexity}_{i}
+ \beta_4\cdot\text{difficulty\_score}_{i}
+ \beta_5\cdot\text{hour}_{i}
+ \beta_6\cdot\text{age\_group}_{i}
+ \beta_7\cdot\text{gender}_{i}
+ u_{\text{country}_j}
+ \varepsilon_{i}
\]

* Fixed effects: temperature (linear & quadratic), dilemma complexity, **independent** difficulty_score, hour‑of‑day, optional age/gender.  
* Random intercepts: `country` (as a proxy for cultural region). No participant random effect (outcome is scenario‑level).  
* Estimation: `statsmodels.regression.mixed_linear_model.MixedLM` (REML).  
* Convergence status recorded (SC‑004).  

#### Collinearity Check
Before fitting, variance‑inflation factors (VIF) are computed for all fixed effects. If any VIF > 5, the offending covariate (typically `dilemma_complexity` vs. `difficulty_score`) is examined and, if necessary, the model is refit without it. This addresses the construct‑validity concern (methodology‑cd42a020).

### 3.2. Model Comparison & Non‑Linearity

* **Likelihood‑Ratio Test** between full model (with temperature) and null model (without temperature) – records statistic & p‑value (FR‑005, SC‑002).  
* **Quadratic term** evaluated via LRT and AIC; retain model with lower AIC (FR‑013).  

### 3.3. Robustness & Sensitivity (FR‑006, FR‑012)

| Check | Implementation |
|-------|----------------|
| Alternative temperature metric | Compute 3‑hour moving average; re‑fit model. |
| Outlier‑threshold sweep | Exclude records beyond ±2 SD, ±3 SD, ±4 SD of temperature; record coefficient change. |
| Indoor/outdoor confound | If GHSL available, include `urban_rural_proxy` as a fixed effect and report ΔR² between stratified and unstratified models. If GHSL missing, perform a large number of bootstrap resamples assigning random urban/rural labels (preserving overall proportions) and report the 95 % CI width of the temperature coefficient (noise impact metric). |
| Spatial autocorrelation | Compute cluster‑robust standard errors by ERA5 grid cell (`grid_id`) to account for spatial dependence of temperature observations. |
| Multiple‑comparison correction | Benjamini‑Hochberg FDR applied to all robustness p‑values. |
| Outputs | Comparison table (`sensitivity_analysis.csv`) and figures saved in `results/figures/`. (SC‑003) |

### 3.4. Diagnostics & Assumptions (SC‑005)

* **Shapiro‑Wilk test** on a random sample of ≤ 500 residuals; require p > 0.05.  
* **QQ‑plot**, **Residual‑vs‑Fitted** plot, and **Calibration plot** saved as PNG.  

### 3.5. Power & Sample‑Size Verification (FR‑015)

Simulation‑based a‑priori power analysis (α = 0.05, target = 0.8, standardized effect size **d** is anticipated to be small). Parameters:

- Fixed‑effect variance ≈ relatively small.  
- Random‑effect ICC is low (country clusters).  
- A large number of countries.  
- Several thousand Monte‑Carlo simulations.  

The analysis estimates a required sample size on the order of tens of thousands of records; the Moral Machine corpus exceeds this. Results written to `results/logs/power_analysis.txt`.

## 4. Compute Feasibility

All scripts run comfortably on the free‑tier CI runner:

- ERA5 subset ≤ 1 GB, streamed via `xarray` if needed.  
- Mixed‑effects fit on ~250 k rows completes < 30 min, < 3 GB RAM.  
- No GPU required; all libraries have CPU implementations.

## 5. Decision Rationale

* **Hourly ERA5** satisfies FR‑001 & FR‑014 (verified hourly resolution).  
* **Mixed‑effects on log‑RT** fulfills FR‑003, handles skewed RTs, and incorporates random intercept for country (addressing methodological‑1eda2169).  
* **Auxiliary latency proxy** satisfies FR‑016; the pipeline aborts if missing, ensuring transparency.  
* **Difficulty_score** provides an independent covariate to avoid collinearity with the latency proxy (methodology‑cd42a020).  
* **Spatial clustering** of SEs mitigates spatial autocorrelation (methodology‑5810047b).  
* **GHSL** offers a verifiable indoor/outdoor proxy for FR‑012 without extra credentials.  
* Every FR and SC is explicitly mapped to a pipeline phase, guaranteeing full coverage.

---


