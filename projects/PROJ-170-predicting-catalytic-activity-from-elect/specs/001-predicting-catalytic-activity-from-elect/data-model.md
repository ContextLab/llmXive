# Data Model: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Entity Definitions

### CatalystEntry
Unified record after alignment and preprocessing. The target variable (`experimental_tof`) is **null** until an open TOF dataset is supplied.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `catalyst_id` | `string` | Hash of (`composition`, `surface_facet`) | Derived |
| `composition` | `string` | Chemical formula (e.g., `"Pt"`). | OC20 / MP |
| `surface_facet` | `string` | Surface facet index (e.g., `"111"`). | OC20 / MP |
| `synthesis_condition` | `string` \| `null` | Exact synthesis description (optional). | Experimental TOF (if available) |
| `temperature` | `number` \| `null` | Reaction temperature in K (optional). | Experimental TOF |
| `pressure` | `number` \| `null` | Reaction pressure in atm (optional). | Experimental TOF |
| `d_band_center` | `number` | d‑band center (eV, scaled). | Computed via `pymatgen` |
| `p_band_center` | `number` | p‑band center (eV, scaled). | Computed via `pymatgen` |
| `bader_charges` | `number` | Bader charge (e, scaled). | Computed via `pymatgen` |
| `activation_barrier` | `number` | Activation energy (eV, scaled). | Computed from OC20 energetics |
| `reaction_energy` | `number` | Reaction energy (eV, scaled). | Computed from OC20 energetics |
| `coordination_number` | `number` | Avg. coordination number (scaled). | Computed via `pymatgen` |
| `surface_area` | `number` | Surface area (scaled). | Computed via `pymatgen` |
| `experimental_tof` | `number` \| `null` | Experimental TOF (scaled). **Null until open dataset provided**. |
| `is_imputed` | `boolean` | True if any descriptor was filled by k‑NN. | Derived |
| `excluded_from_training` | `boolean` | True if entry is dropped from model training (insufficient neighbors, alignment failure, or missing mandatory covariates). | Derived |

### ModelMetrics
Performance statistics for each trained model.

| Attribute | Type | Description |
|-----------|------|-------------|
| `model_type` | `string` | `"XGBoost"` / `"Linear"` / `"Reduced"` |
| `r_squared` | `number` | Coefficient of determination on the hold‑out set. |
| `mean_absolute_error` | `number` | MAE (log‑TOF units) on the hold‑out set. |
| `pearson_r` | `number` | Pearson correlation coefficient on the hold‑out set. |
| `hyperparameters` | `object` | Hyperparameter dictionary (only for XGBoost). |
| `test_size` | `integer` | Number of samples in the hold‑out set. |

### FeatureImportance
SHAP‑based ranking entry.

| Attribute | Type | Description |
|-----------|------|-------------|
| `descriptor_name` | `string` | Name of the descriptor (e.g., `"d_band_center"`). |
| `mean_absolute_shap_value` | `number` | Mean absolute SHAP value across the test set. |
| `rank` | `integer` | 1 = most important. |
| `physical_mechanism` | `string` | Known mechanism (e.g., “d‑band theory”) or `"novel"` if no established link. |

### ReducedModelMetrics (SC‑003)

| Attribute | Type | Description |
|-----------|------|-------------|
| `r_squared_full` | `number` | R² of the full XGBoost model. |
| `r_squared_reduced` | `number` | R² of the model trained on the top‑5 SHAP descriptors. |
| `ratio` | `number` | `r_squared_reduced / r_squared_full`. |
| `passes_sc003` | `boolean` | True if `ratio ≥ 0.50`. |

### PerformanceSummary (FR‑008)

| Attribute | Type | Description |
|-----------|------|-------------|
| `test_name` | `string` | `"paired_t_test"` or `"wilcoxon_signed_rank"` |
| `p_value` | `number` | P‑value from the chosen test. |
| `delta_mae` | `number` | Reduction in MAE on the log‑TOF scale (ΔMAE). |
| `significant` | `boolean` | True only when `p_value < 0.05` **and** `delta_mae ≥ 0.1`. |

## Data Flow Overview
```mermaid
graph TD
    A[OC20 Stream] --> B[Descriptor Extraction (pymatgen)]
    C[Materials Project API] --> B
    B --> D[Alignment & Cleaning]
    D --> E[Imputation (k=5)]
    E --> F[Scaling (StandardScaler)]
    F --> G[aligned_dataset.csv]
    G --> H[Hold‑out Split (20 %)]
    H --> I[XGBoost Grid Search] 
    H --> J[Linear Baseline]
    I --> K[Statistical Test (t / Wilcoxon)]
    I --> L[SHAP Calculation]
    L --> M[FeatureImportance Ranking]
    M --> N[Reduced‑Model Training]
    I --> O[Final Report]
```

## Data Quality Rules
1. **No NaNs in descriptor columns** after imputation.  
2. **Exact alignment** on `composition` & `surface_facet`; optional fields matched when present.  
3. **Imputation flag** (`is_imputed=True`) recorded for any row where k‑NN filled a value.  
4. **Exclusion logging** – rows with `<5` neighbors or alignment failures are listed in `outputs/imputation_log.json` and `outputs/alignment_log.json`.  
5. **Checksum tracking** – SHA‑256 hashes for every raw and processed file stored in `data/checksums.txt`.  
6. **Schema compliance** – every output file validated against the corresponding schema in `contracts/`.  

## Storage Layout
```
data/
├── raw/
│   ├── oc20_parquet/                # streamed shards (not persisted)
│   ├── mp_cache.json                # cached MP descriptors
│   └── experimental_tof_placeholder.csv   # header‑only placeholder
├── processed/
│   └── aligned_dataset.csv
└── checksums.txt

outputs/
├── alignment_metrics.json
├── alignment_log.json
├── scaling_report.json
├── imputation_log.json
├── required_columns.json
├── holdout_indices.npy
├── best_params.json                # created after TOF available
├── best_xgboost.json               # model artifact
├── normality_test.json
├── statistical_test.json
├── shap_rankings.csv
├── shap_barplot.png
├── reduced_model_metrics.json
├── performance_summary.json
├── final_report.md
└── metrics.json                    # runtime, alignment_rate, etc.
```

## Versioning & Validation
- Every artifact’s SHA‑256 hash is recorded in `data/checksums.txt` and the project state file (`state/projects/PROJ-170-…yaml`).  
- All CSV/JSON outputs are validated with `jsonschema` against the schemas in `contracts/`.  
- The `additionalProperties: true` flag in `aligned_dataset.schema.yaml` permits future descriptor extensions without breaking validation.

---
