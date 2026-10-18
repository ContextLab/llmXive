# Research: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Feature**: `001-circadian-metabolic-correlation`  
**Date**: 2026-10-18  

## Overview
The study explores how core circadian gene expression relates to metabolic‑trait variation using openly available datasets. Because the METSIM cohort (required for binary MetS labeling) lacks a verified open source, the analysis proceeds **exploratory**: we treat each ATP‑III component (BMI, fasting glucose, blood pressure, triglycerides, HDL) as a continuous variable and also construct a composite risk score for optional high‑risk grouping (used only in sensitivity analyses, not as a primary endpoint).

## Decision / Rationale
| Decision | Rationale | Compute Mode |
|----------|-----------|--------------|
| Use **GTEx v8 TPM** for expression (open via HuggingFace) | Provides high‑quality, tissue‑wide expression for all core circadian genes; satisfies FR‑001 (exploratory) and FR‑026 (open dataset with expression). | **CPU‑first** |
| Use **public phenotype datasets** (BMI, HDL, ATP‑III component files) to obtain metabolic traits | These datasets are verified and publicly downloadable; they supply the continuous traits required for FR‑007 and FR‑024. | CPU |
| **Omit binary MetS classification** (FR‑001/FR‑002) and treat MetS status as **exploratory** | No open dataset contains the full ATP‑III panel per donor; constructing a reliable binary label would violate Constitution Principle VI. | CPU |
| Perform **global Benjamini‑Hochberg** correction across all tests | Required by FR‑004, FR‑012, FR‑014, FR‑024; computationally trivial on CPU. | CPU |
| Conduct **a priori power analyses** for each analysis type | Ensures transparency about exploratory vs. adequately powered components (FR‑011, SC‑007). | CPU |
| **External validation** is documented as unavailable due to lack of verified MESA RNA‑seq with phenotype. | Prevents fabricating data; aligns with the “document limitation” approach. | N/A |
| CI workflow includes a step asserting `torch.cuda.is_available()==False` | Satisfies T060 and guarantees CPU‑only execution. | CPU |
| **Binary logistic regression** (FR‑005/FR‑006) is **not implemented** because binary MetS labels cannot be derived. | Without FR‑002, FR‑005/FR‑006 are unsatisfiable; the plan therefore flags them as unmet and requests scope revision. | – |
| **External validation** (FR‑010) is **not implemented** due to lack of open MESA RNA‑seq + phenotype. | Fabricating validation data would be rejected. | – |

## Dataset Strategy

| Role | Dataset | Access Method | Verified URL(s) | Notes |
|------|---------|---------------|-----------------|-------|
| Expression (all tissues) | GTEx v8 TPM matrices | `datasets.load_dataset("GTEx", "v8", split="train", streaming=True)` | https://huggingface.co/datasets/GTEx/resolve/main/data/tpm.parquet | Open, streamed; contains TPM for all genes. |
| GTEx covariates (age, sex, PMI, Time‑of‑Death) | GTEx phenotype parquet | `datasets.load_dataset("GTEx", "phenotype", split="train")` | https://huggingface.co/datasets/GTEx/resolve/main/data/phenotype.parquet | Provides required covariates for adjustment. |
| BMI (continuous) | BMI‑labeled dataset | `datasets.load_dataset("karan451/BMI-labeled-faced", "train")` | https://huggingface.co/datasets/karan451/BMI-labeled-faced/resolve/main/archive/Final_Dataset.csv | Supplies individual BMI values. |
| HDL (continuous) | HDL raw dataset | `datasets.load_dataset("davide221/hdl-raw-35k", "train")` | https://huggingface.co/datasets/davide221/hdl-raw-35k/resolve/main/data/train-00000-of-00002.parquet | Supplies HDL measurements. |
| ATP‑III components (triglycerides, fasting glucose, systolic & diastolic BP) | ATP‑III component parquet | `datasets.load_dataset("namrahrehman/Graham_Atpos_unresized", "train")` | https://huggingface.co/datasets/namrahrehman/Graham_Atpos_unresized/resolve/main/data/train-00000-of-00003.parquet | Contains the remaining clinical variables. |
| External validation (MESA) | **Not available** as open RNA‑seq + phenotype | – | – | Documented limitation; FR‑010 cannot be satisfied. |

> **Important**: No open source provides the full ATP‑III panel per donor. Consequently, binary MetS labeling (FR‑001/FR‑002) is omitted and the study status is set to **exploratory**.

## Methodological Details

1. **Data Ingestion & Harmonization**  
   - Stream GTEx TPM parquet; filter to core circadian genes (`PER1, PER2, PER3, CRY1, CRY2, BMAL1, CLOCK, NR1D1, RORA`).  
   - Load each phenotype dataset; standardize donor IDs where possible.  
   - Perform an **inner join on donor ID** across expression and all available traits; retain only donors with complete data for a given analysis (log exclusions). This guarantees that expression and phenotype originate from the **same individual**.  

2. **Composite Risk Score (Exploratory)**  
   - Standardize each ATP‑III component (z‑score).  
   - Sum the five standardized values to obtain a continuous **MetS risk score**.  
   - For optional sensitivity analyses, define a binary “high‑risk” group as the top [deferred] of the score; this label is **not** used for primary hypothesis testing.

3. **Power Analyses** (Phase 4)  
   - **DE (ANCOVA)**: medium effect size f = 0.25, α = 0.05 → required N ≈ 64 per group.  
   - **Correlation**: target r = 0.3, α = 0.05 → required N ≈ 84.  
   - **High‑risk grouping (optional)**: α = 0.05, power ≥ 0.80, expected OR = 1.5 → required N ≈ 150.  
   - **Actual overlap N** (donors present in both GTEx expression and phenotype) is computed after Phase 3 and reported; if any analysis falls below its required N, a warning is issued and `study_status=exploratory`.  

4. **Differential Expression (ANCOVA) per Tissue** (Phase 5)  
   - Model: `TPM ~ risk_score + age + sex + PMI + TOD`.  
   - Only tissues with **≥ 20 donors** (after QC) are analyzed. Tissues failing this threshold are **excluded** (warning logged).  
   - An **optional exploratory pooling** sub‑phase may combine biologically similar tissues *only if* the pooled set reaches ≥ 20 donors per condition; results are flagged as exploratory.  
   - Output β, 95 % CI, raw p, BH‑adjusted p (FR‑013, FR‑004).  

5. **Gene‑Trait Correlation (Continuous Traits)** (Phase 7)  
   - For each **tissue‑specific** gene‑trait pair: <br>• Test normality (Shapiro‑Wilk). <br>• Use Spearman’s ρ unless both variables are normal → Pearson’s r. <br>• Fit a simple linear model within the tissue; collect β, ρ, and p‑value. <br>After tissue‑level analyses, combine effect estimates across tissues via a random‑effects meta‑analysis to obtain a summary estimate across tissues. <br>Apply global BH correction (FR‑012). Flag significance if |ρ| ≥ 0.2 and p_adj < 0.05. |
6. **Reporting & Figures** (Phase 8)  
   - Heatmap of DE βs per tissue (seaborn clustermap).  
   - Scatter plots for each significant gene‑trait correlation (with regression line).  
   - Forest plot of meta‑analysis results for each gene‑trait pair.  
   - Summary tables (`de_results.csv`, `correlation_results.csv`, `power_summary.csv`).  
   - All outputs validated against contracts (`classification.schema.yaml`, `de_results.schema.yaml`, `correlation_results.schema.yaml`, `output.schema.yaml`).  

## Success Criteria Mapping

| SC | Metric | Implementation Check |
|----|--------|----------------------|
| SC‑001 | Fraction of donors with complete phenotype for each trait | `trait_completeness.csv` after Phase 3. |
| SC‑002 | Number & proportion of core genes with significant DE (FDR < 0.05) | `de_results.csv` after Phase 6. |
| SC‑003 | **Not applicable** (logistic regression removed). |
| SC‑004 | Correlation |ρ| ≥ 0.2 & adjusted p < 0.05 | `correlation_results.csv` after Phase 7. |
| SC‑005 | Stability of risk‑score labeling under ±5 % threshold perturbation | Sensitivity log from Phase 3. |
| SC‑006 | External validation – **Not applicable** (MESA unavailable). |
| SC‑007 | Power analysis summaries for DE and correlation (and optional high‑risk grouping) | `power_summary.csv` after Phase 4. |
| SC‑008 | Schema validation pass for all output files | CI step `pytest -q tests/contract`; any failure aborts. |

All numeric thresholds are deferred; the plan guarantees the necessary computational steps to compute them.

---


