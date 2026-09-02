# Data Model: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

## 1. Entity Definitions

### MaterialCompound
Represents a single chemical compound in the dataset.
- `material_id`: Unique string identifier (e.g., "mp-12345").
- `formula`: Chemical formula string (e.g., "H2O").
- `melting_point`: Float (K). Target variable.
- `latent_heat`: Float (J/g) or Null. Target variable (if available).
- `space_group`: String (e.g., "Fm-3m").
- `crystal_system`: String (e.g., "cubic").
- `elemental_descriptors`: Dict of computed properties (electronegativity, radius, etc.).
- `graph_features`: Sparse matrix or list of edge/adjacency data.
- `source`: String ("Materials Project", "NIST", "Literature").

### DescriptorSet
A snapshot of computed features for a compound.
- `compound_id`: FK to MaterialCompound.
- `avg_electronegativity`: Float.
- `avg_atomic_radius`: Float.
- `bond_density`: Float. (Defined as (number of bonds) / (unit cell volume)).
- `symmetry_score`: Float.
- `collinearity_flag`: Boolean (True if VIF > 5).

### ModelResult
Output of a training run.
- `model_id`: UUID.
- `model_type`: String ("Random Forest", "PySR", "Gradient Boosting").
- `r2_score`: Float.
- `mae`: Float.
- `feature_importance`: Dict (feature_name -> score).
- `symbolic_formula`: String (if PySR) or Null.
- `training_timestamp`: ISO 8601.

### ValidationResult
Output of external validation.
- `validation_id`: UUID.
- `dataset_source`: String ("Literature PCMs").
- `rank_accuracy`: Float (0.0 - 1.0).
- `false_positive_rate`: Float.
- `rules_applied`: List of strings (derived formulas).

## 2. Data Flow

1. **Ingestion**: `fetch_materials.py` -> `data/raw/mp_raw.jsonl`, `data/raw/nist_raw.jsonl`.
2. **Preprocessing**: `compute_descriptors.py` -> `data/processed/features.parquet`.
3. **Training**: `train_baselines.py`, `train_symbolic.py` -> `data/results/models/`.
4. **Validation**: `validate_external.py` -> `data/results/validation_report.json`.
5. **Reporting**: `generate_report.py` -> `docs/research_report.md`.

## 3. Constraints & Assumptions

- **Memory**: All feature matrices must fit in 7 GB RAM. Streaming is used for large datasets.
- **Null Handling**: Missing `latent_heat` is imputed only if NIST overlap > 500; otherwise, dropped or flagged.
- **Collinearity**: If VIF > 5 between descriptors, one is excluded from symbolic regression to prevent spurious coefficients. Selection is based on physical interpretability.
- **Reproducibility**: All random seeds are fixed (e.g., `seed=42`).
