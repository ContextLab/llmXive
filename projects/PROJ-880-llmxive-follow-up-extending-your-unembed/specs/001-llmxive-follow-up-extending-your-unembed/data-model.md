# Data Model: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## Overview

This document defines the data artifacts, schemas, and transformation logic for the `001-llmxive-crosslingual` feature. All data is stored in `projects/PROJ-880-llmxive-follow-up-extending-your-unembed/data/`.

## Artifact Lifecycle

1.  **Raw Data**: Downloaded from verified sources (RedPajama, OSCAR, WALS). Stored in `data/raw/`. Checksums recorded in `data/checksums.json`.
2.  **Processed Data**: Frequency distributions, SVD results ($U_k$ matrices), token embeddings, and similarity matrices. Stored in `data/processed/`.
3.  **Derived Artifacts**: Final JSON reports (similarity scores, p-values, token lists, WALS correlation). Stored in `data/reports/`.
4.  **Code Artifacts**: Hashes of all source files in `code/` stored in `data/checksums.json`.

## Data Dictionary

### 1. Frequency Distribution (Input)
*   **Source**: RedPajama (English), OSCAR (French/Chinese).
*   **Format**: `.npy` (NumPy array).
*   **Shape**: `(vocab_size,)`
*   **Content**: Normalized token frequencies ($f_i = \frac{count_i}{\sum count}$).
*   **Constraint**: Must match the vocabulary of the target model exactly. If vocabularies differ, a mapping layer is applied, or the analysis is restricted to the intersection.

### 2. Edge Spectrum Matrix (Intermediate)
*   **Source**: SVD of $W_U$.
*   **Format**: `.npy`.
*   **Shape**: `(hidden_size, k)` where $k=100$ (or $50$ if fallback).
*   **Content**: Top-$k$ left singular vectors ($U_k$).
*   **Constraint**: Columns must be orthonormal.

### 3. Token Embedding Projection (Intermediate)
*   **Source**: Model embeddings $E$ projected onto $U_k$.
*   **Format**: `.npy`.
*   **Shape**: `(N, k)` where $N$ is the number of top frequent tokens.
*   **Content**: Projected embeddings for top-$N$ tokens.

### 4. Similarity Report (Output)
*   **Source**: Cosine similarity calculation.
*   **Format**: `.json`.
*   **Schema**: `contracts/similarity_report.schema.yaml`.
*   **Content**: Pairwise cosine similarities and confidence intervals.

### 5. Permutation Test Result (Output)
*   **Source**: Statistical test.
*   **Format**: `.json`.
*   **Schema**: `contracts/permutation_result.schema.yaml`.
*   **Content**: Observed statistic, p-value, null distribution summary.

### 6. WALS Validation Report (Output)
*   **Source**: Correlation calculation.
*   **Format**: `.json`.
*   **Schema**: `contracts/wals_validation.schema.yaml` (new).
*   **Content**: Correlation coefficient, p-value, WALS features used.

## Transformation Logic

### T-01: Frequency Estimation
*   **Input**: Raw text file (RedPajama/OSCAR).
*   **Process**: Tokenize using the target model's tokenizer. Count tokens. Normalize.
*   **Output**: `data/processed/freq_distributions/{model}_{lang}_freq.npy`.
*   **Validation**: Sum of frequencies must be $1.0 \pm 1e-6$.

### T-02: Subspace Extraction
*   **Input**: Model weights ($W_U$).
*   **Process**: `scipy.sparse.linalg.svds(W_U, k=100)`.
*   **Output**: `data/processed/svd_results/{model}_uk.npy`.
*   **Validation**: Columns are orthonormal; singular values are sorted descending.

### T-03: Token Embedding Projection
*   **Input**: Model embeddings $E$, frequency distribution $f$.
*   **Process**: Select top-$N$ tokens. Compute $P = U_k^T \cdot E[T]$. Compute centroid $\hat{v} = \text{mean}(P)$.
*   **Output**: `data/processed/embeddings/{model}_{lang}_projection.npy`.

### T-04: Similarity Calculation
*   **Input**: Two $U_k$ matrices.
*   **Process**: Compute $S = \text{mean}(\text{cosine\_sim}(u_i, v_i))$ for $i=1..k$.
*   **Output**: Scalar value.

### T-05: Bootstrap Test
*   **Input**: Observed similarity $S_{obs}$, Within-Language Baseline $S_{EN}$.
*   **Process**: Generate a sufficient number of $S_{Cross}^{(b)}$ instances by resampling token frequencies.
*   **Output**: P-value and confidence interval.

### T-06: WALS Correlation
*   **Input**: Subspace orientation, WALS features.
*   **Process**: Compute Pearson correlation.
*   **Output**: Correlation coefficient and p-value.

## Constraints & Assumptions

*   **Vocabulary Alignment**: If models have different vocabularies, the analysis is restricted to the intersection of tokens. If the intersection is < 50% of the vocabulary, the comparison is flagged as "Unreliable".
*   **Memory**: All frequency arrays are stored in `float32` to minimize RAM usage.
*   **Reproducibility**: All random seeds are set to `42` in `config.py`.
*   **Artifact Hashing**: All files in `code/` and `data/` are hashed and recorded in `checksums.json`.
