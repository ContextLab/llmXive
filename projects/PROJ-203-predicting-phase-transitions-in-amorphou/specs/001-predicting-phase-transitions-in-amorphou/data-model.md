# Data Model: Predicting Phase Transitions in Amorphous Solids Using Machine Learning

## Entity Definitions

### Composition
Represents a specific chemical formula.
- `composition_id`: Unique identifier (string).
- `formula`: Chemical formula (string, e.g., "SiO2").
- `family`: Chemical family (enum: "oxide", "sulfide", "organic").
- `element_fractions`: Dict of element -> fraction.
- `avg_atomic_radius`: Float (Å).
- `electronegativity_variance`: Float.

### StructuralDescriptor
Derived from MD simulation.
- `descriptor_id`: Unique ID (string).
- `composition_id`: Foreign key.
- `rdf_peak_position`: Float (Å).
- `rdf_peak_width`: Float (Å).
- `bond_angle_variance`: Float.
- `coordination_number`: Float.
- `simulation_status`: Enum ("success", "truncated", "failed").
- `truncated_steps`: Integer (if truncated, else 0).
- `cooling_rate`: Float (K/min) - **Recorded for artifact control**.
- `SRO_Invariance_Assumed`: Boolean - **Flag for conditional results**.

### ThermalProperty
Experimental ground truth.
- `thermal_id`: Unique ID (string).
- `composition_id`: Foreign key.
- `Tg`: Float (K).
- `Tx`: Float (K).
- `crystallization_label`: Integer (0 or 1).
  - Logic: `1` if `abs(Tx - Tg) <= threshold`, else `0`.
- `source`: String ("Literature Subset").

### ModelPerformance
Output of training.
- `model_id`: Unique ID.
- `family`: Chemical family (or "all").
- `rmse`: Float.
- `roc_auc`: Float.
- `feature_importance`: List of (feature, score).
- `cv_scores`: List of floats.
- `null_model_rmse`: Float - **Baseline for significance**.
- `permutation_p_value`: Float - **Significance test**.
- `corrected_p_values`: List of (comparison_pair, p_value) - **FR-005 compliance**.
- `vif_values`: Dict - **FR-007 compliance**.
- `collinearity_status`: String (e.g., "No high VIF", "High VIF detected").

### SensitivityAnalysis
Output of threshold sensitivity.
- `threshold_k`: Float.
- `accuracy`: Float.
- `fpr`: Float.
- `class_balance`: Float.
- `stability_flag`: Boolean (True if FPR varies >10% across thresholds).

## Data Flow

1. **Input**: `data/raw/literature_subset.csv` (Hard-coded) + `data/raw/compositions.csv` (User provided list).
2. **Simulation**: `run_md_sim.py` generates trajectories -> `data/raw/md_trajectories/`.
3. **Feature Extraction**: `extract_descriptors.py` -> `data/processed/descriptors.csv`.
4. **Labeling**: `merge_labels.py` (T014) -> `data/processed/labels.csv`.
5. **Merge**: Join descriptors and labels -> `data/processed/final_dataset.csv`.
6. **Modeling**: `train_rf.py` -> `artifacts/models/`.
7. **Interpretation**: `interpret.py` -> `artifacts/figures/`, `artifacts/reports/`.

## Data Quality Constraints

- **Missing Values**: Rows with missing $T_g$ or $T_x$ are **excluded**.
- **NaNs**: MD simulations producing NaNs are marked "failed" and excluded.
- **Truncation**: Truncated simulations are flagged but included (with metadata).
- **Independence**: Labels are never derived from MD simulation thermodynamics.
- **Reproducibility**: `data/raw/literature_subset.csv` is checksummed and immutable.