# Data Model: The Use of Climate-Smart Agricultural Practices in Rural Areas to Improve Food Security and Livelihoods

## 1. Conceptual Entities

### Household Record
Represents a single survey unit from the LSMS dataset.
- **Attributes**:
  - `household_id`: Unique identifier (string).
  - `country_code`: ISO 3166-1 alpha-3 (string).
  - `survey_year`: Integer (2015-2023).
  - `latitude`: Float (degrees).
  - `longitude`: Float (degrees).
  - `hdds`: Household Dietary Diversity Score (int, 0-12).
  - `csa_index`: Normalized CSA adoption score (float, 0.0-1.0). **Derived ONLY from agronomic practices.**
  - `digital_access`: Binary/Ordinal (0-2). **Separate variable for moderation/mediation.**
  - `finance_access`: Binary/Ordinal (0-2). **Separate variable for moderation/mediation.**
  - `climate_temp_anomaly`: Float (degrees C deviation).
  - `climate_precip_anomaly`: Float (mm deviation).
  - `household_size`: Integer.
  - `head_education_years`: Integer.
  - `land_size_hectares`: Float.
  - `sampling_weight`: Float. **Inverse probability of selection weight.**
  - `provenance_ids`: List of strings (original survey response IDs).

### Climate Record
Represents environmental conditions matched to a household.
- **Attributes**:
  - `location_id`: String (linked to household).
  - `temp_mean_growing_season`: Float.
  - `precip_total_growing_season`: Float.
  - `data_source`: String ("NASA POWER").

### Model Output
Represents the results of the statistical analysis.
- **Attributes**:
  - `model_id`: String (UUID).
  - `coefficients`: Dict (variable -> estimate).
  - `std_errors`: Dict (variable -> SE).
  - `p_values`: Dict (variable -> p-value).
  - `vif_scores`: Dict (variable -> VIF).
  - `random_effects`: Dict (group -> variance).
  - `mediation_effects`: Dict (path -> estimate). **Indirect and direct effects.**
  - `robustness_metrics`: Dict (bootstrap_variance, leave_one_out_variance).

## 2. Data Flow

1.  **Ingestion**: Raw CSV/Parquet -> `data/raw/`.
2.  **Cleaning**: `download.py` + `clean.py` -> `data/processed/merged_clean.csv`.
3.  **Feature Engineering**: `features.py` -> `data/processed/features_final.csv`.
4.  **Modeling**: `model.py` -> `results/model_output.json`.
5.  **Visualization**: `viz/plots.py` -> `results/figures/*.png`.

## 3. Constraints & Validation Rules
- **CSA Index**: Must be in range [0.0, 1.0]. **Must NOT include digital/finance variables.**
- **HDDS**: Must be integer 0-12.
- **Coordinates**: Latitude [-90, 90], Longitude [-180, 180].
- **Missingness**: Key predictors (CSA, HDDS) must have <5% missing after imputation.
- **Collinearity**: VIF > 5.0 triggers a warning flag but does not halt execution (Constitution Principle VII).
- **Weights**: `sampling_weight` must be > 0 for all records used in modeling.