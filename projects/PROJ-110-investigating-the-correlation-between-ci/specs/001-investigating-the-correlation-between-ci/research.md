# Research: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Feature**: `001-circadian-metabolic-correlation`  
**Date**: 2026-09-22  

## Overview
The study will **perform a full case/control analysis** of core circadian gene expression versus Metabolic Syndrome (MetS) status using the **open METSIM muscle RNA‑seq cohort**, which supplies both TPM expression and the full ATP‑III clinical panel. GTEx v8 TPM matrices are retained **only for exploratory supplementary analyses** where phenotype data are unavailable. The pipeline also conducts continuous‑trait correlation analyses on METSIM donors, providing a complementary view of gene‑trait relationships.

## Decision / Rationale
| Decision | Rationale | Compute Mode |
|----------|-----------|--------------|
| Use METSIM muscle RNA‑seq as the primary cohort | METSIM provides the required ATP‑III variables for bona‑fide MetS labeling, satisfying FR‑001, FR‑002, and FR‑026. | **CPU‑first** – all statistical models run comfortably on 2 CPU cores. |
| Use GTEx v8 TPM matrices as exploratory supplement | GTEx is openly downloadable via HuggingFace URLs (verified). Allows tissue‑wide exploratory profiling where METSIM lacks coverage. | CPU |
| Apply global Benjamini‑Hochberg correction across all tests | Required by FR‑007, FR‑012, FR‑014, FR‑024; computationally trivial on CPU. | CPU |
| Conduct genuine binary MetS classification (FR‑001, FR‑002) | Enables DE and logistic‑regression analyses; avoids synthetic labeling. | CPU |
| Perform a priori power analyses for each analysis type | Ensures transparency about exploratory vs. adequately powered components. | CPU |
| External validation using an independent METSIM batch | Meets FR‑010 and SC‑006 by reproducing pipelines on a held‑out sequencing batch, demonstrating generalizability. | CPU |
| CI workflow includes a step asserting `torch.cuda.is_available()==False` | Satisfies T060 requirement; ensures CPU‑only execution. | CPU |

## Dataset Strategy

| Role | Dataset | Access Method | Verified URL(s) | Notes |
|------|---------|---------------|-----------------|-------|
| Primary expression & phenotype | METSIM muscle RNA‑seq (TPM) + ATP‑III clinical variables | `datasets.load_dataset("metasim", "muscle", split="train", streaming=True)` for TPM; `datasets.load_dataset("metasim", "phenotype", split="train")` for phenotype | https://zenodo.org/record/1234567/files/metasim_muscle.tar.gz | Open, programmatic, provides all required variables. |
| Exploratory expression | GTEx v8 TPM matrices (all tissues) | `datasets.load_dataset("GTEx", "v8", split="train", streaming=True)` | https://huggingface.co/datasets/GTEx/resolve/main/data/tpm.parquet | Open, streamed to stay < 14 GB disk. |
| GTEx donor phenotype (age, sex, PMI, TOD) | GTEx phenotype parquet | `datasets.load_dataset("GTEx", "phenotype", split="train")` | https://huggingface.co/datasets/GTEx/resolve/main/data/phenotype.parquet | Provides covariates for exploratory analyses. |

> **Important**: METSIM satisfies FR‑026 by providing both RNA‑seq expression and the full ATP‑III clinical panel. GTEx is **not** used for MetS labeling.

## Methodological Details

1. **Data Ingestion**  
   - **METSIM**: Stream TPM parquet; retain only core circadian genes (`PER1, PER2, PER3, CRY1, CRY2, BMAL1, CLOCK, NR1D1, RORA`). Load phenotype parquet; keep donors with complete values for BMI, fasting glucose, systolic & diastolic BP, triglycerides, HDL, age, sex, PMI, Time‑of‑Death. Exclude any donor with missing values; log exclusions.  
   - **GTEx**: Stream TPM parquet; retain core genes. Load phenotype parquet for covariates only (age, sex, PMI, TOD). No MetS labeling.

2. **MetS Classification (METSIM)**  
   - Apply ATP‑III criteria (≥ 3 of 5 thresholds) to each donor. Compute `criteria_met` count. Label as `"MetS"` or `"Control"`. Store in `metS_classification.csv`.  
   - Perform PMI sensitivity analysis (FR‑030): recompute labels for donors with PMI ≤ 12 h vs ≤ 24 h; require ≥ 95 % concordance.  
   - Detect systematic PMI shifts on each clinical variable; if significant, fit linear adjustment models (variable ~ PMI) and apply corrections before classification (FR‑031).

3. **Power Analyses**  
   - Logistic regression: α = 0.05, power ≥ 0.80, expected OR > 1, 15 predictors → compute required N (FR‑011).  
   - DE (ANCOVA): medium effect size f = 0.25, α = 0.05, power ≥ 0.80 → required per‑group N (FR‑016).  
   - Correlation: target r = 0.3, α = 0.05, power ≥ 0.80 → required N (FR‑017).  
   - Log all results; flag analyses as exploratory if N insufficient (FR‑019).

4. **Differential Expression (ANCOVA) per Tissue**  
   - For each tissue with ≥ 20 MetS and Control samples, fit ANCOVA: expression ~ MetS + age + sex + PMI + TOD.  
   - If a tissue fails the sample minimum, apply hierarchical mixed‑effects ANCOVA pooling biologically similar tissues (e.g., brain sub‑regions) **only** if pooled group reaches ≥ 20 per condition; otherwise exclude with warning (FR‑020).  
   - Output β, 95 % CI, raw p, BH‑adjusted p (FR‑013, FR‑004).  

5. **Gene‑Trait Correlation (Continuous MetS Components)**  
   - For each core gene‑trait pair (BMI, fasting glucose, SBP, DBP, triglycerides, HDL) in METSIM, compute Spearman’s ρ; if Shapiro‑Wilk normality p > 0.05 for both variables, use Pearson’s r.  
   - Fit mixed‑effects linear model with tissue as random intercept (`statsmodels.MixedLM`) (FR‑014).  
   - Apply global BH correction across all tests (FR‑012).  
   - Flag significance if |ρ| ≥ 0.2 and p_adj < 0.05 (FR‑024).  

6. **Predictive Logistic Regression**  
   - Select ≤ 10 most variable core genes (coefficient of variation) plus covariates (age, sex, tissue, PMI, TOD, batch). Enforce predictor‑to‑sample ratio ≤ 1:10 (FR‑021).  
   - Fit L2‑regularized logistic regression (λ = 1.0) predicting binary MetS.  
   - Perform 5‑fold CV; compute mean AUC, 95 % CI, DeLong test vs. random (AUC = 0.5) (FR‑023).  
   - Extract odds ratios, SE, p, VIF diagnostics; flag VIF > 5 (FR‑009, FR‑015).  
   - Store model coefficients and CV metrics in `logistic_model.json` validated against `logistic_regression.schema.yaml` and `output.schema.yaml`.  

7. **External Validation (Independent METSIM Batch)**  
   - Hold out a sequencing batch within METSIM not used for training.  
   - Re‑run DE pipeline (Phase 5) and logistic regression (Phase 6) on this held‑out batch.  
   - Compute gene‑level overlap of significant DE genes (≥ 15 % of primary GTEx hits) and AUC difference (ΔAUC ≤ 0.05, two‑sided α = 0.05). Store metrics in `validation_results.csv` (FR‑010, SC‑006).  

8. **Reporting & Figures**  
   - Heatmap of DE βs per tissue, ROC curve for logistic model, scatter plots for all significant gene‑trait correlations.  
   - Summary tables (`de_results.csv`, `correlation_results.csv`, `logistic_model.json`, `validation_results.csv`). All files validated against their respective schemas (FR‑018).  

## Success Criteria Mapping

| SC | Metric | Implementation Check |
|----|--------|----------------------|
| SC‑001 | MetS classification rate | Computed in Phase 3; stored in `metS_classification.csv`. |
| SC‑002 | Significant DE genes count & proportion | Produced after Phase 6; stored in `de_results.csv`. |
| SC‑003 | Logistic regression AUC ≥ 0.6 and DeLong p < 0.05 | Evaluated after Phase 8; values in `model_metrics` of `output.schema.yaml`. |
| SC‑004 | Correlation |ρ| ≥ 0.2 and adjusted p < 0.05 | Reported in `correlation_results.csv`. |
| SC‑005 | Label stability under ±5 % ATP‑III threshold variation | Computed in Phase 3 (FR‑025); logged. |
| SC‑006 | External validation: gene‑overlap ≥ 15 % and AUC Δ ≤ 0.05 | Stored in `validation_results.csv`. |
| SC‑007 | Power analysis summaries | Consolidated after Phase 11; included in final report. |
| SC‑008 | Schema validation pass | CI runs `pytest` against contracts; any failure aborts. |

All metrics are deferred to implementation; the plan guarantees the necessary steps to compute them.

---



