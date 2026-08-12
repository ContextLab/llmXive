# Data Model: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

## Entity Definitions

### Compound
Represents an inorganic material entry.
- `formula`: str (e.g., "LiFePO4")
- `formation_energy_per_atom`: float (eV/atom)
- `crystal_system`: str (e.g., "cubic")
- `chemical_family`: str (e.g., "Binary", "Alkali", "Transition", "Oxide")
- `is_inorganic`: bool

### DescriptorSet
Computed features for a Compound.
- `mean_electronegativity`: float
- `var_electronegativity`: float
- `mean_atomic_radius`: float
- `var_atomic_radius`: float
- `mean_valence_electrons`: float
- `var_valence_electrons`: float
- `mean_melting_point`: float
- `var_melting_point`: float
- `mean_ionization_energy`: float
- `var_ionization_energy`: float

### ModelOutput
Results of model training and evaluation.
- `model_type`: str ("RandomForest" or "GradientBoosting")
- `train_r2`: float
- `val_r2`: float
- `train_mae`: float
- `val_mae`: float
- `train_rmse`: float
- `val_rmse`: float
- `overfitting_ratio`: float (train_r2 - val_r2)
- `feature_importances`: dict (feature_name -> importance_score)
- `permutation_importances`: dict (feature_name -> score)
- `vif_scores`: dict (feature_name -> VIF_score)
- `ale_plots`: list of paths (str)
- `ale_non_linearity_score`: float (|R²_quad - R²_lin|)

## Data Flow

1. **Raw Data**: `data/raw/mp-2020.csv` (Downloaded, checksummed).
2. **Cleaned Data**: `data/processed/cleaned_compounds.csv` (Filtered, outliers capped).
3. **Feature Data**: `data/processed/with_descriptors.csv` (Compound + DescriptorSet + chemical_family).
4. **Model Artifacts**: `data/evaluation/model_rf.pkl`, `model_gb.pkl`.
5. **Metrics**: `data/evaluation/model_metrics.json`, `feature_ranking.json`, `permutation_importance.json`, `vif_scores.json`, `ale_metrics.json`, `statistical_tests.json`.
6. **Visuals**: `data/evaluation/ale_*.png`.

## Schema Evolution

- **v1.0**: Initial schema with 5 descriptors (mean/var).
- **v1.1**: Added `chemical_family` for stratification.
- **v1.2**: Added `vif_scores`, `permutation_importances`, `ale_non_linearity_score`, and `statistical_tests` for robustness checks.

## Data Hygiene & Versioning

- All data files in `data/` are checksummed (SHA-256) and recorded in `state/...yaml`.
- Raw data is never modified. Derived files have `_v1`, `_v2` suffixes if schema changes.
- `data/elemental_properties/` contains the versioned reference table for elemental properties.

## Assumptions & Constraints

- **Missing Data**: Rows with missing elemental properties are excluded.
- **Collinearity**: VIF > 10 is logged but does not trigger feature removal.
- **Negative R²**: Valid and recorded.
- **Stratification**: By `chemical_family`, not `crystal_system`.
- **Interpretation**: Feature rankings reflect predictive contribution, not necessarily independent physical causation due to mathematical coupling of Mean/Var descriptors.
