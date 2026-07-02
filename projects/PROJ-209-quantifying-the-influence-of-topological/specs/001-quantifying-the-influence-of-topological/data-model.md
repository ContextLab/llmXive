# Data Model: Quantifying the Influence of Topological Defects on 2D Material Properties

## Entity Definitions

### 1. DefectEntry
Represents a single record of a material structure with a topological defect.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique identifier | UUID |
| `material` | string | Material type | Enum: ["graphene", "MoS2"] |
| `defect_type` | string | Type of defect | Enum: ["dislocation", "grain_boundary", "vacancy", "substitution"] |
| `defect_density` | float | Fraction of atoms affected | Range: [0.001, 0.1] |
| `tilt_angle` | float | Grain boundary tilt angle (degrees) | Range: [0, 360] |
| `synthesis_method` | string | Method of creation (optional) | String |
| `grain_size` | float | Average grain size (optional) | > 0 |
| `conductivity_raw` | float | Electronic conductivity (S/m) | > 0 |
| `youngs_modulus_raw` | float | Young's modulus (GPa) | > 0 |
| `fracture_energy_raw` | float | Fracture energy (J/m²) | > 0 |
| `status` | string | Data quality flag | Enum: ["valid", "missing_fracture", "timeout"] |

### 2. MaterialProperty
Derived properties normalized by **material‑level** pristine reference values (not per‑entry). Pristine references are fetched once per material from the Materials Project API and stored in `data/processed/pristine_refs.json`.

| Field | Type | Description | Formula |
| :--- | :--- | :--- | :--- |
| `entry_id` | string | Foreign key to DefectEntry | - |
| `delta_conductivity` | float | Relative change in conductivity | $(\sigma - \sigma_0) / \sigma_0$ |
| `delta_youngs` | float | Relative change in Young's modulus | $(E - E_0) / E_0$ |
| `delta_fracture` | float | Relative change in fracture strength | $(\sigma_f - \sigma_{f0}) / \sigma_{f0}$ |

### 3. RegressionModel
Configuration and metrics for trained models.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_id` | string | Unique identifier |
| `target_property` | string | Which property is modeled |
| `r2_score` | float | Coefficient of determination |
| `mape` | float | Mean Absolute Percentage Error |
| `cv_std` | float | Standard deviation of R² across 5 folds |
| `fdr_adjusted_p` | float | P‑value after Benjamini-Hochberg correction |
| `collinearity_method` | string | Method used for collinearity (e.g., "Ridge", "Exclusion") |

## Data Flow

1. **Ingest**: `01_data_acquisition.py` fetches pristine structures (API) and defect data (real CSV/JSON or synthetic).
2. **Clean**: `02_data_processing.py` filters invalid entries, computes normalization using material‑level pristine references, and writes `features.csv` and `targets.csv`.
3. **Model**: `03_modeling.py` trains RF models, performs CV, and saves `model_config.yaml`.
4. **Infer**: `04_inference.py` runs permutation tests, applies FDR, conducts sensitivity analysis, and generates `Validation_Report.json` when needed.