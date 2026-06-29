# Research: Predictive Modeling of Host Immune Response from Viral Sequence Features

## Dataset Strategy

The project relies on pairing viral genomic data with host transcriptomic data. The spec requires downloading from NCBI Virus and GEO.

| Data Source | Purpose | Verified URL / Loader | Status |
|:--- |:--- |:--- |:--- |
| **NCBI Virus** | Viral Genome Sequences (FASTA) | **NO verified source found** in the provided list. The spec requires NCBI Virus, but the `# Verified datasets` block does not contain a direct NCBI Virus URL. The pipeline will attempt to fetch from NCBI Virus directly using user-provided accessions. If accessions are missing, the pipeline aborts. | ⚠️ **User Input Required** |
| **GEO Transcriptomics** | Host Expression Counts | **NO verified source found** for the specific GEO series required by the spec. The pipeline will attempt to fetch from GEO using user-provided accessions. If accessions are missing, the pipeline aborts. | ⚠️ **User Input Required** |
| **Medical-5day** | RMSE reference | ` | ✅ Verified (but irrelevant to viral features) |

### Critical Dataset Fit Analysis

**Fatal Flaw Identified**: The spec requires **Viral Genomes** and **Host Transcriptomic Data** paired by strain.
- The `# Verified datasets` block **does not contain** a verified URL for NCBI Viral Genomes or the specific GEO transcriptomic series needed.
- **Resolution Strategy**: The pipeline will **abort** if the user does not provide the specific GEO accessions and NCBI Virus search terms. No synthetic data will be generated for the primary scientific validation. The pipeline is designed to run on real data only.

## Methodological Rationale

### 1. Interferon-Response Score (ISG-PC1)
- **Method**: Principal Component Analysis (PCA) on the expression of 50 canonical Interferon Stimulated Genes (ISGs).
- **Justification**: PC1 captures the maximum variance in the ISG set, serving as a robust summary of the interferon response state.
- **Validation**: The ISG set (n=50) is from Interferome v2.0. For non-human/mouse species, ortholog mapping via Ensembl Compara v109 is required (FR-015).
- **Variance Preservation**: While ISG-PC1 scores are averaged per strain for the primary model (FR-016), sample-level variance is preserved in `data/processed/sample_variance.csv` for exploratory analysis.

### 2. Feature Extraction
- **CAI**: Codon Adaptation Index. Measures codon usage bias.
- **GC-Content**: Global and regional.
- **k-mer Frequencies**: k=3,4,5,6. Captures local sequence motifs.
- **Repeat Density**: Percentage of genome covered by repeats, extracted using `RepeatMasker` (via `pybedtools`).
- **Protein Stability**: Specified as ESM-1b v1.1.
 - **Constraint**: ESM-1b requires GPU and significant RAM.
 - **Decision**: **ESM-1b is a hard requirement**. If CUDA is unavailable, the pipeline will attempt CPU mode (if supported) or fallback to an AAIndex-based stability proxy ONLY if the user sets `--proxy_mode`. Otherwise, it aborts. The proxy is documented as a limitation in the final report.

### 3. Statistical Modeling
- **Model**: Elastic Net Regression.
 - **Why**: Handles high-dimensional features (k-mers) and collinearity better than OLS.
- **Validation**:
 - **5-Fold CV**: For hyperparameter tuning (α, λ).
 - **Permutation Test**: 1000 shuffles to assess global significance (p-value). Includes a **Negative Control** (shuffling viral sequences) to detect spurious correlations.
 - **Stability Selection**: Replaces Debiased Lasso as the primary method for feature-level p-values (FR-012) due to N << P constraints. Debiased Lasso is retained as an exploratory check if N > 200.
 - **FDR Correction**: Benjamini-Hochberg for multiple comparisons (FR-009).
 - **VIF**: Variance Inflation Factor to detect collinearity (FR-008).
- **Power Analysis**: The pipeline calculates effective degrees of freedom after feature selection. If the effective N is insufficient for the target R², the pipeline aborts.
- **Host Covariates**: Host codon usage bias is included as a covariate to control for tautological correlations.

### 4. Compute Feasibility
- **RAM**: k-mer extraction for ~100 genomes is trivial. PCA and Elastic Net on ~100 samples × ~5000 features is well within 7GB RAM.
- **Time**: A generous time limit is allocated for this dataset size on 2 CPUs.
- **No GPU**: ESM-1b is prioritized; proxy is a fallback.

## Edge Case Handling

| Scenario | Handling Strategy |
|:--- |:--- |
| **Missing Genome** | Log warning, exclude strain (FR-013). Abort if <30 samples remain. |
| **Ambiguous Metadata** | Exclude sample, log reason. Abort if >10% missing (FR-014). |
| **Non-Human/Mouse** | Map ISGs via Ensembl Compara. If fail, mark 'response_unknown' and exclude (FR-015). |
| **<5 Strains in Test** | Abort with fatal error (FR-017). |
| **VIF > 5** | Flag predictor, report in logs, but do not remove (unless specified). |
| **ESM-1b Failure** | Attempt CPU mode. If fail, prompt for `--proxy_mode`. If not set, abort. |
| **Low Power** | Calculate effective N. If insufficient for R²=0.30, abort. |
| **Missing Real Data** | Abort with fatal error. No simulation mode. |

## Decision Log

1. **Dataset Gap**: No verified URL for NCBI Viral Genomes or specific GEO transcriptomics found. **Action**: Pipeline requires user-provided accessions. Aborts if missing.
2. **ESM-1b Exclusion**: GPU requirement conflicts with CI constraints. **Action**: Prioritize ESM-1b; fallback to AAIndex proxy ONLY with `--proxy_mode` flag. Document limitation.
3. **Strain-Level Aggregation**: Required by FR-016. **Action**: Average ISG-PC1 scores for samples sharing a strain before modeling. Preserve sample variance for exploratory analysis.
4. **Feature Selection**: Debiased Lasso replaced by Stability Selection for primary inference due to N << P.
5. **Negative Control**: Added to permutation test to detect spurious correlations.
6. **Host Covariates**: Host codon usage bias included as a covariate.