# Data Model: Predicting Coating Adhesion Strength from Composition and Surface Features

## Entity Relationships

### Core Entities

1.  **CoatingSubstratePair**
    - **Description**: A unique record linking a specific coating formulation to a substrate material. **CRITICAL**: This entity is only valid if `validation_status` = 'verified'.
    - **Attributes**:
        - `coating_id`: String (unique identifier for the coating, derived from literature).
        - `substrate_id`: String (unique identifier for the substrate, derived from literature).
        - `adhesion_strength`: Float (target variable, in MPa, from ASTM D4541 tests).
        - `compositional_features`: Dictionary (keyed by feature name, e.g., "Fe": 1.0, "O": 2.0, "atomic_radius_variance": 0.12).
        - `surface_features`: Dictionary (keyed by feature name, e.g., "Ra": 0.5, "Rq": 0.6, "Rsk": 0.1).
        - `source`: String (original source of the record, e.g., "Materials Project", "NIST", "Literature_2023").
        - `publication_date`: Date (for deduplication logic).
        - `sample_count`: Integer (for deduplication logic).
        - `validation_status`: Enum (pending, verified, rejected). **Hard Gate**: Only records with 'verified' status are included in modeling.

2.  **FeatureDescriptor**
    - **Description**: A quantitative metric used for prediction.
    - **Attributes**:
        - `name`: String (e.g., "Ra", "Fe", "crosslinker_density_proxy").
        - `type`: Enum (compositional, surface).
        - `value`: Float.
        - `source`: String (e.g., "Materials Project", "NIST", "Derived").
        - `validation_status`: Enum (pending, verified, rejected). **Hard Gate**: Only features with 'verified' status are included in modeling.

3.  **ModelRun**
    - **Description**: A specific execution of the training pipeline.
    - **Attributes**:
        - `model_type`: Enum (GradientBoosting, RandomForest).
        - `hyperparameters`: Dictionary (e.g., {"n_estimators": 100, "max_depth": 5}).
        - `cv_scores`: Dictionary (keys: "fold_1", "fold_2", ..., values: R², RMSE, MAE).
        - `feature_importance_ranking`: List of tuples (feature_name, importance_score).
        - `shap_values`: Dictionary (feature_name: array of SHAP values).
        - `baseline_comparison`: Dictionary (e.g., {"full_vs_comp": {"p_value": 0.03, "significant": true}}).

### Relationships

- **CoatingSubstratePair** → **FeatureDescriptor**: One-to-Many (each pair has many features).
- **ModelRun** → **CoatingSubstratePair**: One-to-Many (each run uses many pairs).
- **ModelRun** → **ModelRun**: None (independent runs, but compared via baseline comparison).

## Data Flow

### Ingestion Pipeline

1.  **Raw Data Fetch**:
    - **Sources**: Materials Project API, NIST Surface Metrology, Literature.
    - **Format**: JSON/CSV.
    - **Output**: `data/raw/materials_project.json`, `data/raw/nist_surface.csv`, `data/raw/literature.csv`.

2.  **Cleaning & Alignment**:
    - **Steps**:
        - Remove null targets (adhesion_strength).
        - Impute missing surface features (median by substrate class) or exclude.
        - Deduplicate by `coating_id` + `substrate_id` (keep most recent/highest sample count).
        - Apply **Strict Validation Protocol**: Reject any record pair that cannot be linked via a unique, verified identifier. Do not use heuristic mapping.
    - **Output**: `data/processed/coating_adhesion_dataset.csv` (only includes records with `validation_status` = 'verified').

3.  **Feature Engineering**:
    - **Steps**:
        - One-hot encode elemental composition.
        - Calculate derived descriptors (atomic radius variance, crosslinker density proxy).
        - **Construct Validity Assessment**: Validate derived proxies against theoretical models. Exclude unvalidated proxies.
        - Standardize surface features.
    - **Output**: `data/processed/coating_adhesion_dataset_enriched.csv`.

### Modeling Pipeline

1.  **Split**: Nested 5-fold CV (outer loop for evaluation, inner for tuning).
2.  **Train**: GBR and RFR on training folds.
3.  **Evaluate**: Compute R², RMSE, MAE on test folds.
4.  **Interpret**: SHAP values, permutation importance.
5.  **Compare**: Baseline models (composition-only, surface-only) + statistical tests.
6.  **Output**: `data/processed/model_results.json`, `data/processed/feature_rankings.json`.

## Schema Definitions

### CoatingSubstratePair (CSV Schema)

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `coating_id` | String | Unique coating identifier | Not null, unique per row (with substrate_id) |
| `substrate_id` | String | Unique substrate identifier | Not null |
| `adhesion_strength` | Float | Target variable (MPa) | Not null, >0 |
| `publication_date` | Date | Source publication date | Not null |
| `sample_count` | Integer | Number of samples in source | ≥1 |
| `source` | String | Data source | Enum: "Materials Project", "NIST", "Literature" |
| `compositional_features` | JSON | Encoded composition | Not null |
| `surface_features` | JSON | Encoded surface metrics | Not null |
| `validation_status` | Enum | Validation status | Enum: "pending", "verified", "rejected" |

### ModelRun (JSON Schema)

```yaml
model_type: string (enum: "GradientBoosting", "RandomForest")
hyperparameters: object
cv_scores:
  fold_1:
    r2: float
    rmse: float
    mae: float
  ...
feature_importance_ranking:
  - feature_name: string
    importance: float
  ...
shap_values:
  feature_name: array of floats
baseline_comparison:
  full_vs_comp:
    p_value: float
    significant: boolean
  full_vs_surface:
    p_value: float
    significant: boolean
```

## Data Quality Rules

1.  **Null Handling**:
    - `adhesion_strength`: Rows with null values are excluded (logged).
    - Surface features: Imputed with median (by substrate) or excluded (logged).
    - Compositional features: Imputed with zero or excluded (logged).

2.  **Deduplication**:
    - Key: `coating_id` + `substrate_id`.
    - Conflict resolution: Keep record with latest `publication_date` or highest `sample_count`.

3.  **Validation**:
    - All `adhesion_strength` values must be from ASTM D4541 tests (filter in ingestion).
    - No duplicate rows in final dataset.
    - Feature values must be within reasonable ranges (e.g., Ra > 0, adhesion_strength > 0).
    - **Hard Gate**: Only records with `validation_status` = 'verified' are included in modeling.

4.  **Checksums**:
    - All raw and processed files must be checksummed (SHA-256) and recorded in `state/...yaml`.

## Storage Strategy

- **Raw Data**: `data/raw/` (immutable, checksummed).
- **Processed Data**: `data/processed/` (derived, checksummed).
- **Logs**: `data/processed/logs/` (ingestion logs, exclusion logs, validation logs).
- **Models**: `data/processed/models/` (serialized models, if needed).

## Constraints & Assumptions

- **Memory**: Dataset ≤5,000 rows (7 GB RAM limit).
- **Runtime**: Pipeline ≤4 hours (6-hour limit with safety margin).
- **Feature Stability**: Derived features (e.g., crosslinker density) must be numerically stable (no overflow/underflow).
- **Alignment**: **No heuristic mapping**. Records must be linked via unique, verified identifiers. Unmappable records are rejected.
- **Construct Validity**: Derived proxies must be validated against theoretical models. Unvalidated proxies are excluded.