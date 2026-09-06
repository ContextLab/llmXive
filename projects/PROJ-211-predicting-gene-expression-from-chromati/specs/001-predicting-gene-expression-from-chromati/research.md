# Research: Predicting Gene Expression from Chromatin Accessibility

## 1. Scientific Rationale

The central hypothesis is that chromatin accessibility, as measured by DNase-seq or ATAC-seq, is a strong predictor of gene expression levels in human cells. While correlation does not imply causation, accessibility is a necessary (though not sufficient) condition for transcription factor binding and subsequent gene activation. This project aims to quantify this predictive power across multiple cell lines, providing a "first-order approximation" of gene regulation.

**Critical Caveat (per Freeman-Dyson)**: Bulk profiles average over cellular heterogeneity. As noted by reviewer Freeman-Dyson, this smooths over the single-cell dynamics that drive differentiation. The results must be interpreted as population-level associations, not cell-specific mechanisms. The models identify statistical associations; no causal claims are made. The design is observational; randomization is not possible in this context.

### 1.1 Biological Context
- **Bulk vs. Single-Cell**: Bulk profiles average over cellular heterogeneity. As noted by reviewer Freeman-Dyson, this smooths over the single-cell dynamics that drive differentiation. The results must be interpreted as population-level associations, not cell-specific mechanisms.
- **Causality**: The models identify statistical associations. No causal claims are made. The design is observational; randomization is not possible in this context.
- **Genomic Scope**: The analysis is limited to ±50kb windows around TSS. Distal enhancers outside this range are not modeled, which may limit predictive accuracy for genes regulated by long-range interactions.
- **Circularity Avoidance**: To avoid validating a known biological coupling (where the promoter is part of the active gene state), the **promoter region (TSS ± 2kb) is excluded** from the predictor features. Only distal regulatory elements within the ±50kb window (excluding the immediate promoter) are used as predictors.

## 2. Dataset Strategy

### 2.1 Data Sources
The project uses the **ENCODE Consortium** dataset, which provides standardized RNA-seq and DNase/ATAC-seq data for multiple human cell lines.

| Dataset | Description | Source | Verified URL |
| :--- | :--- | :--- | :--- |
| ENCODE RNA-seq | Bulk RNA-seq count matrices for GM12878, K562, HMEC, IMR90, HepG2. | ENCODE | https://www.encodeproject.org/ |
| ENCODE DNase/ATAC-seq | Peak calls and signal tracks for the same cell lines. | ENCODE | https://www.encodeproject.org/ |

**Note**: The ENCODE portal requires programmatic access via API or direct file download. The `download_encode.py` script will use the ENCODE API to fetch metadata and download files directly. No credentials are required for public data.

### 2.2 Data Availability & Feasibility
- **Open Access**: ENCODE data is open and directly downloadable. No registration or data-use agreement is required for bulk RNA-seq and DNase-seq data.
- **Size**: The full dataset for multiple cell lines is estimated at several gigabytes. The pipeline will stream data and process it in chunks to stay within 7GB RAM.
- **Streaming Strategy**: The `datasets` library (HuggingFace) or `requests` with chunked reading will be used to avoid loading the entire dataset into memory at once.
- **Sample Size Constraint**: Typical ENCODE experiments provide multiple replicates per cell line. This limits statistical power. The plan includes a **Sample Size Gate** to skip cell lines with N < 4.

### 2.3 Variable Fit
- **Predictors**: Aggregated accessibility signal (sum of peaks) within **200 fixed-width bins** of each gene's TSS (±50kb, excluding TSS ± 2kb).
- **Outcome**: Log-transformed RNA-seq counts (log(counts + 1)).
- **Covariates**: None explicitly modeled; the model assumes accessibility is the primary driver.
- **Verification**: The ENCODE dataset contains both RNA-seq and DNase/ATAC-seq for the required cell lines. No variable mismatch is expected.

## 3. Statistical Methodology

### 3.1 Model Selection
- **Elastic Net**: Chosen for its interpretability (sparse coefficients) and ability to handle correlated predictors (collinearity among nearby peaks).
- **Regularization**: `alpha=0.5` (equal L1/L2 penalty) is fixed per spec. `l1_ratio` will be tuned via **Leave-One-Out Cross-Validation (LOOCV)**.
- **Cross-Validation**: **LOOCV** is used instead of 5-fold CV because N=3-5 samples per cell line makes 5-fold CV mathematically impossible (requires N>=5 for distinct folds). LOOCV maximizes training data usage. The choice of CV methodology is supported by standard statistical texts and the arXiv paper (source: 2507.20048, https://arxiv.org/abs/2507.20048).

### 3.2 Multiple Testing Correction
- **Bonferroni Correction**: Applied to p-values from the **global model fit** across the 5 cell lines (m=5), not to individual genes.
- **Justification**: With 5 cell lines tested, the probability of false positives is high. Bonferroni is conservative but appropriate for this exploratory study. The correction is **not** applied across [deferred] genes because the model is multivariate (predicting expression from multiple bins simultaneously), not a set of [deferred] univariate tests.

### 3.3 Power & Sample Size
- **Limitation**: The number of samples per cell line is limited (typically 3-5 replicates per ENCODE experiment). This limits statistical power.
- **Acknowledgement**: The plan explicitly acknowledges this power limitation. With N=3-5 and P=200 (bins), the model is severely underdetermined (P >> N). Results will be framed as "associations observed in available replicates" rather than definitive effect sizes. R² will be reported with large confidence intervals (via bootstrapping if N>=4) or as descriptive statistics.

### 3.4 Causal Inference Assumptions
- **Observational Design**: The study is purely observational. No randomization or identification strategy is used.
- **Claim Framing**: All claims will be framed as "predictive" or "associational," never causal. The limitations section will explicitly state this.

### 3.5 Measurement Validity
- **Instruments**: ENCODE data is standardized and validated. RNA-seq counts are normalized (TPM/FPKM) and DNase/ATAC-seq peaks are called using standard pipelines.
- **Citation**: ENCODE Consortium provides validation evidence for their data processing pipelines.

### 3.6 Predictor Collinearity
- **Issue**: Peaks within ±50kb of a TSS are highly correlated (definitionally related).
- **Handling**: Instead of reporting individual peak coefficients (which are unstable), the plan reports **bin importance**. Peaks are aggregated into 200 fixed-width bins. The model coefficients represent the aggregate weight of each bin. This reduces collinearity and provides a more stable interpretation of regional regulatory importance.

## 4. Compute Feasibility

### 4.1 CPU-First Approach
- **Method**: Elastic Net is computationally efficient and runs well on CPU.
- **Memory**: Data will be processed in chunks. The feature matrix (200 bins x N_samples) is small. The pipeline uses **gene-by-gene** processing to keep memory usage low (<1GB).
- **Runtime**: Models are trained **serially** on the 2-CPU runner. With the Sample Size Gate (skipping lines with N<4), total runtime is estimated at 3-4 lines * 1.5h = 4.5-6h, fitting within the 6h limit.

### 4.2 GPU Escape Hatch
- **Not Required**: Elastic Net does not require a GPU. No GPU offload is planned.
- **Justification**: The method is faithful to the CPU constraint. No simulation or synthetic stand-in is needed.

## 5. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Elastic Net** | Interpretable, handles collinearity, CPU-efficient, aligns with spec. |
| **LOOCV** | Required due to N=3-5 samples; 5-fold CV is impossible. Supported by arXiv 2507.20048. |
| **Bonferroni (m=5)** | Applied to cell-line level p-values, not gene-level, to avoid over-correction. |
| **200 Bins/Gene** | Reduces P from a high magnitude to a significantly smaller value, making P > N manageable. Avoids per-peak instability. |
| **Promoter Exclusion** | Excludes TSS ± 2kb to avoid circularity (predicting expression from the gene's own promoter). |
| **Serial Execution** | Ensures compliance with 2-CPU constraint; parallelization is disabled. |
| **Sample Size Gate** | Skips lines with N<4 to ensure minimum statistical validity. |

## 6. Limitations & Caveats

- **Bulk vs. Single-Cell**: Results represent population-level averages. Single-cell heterogeneity is not captured.
- **Correlation vs. Causation**: No causal claims are made. The models identify statistical associations.
- **Genomic Scope**: Distal enhancers (>50kb) are not modeled.
- **Sample Size**: Limited replicates per cell line (N=3-5) reduce statistical power and increase variance in R² estimates.
- **Collinearity**: Nearby bins are correlated; independent effects cannot be disentangled.
- **Underdetermined Model**: With N=3-5 and P=200, the model is P >> N. Results are exploratory.
- **Circularity Avoidance**: Promoter region excluded, but distal regulatory elements may still be correlated with promoter activity.