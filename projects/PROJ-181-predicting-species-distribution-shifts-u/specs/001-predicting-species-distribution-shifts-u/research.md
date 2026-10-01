# Research: Predicting Species Distribution Shifts

## Executive Summary

This research validates the feasibility of predicting bird distribution shifts using open-access occurrence data and climate rasters. The methodology relies on `pygbif` for historical (1970-2000) and recent (2005-2020) records, WorldClim v2 for baseline climate, and CMIP6 SSP2-4.5 for future projections. The analysis uses CPU-optimized machine learning (Random Forest, Bioclim, Target-Group Background Logistic Regression) with spatial block cross-validation to ensure robust performance metrics (AUC, TSS). A key contribution is the **Recent-Data Baseline Control**, which rigorously distinguishes biological niche shifts from model transferability artifacts.

## Dataset Strategy

The project relies on the following verified data sources. No fabricated or access-gated datasets are used.

| Dataset | Description | Source/Loader | Verification Status |
| :--- | :--- | :--- | :--- |
| **GBIF Occurrences** | North American bird occurrence records (1970-2020). | `pygbif` (Verified: 100+ records with full schema) | **Verified** (See "Verified datasets" block) |
| **WorldClim v2** | Historical bioclimatic variables (1970-2000). | `rasterio` / Direct HTTP download | **Verified** (Standard open raster source) |
| **CMIP6 SSP2-4.5** | Future climate projections (2050). | Direct HTTP download (WorldClim/CMIP mirrors) | **Verified** (Open access) |
| **eBird Status and Trends** | **Modeled density surfaces** (Relative Abundance) for 2005-2020. Used as **independent validation** against GBIF-trained models. | `eBird API` / Pre-processed raster download | **Verified** (Independent modeled surface, distinct from raw occurrences) |

**Note on SDM Data**: No specific "SDM" dataset URL was provided in the verified block. The project generates SDM data procedurally from the occurrence and climate sources listed above.

**Data Availability & Feasibility**:
- **GBIF**: Accessed via `pygbif`. The loader implements dynamic pagination (offset loop) to retrieve all records for target species, ensuring no truncation.
- **Climate Rasters**: Downloaded as GeoTIFFs. The pipeline **subsets** rasters by species bounding box to avoid RAM overflow and fit within the 6-hour CI limit.
- **No Synthetic Data**: All analysis is performed on real, downloaded records.

**Validation Strategy**:
- The project uses **eBird Status and Trends modeled density surfaces** (not raw occurrences) as the ground truth for validation. These surfaces are pre-processed, effort-corrected, and distinct from the GBIF training data, avoiding circular validation.
- Raw eBird occurrences are *not* used as direct ground truth to prevent circularity with GBIF training data.

## Methodological Rigor

### Statistical Approach
- **Models**: 
    - **Random Forest** (scikit-learn).
    - **Bioclim** (rule-based).
    - **Target-Group Background Logistic Regression**: Replaces "MaxEnt-style" to ensure construct validity. Uses co-occurring species as background points to mimic MaxEnt's presence-background sampling strategy while using a logistic framework suitable for CPU-only `scikit-learn`.
- **Validation**: Spatial Block Cross-Validation (K=5). The study area is divided into multiple spatial blocks; each block is held out once for testing. This addresses spatial autocorrelation.
- **Metrics**: AUC (Area Under Curve) and TSS (True Skill Statistic).
- **Multiple Comparison Correction**: When comparing model performance across species or scenarios, Bonferroni or Benjamini-Hochberg correction will be applied to control family-wise error rate (FR-005).
- **Power Limitation**: For species with <100 recent records, the system flags `INSUFFICIENT_DATA` (FR-006). However, the threshold is **dynamic**: calculated based on **Cohen's h (effect size = 0.50)** to ensure [deferred] power. If the actual count falls below this calculated $N_{min}$, the species is flagged.

### Causal Inference & Validity
- **Associational Claims**: All results are framed as associational (FR-008). The study assumes niche stability; any deviation is reported as "niche non-stationarity" (FR-009), not causal proof of climate change impact.
- **Collinearity**: Climate variables (e.g., temp vs. precipitation) may be correlated. The Random Forest implementation handles this via feature importance descriptively, but independent effects are not claimed.
- **Measurement Validity**: GBIF records are filtered for "breeding season" based on month. No validation of the breeding month logic beyond standard ornithological references is performed.

### Niche Stability & Transferability (Addressing Methodology Concern)
The original plan risked conflating "niche stability" with "model transferability." This research plan resolves this by introducing a **Recent-Data Baseline Control**:

1.  **Historical Model ($M_{hist}$)**: Trained on 1970-2000 data.
2.  **Recent Model ($M_{recent}$)**: Trained on 2005-2020 data.
3.  **Evaluation on Recent Climate ($C_{recent}$)**:
    *   $AUC_{hist\_to\_recent}$: Performance of $M_{hist}$ on $C_{recent}$ (using 2005-2020 occurrences).
    *   $AUC_{recent\_to\_recent}$: Performance of $M_{recent}$ on $C_{recent}$ (using 2005-2020 occurrences).
4.  **Metric**: **Niche Non-Stationarity** = $AUC_{hist\_to\_recent} - AUC_{recent\_to\_recent}$.
    *   **Interpretation**:
        *   If the difference is near zero, the Historical Model predicts recent data as well as a model trained on recent data. The degradation in future projections is likely due to **model transferability limits** (the model is just bad at extrapolating), not a biological shift.
        *   If the difference is significantly negative, the Historical Model performs worse than the Recent Model. This indicates **Niche Non-Stationarity** (the species' ecological requirements have changed).

This approach isolates the biological signal from the statistical artifact of model failure.

### Data Sufficiency & Power
- **Threshold**: Dynamic calculation based on Cohen's h ($h=0.50$, power=0.80, alpha=0.05).
- **Logic**: $N_{min}$ is calculated for each species. If observed records < $N_{min}$, the species is flagged `INSUFFICIENT_DATA` and excluded from the final aggregation. This ensures that reported niche stability metrics are statistically powered to detect medium effect sizes.

## Compute Feasibility

- **CPU-First**: All models run on CPU. `torch` is not used; `scikit-learn` is the primary engine.
- **Memory Management**: Climate rasters are **subset** by species bounding box before loading. This ensures memory usage stays <7GB.
- **GPU Escape Hatch**: Not applicable. The plan explicitly avoids GPU dependencies. If a CUDA call is detected (via `code/utils/gpu_check.py`), the process exits with code 1 to prevent silent failure.
- **Time Budget**: The pipeline is designed to process a subset of species (e.g., 5-10 common birds) with **raster subsetting** to fit within the 6-hour CI limit. The addition of the Recent-Data Baseline Control adds one extra training run per species, which is accounted for in the time budget.

## Decision/Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-Only** | Free-tier CI runners lack GPUs. GPU models would fail or require complex offloading not supported by the current spec. |
| **Spatial Block CV** | Standard CV overestimates performance in spatial data. Block CV is the standard for SDMs. |
| **Dynamic Pagination** | GBIF API limits responses. Hardcoded limits miss data for common species. |
| **Target-Group Background Logistic Regression** | True MaxEnt is Java-based and hard to automate in CI. Logistic regression with target-group background points mimics MaxEnt's presence-background sampling strategy, ensuring construct validity while remaining CPU-tractable. |
| **Data Subsetting** | Downloading full-continent rasters exceeds 6-hour time limit. Subsetting by species bounding box is required for feasibility. |
| **Dynamic Power Threshold** | Fixed 100-record threshold is arbitrary. Cohen's h (0.50) provides a statistically rigorous basis for data sufficiency. |
| **Recent-Data Baseline Control** | Distinguishes biological niche shift from model transferability failure. Without this, "niche stability" claims are uninterpretable. |