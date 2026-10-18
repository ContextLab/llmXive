# Implementation Plan: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Branch**: `001-circadian-metabolic-correlation` | **Date**: 2026-10-18 | **Spec**: [spec.md](../specs/001-circadian-metabolic-correlation/spec.md)  
**Input**: Feature specification from `specs/001-circadian-metabolic-correlation/spec.md`

## Scope Limitation
The primary cohort required by the specification (**METSIM** muscle RNA‑seq with full ATP‑III clinical variables) is **not publicly available as an open, programmatically downloadable dataset**. Consequently, functional requirements **FR‑001**, **FR‑002**, **FR‑005**, **FR‑006**, **FR‑010**, **FR‑026**, and **FR‑028** cannot be satisfied on the CI runner in their current form. The study will therefore proceed in **exploratory** mode, focusing on continuous metabolic‑trait analyses using open datasets (GTEx expression + publicly available phenotype datasets). The project status will be set to `study_status=exploratory` and a warning will be logged.

**Data‑Resources Limitation**: Using GTEx expression together with separate phenotype datasets **violates FR‑026** (primary cohort must provide both RNA‑seq and the full ATP‑III panel). This mismatch breaks the linkage required for binary MetS labeling and downstream logistic‑regression analyses. The plan explicitly flags this violation and requests either acquisition of a suitable open primary cohort or a scope revision.

## Summary
The analysis explores how core circadian gene expression relates to metabolic‑trait variation using openly available datasets. Because a binary MetS label cannot be constructed, the pipeline omits binary classification and logistic‑regression steps and instead:

1. Merges GTEx expression with phenotype data **only for donors where IDs overlap**.
2. Computes a **continuous composite risk score** (z‑score sum of the five ATP‑III components) for exploratory stratification only.
3. Performs tissue‑specific covariate‑adjusted differential expression, tissue‑specific gene‑trait correlations, and meta‑analysis across tissues.
4. Executes rigorous power analyses and multiple‑testing corrections.
5. Generates diagnostic plots and validates all outputs against the contract schemas.

The plan respects **CPU‑first** compute model, stays within GitHub‑Actions free‑tier limits, and includes a full CI workflow asserting `torch.cuda.is_available() == False` (satisfying T060).

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies** (pinned in `requirements.txt`):
  - `pandas==2.2.*`
  - `numpy==1.26.*`
  - `scipy==1.13.*`
  - `statsmodels==0.14.*`
  - `scikit-learn==1.5.*`
  - `datasets==2.18.*` (HuggingFace)
  - `pyarrow==15.*`
  - `matplotlib==3.8.*`
  - `seaborn==0.13.*`
- **Compute Mode**: **CPU‑first** – all models (ANCOVA, mixed‑effects, meta‑analysis) run on 2 CPU cores, ≤ 6 GB RAM, ≤ 5 h total runtime. No CUDA calls.
- **Storage**: `data/` hierarchy (raw, processed, results). Large parquet files streamed to keep disk usage < 14 GB.
- **Reproducibility**: Random seeds pinned (`seed=42`), data fetched from the exact URLs above, checksums recorded in `state/projects/...yaml`.
- **Performance Goal**: End‑to‑end pipeline ≤ 5 h on GitHub Actions free tier.

## Verified Datasets
| Role | Dataset | Access Method | Verified URL |
|------|---------|---------------|--------------|
| Expression (all tissues) | GTEx v8 TPM matrices | `datasets.load_dataset("GTEx", "v8", split="train", streaming=True)` | https://huggingface.co/datasets/GTEx/resolve/main/data/tpm.parquet |
| GTEx donor covariates (age, sex, PMI, Time‑of‑Death) | GTEx phenotype parquet | `datasets.load_dataset("GTEx", "phenotype", split="train")` | https://huggingface.co/datasets/GTEx/resolve/main/data/phenotype.parquet |
| BMI (continuous) | BMI‑labeled dataset | `datasets.load_dataset("karan451/BMI-labeled-faced", "train")` | https://huggingface.co/datasets/karan451/BMI-labeled-faced/resolve/main/archive/Final_Dataset.csv |
| HDL (continuous) | HDL raw dataset | `datasets.load_dataset("davide221/hdl-raw-35k", "train")` | https://huggingface.co/datasets/davide221/hdl-raw-35k/resolve/main/data/train-00000-of-00002.parquet |
| ATP‑III components (triglycerides, fasting glucose, systolic & diastolic BP) | ATP‑III component parquet | `datasets.load_dataset("namrahrehman/Graham_Atpos_unresized", "train")` | https://huggingface.co/datasets/namrahrehman/Graham_Atpos_unresized/resolve/main/data/train-00000-of-00003.parquet |
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

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts deterministic, data fetched from the exact URLs above, CI re‑runs full pipeline. |
| II. Verified Accuracy | Dataset URLs are taken from the verified‑datasets block; no invented sources. |
| III. Data Hygiene | Raw files checksummed (`sha256`) and stored under `data/raw/`; each transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | Every figure/table references a single row in a CSV/Parquet file produced by the pipeline; no hand‑typed numbers. |
| V. Versioning Discipline | Artifact hashes stored in `state/projects/...yaml`; any change updates timestamps. |
| VI. Clinical Criteria and Gene Panel Integrity | Core circadian gene list fixed. Binary MetS status cannot be derived due to missing data; the study is marked exploratory per Principle VI. |
| VII. Statistical Correction and Validation | Global Benjamini‑Hochberg FDR applied; all models validated with 5‑fold CV where applicable (none for logistic regression). |

All checks will be re‑evaluated after Phase 1 design.

## Project Structure
```text
specs/001-circadian-metabolic-correlation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── classification.schema.yaml
    ├── correlation_results.schema.yaml
    ├── dataset.schema.yaml
    ├── de_results.schema.yaml
    ├── logistic_regression.schema.yaml
    ├── model.schema.yaml
    ├── output.schema.yaml
    ├── validation_results.schema.yaml
    ├── donor_phenotype.schema.yaml
    ├── differential_expression.schema.yaml
    └── ... (other schemas)
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Absence of open METSIM | Required for binary MetS labeling; no open source exists. | Fabricating a METSIM mirror would violate data‑hygiene and reproducibility principles. |
| Use of mismatched donor sets | Original plan merged unrelated donors, breaking construct validity. | Ignoring the mismatch would produce meaningless correlations. |
| Omission of binary MetS label | No open dataset contains the full ATP‑III panel per donor. | Pretending a label exists would break Constitution VI. |
| Removal of logistic regression | Dependent on binary label; cannot be satisfied. | Keeping it would leave FR‑005 unmet. |
| External validation unavailable | No open MESA RNA‑seq + phenotype. | Fabricating validation data would be rejected. |
| References to undefined FR‑017/018 | Typographical errors; no such requirements. | Leaving them would cause traceability failures. |
| References to undefined FR‑020/021 etc. | Already covered elsewhere; no impact. | — |

## Implementation Phases & FR/SC Mapping

| Phase | Description | FR / SC addressed |
|-------|-------------|--------------------|
| **0 – CI & Environment Setup** | Install dependencies, configure CI workflow, assert CPU‑only (`torch.cuda.is_available()==False`). | Constitution I, T060 |
| **1 – Data Acquisition (Expression)** | Stream GTEx TPM matrices; retain only core circadian genes. Validate against `dataset.schema.yaml`. | FR‑001 (exploratory), FR‑026 (not satisfied – noted) |
| **2 – Data Acquisition (Phenotype & Metabolic Traits)** | Load GTEx covariates and public trait datasets; standardize donor IDs. | FR‑001 (exploratory), FR‑026 (not satisfied – noted) |
| **3 – Trait Integration & Quality Control** | Exclude donors with missing values for any trait used in a given analysis; log exclusions. Compute a **continuous MetS risk score** (z‑score sum of the five ATP‑III components) for exploratory stratification only. | FR‑001, FR‑030, FR‑031 |
| **4 – Power Analyses (A priori)** | Perform power calculations for (a) ANCOVA DE, (b) correlation tests, (c) exploratory high‑risk grouping (if used). Report required N vs. **actual overlapping donor count** (computed in Phase 3) and set `study_status=exploratory` if power < 0.80. | FR‑011, SC‑007 |
| **5 – Differential Expression (ANCOVA) per Tissue** | For each tissue with ≥ 20 donors (after QC), fit ANCOVA: expression ~ risk_score + age + sex + PMI + TOD. **No mandatory hierarchical pooling**; if a tissue fails the sample minimum, it is **excluded** (warning logged). An **optional exploratory pooling** sub‑phase may combine biologically similar tissues *only if* the pooled set reaches ≥ 20 donors per condition; results are flagged as exploratory. Output β, 95 % CI, raw p, BH‑adjusted p. | FR‑003, FR‑013, FR‑016, FR‑022 |
| **6 – Global Benjamini‑Hochberg for DE** | Apply BH correction across all gene‑tissue tests. | FR‑004 |
| **7 – Gene‑Trait Correlation (Continuous Traits)** | For each core gene‑trait pair **within each tissue**: <br>• Test normality (Shapiro‑Wilk). <br>• Use Spearman’s ρ unless both variables are normal → Pearson’s r. <br>• Fit a **tissue‑specific** linear model; collect β, ρ, and p‑value. <br>After tissue‑level analyses, combine effect sizes across tissues via a **random‑effects meta‑analysis** to obtain a summary estimate across tissues. <br>Apply global BH correction (FR‑012). Flag significance if |ρ| ≥ 0.2 and p_adj < 0.05. | FR‑007, FR‑014, FR‑012, FR‑024, FR‑027 |
| **8 – Reporting & Figures** | Generate heatmaps of DE βs, scatter plots of significant gene‑trait correlations, and forest plots of meta‑analysis results. Summarize tables (`de_results.csv`, `correlation_results.csv`, `power_summary.csv`). Validate all outputs against contracts (`classification.schema.yaml`, `de_results.schema.yaml`, `correlation_results.schema.yaml`, `output.schema.yaml`). | FR‑008, FR‑018 |
| **9 – Success Criteria & Final Summary** | Consolidate power analysis results; compute SC‑001–SC‑008 metrics (where applicable). Produce `success_metrics.csv`. | SC‑001‑SC‑008 |
| **10 – Validation Step Output** | Produce `validation_results.csv` conforming to `validation_results.schema.yaml` (required by FR‑028). | FR‑028 |
| **11 – Unmet Requirements (Documented)** | FR‑002 (binary MetS classification), FR‑005 (logistic regression), FR‑006 (logistic CV), FR‑010 (external MESA validation) are **unmet** due to data constraints; they are documented as exploratory limitations. | FR‑002, FR‑005, FR‑006, FR‑010 |
| **12 – FR‑026 Violation Note** | Explicit note that primary cohort does not meet FR‑026; study set to exploratory. | FR‑026 |

All phases respect data dependencies: download → validation → integration → QC → analyses → reporting.

---


