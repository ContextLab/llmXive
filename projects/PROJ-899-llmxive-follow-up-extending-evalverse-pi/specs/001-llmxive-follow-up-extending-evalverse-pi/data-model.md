# Data Model: VLM Proxy Dimension Mimicry & Bias Characterization

## 1. Overview
This document defines the schema for all data artifacts produced by the pipeline. All artifacts are stored in `data/processed/` as CSV or JSON files.

## 2. Input Data (Streaming)
- **Source**: Verified HuggingFace Parquet files (VLM_SingleAction2, vlm_split, vlmsareblind).
- **Fields**: `video_url`, `action_label`, `score` (VLM-generated), `metadata`.
- **Processing**: No permanent storage of raw input; processed row-by-row.

## 3. Output Artifacts

### 3.1 `correlations.csv`
Contains the correlation results for each dimension.
- **Columns**:
  - `dimension`: Name of the video dimension (discovered dynamically, e.g., "action_jump").
  - `feature_type`: Type of low-level feature used (e.g., "optical_flow").
  - `pearson_r`: Correlation coefficient.
  - `pearson_ci_lower`: Lower bound of 95% CI.
  - `pearson_ci_upper`: Upper bound of 95% CI.
  - `spearman_r`: Spearman correlation.
  - `n_samples`: Number of clips used.
  - `p_value`: Raw p-value.
  - `adjusted_p_value`: Benjamini-Hochberg adjusted p-value.

### 3.2 `baseline_predictions.csv`
Contains the performance of baseline models.
- **Columns**:
  - `dimension`: Dimension name.
  - `predictor_type`: "mean" or "shuffled".
  - `rmse`: Root Mean Squared Error.
  - `r2`: R-squared score.

### 3.3 `permutation_raw.csv`
Raw results from the permutation test (10,000 permutations).
- **Columns**:
  - `dimension`: Dimension name.
  - `iteration`: Permutation iteration ID (0-9999).
  - `permuted_r`: Correlation calculated on shuffled data.

### 3.4 `max_t_stats.csv`
Aggregated Max-T statistics for multiple comparison control.
- **Columns**:
  - `dimension`: Dimension name.
  - `max_t`: Maximum T-statistic observed across permutations.
  - `p_value`: Adjusted p-value based on Max-T.

### 3.5 `permutation_results.csv`
Final permutation results with FDR correction.
- **Columns**:
  - `dimension`: Dimension name.
  - `raw_p`: Raw p-value.
  - `adjusted_p`: Benjamini-Hochberg adjusted p-value.

### 3.6 `dimension_viability.csv`
The final decision table.
- **Columns**:
  - `dimension`: Dimension name.
  - `viability_status`: "VLM-Reliance-High", "VLM-Reliance-Low", "Underpowered", or "Ambiguous".
  - `reason`: "CI Lower >= threshold", "CI Lower < threshold", "N < min_n", or "Point estimate > threshold but CI < threshold".
  - `confidence`: "high" (CI lower > threshold), "low" (CI lower < threshold but point estimate > threshold), or "underpowered" (N < min_n).
  - **Logic**: A "low" confidence state results in a `viability_status` of "VLM-Reliance-Low" or "Ambiguous", ensuring the classification is not "feature-sufficient".

### 3.7 `profiling_logs.json`
Memory and time profiling data.
- **Structure**: List of objects.
  - `clip_id`: Unique identifier.
  - `artifact_hash`: SHA-256 of the clip data.
  - `git_commit`: Commit hash of the code.
  - `seed`: Random seed used.
  - `peak_memory_mb`: Peak RAM usage in MB.
  - `processing_time_ms`: Time taken to process the clip.

### 3.8 `batch_raw_logs.json`
Batch processing logs.
- **Structure**: List of objects.
  - `batch_id`: Unique identifier.
  - `start_index`: Start index of the batch.
  - `end_index`: End index of the batch.
  - `processing_time_ms`: Time taken to process the batch.

### 3.9 `sensitivity_matrix.json`
Sensitivity analysis matrix (SC-004).
- **Structure**: Object mapping threshold -> list of dimensions with flip rates and stability indices.

### 3.10 `scaling_projection.json`
Linear scaling validation (FR-006).
- **Structure**: Object with `expected_n`, `time_per_clip_ms`, `projected_total_time_h`.

### 3.11 `power_analysis.json`
Power analysis results (Phase 0.6).
- **Structure**: Object with `min_n`, `expected_n`, `power_status` ("sufficient", "underpowered").

## 4. Data Lineage
- **Raw** (Streaming) -> **Extracted Features** (In-memory) -> **Correlations** (CSV) -> **Viability Decision** (CSV).
- No data is modified in place. All derived files are new.