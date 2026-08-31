# Data Model: Quantify Dataset Sparsity Impact

## 1. Entity Definitions

### MaterialEntry
Represents a single material structure in the dataset.
- `material_id`: Unique identifier (string).
- `composition`: Chemical formula string (e.g., "Fe2O3").
- `formation_energy_per_atom`: Target variable (float).
- `elemental_descriptors`: Dict of computed features (avg atomic number, electronegativity, etc.).
- `is_in_test_set`: Boolean flag.

### SparsitySubset
Represents a specific training split.
- `subset_id`: Unique identifier (string).
- `sparsity_level`: Percentage of full dataset (float, e.g., 5.0).
- `seed`: Random seed used for generation (int).
- `row_indices`: List of indices into the full dataset.
- `parent_subset_id`: Reference to the subset from which this was sampled (for nesting validation).

### PerformanceMetric
Represents the result of a model evaluation.
- `subset_id`: Reference to SparsitySubset.
- `model_type`: String ("GPR" or "RF").
- `metric_name`: String ("RMSE", "MAE", "CalibrationSlope").
- `value`: Float.
- `fold_id`: Integer (if cross-validated).

## 2. Data Flow Diagram

```mermaid
graph TD
    A[Materials Project API] -->|Download| B(raw_pool.csv)
    B -->|Filter| C[filtered_pool.csv]
    C -->|Descriptors| D[descriptors_pool.csv]
    D -->|Impute| E[full_pool_final.csv]
    E -->|Split (20% Test)| F[Fixed Test Set] & G[Training Pool]
    G -->|Nested Subsampling (100% -> 50% -> ... -> 5%)| H[Sparsity Subsets]
    H -->|Validate (Corr >= 0.95)| I[Validated Subsets]
    I -->|Train (GPR FITC, RF)| J[Model Artifacts]
    J -->|Evaluate on F| K[Performance Metrics]
    K -->|Analyze (LMM, Tukey)| L[ANOVA Results & Plots]
    L -->|Calibration Report| M[data/results/calibration_report.json]
```

## 3. Storage Schema

- **Raw Data**: `data/raw/raw_pool.csv` (CSV, unmodified API dump).
- **Processed Data**: `data/processed/filtered_pool.csv`, `data/processed/descriptors_pool.csv`, `data/processed/full_pool_final.csv`, `data/processed/test_set.csv`.
- **Metadata**: `data/metadata/` (JSON files for checksums, sparsity configs `sparsity_<level>_<seed>.json`).
- **Results**: `data/results/` (Pickle models, CSV metrics, PNG plots, `calibration_report.json`).