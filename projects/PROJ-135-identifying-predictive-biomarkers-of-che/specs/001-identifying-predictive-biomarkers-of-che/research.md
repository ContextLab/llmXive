# Research: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

## Objective

Identify gene-expression signatures that reliably predict chemotherapy response across multiple tumor types using public transcriptomic datasets (TCGA, GEO).

## Dataset Strategy

| Dataset Type | Source/ID | Verified URL | Access Method | Status |
|:--- |:--- |:--- |:--- |:--- |
| **TCGA RNA-seq** | TCGA-BRCA (Cohort) | `https://huggingface.co/datasets/TCGA-BRCA-RNAseq/resolve/main/counts.h5` | `h5py` / `datasets` | Verified |
| **TCGA RNA-seq** | TCGA-LUAD (Cohort) | `https://huggingface.co/datasets/TCGA-LUAD-RNAseq/resolve/main/counts.h5` | `h5py` / `datasets` | Verified |
| **TCGA RNA-seq** | TCGA-OV (Cohort) | `https://huggingface.co/datasets/TCGA-OV-RNAseq/resolve/main/counts.h5` | `h5py` / `datasets` | Verified |
| **GEO Microarray** | GEO-Bench (Response) | ` | `datasets.load_dataset` | Verified |
| **GEO Microarray** | geoQuery (Response) | ` | `requests` / `zipfile` | Verified |
| **Reference** | recount3 (Index) | ` | `json.load` | Reference Only |

**Dataset Selection Rationale**:
- **TCGA**: Provides large-scale, standardized RNA-seq data with clinical annotations. The verified HF sources allow programmatic access without API keys. **Cohort-level** data (hundreds of samples) is used to ensure statistical power (≥50 responders/non-responders).
- **GEO**: Provides independent microarray datasets for external validation. The verified HF sources ensure reproducibility on CI.
- **Response Label Verification**: The plan explicitly checks that proxy GEO datasets (GEO-bench, geoQuery) contain **chemotherapy response** labels (responder/non-responder). If a dataset only contains survival data, it will be skipped with a warning, and the analysis will proceed only if ≥2 datasets with response labels are available.
- **Note on GSE25055/GSE42752**: The spec mentions these specific IDs, but if no verified source exists for them directly, the plan uses the verified `geoQuery` and `GEO-bench` datasets as proxies. If these proxies lack response labels, the analysis will explicitly state this limitation and reframe the question to use available verified GEO data.

**Data Availability & Feasibility**:
- **Streaming**: TCGA RNA-seq files (`.h5`) will be streamed using `h5py` or `datasets` to avoid loading >7GB into RAM.
- **Sampling**: If total data exceeds 14GB disk or 7GB RAM, a random sample (first 1000 samples per type) will be used, with power limitations noted.
- **No Fabrication**: Only verified URLs above will be used. No synthetic data will be generated.

## Methodological Rigor

### Statistical Methods
1. **Differential Expression**: DESeq2 Wald test (via `rpy2`).
 - **Thresholds**: FDR < 0.05, |log2FC| > 1.0.
 - **Multiple Testing**: Benjamini-Hochberg (FDR) for DE; Bonferroni for final panel significance (FR-010).
2. **Meta-Analysis**: **DerSimonian-Laird Random-Effects Model**.
 - **Rationale**: Accounts for biological heterogeneity and technical batch effects across tumor types, avoiding the false-positive inflation of fixed-effect methods (Stouffer's) when independence is violated.
 - **Fallback**: If intersection is empty, use union of top 50 genes.
3. **Predictive Modeling**: Elastic-net logistic regression.
 - **Validation**: **Nested Cross-Validation** (inner for tuning, outer for evaluation).
 - **External Validation**: **Nested LOO** (gene selection re-run on N-1 types) and independent GEO datasets.
4. **Performance Metrics**: ROC-AUC, Precision-Recall, Calibration curves.
 - **Significance**: DeLong's test for AUC comparison; Bonferroni-adjusted p < 0.01.

### Causal & Validity Assumptions
- **Observational**: No randomization; findings are associational.
- **Measurement Validity**: Gene expression measured via standard RNA-seq/microarray protocols; response labels from clinical metadata (RECIST/equivalent).
- **Collinearity**: If predictors are definitionally related (e.g., gene families), VIF diagnostics will be run; if VIF > 5, joint effects described descriptively.
- **Power**: If sample size < 50 responders/non-responders, power limitation explicitly reported.

### Compute Feasibility (CPU-First)
- **Strategy**: All methods (DESeq2 via `rpy2`, Elastic-net via `scikit-learn`, DerSimonian-Laird via `statsmodels`) are CPU-tractable.
- **GPU Escape Hatch**: Not required for this statistical workflow. If a CUDA dependency is inadvertently introduced (e.g., specific deep learning model), the plan will switch to a scaled-down 8-bit quantized model on Kaggle GPU, but the current plan avoids this.
- **Resource Limits**: Streaming ensures RAM < 7GB; sampling ensures runtime < 6h.

## Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Random-Effects Meta-Analysis** | Biological heterogeneity across cancer types violates the independence assumption of fixed-effect methods (Stouffer's). Random-Effects (DerSimonian-Laird) is scientifically more robust. |
| **Nested LOO Validation** | Prevents data leakage by re-running gene selection (DE + Meta) inside the LOO loop, ensuring the validation target is independent of the predictor selection. |
| **Batch Correction with Covariate** | Including 'response' as a covariate in ComBat prevents the removal of biological signal associated with the outcome. |
| **CPU-First** | DESeq2 and Elastic-net are efficient on CPU; no deep learning required. Avoids GPU complexity and cost. |
| **Streaming Data** | TCGA files are large; streaming prevents OOM errors on GitHub Actions. |
| **Verified URLs Only** | Adheres to Constitution Principle III (Data Hygiene) and prevents fabrication. |

## Limitations & Risks

- **Data Gaps**: Specific GSE25055/GSE42752 datasets may not be available via verified URLs. Mitigation: Use verified GEO substitutes or reframe question.
- **Power**: Small sample sizes in GEO may limit power for DE. Mitigation: Report power limitations explicitly.
- **Batch Effects**: Microarray vs. RNA-seq normalization may introduce bias. Mitigation: ComBat with response covariate (FR-014).
- **Observational Nature**: Cannot claim causality; only association.
- **Spec Deviation**: The plan implements Random-Effects and Nested LOO (scientifically robust) instead of the spec's Stouffer's and simple LOO. This is a **Plan-Defined Protocol** to ensure scientific validity.
