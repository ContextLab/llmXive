# Data Model: llmXive follow-up: extending "Orca: The World is in Your Mind"

## Overview
This document defines the data structures, schemas, and flow for the counterfactual analysis pipeline. All data artifacts are stored in `data/` and are versioned by content hash.

## Entities

### 1. PhysicalScenario
Represents a single video clip and its associated metadata.
- **video_id**: `str` (Unique identifier from the source dataset)
- **clip_path**: `str` (Local path to the video file or frame sequence)
- **interaction_type**: `str` (e.g., "falling", "collision", "floating")
- **counterfactual_prompt**: `str` (Manual annotation, e.g., "remove gravity")
- **is_valid**: `bool` (True if the clip passed corruption checks and filtering)
- **is_ambiguous**: `bool` (True if the prompt was semantically ambiguous)

### 2. LatentVector
Represents the frozen Orca model's output for a specific frame/scenario.
- **scenario_id**: `str` (Foreign key to PhysicalScenario)
- **latent_tensor**: `numpy.ndarray` (Flattened or list representation of the vector)
- **vector_dim**: `int` (Dimensionality of the latent space)
- **has_linguistic_scaffold**: `bool` (True if the vector includes linguistic tokens)

### 3. CounterfactualEdit
Represents the transformation applied to a LatentVector.
- **edit_id**: `str` (Unique identifier)
- **source_latent_id**: `str` (Foreign key to LatentVector)
- **operation_type**: `str` (e.g., "subtraction", "masking")
- **concept_token**: `str` (e.g., "gravity", "friction")
- **modified_latent**: `numpy.ndarray` (The resulting $z_{cf}$ vector)
- **validation_status**: `str` ("valid", "ambiguous", "failed")
- **physics_outcome**: `str` (e.g., "floats", "falls" - from simulation or logical expectation)

### 4. ReadoutPrediction
Represents the output of the trained models.
- **prediction_id**: `str`
- **scenario_id**: `str`
- **model_type**: `str` ("decision_tree", "linear_probe", "pixel_baseline")
- **input_source**: `str` ("latent", "pixel")
- **predicted_outcome**: `str`
- **confidence_score**: `float`
- **ground_truth**: `str`
- **is_correct**: `bool`

## Data Flow

1. **Raw Data Ingestion**: Download video clips (or IDs) from the verified source.
2. **Latent Extraction**: Generate `LatentVector` records. Filter out invalid clips.
3. **Counterfactual Injection**: Generate `CounterfactualEdit` records for ALL clips (N=450). Flag ambiguous ones.
4. **Physics Validation**: Run simulations for a subset (N=50). Update `validation_status` and `physics_outcome` for the subset.
5. **Filtering**: Exclude `is_ambiguous=True` or `validation_status="failed"` (if causal claim is blocked) from training sets.
6. **Model Training**: Train models on filtered data. Generate `ReadoutPrediction` records.
7. **Aggregation**: Compute accuracy, p-values, and robustness metrics.

## Storage Format

- **Metadata**: CSV files (`data/metadata/scenarios.csv`, `data/metadata/edits.csv`).
- **Vectors**: NumPy `.npy` files or compressed `.npz` archives (to save disk space).
- **Logs**: JSONL files (`data/logs/audit.log`, `data/logs/failed_scenarios.log`).
- **Models**: Pickled `scikit-learn` objects (`data/models/*.pkl`).
