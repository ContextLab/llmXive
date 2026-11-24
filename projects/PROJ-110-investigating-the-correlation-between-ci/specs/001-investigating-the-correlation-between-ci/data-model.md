# Data Model: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Core Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| **Donor** | Human subject with phenotype data. | `donor_id` (str), `age` (int), `sex` (enum: "M"/"F"), `tissue` (str), `PMI` (float), `time_of_death` (float), `BMI` (float), `fasting_glucose` (float), `systolic_bp` (float), `diastolic_bp` (float), `triglycerides` (float), `HDL` (float) |
| **GeneExpression** | TPM value for a core circadian gene. | `donor_id` (str), `gene_symbol` (str), `tpm` (float), `tpm_log` (float) |
| **Classification** | Binary MetS label (or Unlabeled) for donors with complete phenotype data. | `donor_id` (str), `label` (enum: "MetS","Control","Unlabeled"), `criteria_met` (int) |
| **DEResult** | ANCOVA outcome for the binary MetS label. | `gene_symbol` (str), `tissue` (str), `beta` (float), `ci_lower` (float), `ci_upper` (float), `p_raw` (float), `p_adj` (float) |
| **CorrelationResult** | Gene‑trait association. | `gene_symbol` (str), `trait` (str), `tissue` (str), `rho` (float), `p_raw` (float), `p_adj` (float), `model_type` (enum: "Spearman", "Pearson") |
| **UnivariateLogisticResult** | Odds ratios for each metabolic trait. | `trait` (str), `odds_ratio` (float), `ci_lower` (float), `ci_upper` (float), `p_value` (float) |
| **BatchSensitivityResult** | Coefficient stability with/without batch covariate. | `predictor` (str), `stability` (float), `stable` (boolean) |
| **SuccessMetrics** | Consolidated study‑level metrics for all SCs. | `metric_name` (str), `value` (float), `description` (str) |

## File Layout (`data/processed/`)

| File | Entity | Format | Schema |
|------|--------|--------|--------|
| `donors_integrated.parquet` | Donor | Parquet | `dataset.schema.yaml` |
| `expression_filtered.parquet` | GeneExpression | Parquet | `dataset.schema.yaml` |
| `classification.csv` | Classification | CSV | `classification.schema.yaml` |
| `de_results.csv` | DEResult | CSV | `de_results.schema.yaml` |
| `correlation_results.csv` | CorrelationResult | CSV | `correlation_results.schema.yaml` |
| `univariate_logistic_results.csv` | UnivariateLogisticResult | CSV | `logistic_regression.schema.yaml` |
| `batch_sensitivity.csv` | BatchSensitivityResult | CSV | `model.schema.yaml` |
| `success_metrics.csv` | SuccessMetrics | CSV | `output.schema.yaml` |
| `power_summary.csv` | Statistical Power | CSV | `output.schema.yaml` |
| `validation_results.csv` | External Validation | CSV | `validation_results.schema.yaml` |
| `cv_performance.csv` | Logistic CV performance | CSV | `cv_performance.schema.yaml` |

## Relationships
- **One-to-Many**: One `Donor` → multiple `GeneExpression` entries (one per core gene).  
- **One-to-One**: One `Donor` → one `Classification` (when phenotype complete).  
- **Many-to-One**: Multiple `DEResult` / `CorrelationResult` entries → a single `Donor` group per tissue.  

*All processed artifacts are stored under `data/processed/` in compliance with Constitution Principle IV (Single Source of Truth).*
