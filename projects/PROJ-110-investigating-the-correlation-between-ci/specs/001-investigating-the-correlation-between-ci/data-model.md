# Data Model: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Core Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| **Donor** | Human subject identifier; includes phenotype variables required for MetS labeling and covariates. | `donor_id` (str), `age` (int), `sex` (enum: M/F), `tissue` (str), `PMI` (float, optional), `time_of_death` (float, optional), `BMI` (float), `fasting_glucose` (float), `systolic_bp` (float), `diastolic_bp` (float), `triglycerides` (float), `HDL` (float) |
| **GeneExpression** | TPM value for a single gene in a donor. | `donor_id` (str), `gene_symbol` (str), `tpm` (float) |
| **MetSClassification** | Binary MetS label derived from ATP‑III criteria. | `donor_id` (str), `label` (enum: MetS/Control), `criteria_met` (int 0‑5) |
| **CorrelationResult** | Mixed‑effects correlation outcome for a gene‑trait pair. | `gene_symbol`, `trait`, `rho`, `p_raw`, `p_adj`, `model_type` |
| **DEResult** | ANCOVA differential expression outcome per gene‑tissue. | `gene_symbol`, `tissue`, `beta`, `ci_lower`, `ci_upper`, `p_raw`, `p_adj` |
| **LogisticModel** | Multivariate logistic regression fitted on METSIM data. | `model_id` (UUID), `predictors` (list of strings), `coefficients` (list of floats), `odds_ratios` (list of floats), `auc_mean`, `auc_std`, `cv_folds` |
| **ValidationResult** | External validation metrics comparing METSIM and GTEx pipelines. | `metric` (e.g., gene_overlap, auc_delta), `value` (float), `p_value` (float), `pass` (bool) |

## File Layout (under `data/processed/`)

| File | Entity | Format | Schema |
|------|--------|--------|--------|
| `donors.parquet` | Donor | Parquet | `dataset.schema.yaml` |
| `expression.parquet` | GeneExpression | Parquet | `dataset.schema.yaml` |
| `metS_classification.csv` | MetSClassification | CSV | `classification.schema.yaml` |
| `de_results.csv` | DEResult | CSV | `de_results.schema.yaml` |
| `correlation_results.csv` | CorrelationResult | CSV | `correlation_results.schema.yaml` |
| `logistic_model.json` | LogisticModel | JSON | `logistic_regression.schema.yaml` (coefficients) + `output.schema.yaml` (model_metrics) |
| `validation_results.csv` | ValidationResult | CSV | `validation_results.schema.yaml` |

All files include a `generated_at` timestamp and a SHA‑256 checksum recorded in `state/projects/PROJ-110-investigating-the-correlation-between-ci.yaml`.

## Relationships

- **One‑to‑many**: One `Donor` → many `GeneExpression` rows (one per core circadian gene).  
- **One‑to‑one**: One `Donor` → one `MetSClassification`.  
- **Many‑to‑many**: `LogisticModel` predictors reference `GeneExpression` and covariate fields.  

Foreign‑key‑like integrity checks are performed during validation (e.g., every `donor_id` in `expression.parquet` must exist in `donors.parquet`).

---


