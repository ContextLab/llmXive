# Research: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

## 1. Domain Context & Problem Statement

Chemotherapy resistance remains a major barrier in oncology. While gene expression signatures have shown promise in specific tumor types (e.g., breast cancer), there is a lack of robust, cross-tumor biomarkers. This project addresses the user question: *"Which gene‑expression signatures derived from publicly available cancer transcriptomic datasets can reliably predict patient response to standard chemotherapeutic agents across multiple tumor types?"*

The challenge lies in integrating heterogeneous data (TCGA RNA-seq, GEO microarrays), handling missing clinical annotations, and ensuring statistical rigor in a low-compute environment.

## 2. Dataset Strategy

The plan relies exclusively on datasets verified in the "Verified datasets" block.

| Dataset Type | Source/ID | Verified URL(s) | Usage in Plan | Constraints/Notes |
|:--- |:--- |:--- |:--- |:--- |
| **TCGA RNA-seq** | TCGA (HDF5) | `<br>`<br>` | Primary discovery cohort. Used for differential expression and model training. | **Critical Gap**: The verified URLs provided are for WSI (Whole Slide Imaging) features or specific metadata, not the full RNA-seq HTSeq-Counts required by FR-001. **Action**: The pipeline MUST use the `TCGAbiolinks` R package (via `rpy2`) to fetch *actual* RNA-seq counts from the GDC API, using the HuggingFace URLs only for metadata verification. If GDC access is blocked, the pipeline halts with `NoValidTCGACohort`. **Construct Validity**: If `response_label` is missing, the pipeline attempts to derive it from survival data (PFS/OS < median) and flags `prognostic_vs_predictive: "proxy"`. |
| **GEO Microarray** | GEO (Parquet) | `<br>` | External validation cohorts. Used to test generalizability (FR-008). | **Critical Gap**: The verified URLs are for QA tasks or generic geoquery tables, not the specific response-annotated datasets GSE25055/GSE42752 mentioned in the spec. **Action**: The pipeline will attempt to download GSE25055/GSE42752 via `GEOquery` (R) or `geodatsets` (Python). If these specific datasets are unavailable or lack response labels, the pipeline attempts to find alternative GEO datasets with response labels from the same study group. If no valid labels or proxies exist in ≥2 datasets, the pipeline halts with `NoValidValidationCohort`. |
| **Reference Genes** | HGNC / Ensembl | N/A (Standard DB) | Identifier harmonization (FR-003). | Use `mygene` or `biopython` to map Ensembl/Entrez to HGNC. |

**Dataset Fit Analysis**:
- **Missing Variables**: The verified TCGA URLs provided are for *WSI features* (image data), not *RNA-seq counts*. This is a **fatal mismatch** for the core requirement (FR-001) which demands RNA-seq HTSeq-Counts.
- **Resolution**: The implementation MUST use the `TCGAbiolinks` R package to programmatically fetch RNA-seq counts from the GDC API. The "Verified datasets" block URLs will be used only for metadata verification or as a secondary source if the GDC API is inaccessible. If GDC access is blocked on GH Actions, the project will fail the "Data Availability" gate.
- **Missing Response Labels**: The verified GEO URLs do not explicitly confirm the presence of GSE25055/GSE42752. The pipeline must query these specific IDs. If they are not found or lack response labels, the pipeline will skip them and log a warning, proceeding only if at least 2 valid validation cohorts exist (with survival proxy fallback).

## 3. Methodological Rigor

### 3.1 Differential Expression (DE)
- **Method**: DESeq2 Wald test (via `rpy2` in a separate R process with memory limits).
- **Thresholds**: FDR < 0.05, |log2FC| > 1.0 (Constitution Principle VII).
- **Multiple Testing**: Benjamini-Hochberg (FDR) for DE; Bonferroni correction for final panel significance (FR-010).
- **Collinearity**: VIF check. If VIF > 5, predictors are described jointly, not as independent effects (Assumption).

### 3.2 Meta-Analysis (LOO-Blind)
- **Method**: **Random-Effects Meta-Analysis (REML)** to account for correlation between tumor types (addresses methodology-6afa132a).
- **Protocol**: For each LOO iteration, the meta-analysis is performed ONLY on the N-1 tumor types (excluding the held-out type). This prevents circular validation (addresses scientific_soundness-c0fd5455, scientific_soundness-4e01e56d).
- **Fallback**: If intersection of significant genes is empty, use union of top 50 ranked genes (FR-006). **Mandatory Flag**: `fallback_reason: "intersection_empty"`.

### 3.3 Predictive Modeling
- **Model**: Elastic-net logistic regression (`sklearn.linear_model.LogisticRegressionCV`).
- **Validation**: Nested Cross-Validation (5-fold outer, 5-fold inner) for hyperparameter tuning (FR-07).
- **Leave-One-Cancer-Type-Out (LOO)**:
 - **Pre-check**: If `N_tumor_types < 3`, halt with `ValidationError` (Resolves T033). **Alternative**: If LOO invalid, switch to 'Nested CV within largest cohort' or 'External GEO-only validation'.
 - **Execution**: Train on `N-1` types, test on held-out type.
- **External Validation**: Apply model to GEO datasets (after **ComBat** alignment for continuous data).

### 3.4 Statistical Significance
- **Metrics**: ROC-AUC, Precision-Recall, Calibration.
- **Thresholds**: AUC ≥ 0.75 (SC-001); Bonferroni-adjusted p < 0.01 (SC-002).
- **DeLong's Test**: Compare model vs. clinical covariates-only baseline (FR-011).
- **Calibration**: Deciles with N ≥ 20 must align within ±10%. N < 20 flagged as underpowered.

## 4. Compute Feasibility & Data Handling

### 4.1 CPU-First Strategy
- **Streaming**: Use `datasets.load_dataset(..., streaming=True)` for large TCGA files to stay within 7GB RAM.
- **Separate R Process**: DESeq2 is executed in a separate R process (via `rpy2` with explicit memory limits) to avoid OOM in the Python process.
- **Sampling**: If full dataset > 14GB disk, use a fixed-seed random sample (e.g., first 1000 samples per tumor type) and report power limitation.
- **Libraries**: `scikit-learn`, `statsmodels`, `rpy2` (for DESeq2) run efficiently on 2 CPU cores.

### 4.2 GPU Escape Hatch (Not Required)
- No transformer or diffusion models are planned. Elastic-net and DESeq2 are CPU-tractable. No GPU offload needed.

### 4.3 Data Availability
- **Open Data**: TCGA and GEO are publicly accessible via API.
- **Gated Data**: If GSE25055/GSE42752 require dbGaP access, the pipeline will skip them and report `NoValidValidationCohort`. No synthetic data will be generated.
- **Construct Validity**: If response labels are missing, the pipeline attempts to use survival proxies (PFS/OS) with a `prognostic_vs_predictive: "proxy"` flag. If no valid labels or proxies exist, it halts.

## 5. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Use R via rpy2 for DESeq2** | DESeq2 is the gold standard for RNA-seq DE. Python alternatives (e.g., `pyDESeq2`) are less mature. `rpy2` allows seamless integration in Python pipeline. |
| **Separate R Process** | Prevents OOM in the Python process by isolating DESeq2 memory usage. |
| **LOO-Blind Meta-Analysis** | Ensures the held-out tumor type is not used in feature selection, preventing circular validation and tautological generalizability claims. |
| **Random-Effects Meta-Analysis (REML)** | Accounts for biological correlation between tumor types, unlike Stouffer's method which assumes independence. |
| **Fallback to Union of Top Genes** | Intersection of significant genes across heterogeneous tumors is often empty. Union of top 50 ensures a viable panel for modeling while flagging the anomaly. |
| **Pre-check for LOO** | Prevents invalid execution paths (T033 resolution) and ensures statistical validity of cross-tumor generalizability claims. |
| **Stream Data** | Essential for fitting within 7GB RAM on GH Actions. Avoids loading full matrices into memory. |
| **ComBat for Continuous Data** | Corrects batch effects for VST-transformed (continuous) data. ComBat-seq is for counts and is inappropriate here. |
