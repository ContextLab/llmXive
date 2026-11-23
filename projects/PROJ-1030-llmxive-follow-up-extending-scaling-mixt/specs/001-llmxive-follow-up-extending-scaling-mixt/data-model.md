# Data Model: llmXive follow-up: extending "Scaling Mixture-of-Experts Video Pretraining for Embodied Intelligence"

## Entities

### VideoClip
- **Description**: A temporal sequence of frames representing a robot action.
- **Attributes**:
  - `clip_id`: Unique identifier (string).
  - `source_dataset`: Name of the source dataset (string).
  - `frame_count`: Number of frames in the clip (integer).
  - `duration`: Duration of the clip in seconds (float).
  - `action_label`: Label of the action (string, optional).
  - `texture_score`: Pre-computed texture score for visual fidelity check (float).

### EstimatedState3D
- **Description**: A vector of 3D positions, velocities, and orientations inferred from the video clip.
- **Attributes**:
  - `clip_id`: Reference to the VideoClip (string).
  - `positions`: 3D position coordinates (list of floats).
  - `velocities`: 3D velocity coordinates (list of floats).
  - `orientations`: Orientation quaternion or Euler angles (list of floats).
  - `confidence`: Confidence score of the depth estimation (float, 0.0 to 1.0).

### ActivationPattern
- **Description**: High-dimensional vector and binary mask representing the internal state of the LingBot-Video model.
- **Attributes**:
  - `clip_id`: Reference to the VideoClip (string).
  - `latent_vector`: Flattened latent activation vector (list of floats).
  - `expert_mask`: Binary mask indicating active experts (list of integers, 0 or 1).
  - `layer_index`: Index of the DiT layer from which features were extracted (integer).

### PhysicalLabel
- **Description**: Binary value indicating whether the action in the clip violates physical constraints.
- **Attributes**:
  - `clip_id`: Reference to the VideoClip (string).
  - `label`: "valid", "invalid", or "null" (string).
  - `source`: "synthetic_perturbation" (string).
  - `exclusion_reason`: Reason for exclusion if label is "null" (string, optional).
  - `perturbation_type`: Type of perturbation applied (e.g., "gravity_defiance", "jitter") (string, optional).

### ClassifierModel
- **Description**: Lightweight machine learning model trained to predict PhysicalLabel from ActivationPattern.
- **Attributes**:
  - `model_type`: "MLP" or "RandomForest" (string).
  - `hyperparameters`: Dictionary of hyperparameters (object).
  - `metrics`: Dictionary of evaluation metrics (F1, precision, recall) (object).
  - `feature_importance`: List of feature importance scores (list of floats).

### AuditMetric
- **Description**: Metric calculated by `prior_audit.py` to verify label independence.
- **Attributes**:
  - `label_independence_score`: Correlation between depth confidence and perturbation type (float).
  - `pass_fail`: "pass" or "fail" (string).
  - `threshold`: Threshold for pass/fail (float).

### FilteringReport
- **Description**: Report generated after filtering out "null" labels.
- **Attributes**:
  - `total_samples`: Total number of samples before filtering (integer).
  - `excluded_count`: Number of samples excluded (integer).
  - `retained_count`: Number of samples retained for training (integer).
  - `exclusion_reasons`: Dictionary of reasons and counts (object).

## Data Flow

1. **Raw Data**: Video clips are downloaded from Hugging Face datasets (`data/raw`).
2. **Visual Fidelity Check**: Clips are filtered based on `texture_score`.
3. **Feature Extraction**: `lingbot_inference.py` processes clips to generate `ActivationPattern` objects, saved as `data/processed/features.npy`.
4. **Labeling**: `depth_reconstruction.py` and `perturbation.py` generate `EstimatedState3D` and `PhysicalLabel` objects, saved as `data/processed/labels.csv` and `data/processed/metadata.json`.
5. **Filtering**: Samples with low confidence or simulation failures are logged in `data/processed/excluded_samples.log` and excluded from the training set. A `filtering_report.json` is generated.
6. **Prior Audit**: `prior_audit.py` calculates `AuditMetric` and saves to `data/processed/audit_report.json`.
7. **Classification**: `train_classifier.py` ingests filtered features and labels, trains the model, and outputs metrics and feature importance.

## Storage Schema

- **features.npy**: NumPy array of shape `(N, D)` where `N` is the number of clips and `D` is the dimension of the latent vector + expert mask.
- **labels.csv**: CSV file with columns `clip_id`, `label`, `confidence`, `exclusion_reason`, `perturbation_type`. (Contains only "valid" and "invalid" for training; "null" samples are excluded from the final training CSV but logged).
- **metadata.json**: JSON file containing dataset statistics, checksums, and processing parameters.
- **excluded_samples.log**: Log file listing excluded clip IDs and reasons.
- **audit_report.json**: JSON file containing `label_independence_score`, `pass_fail`, and `threshold`.
- **memory_log.json**: JSON file containing peak RAM usage during extraction.
- **filtering_report.json**: JSON file containing counts of excluded vs. retained samples.