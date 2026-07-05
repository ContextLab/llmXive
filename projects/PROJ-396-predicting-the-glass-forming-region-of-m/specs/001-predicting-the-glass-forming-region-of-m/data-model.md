# Data Model: Predicting the Glass Forming Region of Metallic Glass Alloys via Machine Learning

## Key Entities

### AlloyComposition
Represents a single metallic alloy sample.

| Field | Type | Description |
|-------|------|-------------|
| `sample_id` | str | Unique identifier |
| `composition` | dict | Elemental fractions (e.g., {"Fe": 0.6, "B": 0.4}) |
| `gfa_label` | str | Binary: "glass-forming" or "non-glass-forming" (derived from Rc < 100 K/s if continuous) |
| `critical_cooling_rate` | float | Continuous Rc value (K/s) if available, else null |
| `delta_h_mix` | float | Mixing enthalpy (kJ/mol) |
| `delta` | float | Atomic size mismatch (%) |
| `vec` | float | Valence electron concentration |
| `delta_chi` | float | Electronegativity difference |
| `source` | str | Dataset origin (e.g., "Zenodo-GFA-DB", "Synthetic") |
| `checksum` | str | SHA256 of raw record |
| `family` | str | Inferred chemical family (Fe, Zr, etc.) based on max atomic fraction |

### ModelArtifact
Represents a trained classifier.

| Field | Type | Description |
|-------|------|-------------|
| `model_id` | str | Unique identifier |
| `algorithm` | str | "RandomForest" or "GradientBoosting" |
| `hyperparameters` | dict | Grid search best params |
| `accuracy` | float | Test set accuracy |
| `auc_roc` | float | Test set AUC-ROC |
| `f1_score` | float | Test set F1 |
| `cross_system_auc` | float | AUC on external alloy family (or null if not applicable) |
| `trained_at` | datetime | Timestamp |
| `seed` | int | Random seed used |
| `is_synthetic` | bool | Flag indicating if trained on synthetic data |

### ValidationReport
Represents the output of the evaluation phase.

| Field | Type | Description |
|-------|------|-------------|
| `report_id` | str | Unique identifier |
| `vif_scores` | dict | VIF per predictor (e.g., {"delta_h_mix": 2.1}) |
| `threshold_sensitivity` | list | Tables for thresholds {0.4, 0.5, 0.6} |
| `max_vif` | float | Maximum VIF score across predictors |
| `conclusion` | str | Explicitly "associational" statement (with provenance note if synthetic) |
| `generated_at` | datetime | Timestamp |
| `power_status` | str | "Confirmatory" (N>=150) or "Exploratory" (N<150) |
| `split_type` | str | "Cross-System" or "Stratified Random" |
| `permutation_p_value` | float | P-value from permutation test |

## Data Flow

1. **Raw Data Ingestion**: Download from verified source → `data/raw/` (checksummed).
2. **Descriptor Computation**: Compute ΔHmix, δ, VEC, Δχ → `data/processed/descriptors.csv`.
3. **Family Assignment**: Infer family based on max atomic fraction.
4. **Model Training**: Split → train RF/GB → `results/models/`.
5. **Validation**: VIF, sensitivity analysis, permutation test → `results/validation/`.
6. **Reporting**: Generate JSON/CSV reports → `results/reports/`.