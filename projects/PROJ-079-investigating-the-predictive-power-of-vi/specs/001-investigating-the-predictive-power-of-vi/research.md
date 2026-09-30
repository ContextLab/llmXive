# Research: Predictive Modeling of Host Immune Response from Viral Sequence Features

## Scientific Background

The study investigates whether intrinsic properties of viral genomes (codon usage, k-mer frequencies, structural stability) correlate with the host's transcriptional immune response (Interferon Response). This is a hypothesis-driven computational study aiming to identify viral "signatures" of immune evasion or activation.

### Key Concepts
- **Interferon Response (ISG-PC1)**: The first principal component of a set of Interferon-Stimulated Genes (ISGs). It serves as a quantitative proxy for the magnitude of the host's antiviral state.
- **Codon Adaptation Index (CAI)**: Measures the similarity of codon usage in a viral genome to that of the host, potentially indicating translational efficiency.
- **k-mer Frequencies**: Short sequence motifs (k=3,4,5,6) that capture local sequence composition and potential regulatory elements.
- **Protein Stability**: Predicted stability of viral proteins, which may influence antigen presentation or immune recognition.

## Dataset Strategy

### Verified Datasets
The plan relies exclusively on the following verified sources:

| Dataset | Purpose | Source URL | Access Method |
|:--- |:--- |:--- |:--- |
| **NCBI GEO (Gene Expression Omnibus)** | Host transcriptomic data (raw counts) and metadata | `https://www.ncbi.nlm.nih.gov/geo/` | `GEOparse` (programmatic fetch from NCBI FTP) |
| **NCBI Virus** | Viral genome sequences | ` | `ncbi-virus` CLI or direct FTP download |

**Note on Data Access**:
- **GEO Data**: The pipeline uses `GEOparse` to programmatically retrieve raw count matrices and Series Matrix files (containing `virus_strain_accession` metadata) directly from NCBI GEO FTP servers. This ensures access to the raw, unnormalized data required for TMM normalization (FR-002) and the specific metadata linkage required for strain-level aggregation.
- **NCBI Virus**: The pipeline queries the NCBI Virus database via the `ncbi-virus` tool or direct FTP access using the specific accession IDs extracted from the GEO metadata.

### Data Flow
1. **Download**: Fetch target GEO series (e.g., GSE147507) using `GEOparse`. Extract sample metadata to identify virus strain accessions.
2. **Fetch Genomes**: For each unique strain accession found in GEO metadata, download the corresponding FASTA from NCBI Virus.
3. **Merge**: Join host expression data with viral genome data based on the strain accession.

### Handling Missing Data
- **Missing Genomes**: If a strain accession in GEO has no corresponding entry in NCBI Virus, log a warning and exclude that strain (FR-013).
- **Missing Metadata**: If `virus_strain_accession` is missing or ambiguous in GEO metadata, exclude the sample (FR-014). Abort if >10% of samples are excluded.
- **Small Dataset**: If the final merged dataset has <30 paired observations, abort with a fatal error (FR-013).

## Statistical Methodology

### Model: Elastic Net Regression
- **Rationale**: Elastic Net handles high-dimensional data (many k-mers) and correlated predictors (collinearity) better than Lasso or Ridge alone.
- **Tuning**: 5-fold cross-validation within the training set to select optimal `alpha` (mixing) and `lambda` (regularization strength).
- **Splitting**: Train/Test split at the **virus strain level** (FR-005) to ensure generalization to unseen strains.

### Validation & Rigor
- **Permutation Test**: 1,000 random label shuffles to generate an empirical p-value for the global model fit (FR-007). **This count is non-negotiable.** If the runtime for 1,000 permutations exceeds the 4-hour limit, the pipeline MUST ABORT with a fatal error rather than reduce the permutation count.
- **Debiased Lasso**: Used to compute p-values for individual coefficients (FR-012).
- **FDR Correction**: Benjamini-Hochberg procedure applied to Debiased Lasso p-values (FR-009).
- **Collinearity Check**: Variance Inflation Factor (VIF) calculated for all predictors; flag if VIF > 5 (FR-008).

### Power Analysis
- **Constraint**: The study requires a minimum of 5 distinct virus strains in the test set (FR-005) and 30 total observations (FR-013).
- **Limitation**: If the available GEO data yields fewer than 30 observations, the study cannot proceed. This is a hard constraint, not a soft recommendation.

## Compute Feasibility & Escape Hatch

### CPU-First Strategy
- **Goal**: Run entirely on GitHub Actions free-tier (standard CPU, 7GB RAM).
- **Strategy**:
 - Stream GEO data if necessary (though GEO datasets are typically small enough to fit in memory).
 - Process viral genomes in batches.
 - Use `scikit-learn` and `statsmodels` which are CPU-optimized.
 - **ESM-1b**: If full ESM-1b inference exceeds memory/time, the pipeline will:
 1. Attempt to run on a subset of proteins (top 5 longest ORFs).
 2. If this still fails, **ABORT** with a clear error message indicating that the feature (ESM-1b) cannot be computed within the resource constraints.
 3. **Do NOT** silently switch to the "Uniform Stability Proxy" without a ratified amendment.

### GPU Escape Hatch (Kaggle)
- **Trigger**: If the pipeline explicitly detects a CUDA requirement (e.g., `device="cuda"` in a future model version) or if a specific ESM-1b configuration requires GPU.
- **Action**: The execution stage will auto-offload to a Kaggle GPU with substantial VRAM capacity.
- **Plan**: The current plan assumes CPU execution. If ESM-1b proves intractable on CPU even with batching, the plan will be updated to use a smaller, quantized model (e.g., `esm2_t6_8M`) on the GPU escape hatch, strictly limited to a few hundred examples to fit the 9h kernel limit.

## Decision Rationale

- **Why Elastic Net?** It balances feature selection (Lasso) and coefficient shrinkage (Ridge), ideal for k-mer features where many are correlated.
- **Why Strain-Level Split?** Prevents data leakage where the model learns strain-specific noise rather than generalizable viral features.
- **Why 1000 Permutations?** Required by Constitution Principle VII for statistical rigor. Reducing this count invalidates the p-value. The pipeline must abort if time exceeds limits rather than silently lowering the bar.
- **Why Abort on Resource Exceed?** Fabricating a "proxy" or reducing statistical power violates the Constitution and the Spec. It is better to fail than to produce unscientific results.

## Proxy Validation Strategy

To address the concern of unverified extrapolation (data_resources-c74a6ebc), the plan implements a **Proxy Validation** step:
1. **Subset Selection**: Select a representative subset of strains by genome length.
2. **Dual Calculation**: Calculate both ESM-1b (if feasible) and the Proxy for these 5 strains.
3. **Correlation Check**: Compute R² between ESM-1b and Proxy scores.
4. **Threshold**: If R² < 0.8, the pipeline aborts with `FatalError: Proxy validation failed (R² < 0.8)`.
5. **Full Application**: Only if the threshold is met is the Proxy applied to the full dataset.