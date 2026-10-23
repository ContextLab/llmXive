# Data Model: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Entity Definitions

### CatalystEntry
Represents a single catalyst after alignment and preprocessing. The target variable is **experimental TOF** (when available); a placeholder null is used until an open dataset is provided.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `catalyst_id` | str | Hash of (`composition`, `surface_facet`) | Derived |
| `composition` | str | Chemical formula (e.g., `"Pt"`) | OC20 / MP |
| `surface_facet` | str | Surface facet index (e.g., `"111"`) | OC20 / MP |
| `synthesis_condition` | str \| null | Exact synthesis description (optional) | Experimental TOF (if available) |
| `temperature` | number \| null | Reaction temperature (K) (optional) | Experimental TOF (if available) |
| `pressure` | number \| null | Reaction pressure (atm) (optional) | Experimental TOF (if available) |
| `d_band_center` | float | d‑band center (eV, scaled) | Derived (pymatgen) |
| `p_band_center` | float | p‑band center (eV, scaled) | Derived (pymatgen) |
| `bader_charges` | float | Bader charge (e, scaled) | Derived (pymatgen) |
| `activation_barrier` | float | Activation energy (eV, scaled) | Derived (pymatgen) |
| `reaction_energy` | float | Reaction energy (eV, scaled) | Derived (pymatgen) |
| `coordination_number` | float | Avg. coordination number (scaled) | Derived (pymatgen) |
| `surface_area` | float | Surface area (scaled) | Derived (pymatgen) |
| `experimental_tof` | float \| null | Experimental turnover frequency (scaled). **Will be populated when an open TOF dataset is supplied**. |
| `is_imputed` | bool | True if any descriptor was imputed via k‑NN. | Derived |
| `excluded_from_training` | bool | True if entry was dropped for insufficient neighbors, alignment failure, or missing mandatory covariates. | Derived |

### ModelMetrics
Performance statistics for each trained model.

| Attribute | Type | Description |
|-----------|------|-------------|
| `model_type` | str | `"XGBoost"` / `"Linear"` / `"Reduced"` |
| `r_squared` | float | R² on hold‑out test set |
| `mean_absolute_error` | float | MAE on test set |
| `pearson_r` | float | Pearson correlation coefficient |
| `test_size` | int | Number of test samples |
| `hyperparameters` | object | Hyperparameter dict (for XGBoost) |

### FeatureImportance
SHAP‑based ranking entry.

| Attribute | Type | Description |
|-----------|------|-------------|
| `descriptor_name` | str | Name of the descriptor |
| `mean_absolute_shap_value` | float | Mean absolute SHAP value |
| `rank` | int | 1 = most important |
| `physical_mechanism` | str | Known mechanism (e.g., “d‑band theory”) or “novel” |

### ReducedModelMetrics (SC‑003)

| Attribute | Type | Description |
|-----------|------|-------------|
| `r_squared_full` | float | R² of the full XGBoost model |
| `r_squared_reduced` | float | R² of the top‑5 descriptor model |
| `ratio` | float | `r_squared_reduced / r_squared_full` |
| `passes_sc003` | bool | True if `ratio ≥ 0.50` |

### PerformanceSummary (FR‑008)

| Attribute | Type | Description |
|-----------|------|-------------|
| `p_value` | float | P‑value from paired test |
| `delta_mae` | float | Reduction in MAE on the log‑TOF scale (ΔMAE) |
| `significant` | bool | True only when `p_value < 0.05` **and** `delta_mae ≥ 0.1` (log‑TOF units) |

## Data Flow Diagram

```mermaid
graph TD
    A[OC20 Stream] --> B[Descriptor Extraction]
    C[MP API] --> B
    B --> D[Alignment (comp + facet)]
    D --> E{Imputation k=5}
    E -->|Success| F[Imputed Dataset]
    E -->|<5 neighbors| G[Excluded Log]
    F --> H[Scaling]
    H --> I[aligned_dataset.csv]
    I --> J[Hold‑out Split (pending TOF)]
    J --> K[Model Training (deferred)]
    K --> L[SHAP Analysis (deferred)]
    L --> M[Reduced Model (deferred)]
    M --> N[Final Report (deferred)]
```

## Data Quality Rules

1. **No NaN in required descriptors** – all numeric descriptor columns must be populated after imputation.  
2. **Exact alignment** – `composition` and `surface_facet` must match exactly; optional fields matched when present.  
3. **Imputation flag** – `is_imputed=True` if any descriptor was filled via k‑NN.  
4. **Exclusion logging** – rows with `<5` neighbors or alignment failures are recorded in `outputs/imputation_log.json` and `outputs/alignment_log.json`.  
5. **Checksum** – SHA‑256 hashes for every raw and processed file stored in `data/checksums.txt` and the project state file.  

## Storage Layout

```
data/
├── raw/
│   ├── oc20_parquet/                # streamed shards
│   └── mp_cache.json                # cached MP descriptors
├── processed/
│   └── aligned_dataset.csv          # final cleaned, imputed, scaled table (experimental_tof may be null)
└── checksums.txt                    # SHA‑256 hashes

outputs/
├── alignment_metrics.json
├── alignment_failure.json
├── scaling_report.json
├── imputation_log.json
├── required_columns.json
├── best_params.json                # will be created after TOF data available
├── best_xgboost.json               # will be created after TOF data available
├── normality_test.json
├── statistical_test.json
├── shap_rankings.csv               # validated against feature_importance.schema.yaml
├── shap_barplot.png
├── reduced_model_metrics.json
├── performance_summary.json
├── final_report.md
└── metrics.json
```

## Versioning & Validation

- All output files are validated against the JSON/YAML schemas in `contracts/`.  
- Content hashes are recorded in `state/projects/PROJ-170-predicting-catalytic-activity.yaml` for reproducibility.  

---

