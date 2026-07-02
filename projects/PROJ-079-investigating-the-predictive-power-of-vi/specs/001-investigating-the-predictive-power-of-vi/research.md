# Research: Predictive Modeling of Host Immune Response from Viral Sequence Features

## Domain Overview

The project investigates the relationship between viral genomic characteristics and the host's interferon (IFN) response. The hypothesis is that viral sequence features (e.g., codon usage, GC content, k-mer frequencies, protein stability) contain predictive signals regarding the magnitude of the host immune response.

## Dataset Strategy

**CRITICAL NOTE**: The "Verified datasets" block provided in the user message contains **no** datasets relevant to viral genomics or host transcriptomics (it lists medical imaging and unrelated road data). Consequently, this research plan **cannot** cite those URLs as the primary data source.

Per the project constraints and the "No verified source" rule:
1.  **Viral Genomes**: Will be fetched dynamically from **NCBI Virus** using `biopython` Entrez or `ncbi-genome-download`. The specific accessions will be derived from the metadata of the selected GEO studies.
2.  **Host Transcriptomics**: Will be fetched from **GEO (Gene Expression Omnibus)** using `GEOparse` or direct API calls. The selection of studies will be based on the "Verified datasets" block's *absence* of relevant data, requiring a programmatic search for studies matching "virus infection" AND "human/mouse" AND "transcriptome" keywords, or using a predefined list of high-quality studies if the spec implied specific ones (which it does not, it says "selected GEO studies").
3.  **Fallback**: If the spec implies specific studies (e.g., "the selected GEO studies"), the pipeline must hardcode a list of known relevant GEO Series (e.g., GSE12345) or allow user configuration. Since the provided "Verified datasets" block is irrelevant, the plan assumes the user will provide a configuration file `config/studies.yaml` mapping virus IDs to GEO accessions.

**Dataset Table**:

| Dataset | Source | Access Method | Relevance to Spec | Status |
| :--- | :--- | :--- | :--- | :--- |
| **NCBI Virus Genomes** | NCBI Virus | `biopython.Entrez` | FR-001: Source of ViralGenome | **Programmatic Fetch** (No verified URL in block) |
| **GEO Transcriptomics** | GEO (NCBI) | `GEOparse` | FR-002: Source of HostExpressionSample | **Programmatic Fetch** (No verified URL in block) |
| **Interferome v2.0** | Interferome | `requests` (JSON/CSV) | FR-002: ISG gene set (n=50) | **Public Resource** (Standard set) |
| **Ensembl Compara** | Ensembl | `rpy2` / API | FR-015: Ortholog mapping | **Programmatic Load** |

**Data Volume Estimation**:
-   **Genomes**: A representative sample of viral strains (typical for a focused study). Small data units each. Total < 50MB.
-   **Expression**: ~100 samples. Matrix storage requirements are moderate, typically on the order of megabytes per matrix. Total < 100MB.
- **Features**: k-mers (k=3, 4 only) + stability + CAI. Matrix size ~100 rows x [deferred] columns. ~4MB.
-   **Feasibility**: Well within the RAM and disk limits.

## Feature Engineering Strategy

1.  **Codon Adaptation Index (CAI)**: Calculated relative to a reference set (e.g., highly expressed human genes for human viruses). **Limitation**: This assumes the virus is adapting to human codon usage. For viruses with complex life cycles or multiple hosts, this metric may be confounded by viral taxonomy. The plan will include virus family as a potential covariate if feasible.
2.  **GC Content**: Global and sliding window (region-specific) for k=1000bp.
3.  **k-mer Frequencies**: Counts for **k=3, 4 ONLY**. **Rationale**: The dataset size (N ~ tens of strains) is insufficient to support the dimensionality of k=5 or k=6 (which would yield >100,000 features). Restricting to k=3 and k=4 is a fixed, a priori dimensionality reduction strategy required to make the problem tractable for Elastic Net and Debiased Lasso inference. k=5, 6 are explicitly excluded. Normalized by total k-mer count.
4.  **Repeat Density**: Percentage of genome covered by RepeatMasker annotations (if available) or simple repeat detection (e.g., `trf`).
5.  **Protein Stability**:
    -   **Method**: **Uniform Stability Proxy** using **Amino Acid Composition (AAC)** and **Hydrophobicity Scales** (e.g., Kyte-Doolittle).
    -   **Rationale**: ESM-1b is too large for limited CPU cores in <4h and, more importantly, a conditional fallback (Proxy for slow, ESM for fast) would introduce a systematic bias correlated with sequence length/complexity. Therefore, the Proxy is used as the **mandatory, uniform** method for **all** samples.
    -   **Spec Flag**: FR-003 (ESM-1b) is flagged for amendment to reflect the CPU-only reality and the need for a uniform method.

## Modeling Strategy

1.  **Target Variable**: Interferon-Response Score (ISG-PC1).
    -   Compute PCA on the expression matrix of the 50 ISG genes.
    -   PC1 captures the dominant variation (activation vs. suppression).
2.  **Predictors**: The feature vector described above (k=3, 4 only).
3.  **Model**: Elastic Net Regression.
    -   **Regularization**: L1+L2 mix.
    -   **Hyperparameter Tuning**: k-fold CV on training set only (FR-006).
4.  **Inference**:
    -   **Debiased Lasso**: To obtain p-values for coefficients (FR-012). **Assumption Check**: Verify design matrix incoherence before applying.
    -   **VIF**: Check for multicollinearity (FR-008). **Note**: VIF is **diagnostic only**. Features are NOT excluded dynamically based on VIF thresholds, as this would invalidate the Debiased Lasso inference (post-selection bias).
    -   **Permutation Test**: A substantial number of shuffles will be performed to ensure statistical robustness. to establish null distribution (FR-007). **Crucial**: For each permutation, **re-run PCA** on the permuted data to preserve the HDLSS structure and prevent inflated Type I errors.
5.  **Validation**:
    -   **Strain-Level Split**: Ensure no strain leakage (FR-005).
    -   **Metrics**: R², RMSE, min FDR p-value.

## Power Analysis & Dimensionality

-   **Sample Size**: The pipeline requires ≥30 samples (FR-013) and ≥5 test strains (FR-017).
- **Dimensionality**: With N < 100 strains and P [deferred] features (k=3,4), the system is severely underdetermined.
-   **Mitigation**: The restriction to k=3 and k=4 is the primary mitigation strategy. While this reduces the feature space, it remains high-dimensional relative to N. Elastic Net is chosen specifically for its ability to handle this regime, but the statistical power to detect small effect sizes is low.
-   **Interpretation**: The success criterion R² ≥ 0.30 (SC-001) is interpreted as a heuristic for "presence of a strong predictive signal" rather than a definitive proof of a specific causal mechanism. Given the sample size, the study is underpowered to distinguish subtle effects from noise, and results should be viewed as hypothesis-generating.

## Statistical Rigor & Assumptions

-   **Multiple Comparisons**: Benjamini-Hochberg (FDR) applied to Debiased Lasso p-values (FR-009).
-   **Power Analysis**: The plan requires ≥30 samples (FR-013) and ≥5 test strains (FR-017). This is a hard constraint; if data is insufficient, the pipeline aborts (FR-017).
-   **Causal Inference**: The study is **observational**. Claims will be limited to "associational" or "predictive" power. No causal claims (e.g., "X causes Y") will be made.
-   **Collinearity**: k-mer frequencies are highly correlated. VIF > 5 triggers a **flag** (FR-008). The plan will report VIFs but will **not** exclude features dynamically based on VIF, as this would introduce post-selection bias invalidating the Debiased Lasso p-values. Elastic Net handles collinearity via regularization.
-   **Measurement Validity**: ISG-PC1 is a validated proxy for IFN response. Protein stability proxy (AAC/Hydrophobicity) is less precise than ESM-1b but robust for CPU and uniform across samples.

## Risk Assessment & Mitigation

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Missing Genomes** | High | FR-013: Log warning, exclude virus, proceed if ≥30 samples remain. |
| **Missing Strain Metadata** | High | FR-014: Abort if >10% samples lack link (Step 2.2). |
| **ESM-1b Timeout** | N/A | **Uniform Proxy** used as standard method. No timeout needed. |
| **Low Sample Size** | High | FR-013/FR-017: Abort with error if <30 samples or <5 test strains. |
| **High Collinearity** | Medium | VIF check (FR-008); report collinearity in results; do not exclude features dynamically. |
| **HDLSS Permutation Error** | High | Re-run PCA within the permutation loop (Step 4.3). |
| **CAI Confounding** | Medium | Include virus family as a covariate if feasible; acknowledge limitation. |
| **Ortholog/ISG Missing** | High | Step 2.1/2.4: Explicit validation checks before PCA; exclude samples if set is empty. |