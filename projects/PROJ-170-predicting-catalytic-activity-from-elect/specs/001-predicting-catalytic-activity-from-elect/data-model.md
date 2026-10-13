# Data Model: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Entity Definitions

### CatalystEntry
Represents a single catalyst after alignment and preprocessing. The target variable is a **proxy DFT activation barrier** (used when experimental TOF is unavailable).

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `catalyst_id` | str | Hash of (`composition`, `surface_facet`) | Derived |
| `composition` | str | Chemical formula (e.g., `"Pt"`) | OC20 / MP |
| `surface_facet` | str | Surface facet index (e.g., `"111"`) | OC20 / MP |
| `synthesis_condition` | str \| null | Exact synthesis description (optional; may be null) | Experimental TOF (if available) |
| `temperature` | number \| null | Reaction temperature (K) extracted from `synthesis_condition` (optional) | Experimental TOF (if available) |
| `pressure` | number \| null | Reaction pressure (atm) (optional) | Experimental TOF (if available) |
| `d_band_center` | float | d‑band center (eV, scaled) | Derived (pymatgen) |
| `p_band_center` | float | p‑band center (eV, scaled) | Derived (pymatgen) |
| `bader_charges` | float | Bader charge (e, scaled) | Derived (pymatgen) |
| `activation_barrier` | float | Activation energy (eV, scaled) – **used as proxy target** | Derived (pymatgen) |
| `reaction_energy` | float | Reaction energy (eV, scaled) | Derived (pymatgen) |
| `coordination_number` | float | Avg. coordination number (scaled) | Derived (pymatgen) |
| `surface_area` | float | Surface area (scaled) | Derived (pymatgen) |
| `experimental_tof` | float \| null | Experimental TOF (if an open dataset becomes available) | – |
| `is_imputed` | bool | True if any descriptor was imputed via k‑NN. | Derived |
| `excluded_from_training` | bool | True if entry was dropped for insufficient neighbors, missing optional covariates, or alignment failure. | Derived |

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
| `rank` | int | 1 = most important |
| `physical_mechanism` | str | Known mechanism (e.g., “d‑band theory”) or “novel” |

### ReducedModelMetrics (SC‑003)

| Attribute | Type | Description |
|-----------|------|-------------|
| `r_squared_full` | float | R² of the full XGBoost model |
| `r_squared_reduced` | float | R² of the top‑5 descriptor model |
| `ratio` | float | `r_squared_reduced / r_squared_full` |
| `passes_sc003` | bool | True if `ratio ≥ 0.50` |

### PerformanceSummary (FR‑008)

| Attribute | Type | Description |
|-----------|------|-------------|
| `p_value` | float | p‑value from the paired t‑test or Wilcoxon signed‑rank test |
| `delta_r_squared` | float | R²(XGBoost) − R²(baseline) on the hold‑out test set |
| `significant` | bool | True only when `p_value < 0.05` **and** `delta_r_squared ≥ 0.02` |

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
    I --> J[XGBoost CV Grid]
    I --> K[Linear Baseline]
    J --> L[Best XGBoost Model]
    K --> M[Baseline Metrics]
    L --> N[SHAP Analysis]
    N --> O[Feature Importance Ranking]
    O --> P[Reduced Model Top‑5]
    L --> Q[Metrics JSON]
    P --> R[Reduced Model Metrics]
    Q --> S[Performance Summary]
    R --> S
    S --> T[Final Report]
```

## Data Quality Rules

1. **No NaN in `activation_barrier`** – This field is the proxy target and must be present for all entries.  
2. **Exact Alignment** – `composition` and `surface_facet` must match exactly; optional fields `temperature`, `pressure`, `synthesis_condition` are matched when present.  
3. **Imputation Flag** – `is_imputed=True` for any descriptor derived via k‑NN.  
4. **Exclusion Log** – All rows with `<5` neighbors or alignment failures are recorded in `outputs/imputation_log.json` and `outputs/alignment_log.json`.  
5. **Checksum** – SHA‑256 checksums for every raw and processed file stored in `data/checksums.txt` and the project state file.  

## Storage Layout

```
data/
├── raw/
│   ├── oc20_parquet/                # streamed chunks
│   └── mp_cache.json                # cached MP descriptors
├── processed/
│   └── aligned_dataset.csv          # final cleaned, imputed, scaled table
└── checksums.txt                    # SHA‑256 hashes
outputs/
├── alignment_metrics.json
├── alignment_failure.json
├── scaling_report.json
├── imputation_log.json
├── required_columns.json
├── best_params.json
├── best_xgboost.json
├── normality_test.json
├── statistical_test.json
├── shap_rankings.csv
├── shap_barplot.png
├── reduced_model_metrics.json
├── performance_summary.json
├── final_report.md
└── metrics.json
```

## Versioning & Validation

- All output files are validated against the corresponding JSON/YAML schemas in `contracts/`.  
- Content hashes are recorded in `state/projects/PROJ-170-predicting-catalytic-activity.yaml` for reproducibility.  
