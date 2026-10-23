# Data Model: Predicting Molecular Properties from Topological Data Analysis

## Entities

### Molecule
- **smiles**: `string` – canonical SMILES (primary key).  
- **logP**: `float` – experimental octanol‑water partition coefficient.  
- **molecular_weight**: `float` – computed via RDKit.  
- **valid**: `bool` – passes RDKit chemical‑validity checks.  
- **exclusion_reason**: `string` – populated when `valid` is `false`.

### TopologicalDescriptor
- **molecule_id**: `string` – canonical SMILES (primary key; **must be string type**).  
- **filtration**: `string` – `"shortest_path_distance"`.  
- **grid_size**: `int` – e.g., 10, 20, 30.  
- **kernel_bandwidth**: `float` – default `1.0`.  
- **feature_vector**: `array<float>` – flattened persistence image.  
- **feature_names**: `array<string>` – names for each feature dimension.  
- **target_property**: `string` – e.g., `"logP"` (**required by feature_matrix.schema.yaml**).  
- **target_value**: `float` – the ground‑truth property value (**required by feature_matrix.schema.yaml**).

### TraditionalDescriptor
- **molecule_id**: `string` – canonical SMILES (**must be string type**).  
- **mw**: `float`.  
- **atom_counts**: `object` – map of element symbol → count.  
- **fingerprint**: `array<int>` – Morgan fingerprint (radius = 2, nBits = 1024).

### CombinedFeatureMatrix (derived)
- **molecule_id**: `string` – canonical SMILES (**must be string type**).  
- **features**: `array<float>` – concatenation of Traditional + Topological vectors.  
- **target**: `float` – `logP`.  
- **NOTE**: The `target` column is **removed** from the predictor matrix before model training to avoid circular prediction.

### ModelPerformance (per model configuration)
- **feature_set**: `enum["traditional","topological","combined"]`.  
- **model_type**: `enum["linear_l2","random_forest"]`.  
- **r2_per_fold**: `array<float>` (length = 5).  
- **rmse_per_fold**: `array<float>` (length = 5).  
- **r2_mean**, **r2_std**, **rmse_mean**, **rmse_std**: `float`.  
- **p_value**: `float` – from paired test vs. baseline.  
- **bonferroni_adjusted_p**: `float`.  
- **significant**: `bool`.

### FeatureImportance
- **traditional**: `array<float>` – importance scores for each traditional descriptor.  
- **topological**: `array<float>` – importance scores for each topological descriptor.  
- **model_type**: `string` – e.g., `"linear_l2"` or `"random_forest"`.

### DiagnosticsReport
- **vif**: `object` – predictor name → VIF value (computed only for Linear Regression).  
- **vif_flags**: `array<string>` – predictors with VIF > 5.  
- **mutual_information**: `float` – MI between Traditional and Topological matrices.  
- **sensitivity**: `object` – grid_size → R² mean/std.  
- **resource_usage**: `object` – peak RAM (GB), CPU time (seconds).

## Data Flow
1. `data_ingestion.py` → `Molecule` (validated; downloaded from official MoleculeNet repository).  
2. `02_tda_computation.py` → `TopologicalDescriptor` (with `target_property` & `target_value` per contract).  
3. `03_feature_engineering.py` → `TraditionalDescriptor` + `CombinedFeatureMatrix` (molecule_id cast to string before merge; **target column dropped before training**).  
4. `04_model_training.py` → `ModelPerformance`.  
5. `06_feature_importance.py` → `FeatureImportance` (per model_type).  
6. `06_diagnostics.py` → `DiagnosticsReport`.  
7. `07_resource_monitor.py` → `resource_usage` stored in `reports/metrics/resource_usage.json`.

## Storage Conventions
- Raw CSV: `data/raw/lipophilicity.csv` (immutable; obtained from MoleculeNet repository).  
- Processed features: `data/processed/topological_features_{grid}.csv`, `data/processed/traditional_features.csv`, `data/processed/combined_features.csv`.  
- Checksums: `data/checksums.txt` (idempotent append).  
- Model metrics: `reports/metrics/model_metrics.json` (conforms to `model_metrics.schema.yaml`).  
- Feature importance: `reports/metrics/feature_importance.json`.  
- Diagnostics: `reports/diagnostics/vif_report.json`, `reports/diagnostics/mi_report.json`, `reports/diagnostics/sensitivity_report.json`.  
- Resource log: `reports/metrics/resource_usage.json`.

---

