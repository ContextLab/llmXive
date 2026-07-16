# Data Model: Quantifying the Influence of Topological Defects on 2D Material Properties

## Entity Definitions

### DefectEntry
A single record representing a specific defect configuration in a 2D material.
*   **Defect Type**: Categorical (e.g., "dislocation", "grain_boundary", "vacancy", "substitution").
*   **Defect Density**: Float, fraction of atoms affected ($0 \le \rho \le 0.1$).
*   **Geometric Descriptors**: Floats (e.g., tilt angle, grain boundary width).
*   **Material**: Categorical ("graphene", "MoS2").
*   **Synthesis Method**: Categorical (optional, for stratification).
*   **Data Source**: Categorical ("real", "synthetic"). **MUST be set to 'synthetic' for all generated data.**

### MaterialProperty
Computed physical properties for a given structure.
*   **Electronic Conductivity**: Float (or derived from band gap via BoltzTraP).
*   **Elastic Tensor**: Float array (components).
*   **Fracture Energy**: Float.
*   **Reference Values**: $\sigma_0, E_0, \sigma_{f0}$ (pristine values for normalization).

### RegressionModel
A trained model instance.
*   **Target Property**: The specific property being predicted.
*   **Hyperparameters**: `n_estimators`, `max_depth`, `random_state`.
*   **Performance Metrics**: $R^2$, MAPE, CV standard deviation.
*   **Feature Importance**: Permutation-based scores and p-values.

## Data Flow

1.  **Raw Data**:
    *   `pristine_structures.csv`: Downloaded from Materials Project API.
    *   `defect_dataset_2022.csv`: Attempted download (may be empty).
    *   `synthetic_train.csv`: Generated if real data missing (**data_source='synthetic'**).
    *   `synthetic_holdout.csv`: Generated for independent test (**data_source='synthetic'**).
    *   `surrogate_noise_params.json`: Parameters for noise calibration from DFT.
2.  **Processed Data**:
    *   `features.csv`: Normalized, encoded feature matrix.
    *   `targets.csv`: Normalized target vectors.
    *   `feature_selection_log.json`: Collinearity exclusion log.
3.  **Model Outputs**:
    *   `model_outputs.json`: Performance metrics and predictions.
    *   `Validation_Report.json`: External validation status.

## Schema Constraints

*   **Defect Density**: Must be $> 0$ and $\le 0.1$. Entries with $\le 0$ or NaN are filtered.
*   **Missing Values**: If a required variable is missing, the entry is flagged `[MISSING: requires mock DFTB+ fallback]`. If fallback fails, the entry is excluded.
*   **Normalization**: Targets must be normalized by pristine references. If references are missing, the entry is excluded and logged.
*   **Data Source Flag**: **MUST be set to 'synthetic' for all generated data** (T012, T013, T014). This is a critical requirement for the `defect_entry.schema.yaml`.

## Versioning & Hygiene

*   **Checksums**: All files in `data/` are checksummed (SHA-256) and recorded in `state/...yaml`.
*   **Immutability**: Raw data is never modified. Derivations are written to new files.
*   **Traceability**: Every figure/statistic traces back to a specific row in `data/processed/features.csv` and a specific block in `code/`.