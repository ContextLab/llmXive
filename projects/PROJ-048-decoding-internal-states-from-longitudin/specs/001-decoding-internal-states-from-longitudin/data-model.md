# Data Model: Decoding Internal States from Longitudinal Calcium Imaging Data

## 1. Core Entities

### FluorescenceTrace
Represents the time-series signal of a specific Region of Interest (ROI).
*   **Attributes**:
    *   `roi_id`: Unique identifier for the ROI.
    *   `raw_trace`: Array of raw fluorescence intensity values (float32).
    *   `df_trace`: Array of dF/F normalized values (float32).
    *   `detrended_trace`: Array of detrended signal (float32).
    *   `spike_estimates`: Array of deconvolved spike rates (float32).
    *   `timestamps`: Array of time points (float64, seconds).
*   **Constraints**:
    *   No NaN values allowed (interpolated or raised error).
    *   Memory footprint per trace must be minimized.

### LatentComponent
Represents a row in the NMF components matrix ($H$), describing a spatial pattern.
*   **Attributes**:
    *   `component_id`: Integer index (0 to k-1).
    *   `weights`: Array of spatial weights for each ROI (float32).
    *   `stability_score`: Cosine similarity score against other seeds (float32).
*   **Constraints**:
    *   All weights must be non-negative (NMF property).

### ComponentWeight
Represents the time-varying activation strength of a specific LatentComponent.
*   **Attributes**:
    *   `component_id`: Integer index.
    *   `activation_series`: Array of time-varying weights (float32).
    *   `temporal_smoothness_score`: Regularization score (float32) indicating the degree of smoothness enforced.
*   **Constraints**:
    *   Aligned with `timestamps`.

### BehavioralMetric
Represents an external variable aligned with neural data.
*   **Attributes**:
    *   `metric_name`: String (e.g., "running_speed", "stimulus_onset").
    *   `values`: Array of metric values (float32 or boolean).
    *   `timestamps`: Array of time points (float64).
*   **Constraints**:
    *   Must be resampled to match imaging data timestamps if rates differ.

### AlignmentResult
Represents the result of aligning behavioral metadata with neural data.
*   **Attributes**:
    *   `metric_name`: String.
    *   `alignment_error`: Float representing the maximum temporal misalignment in frames (float32).
    *   `resampling_method`: String (e.g., "linear_interpolation").
*   **Constraints**:
    *   `alignment_error` must be ≤ 1 frame to satisfy SC-005.

### CorrelationResult
Result of the statistical validation.
*   **Attributes**:
    *   `component_id`: Integer.
    *   `metric_name`: String.
    *   `spearman_rho`: Correlation coefficient (float32).
    *   `p_value`: Permutation test p-value (float32).
    *   `corrected_p_value`: FDR-corrected p-value (float32).
    *   `is_significant`: Boolean (corrected p < 0.05).
    *   `null_distribution_mean`: Mean of the time-shuffled null distribution (float32).

## 2. Data Flow

1.  **Raw Data** (Parquet/CSV) → **Download** → `data/raw/session_*.parquet`
2.  **Raw Data** → **Preprocess** → `data/processed/dF_norm.npz` (FluorescenceTrace)
3.  **FluorescenceTrace** → **NMF** → `data/processed/components_H.npz` (LatentComponent, ComponentWeight)
4.  **ComponentWeight** + **BehavioralMetric** → **Alignment** → `data/processed/alignment_results.json` (AlignmentResult)
5.  **ComponentWeight** + **BehavioralMetric** → **Stats** → `data/results/correlations.csv` (CorrelationResult)

## 3. Storage Constraints
*   **Max Memory**: 5GB.
*   **File Format**:
    *   Raw: Parquet (compressed).
    *   Processed: NumPy `.npz` (compressed) for fast loading.
    *   Results: CSV/JSON.
*   **Chunking**: Large arrays (e.g., full session traces) must be loaded in chunks if > 2GB.

