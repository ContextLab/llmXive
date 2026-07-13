# Research: Understanding Oceanic Phytoplankton Communities through Remote Sensing and Oceanographic Data

## Overview

This research phase defines the dataset strategy, model architecture constraints, and statistical rigor required to answer the research question: *How do oceanographic conditions drive the spatial-temporal distribution of phytoplankton?*

## Dataset Strategy

The project relies on the **SeaBASS** dataset, which is verified to contain the necessary multi-modal data: satellite ocean color pixels (derived from MODIS) and in-situ measurements (Chl-a, SST, Salinity).

| Data Type | Source / Description | Verified URL | Strategy |
|:--- |:--- |:--- |:--- |
| **SeaBASS (Multi-Modal)** | In-situ Chl-a, SST, Salinity, and derived satellite ocean color patches. | `https://huggingface.co/datasets/NOAA-SeaBASS/seaBASS` | Use the `datasets` library to load the verified SeaBASS dataset. Extract satellite patches and in-situ metadata for alignment. |
| **VLM Architecture** | Lightweight CLIP-based model (<500M params). | ` | Use the JSON for loss function reference. The model architecture will be implemented using `transformers` with a CPU-optimized configuration. |

**Critical Dataset Fit Assessment**:
The spec requires training a VLM on "concatenated image patches and text prompts." The verified SeaBASS dataset contains **real** satellite patches and in-situ metadata.
* **Match**: The dataset provides the actual visual features (ocean color) and environmental drivers (temp, salinity) required by FR-001.
* **Resolution**: The plan uses the native resolution of the SeaBASS satellite match-ups and aligns them to a station-based grid. This satisfies the requirement to ingest MODIS data without requiring the full global raster download, fitting within the 14GB disk limit.

## Model Architecture & Training Strategy

### 1. Baseline: Random Forest (FR-002)
* **Library**: `scikit-learn`
* **Configuration**: `n_estimators=500`, `max_depth=None`, `random_state=42`.
* **Rationale**: Robust, non-parametric, CPU-efficient. Serves as the lower-bound benchmark.
* **Feasibility**: Trains in <2 hours on sampled data.

### 2. VLM: Lightweight CLIP-based (FR-003)
* **Library**: `torch` (CPU), `transformers`
* **Architecture**: Distilled CLIP variant (e.g., `ViT-B/32` with reduced hidden dims) <500M params.
* **Input**:
 * *Image*: Real ocean color patches from SeaBASS.
 * *Text*: Prompts derived from environmental metadata (e.g., "Temperature: X, Salinity: Y").
* **Training**:
 * **Optimizer**: AdamW (CPU-compatible).
 * **Precision**: FP32 (No 8-bit quantization to avoid CUDA dependencies).
 * **Early Stopping**: If loss does not decrease after 3 epochs, trigger fallback to baseline.
* **Feasibility**: <500M params on 7GB RAM is tight. We will use a batch size of 8 and gradient accumulation. If memory error occurs, further reduce batch size to a lower value.

## Statistical Rigor & Methodology

### Multiple Comparison Correction
* **Issue**: We are testing multiple basins (North Atlantic, Pacific, etc.) and multiple metrics (RMSE, R², MAE).
* **Method**: Apply the **Benjamini-Hochberg (BH)** procedure for False Discovery Rate (FDR) control. This is less conservative than Bonferroni for correlated tests and maintains statistical power while controlling Type I errors.

### Sample Size & Power
* **Pre-Execution Analysis**: Before training, the pipeline will perform a power analysis to determine the minimum sample size (N) required to detect an R² difference of 0.05 with 80% power (alpha=0.05).
* **Limitation**: If the verified SeaBASS dataset yields N < required, the plan will trigger a "Scope Reduction" flag to focus on a single basin or specific season. The final report will explicitly state the power limitation and the achieved N.

### Causal Inference & Confounding
* **Nature**: Observational.
* **Claim**: Results are **associational**. We do not claim causal effects of temperature on phytoplankton without randomization.
* **Collinearity**: Temperature and nutrients are often correlated.
 * **Handling**: We will calculate Variance Inflation Factors (VIF). If VIF > 5 for any predictor, we will report the combined effect or use regularization (L2) in the RF/VLM to mitigate, but explicitly state the collinearity limitation in the results.

### Measurement Validity
* **Chl-a**: Proxy for phytoplankton abundance. Standard oceanographic practice.
* **Reanalysis**: Modeled data, not direct measurement. Validity relies on the accuracy of the reanalysis product (NOAA/Copernicus).

## Computational Feasibility Plan

| Component | Constraint | Mitigation Strategy |
|:--- |:--- |:--- |
| **RAM** | ≤ 7 GB | Data loaded in chunks; `dtype` optimized (float32); processing of SeaBASS data streamed from HuggingFace. |
| **Disk** | ≤ 14 GB | No raw rasters stored. Only processed CSVs and small model checkpoints. |
| **Time** | ≤ 6 hours | Parallelize data loading (if memory allows) or strict sequential processing. Early stopping on VLM. |
| **GPU** | None | `torch` set to `cpu`. No CUDA code paths. |

## Decision Log

1. **Real Data Ingestion**: Replaced synthetic data with the verified SeaBASS dataset to ensure scientific validity and satisfy FR-001.
2. **VLM Fallback**: If VLM training fails to converge (loss plateau), the system defaults to the Random Forest baseline. This ensures a valid result is always produced (SC-001).
3. **Power Analysis**: Added pre-execution power analysis to determine if the verified dataset is sufficient for the intended effect size (R² difference).
4. **Statistical Correction**: Switched from Bonferroni to Benjamini-Hochberg to maintain power for correlated tests.
5. **Versioning**: Unified versioning logic to `code/05_versioning_state.py`.