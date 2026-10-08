# Data Model: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Entity Definitions

### AlloyRecord
Represents a single aluminum alloy entry.
- **material_id**: `string` (Unique identifier from source)
- **formula**: `string` (Chemical formula, e.g., "Al0.95Cu0.05")
- **elemental_composition**: `object` (Map of element symbol to atomic fraction)
  - `Cu`: `float` (0.0 to 1.0)
  - `Mg`: `float` (0.0 to 1.0)
  - `Si`: `float` (0.0 to 1.0)
  - `Zn`: `float` (0.0 to 1.0)
  - `Mn`: `float` (0.0 to 1.0)
  - `Al`: `float` (Calculated balance: 1.0 - sum(other))
- **poissons_ratio**: `float` (Target variable, dimensionless)
- **youngs_modulus**: `float` (GPa)
- **measurement_method**: `string` (e.g., "Ultrasonic", "DFT")
- **source**: `string` ("Materials Project")
- **is_alloy**: `boolean` (True if composition is continuous, not fixed stoichiometry)

### ModelMetrics
Aggregated performance metrics.
- **cv_mae**: `float` (Mean Absolute Error from 5-fold CV or LOOCV)
- **test_mae**: `float` (Mean Absolute Error on held-out test set)
- **n_samples**: `integer` (Total samples used)
- **train_size**: `integer`
- **test_size**: `integer`
- **cv_method**: `string` ("5-fold" or "LOOCV")

### CollinearityDiagnostic
Variance Inflation Factor results for raw predictors.
- **Cu_vif**: `float`
- **Mg_vif**: `float`
- **Si_vif**: `float`
- **Zn_vif**: `float`
- **Mn_vif**: `float`
- **max_vif**: `float`
- **is_flagged**: `boolean` (True if max_vif > 5)
- **note**: `string` ("Computed on raw atomic fractions, not ILR features")

### FeatureImportance
Back-transformed importance scores.
- **Cu_importance**: `float`
- **Mg_importance**: `float`
- **Si_importance**: `float`
- **Zn_importance**: `float`
- **Mn_importance**: `float`
- **ranked_elements**: `array[string]` (Ordered list from highest to lowest importance)

## Data Flow

1.  **Raw**: `data/raw/mp_raw.json` (from `matminer`)
2.  **Clean**: `data/processed/alloys_clean.parquet` (Filtered, normalized, Al balance calculated, `is_alloy` verified)
3.  **Transformed**: `data/processed/alloys_ilr.parquet` (ILR features added)
4.  **Results**: `results/model_metrics.json`, `results/feature_importance.json`, `results/collinearity_diagnostic.json`

## Constraints & Validation Rules

- **Composition Sum**: Sum of Cu, Mg, Si, Zn, Mn, Al must be exactly 1.0 (within tolerance 1e-6).
- **Stoichiometry Conversion**: If the source provides stoichiometry (e.g., Al2Cu), it MUST be converted to atomic fractions by dividing the count of each element by the total count of all elements in the formula.
- **Missing Data**: If sum of major elements (Cu+Mg+Si+Zn+Mn) < 0.95, record is **excluded**.
- **Unit Consistency**: `youngs_modulus` must be in GPa. If MPa, convert (divide by 1000).
- **Independence**: If `measurement_method` is missing or indicates "Derived" from a lower-fidelity source, record is **excluded** or **flagged** (per FR-009 logic).
- **Non-Negative**: All atomic fractions and elastic constants must be non-negative.
- **VIF Target**: VIF MUST be computed on raw atomic fractions, not ILR features.
- **Data Hygiene**: All data files are checksummed using **SHA-256**. Checksums are stored in `data/checksums.json` (Format: JSON object with filename keys and SHA-256 values).

## Formula Parsing & Conversion

To handle arbitrary chemical formulas (e.g., "Al2CuFe"):
1.  **Parse**: Use `chemparse` or similar to extract element counts.
2.  **Normalize**: Calculate total count of all elements.
3.  **Fraction**: For each element, fraction = count / total.
4.  **Target Set**: For the 5 target elements (Cu, Mg, Si, Zn, Mn), use their calculated fractions.
5.  **Non-Target Elements**: If the formula contains elements outside the target set (e.g., Fe, Ti), include them in the total count for normalization but exclude them from the 5-element sum check.
6.  **Al Balance**: `Al = 1.0 - (Cu + Mg + Si + Zn + Mn)`. If `Al < 0`, the record is invalid.