# Data Model: Investigating Neural Signatures of Predictive Processing in Visual Illusions

## Core Entities
| Entity | Description | Key Fields |
|--------|-------------|------------|
| **Subject** | Participant identifier, appears in both illusion datasets. | `subject_id` (string), `age` (int), `gender` (string) |
| **Trial** | Single presentation of an illusion stimulus. | `subject_id`, `trial_id`, `stimulus_params` (JSON), `response` (float) |
| **PrecisionParameter** | Individual precision‑weighting $\lambda$ estimated from Müller‑Lyer model. | `subject_id`, `lambda` (float, $\ge$ 0.01 $\le$ 10.0), `log_likelihood` (float), `aic` (float), `bic` (float) |
| **SusceptibilityScore** | $\beta$ parameter quantifying Ponzo illusion magnitude per subject. | `subject_id`, `beta` (float), `model_r2` (float) |
| **CorrelationResult** | Primary outcome of cross‑illusion analysis. | `r` (float), `p_value` (float), `ci_lower` (float), `ci_upper` (float), `n_subjects` (int) |

## File Artifacts & Schemas
| File | Purpose | Schema |
|------|---------|--------|
| `data/raw/muller_lyer.parquet` | Original training dataset (unchanged). | *No schema file (raw data) – checksum stored in state file* |
| `data/raw/ponzo.parquet` | Original test dataset (unchanged). | *No schema file (raw data) – checksum stored in state file* |
| `data/clean/clean_muller_lyer.csv` | Cleaned training data, no missing critical fields. | `contracts/clean-muller-lyer.schema.yaml` |
| `data/clean/clean_ponzo.csv` | Cleaned test data. | `contracts/clean-ponzo.schema.yaml` |
| `data/derived/precision_parameters.csv` | Per‑subject $\lambda$ estimates + diagnostics. | `contracts/precision-parameters.schema.yaml` |
| `data/derived/ponzo_susceptibility.csv` | Per‑subject $\beta$ scores. | `contracts/ponzo-susceptibility.schema.yaml` |
| `data/merged/merged_results.csv` | Joined table of $\lambda$ and $\beta$ for subjects with complete data. | `contracts/merged-results.schema.yaml` |
| `outputs/figures/*.png` | Diagnostic and result visualizations. | *No schema file – images are validated by existence checks* |
| `outputs/correlation_results.json` | JSON summary of primary correlation and bootstrap CI. | `contracts/correlation-results.schema.yaml` |

## Data Flow
1. **Ingestion** reads raw parquet $\rightarrow$ validates checksum $\rightarrow$ writes cleaned CSVs.  
2. **Model fitting** consumes `clean_muller_lyer.csv` $\rightarrow$ writes `precision_parameters.csv`.  
3. **Susceptibility scoring** consumes `clean_ponzo.csv` $\rightarrow$ writes `ponzo_susceptibility.csv`.  
4. **Merging** joins on `subject_id` $\rightarrow$ writes `merged_results.csv`.  
5. **Analysis** reads `merged_results.csv` $\rightarrow$ produces `correlation_results.json` + figures.  

All transformations are pure functions; original raw files remain untouched, satisfying Principle III (Data Hygiene).