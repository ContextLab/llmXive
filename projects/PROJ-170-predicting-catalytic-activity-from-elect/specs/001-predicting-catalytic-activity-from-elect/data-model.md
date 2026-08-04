# Data Model: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Entity Definitions

### CatalystEntry
Represents a unique catalyst configuration after alignment and preprocessing.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `catalyst_id` | str | Unique identifier (hash of composition + facet + condition) | Derived |
| `composition` | str | Chemical formula (e.g., "Pt") | OC20/MP |
| `surface_facet` | str | Surface facet (e.g., "111") | OC20/MP |
| `synthesis_condition` | str | Synthesis condition (fuzzy-matched) | Experimental |
| `d_band_center` | float | d-band center (eV) | Derived (pymatgen) |
| `p_band_center` | float | p-band center (eV) | Derived (pymatgen) |
| `bader_charges` | float | Bader charge (e) | Derived (pymatgen) |
| `activation_barrier` | float | Activation energy (eV) | Derived (pymatgen) |
| `reaction_energy` | float | Reaction energy (eV) | Derived (pymatgen) |
| `coordination_number` | float | Average coordination number (for imputation) | Derived |
| `surface_area` | float | Surface area (for imputation) | Derived |
| `experimental_tof` | float | Experimental TOF (s⁻¹) | OC20 Experimental |
| `is_imputed` | bool | True if descriptor was imputed | Derived |
| `excluded_from_training` | bool | True if entry was excluded (e.g., <5 neighbors) | Derived |

### ModelMetrics
Stores performance statistics for trained models.

| Attribute | Type | Description |
|-----------|------|-------------|
| `model_type` | str | "XGBoost", "Volcano", or "Reduced" |
| `r_squared` | float | R² score on test set |
| `mean_absolute_error` | float | MAE on test set |
| `pearson_r` | float | Pearson correlation coefficient |
| `t_test_p_value` | float | p-value from statistical test (if applicable) |
| `test_size` | int | Number of samples in test set |

### FeatureImportance
Represents descriptor impact from SHAP analysis.

| Attribute | Type | Description |
|-----------|------|-------------|
| `descriptor_name` | str | Name of the descriptor |
| `mean_absolute_shap_value` | float | Mean absolute SHAP value |
| `rank` | int | Rank (1 = most important) |
| `physical_mechanism` | str | Known physical mechanism (if any) |

### ReducedModelMetrics
Stores metrics for the top-5 reduced model (SC-003).

| Attribute | Type | Description |
|-----------|------|-------------|
| `r_squared_full` | float | R² of the full XGBoost model |
| `r_squared_reduced` | float | R² of the top-5 reduced model |
| `ratio` | float | `r_squared_reduced / r_squared_full` |
| `passes_sc003` | bool | True if ratio ≥ 0.50 |

## Data Flow Diagram

```mermaid
graph TD
    A[OC20 Raw] --> B[Download & Stream]
    C[MP API] --> D[Fetch Descriptors]
    B --> E[Descriptor Extraction]
    D --> E
    E --> F{Alignment}
    F -->|Matched| G[Unified Dataset]
    F -->|Unmatched| H[Excluded Log]
    G --> I{Imputation k=5 (Geo-aware)}
    I -->|Success| J[Imputed Dataset]
    I -->|<5 Neighbors| K[Excluded Log]
    J --> L[Scaling]
    L --> M[Aligned Dataset CSV]
    M --> N[XGBoost Training]
    M --> O[Volcano Baseline]
    N --> P[SHAP Analysis]
    O --> P
    P --> Q[Feature Importance Report]
    N --> R[Reduced Model Training (Top-5)]
    R --> S[Reduced Model Metrics]
    N --> T[Model Metrics]
    O --> T
    Q --> U[Final Report]
    S --> U
    T --> U
```

## Data Quality Rules

1. **No NaN in Target**: `experimental_tof` must have no missing values after imputation (entries with missing TOF are excluded).
2. **Unique Alignment**: `synthesis_condition` must be uniquely mappable (fuzzy match) per catalyst; ambiguous entries excluded.
3. **Imputation Flag**: All imputed values are flagged (`is_imputed=True`).
4. **Exclusion Log**: All excluded entries (unmatched, <5 neighbors) are logged with reasons.
5. **Checksum**: All raw and processed files are checksummed (SHA-256).

## Storage Layout

```text
data/raw/
├── oc20_sample.parquet          # Streamed sample from OC20
├── mp_cache.json                # Cached MP descriptors

data/processed/
└── aligned_dataset.csv          # Final aligned, imputed, scaled dataset

outputs/
├── alignment_log.json           # Unmatched entries
├── imputation_log.json          # Entries excluded due to <5 neighbors
├── feature_importance.png       # Top 5 SHAP bar plot
├── reduced_model_metrics.json   # SC-003 metrics
└── final_report.md              # Complete results report
```

