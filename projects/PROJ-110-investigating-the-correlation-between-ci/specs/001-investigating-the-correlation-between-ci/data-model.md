# Data Model: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Overview
All intermediate and final artifacts are stored as CSV or Parquet files under `data/processed/`. The schema definitions below are used by contract tests to guarantee structural integrity.

### 1. `donors.parquet`
| Column | Type | Description |
|--------|------|-------------|
| `donor_id` | string | Unique MESA or GTEx donor identifier |
| `age` | int | Age at blood draw (MESA) or at death (GTEx) (years) |
| `sex` | string (`"M"`/`"F"`) | Biological sex |
| `tissue` | string | Tissue name (`"Blood"` for MESA; GTEx tissue ontology for GTEx) |
| `pmi` | float | Post‑mortem interval (hours) – GTEx only |
| `time_of_death` | float | Clock time of death (hours, 0‑24) – GTEx only |
| `batch` | string | Sequencing batch identifier (if available) |
| `bmi` | float | Body mass index (kg/m²) |
| `fasting_glucose` | float | Fasting glucose (mg/dL) |
| `sbp` | float | Systolic blood pressure (mmHg) |
| `dbp` | float | Diastolic blood pressure (mmHg) |
| `triglycerides` | float | Triglycerides (mg/dL) |
| `hdl` | float | HDL cholesterol (mg/dL) |
| `metabolic_status` | string (`"MetS"`/`"Control"`/`"Exploratory"`) | ATP‑III classification (MESA) or `"Exploratory"` for GTEx (no label) |
| `criteria_count` | int (0‑5) | Number of ATP‑III criteria met |
| `study_status` | string (`"exploratory"`/`"full"`) | Set after power analysis |

### 2. `expression.parquet`
| Column | Type | Description |
|--------|------|-------------|
| `donor_id` | string | Foreign key to `donors` |
| `gene` | string | Gene symbol (core circadian list) |
| `tpm` | float | Transcripts per million (raw) |
| `log_tpm` | float | `log2(tpm + 1)` for modeling |

### 3. `de_results.csv`
| Column | Type | Description |
|--------|------|-------------|
| `gene` | string | Core circadian gene |
| `tissue` | string | Tissue name |
| `beta` | float | Hierarchical ANCOVA coefficient for MetS |
| `ci_lower` | float | 95 % CI lower bound |
| `ci_upper` | float | 95 % CI upper bound |
| `p_value` | float | Raw p‑value |
| `adj_p_value` | float | BH‑adjusted p‑value |
| `significant` | bool | `true` if `adj_p_value < 0.05` |

### 4. `correlation_results.csv`
| Column | Type | Description |
|--------|------|-------------|
| `gene` | string | Core circadian gene |
| `trait` | string | One of `bmi`, `fasting_glucose`, `sbp`, `dbp`, `triglycerides`, `hdl` |
| `rho` | float | Spearman (or Pearson) correlation coefficient |
| `p_value` | float | Raw p‑value |
| `adj_p_value` | float | BH‑adjusted p‑value |
| `significant` | bool | `true` if `adj_p_value < 0.05` |
| `model_beta` | float | Fixed‑effect estimate from mixed‑effects model |
| `model_ci_lower` | float | 95 % CI lower bound |
| `model_ci_upper` | float | 95 % CI upper bound |

### 5. `logistic_model_coefficients.csv`
| Column | Type | Description |
|--------|------|-------------|
| `feature` | string | Predictor name (`gene_PER1`, `age`, `sex_F`, …) |
| `odds_ratio` | float | Exponentiated coefficient |
| `ci_lower` | float | 95 % CI lower bound |
| `ci_upper` | float | 95 % CI upper bound |
| `p_value` | float | Wald test p‑value |
| `vif` | float | Variance Inflation Factor (≥ 5 flagged) |

### 6. `auxiliary_traits_coefficients.csv`
| Column | Type | Description |
|--------|------|-------------|
| `trait` | string | Clinical trait name |
| `odds_ratio` | float | Exponentiated coefficient from traits‑only model |
| `ci_lower` | float | 95 % CI lower bound |
| `ci_upper` | float | 95 % CI upper bound |
| `p_value` | float | Wald test p‑value |

### 7. `cv_performance.csv`
| Column | Type | Description |
|--------|------|-------------|
| `fold` | int | CV fold index (1‑5) |
| `auc` | float | Area Under ROC curve |
| `auc_ci_lower` | float | 95 % CI lower bound (bootstrapped) |
| `auc_ci_upper` | float | 95 % CI upper bound |
| `delta_auc_vs_random` | float | `auc - 0.5` |

### 8. `validation_results.csv` (MESA Blood)
| Column | Type | Description |
|--------|------|-------------|
| `metric` | string | `gene_overlap`, `auc_difference` |
| `value` | float | Numeric result |
| `p_value` | float | Significance test result |
| `pass` | bool | Whether the metric meets the replication threshold (FR‑010) |

All files are version‑controlled via git LFS pointers if > 100 MB; otherwise stored directly under `data/processed/`.

---

