# Research: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Background
Metabolic Syndrome (MetS) is a cluster of cardiometabolic risk factors (BMI, fasting glucose, hypertension, triglycerides, low HDL). The ATP‑III clinical guideline defines MetS as meeting ≥ 3 of these thresholds. Circadian clock genes (e.g., **PER1‑3**, **BMAL1**, **CLOCK**, **NR1D1**, **RORα**) regulate metabolic pathways; dysregulation may contribute to MetS. **MESA** is an open cohort that provides blood RNA‑seq TPM matrices together with full ATP‑III clinical measurements, making it suitable for primary analysis. GTEx release supplies bulk RNA‑seq across many solid tissues but lacks the required clinical variables; it will be used only for exploratory tissue‑level expression without MetS labels.

## Dataset Strategy

| Role | Dataset | Source URL (Verified) | Loader | Variables Needed |
|------|---------|-----------------------|--------|------------------|
| Primary expression & phenotype | MESA RNA‑seq TPM & MetS phenotype | `https://huggingface.co/datasets/MESA2025/mesa/resolve/main/device_1/music/rD9E2aF8K4.json` | `datasets.load_dataset("MESA2025/mesa", split="train")` | TPM for all genes, donor ID, age, sex, tissue (blood), BMI, fasting glucose, systolic/diastolic BP, triglycerides, HDL |
| Exploratory tissue expression | GTEx v8 TPM matrices (no MetS phenotypes) | `https://huggingface.co/datasets/CNX-PathLLM/GTEx-WSI-Description/resolve/main/data/test-00000-of-00001.parquet` | `datasets.load_dataset("CNX-PathLLM/GTEx-WSI-Description", split="train", streaming=False)` | TPM for all genes, donor ID, age, sex, tissue, PMI, Time‑of‑Death (phenotypes for DE covariates) |
| Optional supplement (if needed) | **None** – no open dataset provides the missing ATP‑III variables for GTEx. | – | – | – |

*All datasets are programmatically downloadable; no manual login required.*

## Decision / Rationale
- **CPU‑first**: All statistical models (ANCOVA, mixed‑effects, logistic regression) are classical methods that run efficiently on CPU. No deep‑learning or GPU‑required components are needed, satisfying the compute feasibility constraint.
- **Construct Validity**: ATP‑III thresholds were defined for clinical, in‑vivo measurements. Post‑mortem variables (BMI, glucose, BP, lipids) may be altered by tissue degradation; therefore MetS classification is performed **only on the living‑cohort MESA**. GTEx donors are used solely for exploratory expression analyses without MetS labeling.
- **Missing Data Handling**: Any donor missing *any* of the five ATP‑III variables in MESA is excluded (FR‑001). Missing covariates (age, sex, PMI, TOD) also trigger exclusion with a logged warning. GTEx donors lacking ATP‑III variables are flagged as “exploratory only” and used only for tissue‑level expression analyses.
- **Multiple‑Testing**: Global Benjamini‑Hochberg across *all* gene‑tissue tests (DE) and across *all* gene‑trait correlation tests (FR‑004, FR‑012). This meets the specification and protects the family‑wise error rate.
- **Power Analysis**: Conducted prior to modeling (FR‑011) for (a) logistic regression (binary MetS) using `statsmodels.stats.power.NormalIndPower`; (b) DE (ANCOVA) using Bonferroni‑adjusted α across all tests; (c) correlation tests using effect‑size estimates. If required N > available N, `study_status=exploratory` is set and the limitation documented.
- **Causal Claims**: All statements will be framed as *associational* because the data are observational (no randomization). The logistic model predicts MetS status but does not infer causality.
- **Predictor Independence**: Metabolic traits are **not** used as predictors in the primary logistic model to avoid circularity (addresses SC‑009). An auxiliary traits‑only model is run solely for reporting odds ratios of the clinical variables (FR‑009).

## Methodology Overview

1. **Data Ingestion**  
   - Download MESA and GTEx datasets via `datasets.load_dataset`.  
   - Verify SHA‑256 checksums recorded in `data/checksums.txt`.  

2. **Phenotype Cleaning & MetS Classification** (FR‑001, FR‑002, SC‑005)  
   - Apply ATP‑III thresholds:  
     - BMI ≥ 30 kg/m²  
     - Fasting glucose ≥ 100 mg/dL  
     - Systolic BP ≥ 130 mmHg **or** Diastolic BP ≥ 85 mmHg  
     - Triglycerides ≥ 150 mg/dL  
     - HDL < 40 mg/dL (men) or < 50 mg/dL (women)  
   - Count criteria met; label **MetS** if count ≥ 3, else **Control**.  
   - Compute a continuous severity score = number of criteria met (0‑5).  
   - Perform a **±5 % threshold sensitivity analysis**; require ≥ 90 % label stability (SC‑005).  

3. **Exploratory GTEx Phenotype Check** (Phase 1a)  
   - Verify presence of ATP‑III variables; if absent, flag GTEx as exploratory only (no MetS label).  

4. **Differential Expression (Hierarchical ANCOVA)** (FR‑003, FR‑013)  
   - For each tissue with ≥ 10 MetS and ≥ 10 Control donors (MESA blood) or ≥ 10 donors per group (GTEx exploratory), fit a hierarchical mixed‑effects ANCOVA:  
     `TPM_gene ~ MetS + age + sex + PMI + TOD + (1|tissue)` using `statsmodels.MixedLM`.  
   - Extract β for MetS, 95 % CI, raw p‑value.  

5. **Global FDR Correction (DE)** (FR‑004)  
   - Concatenate all raw p‑values across gene‑tissue tests; apply `statsmodels.stats.multitest.multipletests(method='fdr_bh')`.  

6. **Gene‑Trait Correlation** (FR‑007, FR‑014)  
   - For each (gene, trait) pair test normality of both variables with Shapiro‑Wilk.  
   - Use Spearman ρ unless both are normal (p > 0.05) → use Pearson r.  
   - Fit mixed‑effects model: `trait ~ gene_expression + (1|tissue)` using `statsmodels.MixedLM`.  
   - Compute empirical p‑values via 10 000 permutations; apply global BH (FR‑012).  
   - Report ρ, raw p‑value, and BH‑adjusted p‑value; significance evaluated against null ρ = 0 (SC‑004).  

7. **Predictive Logistic Regression (Primary)** (FR‑005, FR‑009)  
   - Features: log‑TPM of core circadian genes + age + sex + tissue (one‑hot) + PMI + TOD + sequencing batch.  
   - Compute VIF; if VIF > 5, automatically switch to ridge (`C=1.0`).  
   - Optionally retain top 5 genes by variance to keep predictor‑to‑sample ratio safe.  
   - Fit `LogisticRegression(penalty='none', solver='lbfgs')` via scikit‑learn.  
   - Convert coefficients to odds ratios, compute 95 % CI using Wald test.  

8. **Auxiliary Traits‑Only Model** (FR‑009)  
   - Fit a logistic model with only the five ATP‑III clinical traits to report their odds ratios for MetS prediction (no gene predictors).  

9. **Cross‑Validation & Baseline AUC** (FR‑006, SC‑003)  
   - Stratified k‑fold CV preserving MetS proportion.  
   - Compute AUC per fold (`sklearn.metrics.roc_auc_score`).  
   - Compare against random classifier (AUC = 0.5); report ΔAUC and a two‑sided DeLong test (p‑value).  

10. **Batch‑Effect Sensitivity** (FR‑015)  
    - Re‑fit logistic model without `batch` covariate.  
    - Compute Pearson correlation between coefficient vectors; require ≥ 0.90 stability.  

11. **Power Analysis (Logistic, DE, Correlation)** (FR‑011)  
    - Logistic: α = 0.05, power = 0.80, expected OR ≈ 1.5, predictors ≈ 15 → required N.  
    - DE: Bonferroni‑adjusted α across all gene‑tissue tests; estimate detectable β given observed variance.  
    - Correlation: α = 0.05, power = 0.80, target ρ = 0.2 → required N.  
    - Record required vs. available N; set `study_status` flag accordingly.  

12. **External Validation (MESA Blood)** (FR‑010, SC‑006)  
    - Replicate DE (Phase 2–3) **on MESA whole‑blood samples** only.  
    - Compute overlap = |MESA ∩ GTEx‑Blood significant genes| / |GTEx‑Blood significant genes| (must be ≥ 30 %).  
    - Apply trained primary logistic model to an independent MESA validation split; report AUC difference (ΔAUC ≤ 0.05, DeLong test).  

13. **Diagnostics & Figures** (FR‑008, FR‑009)  
   - Heatmap of DE β values (seaborn clustermap).  
   - ROC curves for each CV fold plus baseline; display ΔAUC and DeLong p‑value.  
   - Scatter plots for significant gene‑trait correlations with regression line and permutation‑derived confidence bands.  
   - Compute and report **SC‑002**: proportion of core circadian genes with FDR‑adjusted p < 0.05 across all tissues.  

## Statistical Rigor Checklist
| Requirement | Implementation |
|-------------|----------------|
| Multiple‑comparison correction | Global BH FDR for DE, correlation, and model coefficient significance (FR‑004, FR‑012). |
| Power justification | A priori power analyses for logistic regression, DE, and correlation (Phase 5). |
| Causal inference | Explicitly state all findings are associational; no causal claims beyond observed associations. |
| Measurement validity | ATP‑III criteria sourced from NCEP Adult Treatment Panel III (2001). Gene expression measured as TPM (standardized). |
| Predictor collinearity | Compute Variance Inflation Factor (VIF) for all predictors; flag VIF > 5 and switch to ridge regularization. |

---

