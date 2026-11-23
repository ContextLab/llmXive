# Data Model: Investigating Neural Signatures of Predictive Processing in Visual Illusions

## Core Entities
| Entity | Description | Key Fields |
|--------|-------------|------------|
| **Subject** | Participant identifier appearing in both illusion datasets. | `subject_id` (string), optional `age` (integer), optional `gender` (string) |
| **Trial** | Single stimulus presentation. | `subject_id` (string), `trial_id` (string), `stimulus_params` (JSON string), `response` (float) |
| **PrecisionParameter** | Individual precision‑weighting λ from the Müller‑Lyer model. | `subject_id` (string), `lambda` (float, ≥ 0.01 ≤ 10.0), `log_likelihood` (float), `aic` (float), `bic` (float) |
| **SusceptibilityScore** | β parameter quantifying Ponzo illusion magnitude. | `subject_id` (string), `beta` (float), `r2` (float, 0 – 1) |
| **CorrelationResult** | Primary outcome of the cross‑illusion analysis. | `r` (float), `p_value` (float), `ci_lower` (float), `ci_upper` (float), `n_subjects` (integer) |

## File Artifacts & Schemas
| File | Purpose | Schema |
|------|---------|--------|
| `data/raw/muller_lyer.parquet` | Unmodified training dataset (checksum stored in project state). | *raw – no schema* |
| `data/raw/ponzo.parquet` | Unmodified test dataset (checksum stored). | *raw – no schema* |
| `data/clean/clean_muller_lyer.csv` | Cleaned training data; no missing critical fields. | `contracts/clean-muller-lyer.schema.yaml` |
| `data/clean/clean_ponzo.csv` | Cleaned test data. | `contracts/clean-ponzo.schema.yaml` |
| `data/derived/precision_parameters.csv` | Per‑subject λ estimates + diagnostics. | `contracts/precision-parameters.schema.yaml` |
| `data/derived/ponzo_susceptibility.csv` | Per‑subject β scores + model R². | `contracts/ponzo-susceptibility.schema.yaml` |
| `data/merged/merged_results.csv` | Joined λ and β for subjects with complete data; includes null‑model AIC/BIC. | `contracts/merged-results.schema.yaml` |
| `outputs/correlation_results.json` | JSON summary of the primary λ‑β correlation analysis. | `contracts/correlation-results.schema.yaml` |
| `outputs/figures/*.png` | Diagnostic and result visualizations (existence‑only check). | *no schema* |
| `data/manifest.yaml` | Single Source of Truth manifest recording provenance (source URL, checksum, generation timestamp) for every artifact. | *no schema* |

## Data Flow
1. **Ingestion**: `load_illusions.py` reads raw parquet → validates checksum → writes cleaned CSVs.  
2. **Model fitting**: `predictive_coding.py` consumes `clean_muller_lyer.csv` → writes `precision_parameters.csv`.  
3. **Susceptibility scoring**: `null_model.py` consumes `clean_ponzo.csv` → writes `ponzo_susceptibility.csv`.  
4. **Merging**: `correlation.py` joins on `subject_id` → writes `merged_results.csv` (including null‑model AIC/BIC).  
5. **Analysis**: `correlation.py` reads `merged_results.csv` → produces `correlation_results.json` + PNGs.  

All steps are pure functions; raw files remain untouched, satisfying Principle III (Data Hygiene).

---

