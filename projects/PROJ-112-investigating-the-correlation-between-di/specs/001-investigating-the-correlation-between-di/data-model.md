# Data Model: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Overview
Four logical data states are persisted under `data/`:

1. **Raw** – downloaded 16S tables & metadata (unchanged).
2. **Harmonized** – unit‑standardized, filtered, and imputed sample table.
3. **Analysis Matrix** – CLR‑transformed taxon abundances (for Spearman) **and** raw count matrix (for MaAsLin2 & DESeq2) linked to sample metadata.
4. **Results** – association tables, differential abundance tables, replication flags, and summary reports.

## Schemas (refer to `contracts/`)

### 1. Harmonized Sample Record (`dataset.schema.yaml`)
| Field | Type | Constraints |
|-------|------|-------------|
| `sample_id` | string | Unique; SHA‑256 hash of original ID + cohort. |
| `fiber_intake_g` | number | 0 ≤ value ≤ 200. |
| `age` | number | Positive. |
| `sex` | string | `"M"` or `"F"`. |
| `bmi` | number | Positive. |
| `antibiotic_use` | string | `"Yes"` or `"No"`. |
| `batch` | string | Sequencing batch identifier (non‑empty). |
| `read_depth` | integer | ≥ 5,000. |
| `cohort` | string | `"AGP"` or `"UKBB"`. |

### 2. CLR‑Transformed Taxon Matrix (`analysis_matrix_clr.csv` – not a schema file)
Columns: `sample_id`, `taxon_id`, `clr_value`.  
`clr_value` is a real number; zeros handled by Bayesian replacement before transformation.

### 3. Raw Count Taxon Matrix (`analysis_matrix_counts.csv` – not a schema file)
Columns: `sample_id`, `taxon_id`, `count` (integer ≥ 0).  
**Used by** MaAsLin2 and DESeq2 (which require raw integer counts).

### 4. Association Result (`correlation_result.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `taxon` | string | Taxon identifier (e.g., g__Bacteroides). |
| `spearman_rho` | number | Spearman correlation coefficient (rounded to 3 dp). |
| `spearman_se` | number | Standard error via Fisher Z (rounded to 3 dp). |
| `raw_p_value` | number | 0 ≤ p ≤ 1. |
| `q_value` | number | Benjamini‑Hochberg adjusted q-value (0 ≤ q ≤ 1). |
| `significant` | boolean | `q_value < 0.05`. |
| `beta_coefficient` | number | Linear‑model β from MaAsLin2 on raw counts (rounded to 3 dp). |
| `cohort` | string | `"AGP"`, `"UKBB"` or `"Combined"`. |

### 5. Differential Abundance Result (`diff_abundance.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `taxon_id` | string | Taxonomic identifier. |
| `method` | string | `"ANCOM-II"` or `"DESeq2"`. |
| `q_value` | number | Adjusted p‑value. |
| `effect_size` | number | Log‑fold change (DESeq2) or W‑statistic (ANCOM‑II). |
| `direction` | string | `"Positive"` or `"Negative"`. |
| `replicated` | boolean | `True` only if significant (q < 0.05) in **both** cohorts with same direction. |

## Validation Rules
- All numeric fields respect the ranges noted above.
- `replicated` is `True` ⇔ (`q_value < 0.05` in AGP **and** UKBB) **and** `direction` identical.
- `batch` must be non‑empty; it is used as a covariate in association models.
- Missing covariates >20 % → sample excluded before schema validation.

---


