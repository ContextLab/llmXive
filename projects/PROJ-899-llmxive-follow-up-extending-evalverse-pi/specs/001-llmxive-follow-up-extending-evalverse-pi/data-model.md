# Data Model: llmXive follow-up: extending "EvalVerse" with CPU-tractable Feature Distillation

## Entities

### VideoClip
Represents a single entry from the EvalVerse dataset.
- **id**: `str` (Unique identifier, e.g., "clip_001")
- **path**: `str` (Relative path to the video file in `data/raw/evalverse/`)
- **duration**: `float` (Duration in seconds)
- **has_audio**: `bool` (True if audio track exists)
- **expert_scores**: `dict` (Mapping of dimension names to human expert scores, e.g., `{"camera_smoothness": 4.5}`)
- **vlm_scores**: `dict` or `null` (Mapping of dimension names to VLM reference scores, e.g., `{"camera_smoothness": 4.3}`) — *Optional; used only for preliminary validation (FR-009) if available.*
- **status**: `str` (e.g., "valid", "low-quality", "missing_audio")

### FeatureVector
Numerical representation of a video clip derived from hand-crafted algorithms.
- **clip_id**: `str` (Foreign key to VideoClip)
- **visual_features**: `list[float]` (Optical flow magnitude, variance, HOG density, histogram stats)
- **audio_features**: `list[float]` or `null` (Spectral centroid, zero-crossing rate; null if no audio)
- **extraction_time**: `float` (Time taken to extract features in seconds)
- **memory_peak**: `float` (Peak memory usage during extraction in MB; populated by `profiles.py` module during feature extraction to satisfy FR-006)
- **status**: `str` (e.g., "valid", "low-quality", "missing_audio")

### ModelPerformance
Record of model evaluation metrics for a specific dimension trained against human expert ground truth.
- **dimension**: `str` (e.g., "camera_smoothness")
- **model_type**: `str` (e.g., "Ridge", "Lasso", "XGBoost")
- **pearson_correlation**: `float` (Point estimate of correlation with human expert scores)
- **spearman_correlation**: `float` (Point estimate of correlation with human expert scores)
- **ci_lower_95**: `float` (Lower bound of 95% CI for Pearson)
- **ci_upper_95**: `float` (Upper bound of 95% CI for Pearson)
- **baseline_mean_predictor_r**: `float` (Correlation of mean predictor baseline; should be near 0)
- **baseline_shuffled_features_r**: `float` (Correlation of shuffled-features baseline; should be near 0)
- **exceeds_baselines_p_value**: `float` (Permutation test p-value for whether model exceeds baselines; must be < 0.05 for sufficiency)
- **classification**: `str` (e.g., "feature-sufficient", "VLM-required", "ambiguous", "insufficient")
- **threshold_sweep**: `dict` (Mapping of threshold values to classification outcomes for sensitivity analysis)

### ValidationReport
Record of the preliminary validation step (FR-009). This validates any optional VLM proxy against human expert scores but does NOT change the main target variable (which is always human expert scores).
- **sample_size**: `int` (Number of clips used in validation)
- **pearson_r**: `float` (Correlation between VLM and human expert scores)
- **p_value**: `float` (Significance of the correlation)
- **status**: `str` (e.g., "valid", "invalid", "no_vlm_available")
- **timestamp**: `str` (ISO 8601)
- **note**: `str` (If invalid, describes why; e.g., "r=0.65 < 0.70 threshold". If no VLM available, states "VLM scores not found in EvalVerse metadata; main study will use human expert scores only.")

### DimensionCorrelationMatrix
Record of the correlation structure among target dimensions (cinematic quality sub-dimensions). Used to inform permutation-based FWER control for multiple comparisons.
- **dimensions**: `list[str]` (List of dimension names)
- **correlation_matrix**: `list[list[float]]` (Symmetric matrix of Pearson correlations between dimensions)
- **timestamp**: `str` (ISO 8601)
- **note**: `str` (e.g., "Used to inform permutation-based FWER control for multiple comparisons. Accounts for observed correlation structure of target variables.")

## Relationships

- **VideoClip** `1` -- `N` **FeatureVector** (One clip generates one feature vector)
- **FeatureVector** `N` -- `1` **ModelPerformance** (Features are used to train models for multiple dimensions)
- **ValidationReport** `1` -- `N` **VideoClip** (One validation report covers a subset of clips)
- **DimensionCorrelationMatrix** `1` -- `N` **ModelPerformance** (One correlation matrix informs multiple dimension analyses)

## Data Flow

1. **Raw Data**: `data/raw/evalverse/` (Video files + metadata JSON with human expert scores)
2. **Data Validation**: `scripts/checksum_data.py` computes SHA-256 checksum of raw data and records it in `state/projects/.../artifact_hashes` (Principle II verification)
3. **Processed Data**: `data/processed/features.parquet` (Feature vectors; memory_peak field populated by profiles.py)
4. **Validation**: `reports/validation.json` (ValidationReport; gates optional VLM usage but does not affect main target variable)
5. **Model Data**: `data/processed/model_results.csv` (ModelPerformance records trained against human expert scores)
6. **Dimension Correlation**: `data/processed/dimension_correlation_matrix.csv` (DimensionCorrelationMatrix for multiple-comparison control)
7. **Reports**: `reports/summary.md` (Final summary with flags and classifications)
