# Research: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Research Question & Hypothesis
- **Question**: Is dietary fiber intake associated with gut microbiome composition, and do identified associations replicate across independent cohorts?
- **Hypothesis**: Higher fiber intake correlates positively with fiber‑degrading taxa (e.g., *Faecalibacterium*, *Roseburia*) and negatively with pro‑inflammatory taxa, after adjusting for age, BMI, sex, recent antibiotic use, **and sequencing batch**.  
  *Only associative statements are made; no causal inference is claimed.*

## Dataset Strategy
| Cohort | Source (Verified) | Variable Fit Check |
|--------|-------------------|--------------------|
| **American Gut Project (AGP) – Open Diet Release** | `datasets.load_dataset("american_gut/agp_diet")` (public HuggingFace dataset) | The loader verifies presence of `fiber_intake_g`, `age`, `bmi`, `sex`, `antibiotic_use`, `batch`, `read_depth`, and a taxon count matrix. |
| **User‑provided open dataset** | Any open CSV/BIOM placed in `data/user_dataset/` (must contain the required columns). | The ingestion step validates the presence of **all** required columns (`fiber_intake_g`, `age`, `bmi`, `sex`, `antibiotic_use`, `batch`, `read_depth`, taxon count matrix). If any column is missing, that cohort is excluded with a clear warning. |
| **UK Biobank (UKBB) Gut Microbiome** | *No verified open URL* – UKBB requires credentialed access and is not downloadable on the CI runner. The pipeline attempts to download an open copy if the user supplies one; otherwise it proceeds with AGP (and optional user dataset) only. | If the UKBB release lacks any required column, that cohort is excluded and a *single‑cohort* flag is set. |

> **Note**: The original specification (FR‑001) mandates AGP and UKBB. Because UKBB is not openly downloadable, the plan falls back to a fully open AGP diet dataset and optionally a user‑provided dataset, satisfying the requirement for publicly obtainable data that contain the necessary `fiber_intake_g` variable.

## Methodological Rigor
| Step | Method | Statistical Rigor |
|------|--------|-------------------|
| **Data Harmonization & QC** | Unit conversion to g/day; filter reads ≥ 5 000; exclude fiber > 200 g/day. | Ensures biologically plausible range; aligns with FR‑001/FR‑002. |
| **Missing‑Data Handling** | Exclude samples with >20 % missing covariates; median/mode impute remaining. | Prevents bias from extensive missingness; retains power. |
| **CLR Transformation (Spearman only)** | Bayesian‑multiplicative replacement (`zCompositions`) → CLR. | Preserves compositional geometry for correlation; satisfies Principle VI. |
| **Partial Spearman Correlation** | Regress covariates (`age`, `bmi`, `sex`, `antibiotic_use`, `read_depth`) from both `fiber_intake_g` and each CLR‑taxon, compute Spearman ρ on residuals; estimate SE via **non‑parametric bootstrap (1 000 resamples)**; obtain raw p‑values. | Adjusts for known confounders; bootstrap SE respects the non‑parametric nature of Spearman after CLR and regression. |
| **MaAsLin2 Linear Model** | Linear model on **CLR‑transformed** counts with covariates `age`, `bmi`, `sex`, `antibiotic_use`, `read_depth`. | Handles compositional data correctly; internal BH correction applied. |
| **Benjamini‑Hochberg FDR** | Applied separately for each analysis (Spearman, MaAsLin2, ANCOM‑II, DESeq2). | Controls family‑wise false discovery rate (SC‑003). |
| **Differential Abundance** | **ANCOM‑II** on relative abundances; **DESeq2** on raw counts. | Each method used within its statistical assumptions; results merged for robustness. |
| **Cross‑Cohort Validation** | Taxa considered replicated only if q < 0.05 in **both** cohorts **and** effect direction matches. | Provides stringent replication; replication rate reported to two decimal places (SC‑006). |
| **Measurement‑Error Simulation** | Generate synthetic data with known β = 0.1, add Gaussian noise (SD = 10 % of mean fiber), re‑run both association methods, compute bias = (estimated − true)/true. | Quantifies attenuation bias from self‑report; reports median absolute bias (SC‑005). |
| **Power Analyses** | **A priori**: document required N per cohort to detect β ≈ 0.1 with 80 % power at α = 0.05 **using methods that match the statistical tests**:<br> • For Spearman correlation on CLR‑transformed data, use `statsmodels.stats.power.CorrelationPower` (appropriate for correlation testing).<br> • For the MaAsLin2 linear model, use `statsmodels.stats.power.FTestPower` (appropriate for multiple‑regression F‑tests).<br> • Additionally, run a **permutation‑based power simulation (1 000 permutations)** for Spearman to verify the analytical estimate.<br>**Post‑hoc**: compute achieved power for the smaller cohort; if requirement not met, issue FR‑013 warning and halt downstream analyses. **We explicitly avoid `TTestIndPower`, which assumes a two‑sample t‑test and would be mismatched to our primary analyses.** | Explicitly acknowledges power limitations; ensures downstream inference is not performed on under‑powered data (SC‑004). |
| **Reporting** | Median fiber intake per group (g/day); replication rate; power metrics; measurement‑error bias; all tables saved as TSV/CSV; final markdown report; **PNG visualizations** (volcano plot, CLR‑ordination PCA) listed in summary. | Meets SC‑001, SC‑003, SC‑007; ensures traceability (Principle IV). |

## Decision Rationale
| Decision | Reason |
|----------|--------|
| **Download AGP – Open Diet Release** | AGP is openly available via HuggingFace and contains self‑reported dietary fiber intake in grams/day, satisfying FR‑001. |
| **Run MaAsLin2 on CLR‑transformed data** | FR‑004 explicitly requires CLR input; this respects compositional‑data assumptions. |
| **Partial Spearman (covariate‑adjusted) with bootstrap SE** | Adjusts for known confounders; bootstrap SE respects the non‑parametric nature of Spearman after CLR and regression. |
| **Merge Spearman & MaAsLin2 results** | Aligns with `correlation_result.schema.yaml` which expects a single combined record per taxon. |
| **Measurement‑error simulation with known truth** | Avoids circular validation; provides an objective bias estimate. |
| **Model‑appropriate power analysis** | Uses statistical power methods matched to the actual tests (CorrelationPower for Spearman, FTestPower for MaAsLin2) and adds permutation backup for robustness. |
| **Single‑cohort fallback** | Satisfies Constitution Principle VII; analysis proceeds with clear limitation flag if UKBB unavailable. |
| **Visualization generation** | Directly satisfies SC‑008 by producing required PNG files. |

---



## projects/PROJ-112-investigating-the-correlation-between-di/specs/001-investigating-the-correlation-between-di/data-model.md===
# Data Model: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Overview
Four logical data states are persisted under `data/`:

1. **Raw** – original AGP 16S count tables and metadata (unchanged). No UK Biobank data are automatically downloaded because it is not publicly accessible; a user‑provided open dataset may serve as an additional raw source.
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
| `spearman_se` | number | Standard error of Spearman ρ (via bootstrap, rounded to 3 dp). |
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
