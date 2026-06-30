# Data Model: Predicting Personal Sleep Quality from Resting‑State fMRI Connectivity

## 1. Entity Definitions

### 1.1 Subject
Represents a single participant in the HCP study.
- **Attributes**:
  - `subject_id` (str): Unique HCP subject identifier (e.g., "100307").
  - `sleep_score` (float): Composite score derived from sleep questionnaire items.
  - `motion_fd` (float): Mean Framewise Displacement (used for exclusion if > 0.3mm).
  - `status` (str): "valid", "excluded_motion", "excluded_missing_sleep".

### 1.2 ConnectivityVector
The feature representation for a single subject.
- **Attributes**:
  - `subject_id` (str): FK to Subject.
  - `vector` (ndarray[float32]): Flattened upper-triangular Fisher-z transformed correlation matrix.
  - `dimensionality` (int): Number of features (post-variance threshold, pre-PCA).
  - `preprocessed_path` (str): Path to the `.npy` file.

### 1.3 FeatureMatrix
The aggregated dataset for modeling.
- **Attributes**:
  - `X` (ndarray[float32]): Shape (n_subjects, n_features).
  - `y` (ndarray[float32]): Shape (n_subjects,).
  - `metadata` (dict): Includes PCA components, variance thresholds, and hyperparameters used.

### 1.4 ModelArtifact
The trained Elastic Net model and its evaluation metrics.
- **Attributes**:
  - `model` (ElasticNetCV): Trained sklearn object.
  - `hyperparams` (dict): Best `alpha`, `l1_ratio`.
  - `metrics` (dict): `pearson_r`, `r2`, `p_value`, `bootstrap_ci`.
  - `coefficients` (ndarray): Non-zero coefficients mapped to edges.

### 1.5 ResultReport
The final JSON output summarizing the experiment.
- **Attributes**:
  - `experiment_id` (str): Hash of code + data.
  - `timestamp` (iso8601).
  - `metrics` (dict): Aggregated performance.
  - `permutation_p_value` (float).
  - `bootstrap_ci` (tuple).
  - `visualization_paths` (list[str]): Paths to generated plots.
  - `logs_path` (str): Path to structured JSON log.

## 2. Data Flow

1. **Ingest**: Raw HCP CIFTI + Behavioral CSV -> `Subject` (filtered).
2. **Process**: `Subject` (valid) -> `ConnectivityVector` (`.npy` files).
3. **Aggregate**: `ConnectivityVector` -> `FeatureMatrix` (X, y).
4. **Model**: `FeatureMatrix` -> `ModelArtifact` (via Nested CV).
5. **Evaluate**: `ModelArtifact` -> `ResultReport` (with Permutation/Bootstrap).
6. **Visualize**: `ModelArtifact` (coefficients) -> Plot files.

## 3. Storage Schema

- **Raw Data**: `data/raw/hcp_1200/` (CIFTI, CSV).
- **Processed Data**: `data/processed/connectivity_vectors/` (`.npy`).
- **Model Data**: `data/processed/model_inputs/` (`.npy` for X, y).
- **Results**: `data/results/` (`.json`, `.png`, `.svg`).
- **Logs**: `data/logs/` (`.jsonl`).

## 4. Constraints

- **Data Integrity**: Raw files are read-only.
- **Size Limits**: `FeatureMatrix` must be < 200MB to fit in RAM comfortably.
- **Seeding**: All random number generators (numpy, sklearn) seeded with `42` (configurable) to ensure reproducibility.
