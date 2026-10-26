# Data Model: Predicting the Impact of Surface Roughness on Tribological Properties

## Core Entity – `Experiment`
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `experiment_id` | string (UUID) | Unique identifier for each tribological test. | ✅ |
| `material_pair_id` | string | Identifier linking the two contacting materials. | ✅ |
| `material_1_id` | string | Materials Project or NIST identifier for material 1. | ✅ |
| `material_2_id` | string | Identifier for material 2. | ✅ |
| `Sa` | float | Arithmetic mean surface height (µm). | ✅ |
| `Sq` | float | Root‑mean‑square height (µm). | ✅ |
| `Ssk` | float | Skewness of the surface height distribution. | ✅ |
| `Sku` | float | Kurtosis of the surface height distribution. | ✅ |
| `Sp` | float | Maximum peak height (µm). | ✅ |
| `Sv` | float | Maximum valley depth (µm). | ✅ |
| `elastic_modulus_1` | float | Elastic modulus of material 1 (GPa). | ✅ |
| `elastic_modulus_2` | float | Elastic modulus of material 2 (GPa). | ✅ |
| `hardness_1` | float | Hardness of material 1 (HV). | ✅ |
| `hardness_2` | float | Hardness of material 2 (HV). | ✅ |
| `hardness_modulus_ratio_1` | float | Hardness divided by elastic modulus for material 1. | ✅ |
| `hardness_modulus_ratio_2` | float | Hardness divided by elastic modulus for material 2. | ✅ |
| `coeff_friction` | float | Measured coefficient of friction (dimensionless). | ✅ |
| `wear_rate` | float | Wear rate (mm³ N⁻¹ m⁻¹). | ✅ |

### Derived Fields (computed during preprocessing, **not used as predictors**)
| Field | Type | Description |
|-------|------|-------------|
| `avg_hardness` | float | Mean of `hardness_1` and `hardness_2`. |
| `avg_modulus` | float | Mean of `elastic_modulus_1` and `elastic_modulus_2`. |
| `hardness_modulus_ratio_avg` | float | Mean of the two hardness‑to‑modulus ratios. |

## Schema Validation
The processed dataset must validate against `contracts/tribology-dataset.schema.yaml` (JSON‑Schema). Validation occurs after Phase 3 (preprocessing) and before modeling.

## Storage Layout
```
data/
├── raw/
│   └── openml_42123/                 # streamed raw files (read‑only)
├── intermediate/
│   └── material_properties.json      # fetched from Materials Project / NIST
├── processed/
│   └── tribology_dataset.parquet     # conforms to schema
```

---

