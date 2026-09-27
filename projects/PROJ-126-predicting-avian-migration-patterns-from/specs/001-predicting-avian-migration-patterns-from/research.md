# Research: Predicting Avian Migration Patterns

## Dataset Strategy

This project relies on two primary data sources: the eBird Basic Dataset (EBD) for biological observations and NASA Earthdata (MODIS) for environmental covariates (Land Surface Temperature and Enhanced Vegetation Index - EVI, used as a proxy for NDVI). The following sources have been verified for programmatic access and format compatibility.

| Dataset | Description | Verified Source URL | Access Method |
| :--- | :--- | :--- | :--- |
| **eBird Basic Dataset (EBD)** | Raw checklist data for *Setophaga ruticilla*. Contains location, date, species counts, and effort metrics (duration, distance). | `https://huggingface.co/datasets/vvud/eb-data/resolve/main/data/train.csv` | `pandas.read_csv` (streaming/chunked) or `datasets.load_dataset` |
| **NASA MODIS (Temp & EVI)** | Land Surface Temperature (MOD11A2) and EVI (MOD13Q1) data for continental scale. | `https://earthdata.nasa.gov/` (via `earthaccess` library) | `earthaccess` library with valid NASA Earthdata token (env var `NASA_EARTHDATA_TOKEN`). |

**Note on Data Availability & Feasibility**:
The NASA MODIS data provides real, continental-scale data required for FR-001 and FR-002.
- **Access Method**: The pipeline will use the NASA Earthdata API with a valid token. If the token is missing or invalid, the pipeline will fail with a clear error message.
- **Fallback Strategy (Regional Scope Reduction)**: If the full continental MODIS dataset cannot be processed due to memory constraints (exceeding 7GB RAM), the pipeline will **automatically reduce the study scope** to a verified regional subset (e.g., Pacific Northwest: lat 45-50, lon -125 to -115). This ensures the code runs and the methodology is validated using **real data**, not synthetic proxies. The final paper will explicitly state: "Due to compute constraints, this study utilized a verified regional subset (Pacific Northwest) of the full continental dataset. Future work will integrate the full dataset once compute resources are expanded."
- **Crucial**: The final paper will **not** use synthetic data. All results will be derived from real MODIS data or a verified regional subset. **No synthetic generation of environmental covariates is performed.**

**Dataset Variable Fit Check**:
- **EBD**: Contains `species`, `latitude`, `longitude`, `date`, `effort`, `obs_count`. **Fits** FR-001 (complete checklists).
- **NASA MODIS**: Contains `T2M` (Temperature), `EVI` (Vegetation Index), `latitude`, `longitude`, `date`. **Fits** FR-002 (continental scale).
- **Resolution**: The plan will use the EBD data for the "ground truth" (arrival dates) and the MODIS data for environmental predictors. The data will be aligned to a 0.5° grid using nearest-neighbor interpolation.

## Methodological Rigor

### Statistical Approach
1.  **Target Variable**: "First Arrival" defined as the week where cumulative observation count reaches $k$ (where $k \in \{3, 5, 10\}$).
2.  **Model**: Gradient Boosting Regressor (XGBoost).
    -   **Loss**: Mean Squared Error (MSE).
    -   **Validation**: Temporal split (Train: 2015-2020, Val: 2021, Test: 2022).
3.  **Hypothesis Testing**:
    -   **Diebold-Mariano Test**: Used to compare RMSE of Combined Model vs. Temperature-only vs. EVI-only.
    -   **Null Hypothesis**: The forecast errors of the two models have equal mean.
    -   **Alternative**: The combined model has significantly lower RMSE (one-sided, $\alpha=0.05$).
4.  **Collinearity Handling**:
    -   Temperature and EVI are often correlated.
    -   **Mitigation**: Use **Permutation Importance** (shuffling features and measuring performance drop) and **SHAP (SHapley Additive exPlanations)** values. SHAP interaction values will be computed to detect if the model relies on the interaction between the two rather than independent effects.
    -   **Reporting**: If collinearity is high, the plan will report the *combined* contribution of the environmental block rather than claiming independent causal effects.
5.  **Observer Effort Confounding**:
    -   The plan explicitly controls for observer effort by filtering for "complete checklists" and flagging low-effort cells.
    -   Sensitivity analysis will compare results with and without low-effort cells to ensure robustness.

### Sample Size & Power
-   The EBD dataset is large (millions of checklists).
-   **Power Limitation**: If the number of grid cells with sufficient data (≥10 obs/year) is low, the power to detect differences in the Diebold-Mariano test may be limited.
-   **Contingency**: The plan will report the effective sample size ($N$) of grid-cell/week observations. If $N < 100$, the results will be flagged as "low power, exploratory" rather than definitive. **If the study scope is reduced to a regional subset, the paper will explicitly state this limitation.**

### Causal Inference
-   **Observational Study**: The plan explicitly states that the relationship is **associational**. No causal claims (e.g., "Temperature causes earlier migration") will be made. The model predicts *when* migration occurs based on *what* the environment was, not *why*.

## Compute Feasibility & Escape Hatch

-   **CPU-First**: XGBoost is highly optimized for CPU. With `n_estimators` capped (e.g., 100-200) and `max_depth` limited (e.g., 4-6), the model should train on a 1M-row subset within 1-2 hours on a 2-core CPU.
-   **Memory**: The pipeline will use `dask.dataframe` or chunked reading to process the EBD CSV. Aggregation to 0.5° grid cells will be done in chunks to prevent RAM overflow.
-   **GPU Escape Hatch**: Not required for XGBoost on this scale. If the dataset size forces a switch to a deep learning model (not planned), the execution agent would detect CUDA requirements and offload to Kaggle. This plan avoids that complexity.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **XGBoost over Random Forest** | XGBoost generally offers better performance and faster training on tabular data. |
| **Temporal Split (2015-2020 / 2021 / 2022)** | Essential to avoid data leakage in time-series forecasting. Random split would allow future data to influence past predictions. |
| **Threshold Sweep (3, 5, 10)** | Required by SC-003 to ensure the "first arrival" definition is robust to observer effort variations. |
| **NASA MODIS (Earthdata)** | Provides real, continental-scale environmental data required for the research question. The fallback to a regional subset ensures the pipeline runs even if full data is too large. **No synthetic data is used.** |
