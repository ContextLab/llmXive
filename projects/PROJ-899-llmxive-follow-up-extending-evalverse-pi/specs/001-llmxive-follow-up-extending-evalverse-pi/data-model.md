# Data Model: llmXive Feature Distillation

## Entities

### VideoClip
Represents a single video segment.
- `id`: Unique identifier (str)
- `path`: File path to the video (str)
- `duration`: Duration in seconds (float)
- `has_audio`: Boolean indicating audio presence (bool)

### FeatureVector
Extracted low-level features for a clip.
- `clip_id`: Reference to VideoClip (str)
- `optical_flow_magnitude`: Mean magnitude of flow vectors (float)
- `optical_flow_variance`: Variance of flow vectors (float)
- `hog_density`: Histogram of Oriented Gradients density (float)
- `spectral_centroid`: Audio spectral centroid (float)
- `zero_crossing_rate`: Audio zero-crossing rate (float)
- `features`: Dictionary of all features (Dict[str, float])

### DimensionScore
Human expert score for a specific dimension.
- `clip_id`: Reference to VideoClip (str)
- `dimension`: Name of the dimension (e.g., "motion", "audio_quality") (str)
- `score`: Human expert rating (float, 0-10)
- `vlm_proxy_score`: Optional VLM proxy score (float, 0-10)

### CorrelationResult
Statistical result for a dimension.
- `dimension`: Name of the dimension (str)
- `pearson_r`: Pearson correlation coefficient (float)
- `spearman_r`: Spearman correlation coefficient (float)
- `ci_lower`: Lower bound of 95% CI (float)
- `ci_upper`: Upper bound of 95% CI (float)
- `status`: "feature-sufficient" or "vlm-required" (str)

## Data Flow
1. `VideoClip` -> `FeatureVector` (via `src/data/preprocess.py`)
2. `VideoClip` + Human Scores -> `DimensionScore` (via `src/data/preprocess.py`)
3. `FeatureVector` + `DimensionScore` -> `CorrelationResult` (via `src/models/metrics.py`)
