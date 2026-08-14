# Data Model: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Data Flow

1. **Raw Input**: `data/raw/z_reward_eval.parquet` (Source: Z-Reward Dataset - *See Research.md for availability status*)
2. **Ingestion**: `code/ingestion.py` validates schema, filters missing annotations, calculates `fidelity_loss`.
3. **Feature Store**: `data/processed/features.json` (Per-sample features + batch metadata).
4. **Model Artifact**: `results/model.pkl` (Trained Random Forest).
5. **Results**: `results/results.json` (Aggregated metrics).

## Entity Definitions

### Sample
- **ID**: Unique identifier (row index or UUID).
- **Prompt**: Text string.
- **Teacher Scores**: Dictionary or 4-column vector (Alignment, Realism, Aesthetics, Plausibility).
- **Student Score**: Float (scalar).
- **Human Annotations**: Dictionary or 4-column vector (Alignment, Realism, Aesthetics, Plausibility).
- **Primary Quality Dimension**: String (e.g., "Alignment") derived from metadata.
- **Fidelity Loss**: Float (MAE between Student Score and Human Annotation for Primary Dimension).

### Entanglement Features (Per Sample)
- **Variance**: Float (Variance of the 4 teacher scores).
- **Entropy**: Float (Shannon entropy of the 4 teacher scores).
- **Skewness**: Float.
- **Kurtosis**: Float.

### Batch Metadata
- **Covariance Matrix**: 4x4 Float matrix.
- **Dominant Eigenvalue**: Float.

## Storage Format

- **Raw**: Parquet (immutable).
- **Processed**: JSON (features) and Pickle (model).
- **Results**: JSON (metrics).

## Constraints

- **Missing Data**: Rows with null `human_annotations` for the target dimension are dropped.
- **Zero Variance**: Handled by setting entropy/variance to 0.
- **Data Integrity**: All transformations are logged; no in-place modification of raw data.
