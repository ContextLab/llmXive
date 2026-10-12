# Data Model: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Entity Definitions

### CatalystEntry
Represents a single catalyst after alignment and preprocessing. The target variable is a **generic catalytic turnover frequency** (surrogate TOF), not CO₂ hydrogenation‑specific.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `catalyst_id` | str | Hash of (`composition`, `surface_facet`, `synthesis_condition`) | Derived |
| `composition` | str | Chemical formula (e.g., `"Pt"`) | OC20 / MP |
| `surface_facet` | str | Surface facet index (e.g., `"111"`) | OC20 / MP |
| `synthesis_condition` | str | Exact synthesis description (must match across sources) | Experimental TOF (surrogate) |
| `temperature` | float | Reaction temperature (K) extracted from `synthesis_condition` | Experimental TOF (surrogate) |
| `pressure` | float | Reaction pressure (atm) extracted from `synthesis_condition` | Experimental TOF (surrogate) |
| `d_band_center` | float | d‑band center (eV, scaled) | Derived (pymatgen) |
| `p_band_center` | float | p‑band center (eV, scaled) | Derived (pymatgen) |
| `bader_charges` | float | Bader charge (e, scaled) | Derived (pymatgen) |
| `activation_barrier` | float | Activation energy (eV, scaled) | Derived (pymatgen) |
| `reaction_energy` | float | Reaction energy (eV, scaled) | Derived (pymatgen) |
| `coordination_number` | float | Avg. coordination number (scaled) | Derived (pymatgen) |
| `surface_area` | float | Surface area (scaled) | Derived (pymatgen) |
| `experimental_tof` | float | null | Surrogate TOF dataset (generic catalytic activity) |
| `is_imputed` | bool | True if any descriptor was imputed via k‑NN. | Derived |
| `excluded_from_training` | bool | True if entry was dropped for insufficient neighbors, missing covariates, or alignment failure. | Derived |

### ModelMetrics
Performance statistics for each trained model.

| Attribute | Type | Description |
|-----------|------|-------------|
| `model_type` | str | `"XGBoost"` or `"Linear"` or `"Reduced"` |
| `r_squared` | float | R² on hold‑out test set |
| `mean_absolute_error` | float | MAE on test set |
| `pearson_r` | float | Pearson correlation coefficient |
| `test_size` | int | Number of test samples |
| `hyperparameters` | object | Hyperparameter dictionary (for XGBoost) |

### FeatureImportance
SHAP‑based ranking entry.

| Attribute | Type | Description |
|-----------|------|-------------|
| `descriptor_name` | str | Name of the descriptor |
| `mean_absolute_shap_value` | float | Mean absolute SHAP value |
| `rank` | int | 1 = most important |
| `physical_mechanism` | str | Known mechanism (e.g., “d‑band theory”) or “novel” |

### ReducedModelMetrics (SC‑003)

| Attribute | Type | Description |
|-----------|------|-------------|
| `r_squared_full` | float | R² of the full XGBoost model |
| `r_squared_reduced` | float | R² of the top‑5 descriptor model |
| `ratio` | float | `r_squared_reduced / r_squared_full` |
| `passes_sc003` | bool | True if `ratio ≥ 0.50` |

## Data Flow Diagram

```mermaid
graph TD
    A[OC20 Stream] --> B[Descriptor Extraction]
    C[MP API] --> B
    D[Surrogate TOF JSONL] --> E[Alignment & Merge]
    B --> E
    E --> F{Imputation k=5}
    F -->|Success| G[Imputed Dataset]
    F -->|<5 neighbors| H[Excluded Log]
    G --> I[Scaling]
    I --> J[aligned_dataset.csv]
    J --> K[XGBoost CV Grid]
    J --> L[Linear Volcano Model]
    K --> M[Best XGBoost Model]
    L --> N[Baseline Metrics]
    M --> O[SHAP Analysis]
    O --> P[Feature Importance Ranking]
    P --> Q[Reduced Model (Top‑5)]
    M --> R[Metrics JSON]
    Q --> S[Reduced Model Metrics]
    R --> T[Final Report]
    S --> T
```

## Data Quality Rules

1. **No NaN in `experimental_tof`** – Entries lacking TOF are excluded before model training.  
2. **Exact Alignment** – `composition`, `surface_facet`, **and** `synthesis_condition` must match exactly; temperature and pressure must be present; otherwise entry is excluded.  
3. **Imputation Flag** – `is_imputed=True` for any descriptor derived via k‑NN.  
4. **Exclusion Log** – All rows with `<5` neighbors or alignment failures are recorded in `outputs/imputation_log.json` and `outputs/alignment_log.json`.  
5. **Checksum** – SHA‑256 checksums for every raw and processed file stored in `state/projects/...yaml`.  

## Storage Layout

```
data/
├── raw/
│   ├── oc20_parquet/                # streamed chunks
│   ├── mp_cache.json                # cached MP descriptors
│   └── tof_surrogate.jsonl          # surrogate TOF values (generic catalytic activity)
├── processed/
│   └── aligned_dataset.csv          # final cleaned, imputed, scaled table
└── checksums.txt                    # SHA‑256 hashes
outputs/
├── alignment_log.json
├── imputation_log.json
├── feature_importance.png
├── reduced_model_metrics.json
├── final_report.md
└── metrics.json
```

---



