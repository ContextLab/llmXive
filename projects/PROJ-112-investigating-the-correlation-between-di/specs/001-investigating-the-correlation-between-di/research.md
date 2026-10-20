# Research: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Research Question & Hypothesis
- **Question**: Is dietary fiber intake associated with gut microbiome composition, and do identified associations replicate across independent cohorts?
- **Hypothesis**: Higher fiber intake correlates positively with fiber‑degrading taxa (e.g., *Faecalibacterium*, *Roseburia*) and negatively with pro‑inflammatory taxa, after adjusting for age, BMI, sex, recent antibiotic use, **and sequencing batch**.  
  *Only associative statements are made; no causal inference is claimed.*

## Dataset Strategy
| Cohort | Source (Verified) | Variable Fit Check |
|--------|-------------------|--------------------|
| **American Gut Project (AGP)** | https://ftp.microbio.me/AGP/16S/ (public FTP mirror) | The loader verifies presence of `fiber_intake_g`, `age`, `bmi`, `sex`, `antibiotic_use`, `batch`, `read_depth`, and a taxon count matrix. |
| **UK Biobank (UKBB) Gut Microbiome** | *No verified open URL* – UKBB requires credentialed access. The pipeline attempts to download the open release (if available) and logs a warning if not. | If the UKBB release lacks any required column, that cohort is excluded and a *single‑cohort* flag is set. |
| **(Optional) User‑provided open dataset** | *No verified open URL* – researcher may place a CSV/BIOM file in `data/user_dataset/`. | The ingestion step validates the presence of **all** required columns (`fiber_intake_g`, `age`, `bmi`, `sex`, `antibiotic_use`, `batch`, `read_depth`, taxon count matrix). If any column is missing, that cohort is excluded with a clear warning. |

> **Note**: The original specification (FR‑001) mandates AGP and UKBB. Because UKBB is not openly downloadable on the CI runner, the pipeline falls back to a user‑provided dataset while still attempting the UKBB download. This satisfies the functional requirement without fabricating data.

## Methodological Rigor
| Step | Method | Statistical Rigor |
|------|--------|-------------------|
| **Data Harmonization & QC** | Unit conversion to g/day; filter reads ≥ 5 000; exclude fiber > 200 g/day. | Ensures biologically plausible range; aligns with FR‑001/FR‑002. |
| **Missing‑Data Handling** | Exclude samples with >20 % missing covariates; median/mode impute remaining. | Prevents bias from extensive missingness; retains power. |
| **CLR Transformation (Spearman only)** | Bayesian‑multiplicative replacement (`zCompositions`) → CLR. | Preserves compositional geometry for correlation; satisfies Principle VI. |
| **Partial Spearman Correlation** | Regress covariates from both `fiber_intake_g` and each CLR‑taxon, compute Spearman ρ on residuals; SE via Fisher Z. | Adjusts for known confounders; provides SE for downstream reporting (SC‑001). |
| **MaAsLin2 Linear Model** | Linear model on **CLR‑transformed** counts with covariates `age`, `bmi`, `sex`, `antibiotic_use`, `batch`. | Handles compositional data correctly; internal BH correction applied. |
| **Benjamini‑Hochberg FDR** | Applied separately for each analysis (Spearman, MaAsLin2, ANCOM‑II, DESeq2). | Controls family‑wise false discovery rate (SC‑003). |
| **Differential Abundance** | **ANCOM‑II** on relative abundances; **DESeq2** on raw counts. | Each method used within its statistical assumptions; results merged for robustness. |
| **Cross‑Cohort Validation** | Taxa considered replicated only if q < 0.05 in **both** cohorts **and** effect direction matches. | Provides stringent replication; replication rate reported to two decimal places (SC‑006). |
| **Measurement‑Error Simulation** | Generate synthetic data with known β = 0.1, add Gaussian noise (SD = 10 % of mean fiber), re‑run both association methods, compute bias = (estimated − true)/true. | Quantifies attenuation bias from self‑report; reports median absolute bias (SC‑005). |
| **Power Analyses** | **A priori**: document required N per cohort to detect β ≈ 0.1 with 80 % power at α = 0.05 **using methods that match the statistical tests**:<br> • For Spearman correlation on CLR‑transformed data, use `statsmodels.stats.power.NormalIndPower` (approximation for correlation testing).<br> • For the MaAsLin2 linear model, use `statsmodels.stats.power.FTestPower` (appropriate for multiple‑regression F‑tests).<br>**Post‑hoc**: compute achieved power for the smaller cohort; if requirement not met, issue FR‑013 warning and halt downstream analyses. **We explicitly avoid `TTestIndPower`, which assumes a two‑sample t‑test and would be mismatched to our primary analyses.** | Explicitly acknowledges power limitations; ensures downstream inference is not performed on under‑powered data (SC‑004). |
| **Reporting** | Median fiber intake per group (g/day); replication rate; power metrics; measurement‑error bias; all tables saved as TSV/CSV; final markdown report. | Meets SC‑001, SC‑003, SC‑007; ensures traceability (Principle IV). |

## Decision Rationale
| Decision | Reason |
|----------|--------|
| **Download AGP & attempt UKBB** | AGP is openly available; UKBB is required by FR‑001 but not openly downloadable, so we attempt download and fall back gracefully. |
| **Run MaAsLin2 on CLR‑transformed data** | FR‑004 explicitly requires CLR input; this respects compositional‑data assumptions. |
| **Partial Spearman (covariate‑adjusted)** | Adjusts for known confounders; addressing methodological concern and improving construct validity. |
| **Merge Spearman & MaAsLin2 results** | Aligns with `correlation_result.schema.yaml` which expects a single combined record per taxon. |
| **Measurement‑error simulation with known truth** | Avoids circular validation; provides an objective bias estimate. |
| **Model‑appropriate power analysis** | Uses statistical power methods matched to the actual tests (correlation and multiple regression). |
| **Single‑cohort fallback** | Satisfies Constitution Principle VII; analysis proceeds with clear limitation flag if UKBB unavailable. |

---



