# Data Model: Predicting the Impact of Composition on the Shear Modulus of Bulk Metallic Glasses

## Entity Definitions

### BMGEntry
Represents a single bulk metallic glass sample.
*   **id**: `str` (UUID or source-specific ID)
*   **composition**: `dict` (Element: Atomic Percent, e.g., `{"Zr": 50, "Cu": 30, ...}`)
*   **shear_modulus**: `float` (GPa)
*   **alloy_family**: `str` (e.g., "Zr-based", "Pd-based", "Mg-based")
*   **source**: `str` ("materials_project", "inoue_compilation", or "synthetic_generator")
*   **raw_data_ref**: `str` (Checksum or URL of the raw row)

### CompositionalDescriptor
Derived features calculated from `BMGEntry`.
*   **atomic_size_mismatch** (`delta`): `float` (dimensionless, often expressed as %)
*   **mixing_enthalpy** (`delta_h_mix`): `float` (kJ/mol)
*   **valence_electron_concentration** (`vec`): `float` (e-/atom)
*   **electronegativity_diff** (`delta_chi`): `float` (Pauling scale)
*   **vif_score**: `float` (Variance Inflation Factor, calculated pre-training)

### ModelPerformance
Evaluation results.
*   **model_type**: `str` ("Linear", "RandomForest", "GradientBoosting", "Ridge")
*   **r2_test**: `float`
*   **mae_test**: `float`
*   **rmse_test**: `float`
*   **cv_scores**: `list[float]` (5-fold CV scores or GroupKFold scores)
*   **best_params**: `dict`
*   **significance_p_value**: `float` (from Wilcoxon Signed-Rank Test vs baseline)
*   **bayes_factor**: `float` (optional, evidence ratio)

## Data Flow

1.  **Ingest**: Raw JSON/CSV $\rightarrow$ `data/raw/bmg_raw.json` + **Checksum recorded in `state/...yaml`**
2.  **Clean**: Filter non-BMG, standardize units $\rightarrow$ `data/processed/bmg_clean.csv`
3.  **Feature**: Add descriptors + **Calculate VIF** $\rightarrow$ `data/processed/bmg_features.csv`
4.  **Prune**: **Remove features with VIF > 5** $\rightarrow$ `data/processed/bmg_pruned.csv`
5.  **Split**: Train/Test/LOFO/GroupKFold $\rightarrow$ `data/processed/train_split.pkl`, `data/processed/test_split.pkl`
6.  **Train**: Model Pickles $\rightarrow$ `data/artifacts/models/`
7.  **Evaluate**: JSON Report $\rightarrow$ `data/artifacts/metrics.json`

## Constraints & Assumptions

* **Composition Format**: All compositions must be normalized to sum to 1.0.
*   **Missing Data**: Entries with missing shear modulus are dropped (FR-002).
*   **Elemental Data**: All elements in the composition must exist in the `mendeleev` database. If not, the row is flagged and dropped.
*   **Collinearity**: Features with VIF > 5 are removed or combined before training.
*   **Validation**: LOFO only for families with N >= 10; otherwise use GroupKFold.
