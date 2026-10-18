# Data Model: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Core Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| **Donor** | Human subject; includes covariates and continuous metabolic traits. | `donor_id` (str), `age` (int), `sex` (enum: "M"/"F"), `tissue` (str), `PMI` (float, optional), `time_of_death` (float, optional), `BMI` (float), `fasting_glucose` (float), `systolic_bp` (float), `diastolic_bp` (float), `triglycerides` (float), `HDL` (float) |
| **GeneExpression** | TPM value for a single gene in a donor. | `donor_id` (str), `gene_symbol` (str), `tpm` (float) |
| **RiskScore** | Continuous composite MetS risk score (z‑score sum of the five ATP‑III components). | `donor_id` (str), `risk_score` (float) |
| **DEResult** | ANCOVA differential‑expression outcome per gene‑tissue. | `gene_symbol`, `tissue`, `beta`, `ci_lower`, `ci_upper`, `p_raw`, `p_adj` |
| **CorrelationResult** | Mixed‑effects correlation for a gene‑trait pair (tissue‑specific estimate). | `gene_symbol`, `trait`, `tissue`, `rho`, `p_raw`, `p_adj`, `model_type` |
| **ValidationResult** | External validation metrics (if available). | `metric` (str), `value` (float), `p_value` (float), `pass` (bool) |

## File Layout (under `data/processed/`)

| File | Entity | Format | Schema |
|------|--------|--------|--------|
| `donors.parquet` | Donor | Parquet | `dataset.schema.yaml` |
| `expression.parquet` | GeneExpression | Parquet | `dataset.schema.yaml` |
| `risk_score.csv` | RiskScore | CSV | `classification.schema.yaml` (re‑purposed for continuous score) |
| `de_results.csv` | DEResult | CSV | `de_results.schema.yaml` |
| `correlation_results.csv` | CorrelationResult | CSV | `correlation_results.schema.yaml` |
| `validation_results.csv` | ValidationResult | CSV | `validation_results.schema.yaml` |
| `power_summary.csv` | Power analysis summary | CSV | `output.schema.yaml` (statistical_results section) |

All files contain a `generated_at` ISO‑8601 timestamp and a SHA‑256 checksum recorded under `state/projects/PROJ-110-investigating-the-correlation-between-ci.yaml` `artifact_hashes` map.

## Relationships

- **One‑to‑many**: One `Donor` → many `GeneExpression` rows (one per core circadian gene).  
- **One‑to‑one**: One `Donor` → one `RiskScore`.  
- **Many‑to‑many**: Predictors for DE and correlation are linked via `GeneExpression`; covariates are stored in `Donor`.  

Integrity checks (foreign‑key‑like) are performed during validation (e.g., every `donor_id` in `expression.parquet` must exist in `donors.parquet`).

---


