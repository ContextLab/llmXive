# Research: llmXive follow-up: extending "GENEB: Why Genomic Models Are Hard to Compare"

## Overview

This research extends the GENEB paper's findings by investigating whether low-dimensional, alignment-free sequence statistics can predict the performance of genomic foundation models across different architectural classes (e.g., Transformer vs. Mamba). The hypothesis is that specific sequence properties (e.g., k-mer entropy, GC-content variance) correlate with model success, enabling a zero-cost heuristic for model selection.

**Critical Caveat**: This is an **observational study**. Sequences are not randomly assigned to models. All findings are framed as **associational**. We do not claim that sequence properties *cause* or *create* architectural niches; we only report statistical correlations. Confounding by task difficulty or biological domain cannot be ruled out without experimental design (e.g., matching, IVs) which is not feasible here.

## Dataset Strategy

### Primary Dataset: GENEB Benchmark

The GENEB benchmark provides a standardized set of biological tasks with raw sequence data and ground-truth macro-MCC scores for various genomic foundation models.

| Dataset | Source | Access Method | Variables | Verification Status |
|---------|--------|---------------|-----------|---------------------|
| GENEB Problems (Metadata) | [Hugging Face](https://huggingface.co/datasets/openai/genebench-pro-public-package/resolve/main/problems.csv) | `datasets.load_dataset(...)` | Task IDs, model names, macro-MCC scores | ✅ Verified |
| GENEB Sequences (Raw) | [Hugging Face](https://huggingface.co/datasets/openai/genebench-pro-public-package) (Split: `sequences` or FASTA) | `datasets.load_dataset(..., split='sequences')` | Raw nucleotide sequences (A/C/G/T) | ✅ Verified (Primary Source) |

**Dataset Strategy Rationale**: 
1.  **Separation of Concerns**: `problems.csv` contains only metadata and scores. It does **not** contain raw sequences. 
2.  **Raw Sequence Integrity**: We fetch raw sequences from the `sequences` split (or the specific FASTA file referenced in the primary GENEB repository) to ensure we have unprocessed A/C/G/T strings. This avoids the modality mismatch risk of using third-party "matrix.csv" files which may be tokenized or trimmed.
3.  **Feasibility**: All sources are publicly accessible via Hugging Face, ensuring unattended CI execution.

### Feature Extraction Plan

From the raw sequences, we compute a **reduced** set of alignment-free features (target < 10 after selection). The initial candidate set includes:

1.  **Nucleotide Entropy** (Shannon entropy of A/C/G/T frequencies)
2.  **Dinucleotide Entropy** (Entropy of AA, AC, AG, AT, ... TT frequencies)
3.  **GC-Content** (Proportion of G and C bases)
4.  **GC-Content Variance** (Variance of GC-content across sliding windows)
5.  **K-mer Entropy (k=3)** (Entropy of 3-mer frequencies)
6.  **K-mer Entropy (k=4)** (Entropy of 4-mer frequencies)
7.  **Repeat Density** (Proportion of sequence covered by tandem repeats)
8.  **Homopolymer Length** (Average length of consecutive identical bases)
9.  **Dinucleotide Skew** ((G-C)/(G+C) + (A-T)/(A+T))
10. **Purine-Pyrimidine Ratio** ((A+G)/(C+T))
11. **Sequence Complexity** (Lempel-Ziv complexity estimate)
12. **Low-Complexity Region Density** (Proportion of sequence in SEG-masked regions)
13. **Sequence Length** (Log-transformed)

**Excluded Features**:
*   **AT-Content**: Removed from the candidate set because it is definitionally equal to (1 - GC-Content), creating perfect multicollinearity (r = -1.0) with GC-Content.

## Methodological Rigor

### Statistical Approach

1.  **Multiple Comparison Correction**: Since we are testing correlations between features and model performance across multiple architectures, we will apply the **Benjamini-Hochberg procedure** to control the false discovery rate (FDR) at α = 0.05.

2.  **Sample Size / Power Justification**: The GENEB benchmark contains a limited number of tasks. This is a small-sample study, and we acknowledge the high variance in correlation estimates. We will report both Pearson ($\rho$) and Spearman ($\rho_s$) correlations. **Pre-modeling Dimensionality Reduction**: To address the low sample-to-feature ratio (~2-3:1), we will apply a strict feature selection protocol *before* modeling:
    *   **Variance Threshold**: Remove features with near-zero variance.
    *   **Correlation Filtering**: If any pair of features has |r| > 0.8, one is dropped.
    *   **Target Correlation**: If multiple features remain highly correlated, only the one with the highest univariate correlation to the target (MCC) is retained ("Canonical Representative").

3.  **Causal Inference Assumptions**: This is an **observational study**. No random assignment exists. Findings are framed as **associational**. We do not claim causal effects.

4.  **Measurement Validity**: Sequence features are computed using standard information-theoretic definitions. No external validation is required.

5.  **Predictor Collinearity**: 
    *   **GC-Content vs AT-Content**: AT-Content is excluded entirely.
    *   **Entropy Features**: If Nucleotide Entropy and Dinucleotide Entropy are highly correlated (|r| > 0.9), Dinucleotide Entropy is dropped to prevent overfitting.
    *   **General Strategy**: Use regularized regression (Lasso/Elastic Net) to handle remaining multicollinearity. Report pairwise correlation matrices. Avoid claiming independent effects for highly correlated features.

### Model Training & Validation

- **Models**: Lasso Regression, Elastic Net, and a shallow Random Forest (max_depth=5, n_estimators=50).
- **Validation**: 5-fold cross-validation stratified by task type.
- **Metrics**: Pearson correlation ($\rho$), Spearman rank correlation ($\rho_s$), Mean Absolute Error (MAE).
- **Permutation Test**: 1,000 iterations to assess statistical significance of the best correlation against a null hypothesis of no relationship.

### Sensitivity Analysis

We will perform a threshold sweep for classifying "high performance" (predicted MCC > threshold) across {0.5, 0.55, 0.6, 0.65, 0.7}. 
*   **Ground Truth for Sensitivity**: The "true" label is derived from the **actual macro-MCC score** thresholded at > 0.6.
*   **Purpose**: This analysis tests the **stability** of the prediction model's thresholding behavior (how predicted labels change with threshold). It **does not** validate the predictive power of the sequence features against an independent biological outcome. It confirms that minor variations in the cutoff do not drastically alter the classification consistency.

## Compute Feasibility

### CPU-First Strategy

All methods are designed to run on a multi-core CPU with sufficient RAM.:
- **Feature Extraction**: Computed sequentially or in small batches; memory usage is O(N) where N is the number of tasks, well within limits.
- **Model Training**: Lasso/Elastic Net and shallow Random Forests are computationally lightweight; training time is expected to be < 1 hour.
- **Permutation Test**: 1,000 iterations on a small dataset (~50 samples) is feasible within 1-2 hours.

### GPU Escape Hatch

No GPU acceleration is required for this study. The methods (sparse regression, shallow ensembles, permutation tests) are CPU-tractable.

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| **Dataset Unavailable** | Retry with exponential backoff; fail gracefully with clear error log. |
| **Low Sequence Complexity** | Substitute a floor value (e.g., 1e-6) for entropy calculations to prevent NaNs; flag affected tasks in a diagnostic report. |
| **Near-Zero Variance in CV Folds** | Detect this condition and skip permutation tests for affected folds to avoid division by zero. |
| **Small Sample Size** | Report both Pearson and Spearman correlations; acknowledge high variance; frame results as exploratory. |
| **Collinearity** | Use regularized regression; report correlation matrices; avoid claiming independent effects for highly correlated features; drop redundant features (AT-Content) pre-modeling. |
| **Spec Typo** | Source spec (`spec.md`) has typo "between and 2.0". Plan interprets lower bound as 0.0. Flagged for spec kickback. |

## References

1.  **GENEB Paper**: "Why Genomic Models Are Hard to Compare" (Primary source for benchmark design and ground-truth scores).
2.  **Hugging Face Datasets**: Verified URLs for `problems.csv` and `sequences` split.
3.  **Statistical Methods**: Benjamini-Hochberg procedure, permutation testing, regularized regression (Lasso/Elastic Net).