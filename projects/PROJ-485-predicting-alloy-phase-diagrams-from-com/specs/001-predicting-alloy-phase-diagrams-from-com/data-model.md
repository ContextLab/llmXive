# Data Model: Predicting Alloy Phase Diagrams

## 1. Key Entities

### AlloyComposition
Represents a specific mixture of elements.
- **Attributes**:
  - `system_id`: Unique identifier for the binary system (e.g., "Cu-Zn").
  - `element_a`: Symbol of the first element.
  - `element_b`: Symbol of the second element.
  - `composition_a`: Mole fraction of element A (0.0 to 1.0).
  - `composition_b`: Mole fraction of element B (1.0 - `composition_a`).
- **Derived Descriptors**:
  - `mean_atomic_radius`: Weighted average of atomic radii.
  - `electronegativity_variance`: Variance of electronegativity values.
  - `valence_electron_count`: Weighted average of valence electrons.
  - `hume_rothery_concentration`: Derived Hume-Rothery metric.

### PhaseBoundary
Represents a point on the phase diagram.
- **Attributes**:
  - `alloy_id`: Foreign key to `AlloyComposition`.
  - `temperature`: Experimental phase boundary temperature (Kelvin).
  - `phase_type`: Label (e.g., "liquidus", "solidus").
  - `source`: Origin of the data point (e.g., "SGTE", "NIST-JANAF").

### ModelMetrics
Stores performance results.
- **Attributes**:
  - `fold_id`: Identifier for the LOSO fold.
  - `test_system`: The system held out for this fold.
  - `mae`: Mean Absolute Error for this fold.
  - `r2`: R² Score for this fold.
  - `n_samples`: Number of test samples.

### PowerAnalysisResult
Stores statistical power justification.
- **Attributes**:
  - `effect_size`: Estimated effect size (Cohen's d).
  - `sample_size`: Total number of samples used.
  - `alpha`: Significance level (0.05).
  - `calculated_power`: Resulting statistical power.
  - `status`: "PASS" or "FAIL".

## 2. Data Flow

1.  **Raw Ingestion**: `data/raw/sgte_final.parquet` -> `data/processed/raw_cleaned.csv`
    - Filters: Valid temperature, binary systems only.
2.  **Feature Engineering**: `data/processed/raw_cleaned.csv` -> `data/processed/features_enriched.csv`
    - Joins with `data/raw/elemental_properties.csv`.
    - Calculates descriptors.
3.  **Model Training**: `data/processed/features_enriched.csv` -> `artifacts/model.pkl` + `artifacts/metrics.json`
    - LOSO Split.
    - Training & Evaluation.
4.  **Visualization**: `artifacts/predictions.csv` -> `artifacts/phase_diagram_CuZn.png`

## 3. Constraints & Validations

- **Temperature Range**: Must be > 0 K.
- **Composition**: Sum of fractions must be 1.0 (±0.01 tolerance).
- **Missing Data**: Rows with missing temperature are dropped (FR-001).
- **Elemental Consistency**: Test sets cannot introduce new elements (FR-010).
