# Data Model: Assessing Uncertainty Quantification Techniques

## Entity Overview

| Entity | Description |
|--------|-------------|
| **MaterialsDataset** | Represents a specific property dataset (Band Gap, Thermal Conductivity, Formation Energy). |
| **UQMethod** | Encapsulates a UQ technique and its configuration. |
| **EvaluationMetric** | Stores a scalar metric (Calibration Error, Sharpness, Coverage Error) for a method‑dataset pair. |
| **StatisticalTestResult** | Holds the outcome of a paired Wilcoxon test between two methods on a given dataset. |

### MaterialsDataset

| Field | Type | Notes |
|-------|------|-------|
| dataset_id | string | e.g., `band_gap`, `thermal_conductivity`, `formation_energy`. |
| source_url | string (URI) | Verified URL from `research.md`. |
| property_name | string | Human‑readable target name. |
| n_samples | integer ≥ 1 | Total rows after loading. |
| n_train | integer ≥ 1 | Training rows. |
| n_val | integer ≥ 0 | Validation rows. |
| n_test | integer ≥ 1 | Test rows (≥ 200 per SC‑001 and power‑analysis strategy). |
| features | array[string] | Feature column names after featurization. |
| target | string | Target column name. |
| checksum | string | SHA‑256 of the processed CSV. |

### UQMethod

| Field | Type |
|-------|------|
| method_id | enum: `gpr`, `mc_dropout`, `deep_ensemble`, `conformal` |
| baseline_model | string (e.g., `xgboost`, `mlp`, `gpr_standalone`) |
| hyperparams | object (JSON‑serialisable) |
| n_iterations | integer (MC passes or ensemble size) |
| status | enum: `success`, `failed`, `skipped` |
| error_msg | string (optional) |

### EvaluationMetric

| Field | Type |
|-------|------|
| dataset_id | string |
| method_id | string |
| metric_type | enum: `calibration_error`, `sharpness`, `coverage_error` |
| value | number |
| nominal_coverage | number ∈ [0,1] (only for interval metrics) |
| timestamp | string (ISO‑8601) |

### StatisticalTestResult

| Field | Type |
|-------|------|
| dataset_id | string |
| method_a | string |
| method_b | string |
| metric_type | enum: `calibration_error`, `sharpness` |
| p_value | number ∈ [0,1] |
| test_type | enum: `wilcoxon_signed_rank` |
| significant | boolean |
| alpha | number |
| correction | enum: `bonferroni`, `none` |

## Data Flow

1. **download.py** → raw CSVs in `data/raw/`.  
2. **featurize.py** → `data/processed/<dataset_id>.csv`.  
3. **models/** → trained artefacts saved under `results/models/`.  
4. **metrics/evaluation.py** → `results/metrics_<dataset_id>.csv`.  
5. **stats/significance.py** → `results/statistical_report.csv`.  
6. **pipeline.py** aggregates all CSVs into `results/summary.csv` **and** writes:
   - `results/uq_methods.csv` (UQMethod registry, matching this entity definition)
   - `results/pipeline_log.csv` (pipeline execution log conforming to `contracts/pipeline.schema.yaml`).  
7. **results/** contain the final deliverables for downstream analysis and paper generation.

---

