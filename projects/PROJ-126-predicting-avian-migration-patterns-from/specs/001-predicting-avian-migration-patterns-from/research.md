# Research: Predicting Avian Migration Patterns from Publicly Available eBird Data

## Problem Statement & Hypothesis

**Problem**: Predicting the onset of avian migration (first arrival) is critical for ecological monitoring. While traditional methods rely on sparse manual observations, large-scale citizen science data (eBird) and remote sensing (MODIS) offer high-resolution spatiotemporal coverage. However, integrating these heterogeneous data sources while managing observer bias and environmental collinearity remains a challenge.

**Hypothesis**: A Gradient Boosting Regressor utilizing lagged Land Surface Temperature (LST) and Normalized Difference Vegetation Index (NDVI) can accurately predict the "first arrival" date of *Setophaga ruticilla* (American Robin) within the verified Lake Powell region. The model will demonstrate that temperature is the primary driver of migration onset, with NDVI acting as a secondary modulator, and that these relationships hold robustly across different definitions of "arrival" (sensitivity analysis).

**Scope Limitation**: This study is explicitly limited to the **verified Lake Powell region** due to the constraints of the available open data. The model is not claimed to generalize to the entire North American continent. This limitation is acknowledged in all outputs and interpretations.

## Dataset Strategy

This project relies on two primary data sources. Per the "Verified datasets" constraint, we utilize the provided Hugging Face links which serve as verified proxies for the full EBD and MODIS datasets.

| Dataset | Description | Source URL | Usage Strategy |
|:--- |:--- |:--- |:--- |
| **eBird Basic Dataset (EBD)** | Raw checklists containing species presence, observer effort, and location. | ` (Primary) <br> ` (Fallback) | **Streaming**: We will load the EBD data in chunks or via streaming to fit within 7GB RAM. We filter for *Setophaga ruticilla* (Taxon Code: AMRO) and apply "complete checklist" filters (duration ≥ 1 min, observers ≥ 1, distance ≤ 10 km). Data is filtered to the Lake Powell region coordinates. |
| **MODIS Environmental Data** | Land Surface Temperature (MOD11A2) and NDVI (MOD13Q1) derived metrics. | ` (Primary) <br> ` (Fallback) | **Mapping**: We will map the MODIS data to the 0.5° grid cells defined by the EBD aggregation. The dataset is explicitly treated as the ground truth for the Lake Powell region only. No attempt is made to extrapolate to other regions. |

**Critical Data Scope Note**: The verified MODIS datasets provided are labeled as "toy datasets" or "lake-powell" specific. The full continental MODIS dataset is not directly available via a single verified URL in the provided block.
* **Strategy**: We will proceed by constructing the *full pipeline* using the verified Lake Powell data to demonstrate the methodology (FR-001 to FR-007) within the valid spatial extent.
* **Feasibility**: The plan acknowledges that a full continental analysis (recent years) cannot be executed on the free tier with the *full* MODIS raster files without a larger dataset source. The implementation will be designed to be scalable: if a larger verified source becomes available, the streaming code will support it. For now, the "Lake Powell" dataset serves as the ground truth for *methodological validation*.
* **Mitigation**: The plan explicitly scopes the "regional-scale maps" (FR-007) to the *spatial extent of the verified data*. The primary success metric (SC-004) is the *completion of the pipeline* within 6 hours, and the *validity of the method* within the verified region, not the generation of a full-continent map.

## Methodological Approach

### 1. Data Ingestion & Preprocessing (US-1)
* **Filtering**: Apply strict "complete checklist" filters to EBD data.
* **Grid Aggregation**: Bin observations into 0.5° grid cells within the Lake Powell region.
* **Observer Bias Control**: Model the probability of observation as a function of weather (temperature, precipitation proxies) using a logistic regression. The "first arrival" date is derived from a **bias-corrected** cumulative count or the analysis explicitly includes 'observer effort' (duration, distance) as a covariate.
* **Target Derivation**: For each grid cell/year, calculate the cumulative count of *Setophaga ruticilla* observations. The "First Arrival" date is defined as the week where the cumulative count reaches a predetermined threshold.
 * *Construct Validity Justification*: The threshold of 5 is chosen based on standard phenology literature (e.g., Parmesan & Yohe) for low-density species in grid cells, balancing the bias of early false positives with the variance of late detection.
 * *Sensitivity*: Repeat for thresholds {, 5, 10}.
 * *Exclusion*: Grid cells with total annual counts < 10 are excluded to avoid false positives.
* **Feature Engineering**: Extract lagged environmental variables (Mean Temp, Mean NDVI) for 1, 2, 3, and 4 weeks prior to the observation week.

### 2. Model Training (US-2)
* **Algorithm**: XGBoost Regressor (`xgboost.XGBRegressor`).
* **Configuration**: `tree_method='hist'` for CPU efficiency.
* **Split Strategy**:
 * **Train**: Lake Powell Region, Years 2015-2020.
 * **Validate**: Lake Powell Region, Year 2021.
 * **Test**: Lake Powell Region, Year 2022.
 * *Note*: The split is purely temporal to satisfy Principle VII and avoid invalid spatial generalization on a localized dataset.
* **Objective**: Predict "First Arrival" week (integer).
* **Hyperparameter Tuning**: Grid search on `max_depth`, `learning_rate`, `n_estimators` using the validation set.

### 3. Interpretability & Statistical Validation (US-3)
* **SHAP Analysis**: Compute SHAP values to determine global feature importance and local interactions. This addresses the collinearity between temperature and NDVI.
* **Permutation Importance on RMSE**: Run permutation tests on the **model performance metric** (RMSE) to test the statistical significance of the difference between drivers (e.g., is the drop in RMSE when permuting Temp significantly larger than when permuting NDVI?).
* **Bootstrap Resampling for Model Comparison**: Use `scipy` to perform a sufficient number of bootstrap iterations on the test set to compare the performance (RMSE, correlation) of temperature-only, NDVI-only, and combined predictor models. This replaces the circular LMM approach.
* **Sensitivity Analysis**: Compare the "First Arrival" dates derived from thresholds {3, 5, 10}. If the primary drivers (Temp vs. NDVI) shift significantly, the result is flagged as sensitive.
* **Observer Effort Check**: Correlate the derived arrival dates with average observer effort (duration, distance) to ensure the target is not an artifact of effort bias.

## Statistical Rigor & Limitations

* **Multiple Comparisons**: When comparing multiple predictor sets (Temp, NDVI, Combined), we will apply a Bonferroni correction to the p-values from the bootstrap resampling to control the family-wise error rate.
* **Sample Size/Power**: Power is limited by the size of the verified "Lake Powell" dataset. We will report the effective sample size (number of grid-cell-year observations) and explicitly acknowledge that the study may be underpowered to detect small effect sizes. P-values should be interpreted with caution.
* **Causal Inference**: The study is observational. We will explicitly state that the model identifies *associations* between environmental variables and migration timing, not causal mechanisms. No randomization exists.
* **Collinearity**: Temperature and NDVI are often correlated. We will not interpret raw coefficients as independent effects. Instead, we rely on SHAP interaction values and permutation tests on RMSE to disentangle their contributions.
* **Dataset Fit**: The verified MODIS dataset is a "Lake Powell" sample. The model is trained on this sample. The study validates the *methodology* within this region. The *quantitative predictions* for the full continent are **not** claimed. This is a known limitation of the available open data.
* **Observer Bias**: The model includes observer effort as a covariate and uses bias-corrected arrival dates to mitigate the confounding effect of weather on observation probability.

## Decision Rationale: CPU vs. GPU

* **Choice**: **CPU-First**.
* **Rationale**: The XGBoost algorithm is highly optimized for CPU execution. With `tree_method='hist'`, it can handle the expected dataset size (even if scaled up) within the RAM and core constraints of the GitHub Actions runner.
* **GPU Necessity**: No. The problem does not require deep learning (transformers/CNNs) or massive matrix operations that necessitate CUDA. A GPU escape hatch is not needed for this specific methodology.
* **Feasibility**: The entire pipeline (streaming, aggregation, training, SHAP, Bootstrap) is designed to be memory-efficient and will run comfortably within the 6-hour limit on the free tier.
