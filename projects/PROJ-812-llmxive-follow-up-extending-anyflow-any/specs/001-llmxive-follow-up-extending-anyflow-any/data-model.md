# Data Model: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Entities & Relationships

### 1. VideoClip
Represents a single 16-frame video segment.
- **ID**: Unique identifier (UUID or hash of file path).
- **Source**: URL or dataset name (e.g., "Kinetics-400").
- **Type**: "continuous" or "cut" (stratification label).
- **Path**: Local file path to the 16-frame clip.
- **Frames**: 16 frames, 30fps.
- **Motion_Complexity**: Float (optical flow magnitude).
- **Texture_Density**: Float (gradient variance).

### 2. ContinuityScore
Manual ground-truth annotation.
- **VideoClip_ID**: Foreign key to VideoClip.
- **Score**: Float [0.0, 1.0]. 0.0 = perfect continuity, 1.0 = maximum discontinuity.
- **Annotator_ID**: Identifier for the human annotator (if multiple).
- **Timestamp**: Time of annotation.

### 3. DivergenceMetric
Computed model instability score.
- **VideoClip_ID**: Foreign key to VideoClip.
- **DivergenceScore**: Float (L2 distance).
- **EulerSteps**: Integer (N=500 or N=200).
- **ModelVersion**: String (AnyFlow frozen weights hash).
- **Timestamp**: Time of computation.

### 4. CorrelationResult
Aggregate statistical output.
- **MetricType**: "Pearson" or "Spearman".
- **Coefficient**: Float ($r$ or $\rho$).
- **PValue**: Float.
- **SampleSize**: Integer (N=500).
- **RelationshipType**: String ("Associational").
- **Partial_Coefficient**: Float (controlling for motion/texture).

### 5. SensitivityReport
Threshold analysis output.
- **Threshold**: Float (0.01, 0.05, 0.1).
- **FalsePositiveRate**: Float.
- **FalseNegativeRate**: Float.
- **Accuracy**: Float.

### 6. VarianceReport
Variance analysis output (SC-004).
- **Variance**: Float (variance of `ContinuityScore`).
- **Status**: String ("PASS" or "FAIL").
- **Threshold**: Float (0.05).

## Data Flow

1.  **Raw Data**: `data/raw/videos/` (Video files) + `data/raw/continuity_scores.csv` (Manual scores).
2.  **Processed Data**: `data/processed/divergence_scores.csv` (Computed metrics) + `data/processed/confounders.csv` (Motion/Texture).
3.  **Analysis Data**: `data/processed/correlation_results.csv`, `data/processed/sensitivity_report.csv`, `data/processed/variance_report.csv`.
4.  **Reports**: `data/processed/final_report.md`.

## Validation Rules

- **ContinuityScore**: Must be in range [0.0, 1.0].
- **DivergenceMetric**: Must be non-negative.
- **Variance**: The variance of `ContinuityScore` must be ≥ 0.05 (FR-010).
- **Stratification**: At least 20% of clips must be labeled "cut".

## File Formats

- **CSV**: All data files are CSV with headers.
- **JSON**: Configuration files (if any).
- **YAML**: Contract schemas (see `contracts/`).