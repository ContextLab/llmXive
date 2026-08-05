# Methodology

This document outlines the theoretical framework, mathematical derivations, and procedural steps used in the llmXive follow-up study: "Extending Your Unembedding Matrix is Secretly a Feature Lens for Text Embeddings."

## 1. Introduction

This research investigates the geometric structure of the "edge spectrum" subspace within the unembedding matrices ($W_U$) of large language models (LLMs). We hypothesize that this subspace captures language-specific priors and that cross-lingual differences in this subspace correlate with typological and performance metrics.

## 2. Shared-Vocabulary Projection

### 2.1 Mathematical Derivation
To compare the geometric structure of $W_U$ across models with different vocabularies (e.g., Llama-3, Mistral, BLOOM), we first project the matrices onto a shared vocabulary space. Let $V_{shared} = V_A \cap V_B$ be the intersection of token IDs between model A and model B.

The projected unembedding matrix $W_U^{proj}$ is constructed by selecting rows corresponding to indices in $V_{shared}$:
$$ W_U^{proj} = W_U[V_{shared},:] $$

**Justification**: Intersecting token IDs is preferred over translation-based alignment (e.g., MUSE) for this specific hypothesis test because:
1. **Basis Invariance**: The "Edge Spectrum" hypothesis relies on the singular vectors of the unembedding matrix. Translation matrices introduce their own rotational noise, potentially obscuring the intrinsic geometric signal of the model's own training.
2. **Direct Comparison**: We aim to measure the similarity of the *models'* representations of *shared* concepts. Using a shared vocabulary ensures we are comparing the same semantic units without the error propagation of an external alignment layer.
3. **Determinism**: Intersection is a deterministic set operation, whereas translation alignment often involves optimization that can vary between runs.

This approach aligns with the "Edge Spectrum" paper's discussion on basis invariance, where the focus is on the subspace spanned by the singular vectors rather than the specific basis vectors themselves.

## 3. Mean Embedding Interpretation

### 3.1 Definition
We define the "Mean Embedding" vector $\hat{h}$ for a language $L$ as the frequency-weighted average of the embedding vectors:
$$ \hat{h}_L = W_E \times f_L $$
Where:
- $W_E$ is the embedding matrix of the model.
- $f_L$ is the normalized frequency distribution vector of tokens in language $L$ (derived from external corpora like RedPajama or OSCAR).

### 3.2 Physical Interpretation
The vector $\hat{h}_L$ represents the **vocabulary centroid** in the embedding space. It captures the "average" direction in which the model projects tokens that are common in language $L$.

**Assumption**: We assume that frequency-weighted centroids capture "common sense" priors specific to the language. High-frequency tokens (function words, common nouns) dominate this vector, effectively summarizing the "typical" semantic content of the language as represented by the model. By projecting this centroid onto the edge spectrum subspace, we can measure how much the "common sense" prior of a language aligns with the model's most salient geometric features.

## 4. Statistical Significance and Null Hypothesis

### 4.1 The Permutation Test
To determine if the observed cross-lingual similarity in the edge spectrum subspace is statistically significant, we perform a permutation test.

**Null Hypothesis ($H_0$)**:
"The observed cross-lingual subspace similarity is indistinguishable from the similarity observed between within-language model pairs."

**Implementation Details**:
1. **Observed Statistic**: We compute the cosine similarity between the edge spectrum subspace of an English model (e.g., Llama-3-EN) and a target language model (e.g., BLOOM-FR).
2. **Null Distribution**: We generate a null distribution by computing cosine similarities between **within-language model pairs** (e.g., Llama-3-EN vs. Mistral-EN). This serves as the baseline for "natural" variation between models trained on the same language.
3. **Procedure**:
 - Compute $S_{obs} = \text{cosine\_sim}(Subspace_{EN}, Subspace_{Target})$.
 - For each iteration $i$ in $N$ permutations:
 - Select a random within-language pair $(Model_{A, EN}, Model_{B, EN})$.
 - Compute $S_{null}^{(i)} = \text{cosine\_sim}(Subspace_{A, EN}, Subspace_{B, EN})$.
 - Calculate the p-value as the proportion of $S_{null}^{(i)} \geq S_{obs}$ (or $\leq$, depending on the direction of the hypothesis).

**Rationale**: By using within-language pairs as the null distribution, we control for the fact that different models trained on the same language will naturally have some divergence in their subspaces due to architectural differences and random initialization. If the cross-lingual similarity is significantly *lower* (or higher, depending on the specific hypothesis direction) than the within-language variation, we reject $H_0$ and conclude that the cross-lingual shift is a distinct phenomenon.

*Note: This definition strictly matches the implementation in `code/statistical_test.py` (Task T026), which generates the null distribution from same-language model pairs.*

## 5. Data Sources and Integrity

- **Corpora**: RedPajama (English), OSCAR (French/Chinese).
- **Validation**: WALS (World Atlas of Language Structures), SentEval.
- **Integrity**: All data loading uses streaming (`streaming=True`) with strict schema validation. No synthetic fallbacks are permitted; pipeline halts on data fetch failure.

## 6. Reproducibility

All experiments use fixed random seeds defined in `config.py`. The full pipeline can be reproduced by running `python code/main.py --reproducibility-check`.