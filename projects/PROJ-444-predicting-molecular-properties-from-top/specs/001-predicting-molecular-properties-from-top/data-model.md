# Data Model: Predicting Molecular Properties from Topological Data Analysis

## Entities

### Molecule
- **molecule_id**: `string` – canonical SMILES (primary key).  
- **smiles**: `string` – canonical SMILES.  
- **logP**: `float` – experimental octanol‑water partition coefficient (from `XLogP3`).  
- **valid**: `bool` – passes RDKit chemical‑validity checks.  
- **exclusion_reason**: `string` – populated when `valid` is `false`.

### TopologicalDescriptor
- **molecule_id**: `string` – matches `Molecule.molecule_id`.  
- **filtration**: `string` – `"shortest_path_distance"`.  
- **grid_size**: `int` – one of `{10,20,30}`.  
- **kernel_bandwidth**: `float` – default `1.0`.  
- **feature_vector**: `array<float>` – flattened persistence image (grid_size × grid_size).  
- **feature_names**: `array<string>` – names for each pixel (e.g., `pixel_0`, `pixel_1`, …).  
- **target_property**: `string` – `"logP"` (required by `feature_matrix.schema.yaml`).  
- **target_value**: `float` – the ground‑truth `logP` for this molecule (required by `feature_matrix.schema.yaml`).

### TraditionalDescriptor
- **molecule_id**: `string`.  
- **mw**: `float` – molecular weight (RDKit).  
- **atom_counts**: `object` – mapping element symbol → count.  
- **fingerprint**: `array<int>` – Morgan fingerprint (radius = 2, nBits = 1024).  

### CombinedFeatureMatrix (derived)
- **molecule_id**: `string`.  
- **features**: `array<float>` – concatenation of Traditional + Topological vectors.  
- **target**: `float` – `logP`.  
- **NOTE**: The `target` column is **removed** from the predictor matrix before any model training (preventing circular prediction).

### ModelPerformance (per configuration)
- **feature_set**: `enum["traditional","topological","combined"]`.  
- **model_type**: `enum["linear_l2","random_forest"]`.  
- **r2_per_fold**: `array<float>` (length = 5).  
- **rmse_per_fold**: `array<float>` (length = 5).  
- **r2_mean**: `float`  
- **r2_std**: `float`  
- **rmse_mean**: `float`  
- **rmse_std**: `float`  
- **p_value**: `float` – from paired test vs. baseline.  
- **bonferroni_adjusted_p**: `float`.  
- **significant**: `bool`.

### FeatureImportance
- **traditional**: `array<float>` – importance scores for each traditional descriptor.  
- **topological**: `array<float>` – importance scores for each topological descriptor.  
- **model_type**: `string` – `"linear_l2"` or `"random_forest"`.

### DiagnosticsReport
- **vif**: `object` – predictor name → VIF value (Linear Regression only).  
- **vif_flags**: `array<string>` – predictors with VIF > 5.  
- **mutual_information**: `float` – MI between Traditional and Topological matrices.  
- **sensitivity**: `object` – `grid_size` → `{ "r2_mean": float, "r2_std": float }`.  
- **resource_usage**: `object` – `peak_ram_gb`: float, `cpu_seconds`: float.

## Data Flow
1. `01_download_pubchem.py` → `Molecule` (validated; streamed from Hugging Face).  
2. `02_tda_computation.py` → `TopologicalDescriptor` (includes `target_property` & `target_value`).  
3. `03_feature_engineering.py` → `TraditionalDescriptor` + `CombinedFeatureMatrix` (string‑cast IDs, target column dropped before training).  
4. `04_model_training.py` → `ModelPerformance`.  
5. `07_feature_importance.py` → `FeatureImportance`.  
6. `06_diagnostics.py` → `DiagnosticsReport`.  
7. `08_resource_monitor.py` → `resource_usage` stored in `reports/metrics/resource_usage.json`.

## Storage Conventions
- **Raw**: `data/raw/pubchem.parquet` (streamed, never fully materialized).  
- **Processed**:  
  - `data/processed/molecules.csv` (validated SMILES + logP).  
  - `data/processed/topological_features_{grid}.csv` (baseline 10, plus 20 & 30).  
  - `data/processed/traditional_descriptors.csv`.  
  - `data/processed/combined_features.csv`.  
- **Checksums**: `data/checksums.txt`.  
- **Metrics**: `reports/metrics/model_metrics.json` (conforms to `model_metrics.schema.yaml`).  
- **Feature Importance**: `reports/metrics/feature_importance.json`.  
- **Diagnostics**: `reports/diagnostics/vif_report.json`, `reports/diagnostics/mi_report.json`, `reports/diagnostics/sensitivity_report.json`.  
- **Resource Log**: `reports/metrics/resource_usage.json`.

---
