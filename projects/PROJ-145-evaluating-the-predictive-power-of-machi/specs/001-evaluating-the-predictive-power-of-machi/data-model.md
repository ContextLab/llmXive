# Data Model: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

## 1. Conceptual Model

The data model revolves around three core entities: `Composition`, `DescriptorSet`, and `PredictionResult`.

1.  **Composition**: Represents a chemical formula (e.g., `CoCrFeMnNi`). Contains elemental counts and a unique hash.
2.  **DescriptorSet**: Derived features (mean/var of radius, electronegativity, etc.) calculated from the Composition.
3.  **PredictionResult**: Model output (predicted formation energy, uncertainty) and ground truth (if available).

## 2. Physical Data Flow

```mermaid
graph TD
    A[Raw Parquet (AFLOW/API)] -->|Filter 5+ Elements| B(heas_train.csv)
    B -->|Feature Eng (pymatgen)| C(heas_train_descriptors.csv)
    B -->|Split 10%| D(holdout_known.csv)
    D -->|Feature Eng| E(holdout_known_descriptors.csv)
    B -->|Combinatorial Gen| F(true_novel_candidates)
    F -->|Thermo Stability Filter| G(stable_candidates)
    G -->|Filter Not in Source| H(true_novel.csv)
    H -->|Final API Check| I(true_novel_final.csv)
    I -->|Feature Eng| J(true_novel_descriptors.csv)
    C -->|Train| K(Model RF/GB)
    E -->|Eval| L(Holdout Metrics)
    J -->|Predict| M(Novel Predictions)
    M -->|Uncertainty Calc| N(Report CSV)
```

## 3. File Schemas

### 3.1 Input: Raw Data (Parquet)
*Source*: Verified Hugging Face datasets.
*Structure*: Flexible, depends on source. Key columns expected: `composition`, `formation_energy`, `mixing_enthalpy`. **Schema validation ensures presence of these columns.**

### 3.2 Intermediate: Processed HEA (CSV)
*File*: `data/processed/heas_train.csv`, `holdout_known.csv`, `true_novel.csv`
*Columns*:
*   `composition_id`: Unique hash (SHA256 of sorted elemental string).
*   `formula`: Human-readable formula (e.g., `CoCrFeMnNi`).
*   `elements`: JSON list of elements.
*   `formation_energy`: Float (Target).
*   `mixing_enthalpy`: Float (Target).

### 3.3 Feature-Engineered Data (CSV)
*File*: `data/processed/heas_train_features.csv` (and equivalents for test sets)
*Columns*:
*   `composition_id`: PK.
*   `radius_mean`, `radius_var`: Float.
*   `electroneg_mean`, `electroneg_var`: Float.
*   `vec_mean`, `vec_var`: Float.
*   `melting_mean`, `melting_var`: Float.
*   `target`: Float (Formation Energy).
*   **Streaming Constraint**: Data is processed in chunks to respect the 7GB RAM limit.

### 3.4 Output: Predictions & Metrics (CSV)
*File*: `data/processed/predictions_novel.csv`
*Columns*:
*   `composition_id`.
*   `predicted_energy`: Float.
*   `uncertainty_variance`: Float.
*   `hull_distance`: Float (Mahalanobis distance).
*   `rank`: Integer (1-100).

*File*: `data/processed/metrics_summary.csv`
*Columns*:
*   `metric_name`: String (e.g., `train_r2`, `holdout_r2`, `spearman_rho`).
*   `value`: Float.
*   `p_value`: Float (if applicable).
*   `description`: String.

### 3.5 Split Metadata (CSV)
*File*: `data/processed/split_metadata.csv`
*Columns*:
*   `split_name`: String (e.g., `train`, `holdout`, `novel`).
*   `row_count`: Integer.
*   `checksum`: String (SHA256).
*   `validation_status`: String (e.g., `passed`, `failed`).

## 4. Constraints & Rules

*   **Clamping**: `radius_var`, `electroneg_var`, etc., must be $\ge 1e-6$.
*   **Uniqueness**: `composition_id` must be unique within each file.
*   **Missing Data**: Rows with missing `formation_energy` are dropped during ingestion.
*   **Precision**: All floats stored with 6 decimal places.
*   **Streaming**: Ingestion is limited to a scalable total dataset size, processed in 1000-row chunks.
*   **Stability Filter**: "True Novel" candidates must have predicted formation energy < 0.1 eV/atom.
