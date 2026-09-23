# Research: Predicting Avian Migration Patterns from Publicly Available eBird Data

## 1. Problem Definition & Scientific Context

The project aims to predict the "first arrival" date of *Setophaga ruticilla* (American Redstart) within the **Lake Powell region** (North America) using environmental covariates. The core hypothesis is that spring migration timing is **associatively correlated** with phenological cues, specifically Land Surface Temperature (LST) and vegetation greenness (NDVI), lagged by 1-4 weeks.

**Key Challenge**: The data is observational, sparse, and noisy. eBird data is biased by observer effort (citizen science), and MODIS data suffers from cloud cover gaps. The "first arrival" metric is an operational definition (e.g., 5th observation) that must be robust to these biases.

**Scope Constraint**: The verified MODIS dataset is limited to the Lake Powell region. Therefore, the study scope is explicitly reduced to this region. Claims of "continental" migration patterns are not supported by the verified data and are excluded from this study.

**Critical Data Constraint**: The project relies on a verified EBD subset from HuggingFace. If this subset lacks *Setophaga ruticilla* or the 2015-2023 temporal range, the pipeline will **fail explicitly** (fail-fast) rather than proceeding with incomplete data. No alternative verified source for the full EBD is available in the prompt's verified block; the study is contingent on the subset's adequacy.

## 2. Dataset Strategy

The plan relies exclusively on the verified datasets provided in the prompt.

| Dataset | Purpose | Verified URL(s) | Access Method |
|:--- |:--- |:--- |:--- |
| **EBD (eBird Basic Dataset)** | Raw checklist records (species, date, location, effort). | ` (and verified Parquet alternatives) | `datasets.load_dataset` (HuggingFace Hub) with streaming. **Validation**: Checks for *Setophaga ruticilla* and years 2015-2023. If missing, aborts. |
| **MODIS (LST & NDVI)** | Environmental predictors (Temperature, Greenness). | ` | `datasets.load_dataset` (HuggingFace Hub) or direct CSV fetch. |

**Dataset Fit & Limitations**:
- **EBD**: The verified source provides a subset of EBD data. The plan includes a **Data Validation** step to verify that the specific species *Setophaga ruticilla* and the years 2015-2023 are present. **If the verified subset lacks these, the pipeline fails with a clear error message** (e.g., "CRITICAL: Verified EBD subset lacks target species or required years. Aborting.") rather than proceeding with incomplete data. **No alternative verified source is identified**; the study is contingent on the subset's adequacy.
- **MODIS**: The verified source is a "Lake Powell toy dataset." This is a **critical constraint** for the study scope.
 - **Resolution**: The plan explicitly reduces the study scope to the Lake Powell region. The analysis is designed to model migration patterns **only** within the geographic extent of the verified MODIS dataset. No attempt is made to claim continental coverage. This ensures construct validity: the measurements (Lake Powell LST/NDVI) match the construct (migration drivers in Lake Powell).
 - **Geographic Alignment**: The validation target (arrival dates) and predictors (LST/NDVI) share the exact same geographic domain (Lake Powell) to prevent hallucination.

**Data Availability & Feasibility**:
- Both datasets are hosted on HuggingFace, allowing programmatic access via `datasets` library.
- **Streaming**: To respect the 7 GB RAM limit, the EBD data will be processed in chunks (streaming). The MODIS data, if small (toy dataset), can be loaded in memory; if larger, streaming will be used.
- **Missing Data**: Cloud cover in MODIS and observer absence in eBird will be handled via:
 - eBird: Exclusion of grid cells with < 10 total annual observations (FR-003).
 - MODIS: Temporal interpolation or nearest-neighbor fill for single-week gaps; exclusion if gaps exceed a consecutive-week threshold.

## 3. Methodology & Statistical Rigor

### 3.1 Data Processing Pipeline
1. **Filtering**: Retain only "complete checklists" (duration ≥ 1 min, observers ≥ 1, distance ≤ 10 km).
2. **Aggregation**: Bin observations into 0.5° grid cells and weekly intervals.
3. **Target Derivation**: Calculate "first arrival" as the week where cumulative count reaches threshold $T \in \{3, 5, 10\}$.
 - *Sensitivity Analysis*: Run the pipeline for all $T$ values to assess robustness (FR-003).
 - *Effort Correction Note*: The "first arrival" metric is sensitive to observer density. While the plan filters for complete checklists, it acknowledges that high-effort areas may show earlier arrival. Rarefaction is noted as a potential limitation/optional step if data density permits.
4. **Feature Engineering**: Create lagged features for LST and NDVI (lags 1, 2, 3, 4 weeks).
5. **Multicollinearity Mitigation**: Compute Variance Inflation Factor (VIF) for all predictors. Drop features with VIF > 5 before model training to ensure stable coefficients and avoid SHAP value splitting artifacts.

### 3.2 Modeling Strategy
- **Algorithm**: XGBoost Regressor (Gradient Boosting).
- **Split Strategy**: Strict temporal split.
 - Train: Early 2010s–2020.
 - Validation:.
 - Test: recent years.
- **Why Temporal?**: Prevents look-ahead bias; mimics real-world prediction of future migration.
- **Evaluation Metric**: RMSE and Pearson Correlation calculated on **temporal residuals** (deviation from the long-term mean for that location) rather than absolute dates. This ensures the model predicts year-over-year shifts rather than just spatial latitude effects.
- **Collinearity Handling**:
 - Temperature and NDVI are often correlated.
 - **Action**: VIF filtering removes redundant features. **Permutation Importance** (shuffling features to measure drop in performance) and **SHAP values** (Shapley Additive exPlanations) are used to determine true feature contribution.
 - **Constraint**: If predictors are definitionally related (e.g., NDVI is derived from same spectral bands), independent effects cannot be claimed. Results will be framed as "associational contributions."

### 3.3 Statistical Validation
- **Metric**: Root Mean Squared Error (RMSE) and Pearson Correlation (SC-001).
- **Model Comparison**: **Diebold-Mariano (DM) Test** to compare the predictive accuracy of:
 1. Temperature-only model.
 2. NDVI-only model.
 3. Combined model.
- **Unit of Analysis**: The DM test is applied to the **time-series of aggregated errors** (mean error per week across the region), not spatially independent cells. This satisfies the independence assumption of the DM test and provides sufficient degrees of freedom.
- **Significance**: $p < 0.05$ (SC-002).
- **Power Limitation**: If the sample size (grid cells × weeks) is small due to data filtering or the "toy" nature of the verified MODIS dataset, the plan will explicitly state the power limitation and interpret p-values with caution.

### 3.4 Compute Feasibility (CPU-First)
- **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Strategy**:
 - Use `xgboost` with `tree_method='hist'` for CPU efficiency.
 - Limit tree depth (`max_depth`) to 4-6 to prevent overfitting and speed up training.
 - Use `streaming=True` for HuggingFace datasets to avoid loading full EBD into RAM.
 - **GPU Escape Hatch**: If the dataset size or model complexity exceeds CPU limits (unlikely for this scope), the plan acknowledges the "GPU escape hatch" (Kaggle auto-offload) but notes that XGBoost is generally CPU-tractable for this scale. No GPU is *planned* unless the CPU run fails.

## 4. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Streaming EBD** | EBD is massive; loading into RAM > 7 GB is impossible. Streaming is the only feasible path. |
| **Temporal Split** | Random splits leak future phenology; temporal split is required for valid predictive modeling (Constitution Principle VII). |
| **Permutation Importance + VIF** | XGBoost `feature_importance` is biased towards correlated features. VIF removes redundancy; Permutation is robust to collinearity (FR-005). |
| **Diebold-Mariano Test (Temporal Aggregates)** | Standard t-tests assume independent errors; DM test accounts for time-series autocorrelation. Applied to aggregated errors to avoid spatial autocorrelation violations. |
| **Sensitivity Sweep (3, 5, 10)** | The "first arrival" definition is arbitrary. Sweeping thresholds ensures results are not artifacts of a single choice (FR-003). |
| **Regional Scope (Lake Powell)** | Verified MODIS data is limited to Lake Powell. Continental claims would be hallucinations. Scope is reduced to ensure data validity. |
| **Fail-Fast Validation** | Verified EBD subset may lack target species/years. Proceeding would produce invalid results. The pipeline must abort if the subset is insufficient. No alternative verified source exists. |

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Verified MODIS dataset is too small (Lake Powell only)** | Cannot model continental migration. | **Mitigation**: Reframe study to "Regional Analysis of Lake Powell". Explicitly state geographic limitation in all outputs. |
| **Missing eBird data in remote areas** | Sparse grid cells, unreliable arrival dates. | **Mitigation**: Exclude cells with < 10 annual observations (FR-003). |
| **Cloud cover in MODIS** | Gaps in LST/NDVI time series. | **Mitigation**: Temporal interpolation; exclude weeks with > 50% cloud cover. |
| **Compute Time > 6 hours** | CI job fails. | **Mitigation**: Use smaller grid resolution (if needed), limit `n_estimators`, and stream data. Phase 4 verifies this. |
| **Observer Effort Bias** | High-effort areas show earlier arrival. | **Mitigation**: Filter for complete checklists; acknowledge limitation; optional rarefaction step. |
| **Collinearity (Temp vs NDVI)** | Unstable coefficients. | **Mitigation**: VIF filtering before training; Permutation Importance for ranking. |
| **DM Test Assumption Violation** | Spatial autocorrelation invalidates p-values. | **Mitigation**: DM test performed on time-series of aggregated errors, not spatial cells. |
| **Verified EBD Subset Insufficient** | Pipeline fails to find target species/years. | **Mitigation**: **Fail-fast validation** in Phase 0. If the subset lacks *Setophaga ruticilla* or 2015-2023, the pipeline aborts with a clear error. No alternative verified source exists; the study is contingent on the subset's adequacy. |
