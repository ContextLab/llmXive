# Data Model: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

## Entity Definitions

### 1. HEA Composition (Raw)
Represents the raw input record from the source dataset.
* `elemental_fractions`: Dict or JSON string mapping element symbols (e.g., "Fe", "Cr") to atomic fractions (float).
* `phase_structure`: String (e.g., "FCC", "BCC", "Single-phase", "Multi-phase").
* `testing_temperature`: Float (°C).
* `yield_strength`: Float (Original unit, e.g., MPa or GPa).
* `source_id`: String (Unique identifier from the source dataset).

### 2. HEA Composition (Processed)
The cleaned and enriched record ready for modeling.
* `id`: String (Unique project ID).
* `elements`: Dict (Element -> Fraction).
* `phase`: String (Filtered to "Single-phase").
* `temperature`: Float (Filtered to 20-25°C).
* `yield_strength_mpa`: Float (Normalized to MPa).
* `descriptor_delta`: Float (Atomic size mismatch).
* `descriptor_delta_chi`: Float (Electronegativity variance).
* `descriptor_vec`: Float (Valence electron concentration).
* `descriptor_entropy`: Float (Mixing entropy).
* `descriptor_delta_tm`: Float (Melting temperature variance).
* `vif_scores`: Dict (Descriptor name -> VIF value).
* `is_collinear`: Boolean (True if any VIF > 10).

### 3. Model Metrics
The output of the evaluation phase.
* `model_type`: String ("RandomForest", "GradientBoosting", "OLS").
* `metric_name`: String ("R2", "MAE", "RMSE").
* `value`: Float.
* `split`: String ("train_cv", "test_holdout").
* `seed`: Integer (42).

### 4. Statistical Validation Results
* `descriptor`: String.
* `permutation_p_value`: Float.
* `corrected_p_value`: Float (Bonferroni applied to k=5).
* `is_significant_alpha_05`: Boolean.
* `bootstrap_ci_lower`: Float (95% CI lower bound).
* `bootstrap_ci_upper`: Float (95% CI upper bound).

## Data Flow

1. **Ingestion**: Raw data downloaded to `data/raw/`.
2. **Cleaning**:
 * Filter: `phase == "Single-phase"` AND `20 <= temperature <= 25`.
 * Unit Conversion: `yield_strength` -> `MPa`.
 * Exclusion: Rows with missing elemental properties.
3. **Descriptor Calculation**:
 * Load elemental properties from Zenodo ().
 * Compute δ, Δχ, VEC, Entropy, ΔTm.
 * Store in `data/processed/processed_hea.csv`.
4. **Modeling**:
 * Split: [deferred] Train, [deferred] Test (stratified by quartile of yield strength).
 * Train: RF, GBM, OLS.
 * Evaluate: Generate `output/metrics.json`.
5. **Validation**:
 * Permutation, Bootstrap, VIF (on all 5 descriptors).
 * Generate `output/stability.json` and `output/report.md`.

## Constraints & Assumptions
* **Missing Data**: If an element in the composition is not found in the Zenodo elemental properties, the row is excluded.
* **Collinearity**: If VIF > 10, the descriptor is kept for prediction but flagged as collinear in the report.
* **Sample Size**: If N < 500, the pipeline proceeds but flags the limitation.
