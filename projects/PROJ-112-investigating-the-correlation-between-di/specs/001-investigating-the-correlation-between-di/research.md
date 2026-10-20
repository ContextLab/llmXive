# Research: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Research Question & Hypothesis
- **Question**: Is dietary fiber intake associated with gut microbiome composition, and do identified associations replicate across independent cohorts?
- **Hypothesis**: Higher fiber intake correlates positively with fiber‑degrading taxa (e.g., *Faecalibacterium*, *Roseburia*) and negatively with pro‑inflammatory taxa, after adjusting for age, BMI, sex, recent antibiotic use, **and sequencing batch**.  
  *Only associative statements are made; no causal inference is claimed.*

## Dataset Strategy
| Cohort | Source (Verified) | Variable Fit Check |
|--------|-------------------|--------------------|
| **American Gut Project (AGP)** | *No verified open URL* – direct download requires credentials. **Fallback**: `openmicrobiome/human_gut_microbiome` (Hugging Face) – **must contain** `fiber_intake_g`, `age`, `bmi`, `sex`, `antibiotic_use`, `batch`. | Pipeline verifies presence of all required columns. If any are missing, the AGP cohort is **excluded** and a clear warning is emitted. |
| **UK Biobank (UKBB)** | *No verified open URL*. **Fallback**: `openmicrobiome/ukbb_gut_microbiome` (Hugging  Face) – **must contain** the same required columns. | Same check as AGP. |

> **Note**: The verified open mirrors currently **do not** contain the necessary exposure (`fiber_intake_g`) or some covariates. Users must supply an alternative open dataset that includes these variables. If only one cohort satisfies the variable requirement, the analysis proceeds on that cohort and the final report flags a **“Single‑Cohort”** result, satisfying Constitution Principle VII.

## Methodological Rigor
| Step | Method | Rationale / Statistical Rigor |
|------|--------|--------------------------------|
| **Data Harmonization & QC** | Unit conversion to g/day; filter reads ≥ 5,000; exclude fiber > 200 g/day. | Ensures biologically plausible range; aligns with FR‑001/FR‑002. |
| **Missing‑Data Handling** | Exclude samples with >20 % missing covariates (including batch); median/mode impute remaining. | Prevents bias from extensive missingness; retains power. |
| **CLR Transformation (Spearman only)** | Bayesian‑multiplicative replacement (`zCompositions`) → CLR. | Preserves compositional geometry for correlation; satisfies Principle VI. |
| **Association Analysis** | **Spearman ρ** on CLR matrix (fiber vs. each taxon). <br> **MaAsLin2** on **raw counts** (adjusting for age, BMI, sex, antibiotic_use, **batch**). <br> Benjamini‑Hochberg FDR across taxa. | MaAsLin2 internally handles compositionality; Spearman provides a non‑parametric complement. FDR controls family‑wise error (SC‑002). |
| **Differential Abundance** | **ANCOM‑II** on relative abundances; **DESeq2** on **raw counts**. | Each tool used according to its statistical assumptions. |
| **Cross‑Cohort Validation** | Taxa considered replicated **only if** (i) q < 0.05 in **both** cohorts **and** (ii) effect direction matches. | Provides stringent replication; yields replication rate (SC‑003). |
| **Power & Sensitivity** | **A priori power justification** (deferred): based on published microbiome‑fiber effect sizes, [deferred] samples per cohort would give 80 % power to detect β≈0.1 at α=0.05. This is documented for transparency. <br> **Post‑hoc power calculation** for the smaller cohort using `statsmodels.stats.power.TTestIndPower`; report achieved power and minimum detectable effect size. <br> **Categorical fiber sensitivity analysis** (low/medium/high) to gauge attenuation bias from self‑report error. | Explicitly acknowledges potential under‑power (addresses concern methodology-012f38a2) and provides quantitative assessment of detectable effects. |
| **Reporting** | Median fiber intake per group (g/day) reported; replication rate reported to two decimal places; single‑cohort flag if only one cohort available. | Meets SC‑009 and ensures transparency. |

## Decision Rationale
| Decision | Reason |
|----------|--------|
| Use **fallback open‑microbiome mirrors** | Direct AGP/UKBB downloads need credentials (violates CI feasibility). Mirrors are open and verified, but we enforce a strict variable‑fit check; if they lack required columns the pipeline aborts with guidance. |
| **Raw counts for MaAsLin2 & DESeq2** | Both methods expect integer counts; applying CLR would violate their model assumptions (addresses concerns 1a8ac0a7 and d47b2b68). |
| **Include sequencing batch** as a covariate | Known technical confounder in 16S studies; omission would inflate false positives (addresses concern 6946def7). |
| **Measurement‑error acknowledgment** | Self‑reported dietary data are noisy; we note attenuation bias and perform a categorical sensitivity analysis (addresses concern fee04c1d). |
| **Post‑hoc power analysis** | Provides an explicit statement of statistical power, satisfying methodological rigor (addresses concern 012f38a2). |
| **Single‑Cohort fallback** | Aligns with Constitution Principle VII; analysis continues on any available cohort and flags the limitation (addresses concern 2df699ec). |

---



