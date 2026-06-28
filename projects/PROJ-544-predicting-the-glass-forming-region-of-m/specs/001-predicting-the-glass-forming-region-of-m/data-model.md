# Data Model: Predicting the Glass Forming Region of Multi-Component Alloys via Machine Learning

## Overview

This document defines the data structures, schemas, and transformation pipeline for the glass-forming region prediction project. All data artifacts are versioned with content hashes and stored under `data/` with raw and derived CSV/parquet files.

## Entity Definitions

### Alloy Composition

Represents a multi-component metallic system with key attributes:

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| composition_id | string | Unique identifier | Required, unique |
| elements | array[string] | Elemental symbols (e.g., ["Cu", "Zr"]) | ≥3 elements, validated against periodic table |
| stoichiometries | array[number] | Atomic fractions | Sum = 1.0, all ≥0 |
| phase_label | string | Glass-forming or crystalline | Required, validated |
| label_confidence | string | "experimental" or "DFT-derived" | Required |
| source_dataset | string | Origin database | Required |
| checksum | string | SHA‑256 hash | Required |
| sampling_ratio | number | Fraction of original dataset retained after RAM‑constrained sampling (0 < ≤ 1) | Optional, default = 1.0 |

### Descriptor Vector

Represents the feature representation of an alloy:

| Attribute | Type | Description | Units |
|-----------|------|-------------|-------|
| composition_id | string | Foreign key to alloy composition | — |
| atomic_size_mismatch | number | δ (atomic size mismatch) - unitless ratio | unitless |
| mixing_enthalpy | number | ΔH_mix (mixing enthalpy) - kJ/mol | kJ/mol |
| electronegativity_variance | number | Δχ (electronegativity variance) - unitless | unitless |
| vif_scores | object | Variance Inflation Factor for each descriptor | unitless |
| computed_at | timestamp | Descriptor computation timestamp | ISO 8601 |
| library_version | string | DScribe/pymatgen version used | semver |
| pca_component_1 | number | First PCA component (if PCA fallback used) | unitless |
| pca_component_2 | number | Second PCA component (if PCA fallback used) | unitless |
| used_features | array[string] | List of feature names actually used for modeling (e.g., ["atomic_size_mismatch","mixing_enthalpy"] or ["pca_component_1","pca_component_2"]) | Required |

### Model Performance Record

Represents evaluation metrics:

| Attribute | Type | Description |
|-----------|------|-------------|
| model_id | string | Unique identifier |
| model_type | string | "RandomForest" or "GradientBoosting" |
| roc_auc | number | ROC‑AUC score |
| roc_auc_std | number | Standard deviation across CV folds |
| precision | number | Precision on held‑out test set |
| recall | number | Recall on held‑out test set |
| cv_folds | integer | Number of cross‑validation folds |
| training_time_seconds | number | Wall‑clock training time |
| random_seed | integer | Random seed used |
| evaluated_at | timestamp | Evaluation timestamp |
| imbalance_flag | boolean | True if class imbalance > 3:1 was detected |
| power_sufficient | boolean | True if the dataset meets the power‑analysis minimum sample size |
| sensitivity_analysis | object | Results of δ‑threshold robustness (keys: δ_values, metrics) |

## Data Flow

```
raw/ (checksummed)
  └── alloy_compositions.csv
        ↓ [compute_descriptors.py]
derived/
  └── descriptor_vector.csv (with VIF filtering / optional PCA)
        ↓ [train_models.py]
models/
  └── trained_models.pkl (with hyperparameters)
        ↓ [evaluate_models.py]
results/
  ├── performance_metrics.json
  ├── shap_plots/
  └── sensitivity_report.json
```

## Transformation Rules

1. **Raw Data Preservation**: Files under `data/raw/` are never modified; checksums recorded in `state/` (Constitution Principle III).
2. **Derived Files**: All transformations produce new files with derivation documentation (e.g., `descriptor_vector.csv` derived from `alloy_compositions.csv` via `compute_descriptors.py`).
3. **VIF Filtering**: Features with VIF > 5.0 removed before model training (FR‑008). If all three descriptors exceed the threshold, a PCA fallback (2 components) is applied and recorded in the `pca_component_*` fields.
4. **Class Imbalance Check**: If ratio > 3:1, `imbalance_flag` set true; downstream training may use class weighting or SMOTE (FR‑006). Flag logged in `results/imbalance_report.json`. The imbalance flag is a soft flag with alternative analysis paths.
5. **Memory Sampling**: If dataset exceeds 7 GB RAM, compositions are sampled; the sampling ratio is stored in `sampling_ratio` (FR‑007, SC‑005).
6. **Power‑Size Annotation**: After Phase 0, `power_sufficient` is set based on the power analysis (Methodology‑56e2afaf). If false, precision‑recall metrics are emphasized (SC‑001).

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Invalid elemental symbols | Flagged with error code, excluded from output |
| Missing phase labels | Excluded, count logged |
| Missing elemental property data | Fallback to nearest periodic‑table neighbor, warning logged |
| Class imbalance > 3:1 | `imbalance_flag` set; alternative analysis (class weighting, SMOTE, anomaly detection) applied; soft flag not hard stop |
| Dataset > 7 GB RAM | Sampled to fit constraint, `sampling_ratio` recorded |
| Fewer than 100 glass‑forming samples | `power_sufficient` set false; precision‑recall prioritized |
| All descriptors VIF > 5 | PCA fallback executed; `used_features` records PCA components; independent effect claims avoided |