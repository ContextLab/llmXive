# Data Model: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Entities & Relationships

### 1. Sample (Core Entity)
Represents a single evaluation instance.
- **Attributes**:
  - `sample_id` (string): Unique identifier.
  - `prompt` (string): The text prompt used for generation.
  - `teacher_scores` (array[4]): Scores for [Alignment, Realism, Aesthetics, Plausibility].
  - `student_score` (float): Scalar output from the student model.
  - `human_annotations` (dict): Mapping of dimension names to human scores.
  - `metadata` (dict): Includes `primary_quality_dimension` (string).
  - `is_valid` (boolean): True if all required fields are present.

### 2. FeatureRecord
Derived statistical features for a sample.
- **Attributes**:
  - `sample_id` (string): FK to Sample.
  - `variance` (float): Variance of teacher scores.
  - `entropy` (float): Shannon entropy of L1-normalized (shifted) teacher scores.
  - `skewness` (float): Skewness of teacher scores.
  - `kurtosis` (float): Kurtosis of teacher scores.
  - `difficulty_proxy` (float): Mean of teacher scores.
  - `fidelity_loss` (float): MAE between student and human (primary dim).
  - `target_variable_source` (string): The metadata field used to select the primary dimension.

### 3. BatchStats
Global statistics computed over the entire dataset.
- **Attributes**:
  - `batch_id` (string): "global".
  - `covariance_matrix` (array[4][4]): 4x4 matrix.
  - `dominant_eigenvalue` (float).
  - `sample_count` (integer).

## Data Flow

1. **Raw Data** (Parquet or Synthetic) -> **Ingest Script** -> **Cleaned DataFrame** (filtered, aligned) + **Exclusion Log** + **Lineage Report**.
2. **Cleaned DataFrame** -> **Feature Script** -> **Feature DataFrame** (with entanglement scores) + **Covariance Matrix File**.
3. **Feature DataFrame** -> **Train Script** -> **Model (Pickle)** + **Results (JSON)**.

## Storage Strategy

- **Raw**: `data/raw/z_reward.parquet` (Immutable, checksummed) or Synthetic Data.
- **Processed**: `data/processed/features.parquet` (Derived features).
- **Results**: `results/model.pkl`, `results/results.json`, `results/covariance_matrix.json`, `results/exclusion_log.csv`, `results/lineage_report.csv`.
