# Data Model: Predicting the Impact of Composition on the Density of Metallic Glasses

## Entities

### MetallicGlassRecord
Represents a single alloy entry.
- `id`: string (unique identifier)
- `composition`: map<string, float> (Element symbol -> mass fraction)
- `bulk_density`: float (g/cm³)
- `derived_features`: map<string, float> (Computed descriptors)
- `dominant_element`: string (Element with highest mass fraction)
- `baseline_density`: float (g/cm³) (Calculated via Linear Mixing Rule)
- `residual_density`: float (g/cm³) (Actual - Baseline)

### PredictionModel
Represents the trained regressor.
- `algorithm`: string (e.g., "LightGBM")
- `hyperparameters`: map<string, any>
- `feature_importance_map`: map<string, float>
- `model_artifact_path`: string (relative path to `.pkl` file)
- `target_type`: string ("residual_density")

### AnalysisReport
Represents the final output.
- `metrics`: map<string, float> (MAE, R², RMSE)
- `visualizations`: list<string> (Paths to plot files)
- `interpretability_data`: map<string, any> (SHAP values, PDP data)
- `hypothesis_test`: map<string, any> (Results of radius mismatch/packing efficiency analysis, including F-test p-value)

## Data Flow

1. **Ingestion**: `raw_data.csv` (Source) or `mg_lit_curated.csv` (Fallback) -> `data/raw/` (Checksummed)
2. **Cleaning**: `raw_data.csv` -> `clean_data.csv` (Filtered/Imputed)
3. **Baseline Calculation**: `clean_data.csv` -> `baseline_density` added
4. **Residual Calculation**: `clean_data.csv` -> `residual_density` added
5. **Engineering**: `clean_data.csv` -> `processed_data.csv` (Features added, clr transform applied, VIF checked)
6. **Training**: `processed_data.csv` -> `model.pkl` + `metrics.json` (Predicting `residual_density`)
7. **Reporting**: `model.pkl` + `processed_data.csv` -> `report.html`

## Transformations

- **Normalization**: All elemental symbols converted to IUPAC standard.
- **Imputation**: Rows with missing density are dropped (or imputed if <5% missing, documented).
- **Feature Calculation**: Mass fractions converted to atomic fractions for radius mismatch calculation.
- **clr Transform**: Compositional features (mass fractions) transformed using Centered Log-Ratio to mitigate collinearity.
- **Baseline Subtraction**: `residual_density` = `bulk_density` - `baseline_density` (where `baseline_density` = $\sum w_i \rho_i$).

## Storage Strategy
- **Raw Data**: Immutable, stored in `data/raw/` with checksum.
- **Literature Curated**: Static, version-controlled file in `data/literature_curated/`.
- **Processed Data**: Stored in `data/processed/` with derivation log.
- **Models**: Serialized with `joblib` in `code/models/`.
