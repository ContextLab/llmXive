# Data Model: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Overview
Four logical data states are persisted under `data/`:

1. **Raw** – original AGP/UKBB (or user‑provided) 16S count tables and metadata (unchanged).
2. **Harmonized** – after unit conversion, filtering, and covariate imputation.
3. **Analysis Matrices** – (a) CLR‑transformed taxon abundances (for Spearman) and (b) CLR‑transformed count matrix (for MaAsLin2), each linked to sample metadata.
4. **Results** – association tables, differential‑abundance tables, replication flags, measurement‑error bias summaries, power reports, and the final markdown report.

## Schemas (referenced in `contracts/`)

### 1. Harmonized Sample Record (`dataset.schema.yaml`)
| Field | Type | Constraints |
|-------|------|-------------|
| `sample_id` | string | Unique; SHA‑256 hash of original ID + cohort. |
| `fiber_intake_g` | number | 0 ≤ value ≤ 200. |
| `age` | number | Positive. |
| `sex` | string | `"M"` or `"F"`. |
| `bmi` | number | Positive. |
| `antibiotic_use` | string | `"Yes"` or `"No"`. |
| `batch` | string | Non‑empty sequencing batch identifier. |
| `read_depth` | integer | ≥ 5 000. |
| `cohort` | string | `"AGP"` or `"UKBB"` or `"User"`. |

### 2. CLR‑Transformed Taxon Matrix (`analysis_matrix_clr.csv` – not a schema file)
Columns: `sample_id`, `taxon_id`, `clr_value` (real number; zeros handled by Bayesian replacement).

### 3. Raw Count Taxon Matrix (`analysis_matrix_counts.csv` – not a schema file)
Columns: `sample_id`, `taxon_id`, `count` (integer ≥ 0).

### 4. Association Result (`correlation_result.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `taxon` | string | Taxon identifier (e.g., `g__Bacteroides`). |
| `spearman_rho` | number | Spearman correlation coefficient (rounded to 3 dp). |
| `spearman_se` | number | Standard error of Spearman ρ (via Fisher Z, rounded to 3 dp). |
| `raw_p_value` | number | 0 ≤ p ≤ 1. |
| `q_value` | number | BH‑adjusted q (0 ≤ q ≤ 1). |
| `significant` | boolean | `q_value < 0.05`. |
| `beta_coefficient` | number | Linear‑model β from MaAsLin2 on CLR data (rounded to 3 dp). |
| `cohort` | string | `"AGP"`, `"UKBB"` or `"User"`. |

### 5. Differential Abundance Result (`diff_abundance.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `taxon_id` | string | Taxonomic identifier. |
| `method` | string | `"ANCOM-II"` or `"DESeq2"`. |
| `q_value` | number | Adjusted p‑value. |
| `effect_size` | number | Log‑fold change (DESeq2) or W‑statistic (ANCOM‑II). |
| `direction` | string | `"Positive"` or `"Negative"`. |
| `replicated` | boolean | `True` iff significant (q < 0.05) in **both** cohorts with identical direction. |

## Validation Rules
- All numeric fields respect the ranges noted above.  
- `replicated` is `True` ⇔ (`q_value < 0.05` in both cohorts) **and** `direction` identical.  
- Samples failing the >20 % missingness rule are excluded before schema validation.  
- `batch` must be non‑empty; it is used as a covariate in association models.
