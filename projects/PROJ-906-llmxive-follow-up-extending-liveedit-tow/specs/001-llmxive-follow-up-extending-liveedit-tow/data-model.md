# Data Model: llmXive follow-up: extending "LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing"

## 1. Entity Definitions

### 1.1. VideoClip
Represents a single input video unit for the experiment.
-   **`clip_id`**: Unique identifier (string).
-   **`source_path`**: Path to the raw video file in `data/raw/`.
-   **`motion_category`**: Enum: `static`, `slow_rigid`, `fast_non_rigid`.
-   **`mean_flow_magnitude`**: Mean optical flow magnitude for the clip (float, used for quantitative stratification).
-   **`duration_sec`**: Duration in seconds (float).
-   **`frame_count`**: Number of frames (integer).
-   **`resolution`**: Tuple `(height, width)` (integer).
-   **`mask_path`**: Path to the synthetic mask file.
-   **`flow_path`**: Path to the pre-computed optical flow field (numpy/parquet).
-   **`invalid_flow_count`**: Number of frames with invalid flow vectors (integer).

### 1.2. MetricRecord
Represents a single inference result for a specific clip and model variant.
-   **`record_id`**: Unique identifier (string).
-   **`clip_id`**: Foreign key to `VideoClip`.
-   **`model_variant`**: Enum: `baseline`, `flow_coherence`.
-   **`peak_memory_mb`**: Peak RAM usage in MB (float).
-   **`avg_fps`**: Average frames per second (float).
-   **`total_inference_time_sec`**: Total time for the clip (float).
-   **`ssim_mean`**: Mean SSIM between consecutive frames ($t, t-1$) (float).
-   **`ssim_std`**: Standard deviation of SSIM (float).
-   **`bss_mean`**: Mean **Background Stability Score** (SSIM of background region vs original background) (float).
-   **`bss_std`**: Standard deviation of BSS (float).
-   **`flow_normalized_ssim_mean`**: Mean **Flow-Normalized SSIM** (float).
-   **`temporal_gradient_variance`**: Variance of temporal gradients in background regions (float).
-   **`flow_magnitude_mean`**: Mean optical flow magnitude for the clip (float).
-   **`flow_magnitude_max`**: Max optical flow magnitude for the clip (float).
-   **`invalid_flow_flag`**: Boolean, true if any frame had invalid flow.
-   **`artifact_rate`**: Estimated rate of flickering artifacts (float, derived).

### 1.3. AnalysisResult
Represents the aggregated statistical output.
-   **`analysis_id`**: Unique identifier (string).
-   **`test_type`**: Enum: `piecewise_regression`, `ks_test`, `sensitivity`.
-   **`p_value`**: P-value from the statistical test (float).
-   **`threshold_value`**: The identified flow-magnitude threshold (float).
-   **`significance_level`**: Alpha level used (float, default 0.05).
-   **`regression_coefficients`**: Dictionary of coefficients (JSON).
-   **`change_point`**: The identified change-point value (float).
-   **`sensitivity_table`**: Table of cutoffs vs. artifact rates (JSON).

## 2. Data Flow

1.  **Ingestion**: `VideoClip` entities are created from verified DAVIS/VOS sources.
2.  **Preprocessing**: Flow fields are computed; `VideoClip.mean_flow_magnitude` is calculated to assign `motion_category`.
3.  **Inference**: `MetricRecord` entities are generated for each `VideoClip` and `model_variant`.
4.  **Aggregation**: `AnalysisResult` entities are computed from the `MetricRecord` table using Piecewise Regression.

## 3. Storage Format

-   **Raw Data**: MP4 (video), PNG (masks), NPZ (flow fields).
-   **Metrics**: JSON lines (`.jsonl`) or Parquet for `MetricRecord`.
-   **Analysis**: JSON for `AnalysisResult`.
-   **Checksums**: All files in `data/` have corresponding `.sha256` files.