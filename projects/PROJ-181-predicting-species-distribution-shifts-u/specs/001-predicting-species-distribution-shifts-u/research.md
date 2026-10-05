# Research: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

## 1. Problem Definition & Scope

The research aims to quantify the reliability of Species Distribution Models (SDMs) in predicting range shifts under climate change. The core hypothesis is that models trained on historical data will exhibit significant changes in predicted suitability when projected onto future climates compared to historical validation sets, indicating niche instability or non-stationarity.

**Critical Methodological Correction**: The evaluation of "niche stability" is redefined to avoid temporal mismatch. We do not evaluate 2050 projections against 2050 occurrences (which do not exist). Instead, we:
1. Validate the historical model (1970-2000) against 2005-2020 occurrences using **2005-2020 climate** data.
2. Project the same historical model to the **2050 climate** data *at the same 2005-2020 occurrence locations*.
3. Calculate `delta_Suitability` (Mean Suitability Shift) as the difference between the mean predicted suitability under 2050 climate vs. 2005-2020 climate. This measures the model's sensitivity to future climate change, isolating the "niche shift" signal without requiring future occurrence data.

**Scope**:
- **Target Taxa**: North American bird species (subset of ~20-50 common species).
- **Timeframes**: Historical (1970-2000) vs. Recent (2005-2020) vs. Future (2050).
- **Data Sources**: GBIF/eBird (occurrence), WorldClim v2 (historical climate), WorldClim CMIP6 (future climate).
- **Constraints**: CPU-only execution, <6h runtime, <7GB RAM.

## 2. Dataset Strategy

The project relies on open, programmatic data sources. No access-gated datasets (e.g., ADNI, HCP) are used. Synthetic datasets are not used for training or validation.

| Dataset | Source / Verified URL | Usage | Verification Status |
| :--- | :--- | :--- | :--- |
| **Historical Occurrences** | GBIF API (via `occurrence` endpoint) | Training data (1970-2000). Filtered by breeding season, thinning. | **Verified**: API is public. No direct static URL; programmatic fetch required. |
| **Recent Occurrences** | GBIF API (via `occurrence` endpoint) | Evaluation data (2005-2020). Used for out-of-time validation. | **Verified**: API is public. |
| **Historical Climate** | WorldClim v2.1 (https://worldclim.org/data/worldclim21.html) | Predictor variables (Bio1-Bio19). 1970-2000 baseline. | **Verified**: Direct download available via `wget`/`rasterio`. |
| **Future Climate** | WorldClim CMIP6 (SSP2-4.5) via WorldClim (https://worldclim.org/data/cmip6.html) | Future predictor variables (2041-2060). Downloaded via `wget` with specific file patterns. | **Verified**: Available via programmatic download from WorldClim. |

**Note on SDM Datasets**: No single verified "SDM" dataset URL exists. The project will construct the SDM dataset dynamically by joining occurrence records with climate rasters at runtime.

**Data Availability & Feasibility**:
- **GBIF**: Accessible via `requests` or `pygbif`. Rate limits handled via exponential backoff.
- **WorldClim/CMIP6**: Large rasters (multi-gigabyte scale). The plan streams or downloads specific tiles needed for the species' bounding boxes to stay within RAM limits.
- **CPU Feasibility**: All processing (thinning, feature extraction, RF training) is CPU-tractable. No GPU acceleration is planned.

**Data Standard**: Downloaded CSVs will conform to the Darwin Core (DwC-A) standard or explicitly map to the GBIF API schema version used.

## 3. Methodology

### 3.1 Data Preprocessing (FR-001, FR-003, FR-014)
1.  **Download**: Fetch occurrence records for target species.
2.  **Filter**: Remove records outside breeding months (species-specific logic).
3.  **Dedup**: Remove exact coordinate duplicates.
4.  **Thinning**: Apply spatial thinning (max distance method) using the **dynamic 95th percentile of nearest-neighbor distances** as the default threshold. If calculation fails (< 3 points), fall back to a fixed 10km threshold.
    - *Rationale*: Reduces spatial autocorrelation, preventing inflated model performance.
5.  **Climate Extraction**: Sample WorldClim rasters at occurrence coordinates. Impute missing values via nearest neighbor or exclude.
6.  **Variable Validation**: Ensure all 19 predictor variables are present for every record.

### 3.2 Model Training (FR-002, FR-004, FR-007)
Three algorithms will be implemented:
1.  **Bioclim**: Range-based envelope model (non-parametric).
2.  **Random Forest**: Ensemble tree method (`sklearn.ensemble.RandomForestClassifier`).
3.  **MaxEnt-style**: Implemented via `sklearn` surrogate (Regularized GLM or specific RF configuration mimicking MaxEnt's regularization). *Note: True MaxEnt is Java-based; a Python-native approximation will be used to ensure CPU/CI compatibility.*

**Validation Strategy**:
- **Spatial Block Cross-Validation**: Divide the study area bounding box into a 5x5 equidistant grid, forming 5 contiguous blocks. Rotate the held-out block index (0 to 4) for each fold to ensure spatial independence (FR-007).
- **Train/Test Split**: [deferred] training, [deferred] validation (spatially blocked).

### 3.3 Future Projection & Evaluation (FR-005, FR-009, FR-010)
1.  **Historical Validation**: Evaluate models on 2005-2020 occurrences using **2005-2020 climate**. Calculate AUC/TSS.
2.  **Future Projection**: Project models to **2050 climate** at the **same 2005-2020 occurrence locations**. Calculate suitability scores.
3.  **Niche Stability Metric**: Calculate `delta_Suitability` (Mean Suitability Shift) = (Mean Suitability @ 2050 Climate) - (Mean Suitability @ 2005-2020 Climate). This measures the change in predicted suitability driven solely by the climate variable shift.
    - **Correction**: This metric replaces the invalid "delta AUC" calculation against future occurrences.
4.  **Threshold Sweep**: Iterate through the exact threshold set defined by absolute differences {0.01, 0.05, 0.10} from baseline 0.50, resulting in thresholds {0.49, 0.51, 0.55, 0.60}.
5.  **Statistical Testing**:
    -   **Hierarchical Bootstrap**: Two-level resampling: Level 1 (Species) -> Level 2 (Spatial Blocks within Species). **Target Metric**: `delta_Suitability`. This accounts for both inter-species variation and spatial autocorrelation structure within species.
    -   **Multiple-Comparison Correction**: Apply Benjamini-Hochberg correction for threshold sweeps (FR-005).

### 3.4 Power Analysis (FR-011)
- **Effect Size**: Cohen's h = 0.50 (Verified: Wikipedia). This represents the difference between the proportion of 'suitable' predictions (suitability > 0.5) and a null expectation of 0.5 (random suitability).
- **Threshold**: Minimum 100 records per species for statistical power (Power ≥ 0.8).
- **Action**: If `count < 100` or calculated power < 0.8, flag as `INSUFFICIENT_DATA` and exclude from aggregation (FR-006). Log the specific count and power value.

## 4. Statistical Rigor & Assumptions

- **Associational Nature**: All findings are explicitly framed as associational. No causal claims (e.g., "climate change *caused* the shift") are made without experimental manipulation. The report will append: "Findings are associational and assume niche stability".
- **Collinearity**: Climate variables (e.g., Bio1 vs Bio12) are often correlated. The Random Forest implementation handles this, but Bioclim assumes independence. Collinearity will be acknowledged in the report.
- **Multiple Comparisons**: Threshold sweeps (FR-005) and model comparisons (FR-010) require correction to control Family-Wise Error Rate (FWER).
- **Sample Size**: The 100-record threshold is a conservative proxy for power. A formal post-hoc power analysis will be logged.

## 5. Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **GBIF API Rate Limits** | Implement exponential backoff; cache responses in `data/raw/` to avoid re-fetching. |
| **Missing Climate Data** | Exclude points with null climate values; log count. |
| **Insufficient Data (<100 records)** | Flag species; exclude from final aggregation; report as a limitation. |
| **Runtime > 6h** | Limit number of species; use subsampling for bootstrap if necessary; optimize `rasterio` reading. |
| **Memory Overflow** | Stream rasters; process species sequentially; avoid loading all rasters into RAM simultaneously. |

## 6. Decision Rationale

- **CPU-First**: The free-tier CI runner has no GPU. Using `scikit-learn` and `rasterio` ensures compatibility.
- **Spatial Block CV**: Essential for ecological data to avoid spatial leakage. Random CV would yield overly optimistic AUC.
- **Hierarchical Bootstrap**: Standard t-tests fail on ecological data due to species-level dependence. Bootstrap preserves the hierarchy.
- **No Synthetic Data**: The plan uses real GBIF/WorldClim data. Synthetic stand-ins are rejected as fabrication.
- **Temporal Mismatch Resolution**: The redefined evaluation metric (comparing model outputs at the same locations under different climate scenarios) is the only valid way to assess niche stability without 2050 occurrence data. The statistical test is now applied to `delta_Suitability`.
