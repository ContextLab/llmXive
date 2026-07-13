# Research: llmXive Follow-up: Extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## 1. Methodological Overview

This research extends the "edge spectrum" hypothesis by comparing the geometric structure of unembedding matrices across three linguistically distinct models: Llama-3-8B (English-centric), BLOOM-7B (Multilingual), and Qwen-1.5-7B (Chinese-centric). The core hypothesis is that the top singular vectors of the unembedding matrix encode a "language-specific prior" that can be detected by projecting frequency-weighted average token vectors onto these subspaces.

The methodology strictly separates the **Spectral Decomposition** (extracting the basis) from the **Frequency Projection** (defining the vector of interest) to avoid circularity (Constitution Principle VII). Statistical significance is established via a spherical null hypothesis permutation test.

## 2. Dataset Strategy

All datasets are sourced exclusively from the verified list below. No external or guessed URLs are used.

### Verified Datasets

| Dataset Name | Purpose | Verified URL / Source | Notes |
| :--- | :--- | :--- | :--- |
| **Llama-3-8B** | Unembedding Matrix ($W_U$) | `meta-llama/Meta-Llama-3-8B` (Hugging Face Hub) | Requires HF token; weights accessed via `safetensors`. |
| **BLOOM-7B1** | Unembedding Matrix ($W_U$) | `bigscience/bloom-7b1` (Hugging Face Hub) | Multilingual; used for French/English analysis. |
| **Qwen-1.5-7B** | Unembedding Matrix ($W_U$) | `Qwen/Qwen1.5-7B` (Hugging Face Hub) | Chinese-centric; used for Chinese analysis. |
| **RedPajama-Data** | English Frequency List | `togethercomputer/RedPajama-Data-1T-Sample` (Hugging Face) | Subset used for English token frequencies. |
| **CommonCrawl-CC** | Multilingual Frequency | `cc100` (Hugging Face) or `wikitext` (if CC unavailable) | Used for French (via BLOOM) and Chinese (via Qwen) frequencies. |

> **Note on Frequency Data**: If a specific language frequency list (e.g., French) is missing from the verified sources, the system MUST raise a `DataMissingError` (as per Edge Cases) and halt. The plan assumes RedPajama covers English and CC/Wiki covers the others.

### Dataset Variable Fit Check

*   **Requirement**: The dataset must contain token frequencies for the specific language of the model.
*   **Verification**:
    *   **Llama-3**: English frequencies from RedPajama. **Fit**: High.
    *   **BLOOM**: French/English frequencies from CC100. **Fit**: High (CC100 is multilingual).
    *   **Qwen**: Chinese frequencies from CC100. **Fit**: High.
*   **Risk**: If the tokenization granularity differs significantly between the corpus and the model (e.g., subword vs. character), the frequency vector must be normalized. This is handled in `projection.py`.

## 3. Technical Approach

### 3.1 Edge Spectrum Extraction (FR-001, FR-002)
*   **Method**: `scikit-learn`'s `TruncatedSVD` (Lanczos bidiagonalization).
*   **Parameters**: `n_components=50`, `algorithm='randomized'`, `random_seed=42`.
*   **Memory Strategy**: The unembedding matrix ($V \times D$) is loaded in chunks or streamed if the format allows. If the full matrix exceeds RAM, we rely on `TruncatedSVD`'s ability to compute only the top $k$ vectors without forming the full dense matrix in memory, provided the input can be iterated. If the model weights are stored as `safetensors`, we can map them to memory without loading the whole tensor.
*   **Fallback**: If `TruncatedSVD` fails due to memory, we will sample a subset of rows (tokens) to estimate the subspace, though this is a last resort (Edge Case).

### 3.2 Average Token Vector Calculation (FR-003)
*   **Formula**: $\hat{\vh} = \sum_{i} f_i \cdot \ve_i / \sum f_i$, where $f_i$ is the normalized frequency of token $i$ and $\ve_i$ is its embedding.
*   **Alignment**: Since embeddings and unembeddings are often in different bases, we use **Orthogonal Procrustes** to align the space of the average vector to the space of the singular vectors before projection.
*   **Normalization**: Frequencies are normalized by character count to handle tokenization granularity differences (Edge Case).

### 3.3 Statistical Validation (FR-005, SC-003, SC-006)
*   **Null Hypothesis**: The observed cosine similarity between a language's average vector and a foreign edge spectrum is no different than the similarity between a random unit vector and that spectrum.
*   **Permutation Test**:
    1.  Generate $N$ random unit vectors from a spherical distribution ($N \sim \mathcal{N}(0, I)$).
    2.  Project each onto the foreign edge spectrum.
    3.  Compute p-value: $P(\text{null} \ge \text{observed})$.
*   **Sensitivity Analysis**: Sweep $N \in \{100, 1000, 10000\}$. If $\sigma(p) > 0.005$ across sweeps, the result is inconclusive (SC-006).

## 4. Statistical Rigor & Limitations

*   **Multiple Comparisons**: We perform 3 models $\times$ 2 cross-lingual pairs = 6 comparisons. We will apply a **Bonferroni correction** (adjusted $\alpha = 0.05/6 \approx 0.0083$) to the final p-values.
*   **Power Analysis**: Due to the deterministic nature of the "average vector" (it is a single point estimate from the corpus), traditional power analysis is not applicable. Instead, we rely on the **stability of the p-value** across the permutation sweep (SC-006) as our measure of robustness.
*   **Causal Claims**: This is an **observational** study. We can only claim "associational" properties of the geometry. We cannot claim that the model *causes* bias, only that the bias is *encoded* in the weights.
*   **Collinearity**: The top singular vectors are orthogonal by definition. However, the "average token" vector is a linear combination of all tokens. We acknowledge that the average vector is highly correlated with the top few singular vectors (the "mean" direction), which is the phenomenon being measured, not a confounding factor.

## 5. Compute Feasibility

*   **RAM**: `TruncatedSVD` on a $50k \times 4096$ matrix (approx. 200M floats $\approx 800$ MB) is well within 7GB. The bottleneck is loading the model weights. We will use `torch.load(..., map_location='cpu')` and `safetensors` to avoid GPU memory overhead.
*   **Time**: SVD of 50k x 4096 takes ~5-10 mins per model on CPU. Permutation test with N=10,000 is trivial (vector-matrix multiplication). Total runtime estimated < 30 mins.
*   **No GPU**: The entire pipeline is designed for CPU. No CUDA, no 8-bit quantization.

## 6. Decision Rationale

*   **Why TruncatedSVD?** Full SVD is O(N^3) and O(N^2) memory. For $N=50,000$, this is infeasible on 7GB RAM. Randomized SVD is O(N k^2) and is standard for this scale.
*   **Why Procrustes?** Without alignment, the singular vectors of Model A and Model B are in arbitrary orthogonal bases. Direct comparison is mathematically invalid. Procrustes finds the optimal rotation to align them.
*   **Why Spherical Null?** The "average token" is a specific direction in the embedding space. A random unit vector is the most neutral baseline to test if the observed direction is "special" compared to noise.
