# Data Model: Predicting the Impact of Surface Roughness on Tribological Properties

## Core Entity – `Experiment`
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `experiment_id` | string (UUID) | Unique identifier for each tribological test. | ✅ |
| `material_pair_id` | string | Identifier linking the two contacting materials. | ✅ |
| `material_1_id` | string | Materials Project or NIST identifier for material 1. | ✅ |
| `material_2_id` | string | Identifier for material 2. | ✅ |
| `Sa` | number | Arithmetic mean surface height (µm). | ✅ |
| `Sq` | number | Root‑mean‑square height (µm). | ✅ |
| `Ssk` | number | Skewness of the surface height distribution. | ✅ |
| `Sku` | number | Kurtosis of the surface height distribution. | ✅ |
| `Sp` | number | Maximum peak height (µm). | ✅ |
| `Sv` | number | Maximum valley depth (µm). | ✅ |
| `elastic_modulus_1` | number | Elastic modulus of material 1 (GPa). | ✅ |
| `elastic_modulus_2` | number | Elastic modulus of material 2 (GPa). | ✅ |
| `hardness_1` | number | Hardness of material 1 (HV). | ✅ |
| `hardness_2` | number | Hardness of material 2 (HV). | ✅ |
| `hardness_modulus_ratio_1` | number | Hardness divided by elastic modulus for material 1. | ✅ |
| `hardness_modulus_ratio_2` | number | Hardness divided by elastic modulus for material 2. | ✅ |
| `coeff_friction` | number | Measured coefficient of friction (dimensionless). | ✅ |
| `wear_rate` | number | Wear rate (mm³ N⁻¹ m⁻¹). | ✅ |

### Derived Fields (computed during preprocessing, **not used as predictors**)
| Field | Type | Description |
|-------|------|-------------|
| `avg_hardness` | number | Mean of the two hardness values. |
| `avg_modulus` | number | Mean of the two elastic modulus values. |
| `hardness_modulus_ratio_avg` | number | Mean of the two hardness‑to‑modulus ratios. |

## Schema Validation
The processed dataset must validate against `contracts/tribology-dataset.schema.yaml` (JSON‑Schema). Validation occurs after Phase 3 (preprocessing) and before modeling.

## Storage Layout
```
data/
├── raw/
│   └── openml_2352/                 # streamed raw files (read‑only)
├── intermediate/
│   └── material_properties.json      # fetched from Materials Project / NIST
├── processed/
│   └── tribology_dataset.parquet     # conforms to schema
```

