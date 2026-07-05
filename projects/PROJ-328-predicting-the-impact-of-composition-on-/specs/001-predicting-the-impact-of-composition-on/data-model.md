# Data Model: Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys

## Entity Definitions

### SolderComposition (Raw)
Represents a single entry from a literature source or database.
*   `id`: Unique string identifier (e.g., "lit_001").
*   `source_citation`: String (Author, Year, Title).
*   `source_url`: String (if available, else "Manual Entry").
*   `alloy_family`: String (e.g., "Sn-Ag-Cu", "Sn-Pb", "Sn-Zn").
*   `elements`: Dict<string, float> (e.g., `{"Sn": 96.5, "Ag": 3.0, "Cu": 0.5}`).
*   `hardness_hv`: float (Vickers Hardness).
*   `hardness_unit`: String (e.g., "HV", "GPa").
*   `temperature_c`: float (Must be ~25 for room temp).
*   `notes`: String (Any anomalies, e.g., "Different load force").

### CompositionalDescriptor (Derived)
Engineered features derived from `SolderComposition` via CLR transform and property lookup.
*   `composition_id`: FK to `SolderComposition.id`.
*   `clr_transformed`: Dict<string, float> (Log-ratio transformed composition).
*   `weighted_mean_atomic_mass`: float.
*   `electronegativity_variance`: float.
*   `atomic_radius_variance`: float.
*   `weighted_avg_melting_point`: float.
*   `valence_electron_concentration`: float.
*   `element_count`: int (Must be ≤ 5).
*   `transformation_hash`: String (SHA256 of the CLR/Descriptor script parameters).

### ModelPerformance (Output)
Metrics from the evaluation pipeline.
*   `model_type`: String ("XGBoost" or "Linear").
*   `cv_fold`: int (1-5).
*   `r2_score`: float.
*   `rmse_score`: float.
*   `bootstrap_ci_lower`: float (95% lower bound).
*   `bootstrap_ci_upper`: float (95% upper bound).
*   `shap_importance`: Dict<string, float> (Top 3 features).
*   `vif_scores`: Dict<string, float>.

## CLR Transform Interface

The `compositional` library is used to apply the Centered Log-Ratio (CLR) transform.
*   **Input**: A vector of positive composition percentages (e.g., `[96.5, 3.0, 0.5]`).
*   **Output**: A vector of log-ratio transformed values (e.g., `[-0.12, 0.05, -0.03]`).
*   **Mapping**: The output vector is stored in `clr_transformed` in the `CompositionalDescriptor` entity.
*   **Usage**: The model uses the `clr_transformed` vector and the derived descriptors (mass, radius, etc.) as a *single* feature vector. Raw composition percentages are **excluded**.

## Data Flow

1.  **Ingestion**: `data/raw/*.csv` -> `SolderComposition` (validated for N, sum=100%).
2.  **Cleaning**: Filter for `element_count ≤ 5`, `temperature_c ≈ 25`, `hardness_hv` non-null.
3.  **Transformation**: `SolderComposition` -> `CompositionalDescriptor` (Apply CLR, lookup periodic properties).
4.  **Modeling**: `CompositionalDescriptor` (X) + `hardness_hv` (y) -> `ModelPerformance`.
5.  **Output**: `data/processed/metrics.yaml`, `data/processed/plots/*.png`.

## Constraints & Rules

*   **Composition Sum**: `sum(elements)` must be ≥ 95% and ≤ 105% (tolerance for rounding). Records outside this are dropped.
*   **Element Limit**: Alloys with > 5 elements are excluded (FR-002).
*   **Unit Standardization**: All hardness converted to HV. If source is GPa, `HV = GPa * 100` (approx) or exact conversion if formula provided.
*   **Missing Data**: If any element percentage is missing, the record is dropped (FR-002).
*   **Provenance**: Every `CompositionalDescriptor` record must include `source_citation` and `transformation_hash`.
