# Data Model: Predicting the Effect of Alloying on the Elastic Modulus of High‑Entropy Alloys

## Entity Definitions

### HEA Sample
Represents a single alloy instance.
- **Attributes**:
  - `sample_id`: Unique identifier (string).
  - `composition`: Dictionary of element → atomic_fraction (float, sums to 1.0).
  - `elastic_constants`: Dictionary containing `bulk_modulus` (GPa), `shear_modulus` (GPa).
  - `crystal_structure`: String (e.g., "BCC", "FCC").
  - `source`: String ("OQMD", "Materials Project").
  - `miedema_baseline`: Float (Predicted Bulk Modulus via Miedema’s model, GPa).
  - `residual_bulk_modulus`: Float (Observed − Miedema, GPa). **This is the modeling target.**
  - `ilr_features`: List[float] (ILR‑transformed composition coordinates).
  - `mixing_enthalpy`: Float (kJ/mol) **used only for the baseline subtraction**.
  - `atomic_radius_variance`: Float (dimensionless).
  - `entropy_mixing`: Float (J/mol·K).
  - `vec`: Float (Valence Electron Concentration).
  - `electronegativity_variance`: Float.
  - `metadata`:
      - `api_version`: String.
      - `query_params`: String (JSON‑encoded).
      - `checksum`: String (SHA‑256 of raw source).

### Compositional Descriptor
Derived features for modeling (excluding mixing enthalpy as a predictor).
- **Attributes**:
  - `sample_id`: Foreign key to HEA Sample.
  - `atomic_radius_variance`, `entropy_mix`, `vec`, `electronegativity_variance`: Numeric.
  - `ilr_components`: Array[float] (ILR‑transformed composition vector).

### Model Performance Record
Evaluation output for a specific model run.
- **Attributes**:
  - `model_name`: String ("RF", "GB", "EN").
  - `r2_score`, `rmse`, `mae`: Float.
  - `r2_ci_lower`, `r2_ci_upper`: Float (95 % CI from grouped bootstrap; omitted if LOSO fallback used).
  **Additional fields**:
  - `p_value_null`: Float (t‑test against null hypothesis R² = 0).
  - `fdr_corrected`: Boolean.
  - `sensitivity_analysis`:
      - `thresholds_tested`: Array[float] (e.g., [0.25, 0.30, 0.35]).
      - `fpr_variance`: Float (variance of false‑positive rates across thresholds).

## Data Flow

1. **Ingestion** → `data/raw/` (raw API dumps).
2. **Cleaning** → `data/processed/cleaned.csv` (normalized compositions).
3. **Feature Engineering** → `data/processed/features.csv` (descriptors, ILR, residual target).
4. **Modeling** → `results/models/` (trained sklearn objects).
5. **Evaluation** → `results/metrics.yaml`, `results/sensitivity.json`.  

## Constraints & Rules

- **Normalization**: Composition must sum to 1.0; if not, normalize and log the adjustment before feature engineering.
- **Thresholds**:  
  - Minimum samples: A sufficient number to ensure statistical power (hard halt if not met, with deficit log).  
  - Minimum unique alloy groups: sufficient (if fewer, LOSO fallback applied; CI omitted or widened).
- **Data Integrity**: No in‑place modification of `data/raw/`. All derived files receive new filenames and checksums recorded in `state/...yaml`.  
- **Descriptor‑Baseline Separation**: `mixing_enthalpy` is stored for reference but **never used as a predictor** in model training.
