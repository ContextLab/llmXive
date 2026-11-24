# Research: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Feature**: `001-circadian-metabolic-correlation`  
**Date**: 2023-10-27  

## Overview
This study examines the association between core circadian gene expression (*PER1‑3, CRY1‑2, BMAL1, CLOCK, NR1D1, RORα*) and metabolic syndrome (MetS) risk. Because **no open dataset provides both RNA‑seq TPMs **and** the full ATP‑III clinical panel for the same donors**, the analysis proceeds in **exploratory mode**. Binary MetS labeling (FR‑002) is attempted **only when** a dataset with matched expression + ATP‑III phenotypes is supplied; otherwise donors are labeled `Unlabeled` and downstream binary‑outcome analyses (logistic regression, AUC, external validation) are skipped.

## Decision / Rationale
| Decision | Rationale | Compute Mode |
|----------|-----------|--------------|
| **Binary MetS Classification (FR‑002)** | Required by the spec; performed only when complete ATP‑III variables exist for a donor. Otherwise donors are `Unlabeled`. | CPU |
| **PMI Residualization (FR‑031)** | GTEx expression is known to be affected by post‑mortem interval; residualizing TPM on PMI avoids double‑adjustment. | CPU |
| **Mixed‑Effects ANCOVA with Hierarchical Pooling (FR‑020)** | Ensures sufficient sample size per tissue while preserving tissue‑specific inference. | CPU |
| **Mixed‑Effects Gene‑Trait Modeling (FR‑007)** | Directly estimates the association of expression with each metabolic trait while accounting for tissue as a random effect. | CPU |
| **Global BH Correction** | Controls overall false discovery rate across all tests (FR‑004, FR‑012). | CPU |
| **Batch‑Effect Sensitivity (FR‑015)** | Quantifies robustness of logistic coefficients to sequencing batch. | CPU |
| **CPU‑Only Enforcement (T060)** | `src/scripts/cpu_check.py` asserts no GPU is present; CI will enforce this gate. | CPU |

## Dataset Strategy

| Role | Dataset | Access Method | Verified URL | Notes |
|------|---------|---------------|--------------|-------|
| Phenotype & Expression (single source) | **Open dataset containing both TPM matrices and ATP‑III clinical variables** (e.g., a publicly released METSIM subset) | Programmatic download via `datasets.load_dataset(...)` | **Will be added when a verified source becomes available** | Required for binary MetS labeling and all downstream binary analyses. |
| GTEx v8 TPM matrices (exploratory) | GTEx v8 TPM matrices (exploratory) | **N/A** (to be added when a verified URL is provided) | **NO verified source found** | Used for exploratory expression analyses; does **not** contain ATP‑III clinical variables. |

*If no single‑source dataset is available, the pipeline runs in exploratory mode, using GTEx expression and covariates, and computes binary MetS classification only for donors where the ATP‑III variables happen to be present (rare).*

## Methodological Details

### 1. Binary MetS Classification (FR‑002)
For each donor with **all five** ATP‑III variables present, apply the ATP‑III thresholds (≥ 3 criteria) → `MetS` or `Control`. Missing any variable → donor excluded from binary analyses. Output `classification.csv` validated against `classification.schema.yaml`.

### 2. PMI Residualization (FR‑031)
Fit a linear model `TPM ~ PMI` for each gene‑tissue combination; replace raw TPM with residuals before any downstream modeling. PMI is **not** included as a covariate thereafter.

### 3. Covariate‑Adjusted Differential Expression (ANCOVA) (FR‑003, FR‑013, FR‑020)
For each tissue with ≥ 20 donors per **binary** group (MetS / Control) **or** after hierarchical pooling (FR‑020), fit:
$$\text{TPM}_{\text{resid}} = \beta_0 + \beta_1 \text{MetS} + \beta_2 \text{Age} + \beta_3 \text{Sex} + \beta_4 \text{TOD} + \epsilon$$
Output β, 95 % CI, raw p‑value; global BH correction applied (FR‑004).

### 4. Gene‑Trait Mixed‑Effects Modeling (FR‑007, FR‑014)
For each core gene‑trait pair, fit a linear mixed‑effects model:
$$\text{TPM}_{\text{resid}} = \gamma_0 + \gamma_1 \text{Trait} + (1 \mid \text{Tissue}) + \eta$$
Normality of residuals determines reporting of Pearson *r* (if normal) or Spearman ρ (if non‑normal). Global BH correction across all tests (FR‑012). Significance requires adjusted p < 0.05 **and** |ρ| ≥ 0.2 (FR‑024).

### 5. Univariate Logistic Odds Ratios (FR‑009)
Separate logistic regressions for each metabolic trait (BMI, glucose, BP, triglycerides, HDL) predicting binary MetS status. Report odds ratio, 95 % CI, and p‑value in `univariate_logistic_results.csv`.

### 6. Multivariate Logistic Regression (FR‑005, FR‑006)
**Conditional** on ≥ 100 donors with complete binary labels. Fit an L2‑regularized (λ = 1.0) logistic model using **≤ 10** most variable core genes (selected **inside** each training fold) plus age, sex, tissue, Time‑of‑Death, and batch. Perform cross‑validation with multiple folds; report mean AUC and 95 % CI in `cv_performance.csv`. Apply DeLong test vs. baseline (FR‑023).  

### 7. Batch‑Effect Sensitivity (FR‑015)
Refit the multivariate logistic model with and without the batch covariate; compute coefficient stability. Report stability ≥ 90 % as required; otherwise flag instability.

### 8. External Validation (FR‑010)
Planned but **not executable** until a verified MESA muscle RNA‑seq + phenotype dataset is available. The pipeline will automatically run the DE and logistic pipelines on MESA and generate `validation_results.csv` when the data become accessible.

### 9. Power Analysis (FR‑011)
A priori power calculations for ANCOVA (f = 0.25), logistic regression (odds‑ratio = 1.5), and correlation (r = 0.3) using `statsmodels.stats.power`. Results stored in `power_summary.csv`; if power < 0.80, `study_status` is set to `exploratory` with a warning.

### 10. Diagnostics & Figures (FR‑008)
Generate heatmaps of DE results, ROC curves for the logistic model (when fitted), and scatter plots for significant gene‑trait correlations. All figures reference rows in the corresponding CSV files.

### 11. Success Metrics Consolidation
All SC‑related numbers are collated into `success_metrics.csv` (counts, proportions, power, stability). Files are validated against `output.schema.yaml`.

## Statistical Rigor

- **Multiple‑Testing**: Global Benjamini‑Hochberg FDR (q < 0.05) across all gene‑tissue or gene‑trait tests.  
- **Power**: Explicit a priori calculations; study flagged exploratory if power < 0.80.  
- **Causality**: All results are strictly **associational**; observational nature is emphasized.  
- **Collinearity**: VIF computed for all logistic predictors; predictors with VIF > 5 are flagged (FR‑009, FR‑015).  
- **Model Assumptions**: Normality checks (Shapiro‑Wilk) guide choice of Pearson vs. Spearman; mixed‑effects models account for tissue‑level random effects.
