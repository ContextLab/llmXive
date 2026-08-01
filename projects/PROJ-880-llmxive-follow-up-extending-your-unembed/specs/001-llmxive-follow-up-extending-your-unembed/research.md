# Research: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## 1. Hypothesis & Research Question

**Hypothesis**: The "edge spectrum" subspace (top-$k$ singular vectors of $W_U$) does not encode a universal, language-agnostic "common sense" prior. Instead, its composition shifts to reflect language-specific syntactic noise and typological features.

**Research Question**: Does the geometric orientation and semantic content of the edge spectrum subspace differ significantly between English-centric models (Llama-3, Mistral) and multilingual models (BLOOM) when analyzed across different linguistic typologies?

## 2. Dataset Strategy

### Verified Datasets
Cited ONLY from the provided "Verified datasets" block or verified external sources:
- **RedPajama**: Used for English token frequency distribution.
 - Source: ` (and related JSONL files).
 - Access: Direct download via Hugging Face `datasets` library.
- **OSCAR (Common Crawl Snapshot)**: Used for French and Chinese token frequency distribution (Primary Source for FR-006).
 - Source: ` (Verified HF dataset, cleaned Common Crawl).
 - Access: `datasets.load_dataset("oscar", "unshuffled_deduplicated_fr")` and `zh`.
 - **Fallback**: If OSCAR is unavailable, use `wikimedia/wikipedia` (language="fr"/"zh") but acknowledge the distributional limitation (Construct Validity).
- **WALS (World Atlas of Language Structures)**: For typological features.
 - Source: ` (Verified Zenodo mirror of WALS CSV).
 - Access: Direct download of CSV.
- **Multilingual SentEval**: For performance validation.
 - Source: ` (Verified GitHub repository).
 - Access: Download pre-computed STS accuracy tables.

### Data Acquisition Plan
1. **RedPajama**: Download via `datasets.load_dataset("togethercomputer/RedPajama-Data-1T")`. Stream the data to count token frequencies for English.
2. **French/Chinese**: Download OSCAR subsets via `datasets.load_dataset("oscar", "unshuffled_deduplicated_fr")`. If unavailable, fallback to Wikipedia and log the limitation.
3. **WALS**: Download the `wals.csv` file from the verified Zenodo mirror. Map language codes (en, fr, zh) to WALS feature vectors.
4. **SentEval**: Download the STS accuracy results for Llama, Mistral, and BLOOM from the verified GitHub repository.

### Data Feasibility Check
- **RedPajama**: ~1TB raw, but streaming is feasible for frequency counting (FR-006).
- **OSCAR**: ~10GB per language, streamable.
- **WALS/SentEval**: Small CSV/JSON files (<100MB).
- **Compute**: All data fits within the disk limit if streamed.

### Construct Validity & Sensitivity Analysis
- **Limitation Acknowledgement**: Wikipedia is structurally distinct (encyclopedic, formal) from Common Crawl (web, informal). This may bias the "mean embedding" towards formal syntax, potentially masking "syntactic noise".
- **Mitigation**: Task T068 will perform a sensitivity analysis comparing frequency distributions from OSCAR (if available) vs. Wikipedia to quantify the bias. If the bias is significant, the final report will explicitly state the limitation.

## 3. Methodology

### 3.1 Edge Spectrum Extraction (FR-001)
- **Input**: Unembedding matrix $W_U$ from Llama-3, Mistral, BLOOM.
- **Method**: Perform Singular Value Decomposition (SVD) on $W_U$: $W_U = U \Sigma V^T$.
- **Output**: Top-$k$ (k=100) left singular vectors $U_{100}$.
- **Feasibility**: $W_U$ size is ~50k x 4k (approx). SVD of a moderate-sized matrix is trivial on CPU. Memory usage is < 1GB.

### 3.2 Subspace Similarity (FR-002)
- **Input**: $U_{100}$ matrices for each model.
- **Method**: Compute cosine similarity between subspaces *only on the shared vocabulary tokens*.
 1. Identify the intersection of the vocabularies for the two models.
 2. Extract the corresponding rows from $U_{100}$ for both models.
 3. Apply Procrustes alignment if necessary to minimize rotation error on the shared set.
 4. Compute cosine similarity: $\text{sim}(A, B) = \frac{1}{k} \sum_{i=1}^k \cos(u_i^A, u_i^B)$.
 5. **Normalize** by the intersection size to control for vocabulary overlap bias.
- **Output**: Similarity matrix (English-English, English-BLOOM, BLOOM-BLOOM).

### 3.3 Token Attribution (FR-003, FR-005)
- **Input**: Top-$k$ singular vectors, token frequency distribution $f$, embedding matrix $W_E$.
- **Method**:
 1. **Primary Metric (Spec-Compliant)**: Identify the top-N high-frequency tokens for the language. For each token $t$, compute its embedding $e_t$ from $W_E$ and project it onto the edge spectrum subspace: $p_t = U_{100}^T e_t$. Analyze the distribution of $p_t$ to determine which specific tokens drive the variance in the subspace. This addresses the "common sense" vs. "noise" hypothesis without collapsing the vocabulary into a single vector.
 2. **Diagnostic Metric (Mean Embedding)**: Compute the "mean embedding" as the global centroid weighted by frequency: $\hat{\vh} = W_E \times f$. This satisfies FR-005 and User Story 2 as a baseline, but the primary attribution is the individual token projection.
 3. Identify tokens with highest logit weights in the subspace (top-ranked).
- **Output**: Ranked list of tokens per language, mean embedding vector (diagnostic), and distribution of projected vectors (primary).

### 3.4 External Validation (FR-007) - Label Permutation Null Model
- **Input**: Subspace shift vector, WALS feature vectors, SentEval STS accuracy.
- **Method**:
 1. **Dimensionality Reduction**: Apply PCA to the high-dimensional WALS feature matrix to reduce it to $k$ components (matching the subspace dimension).
 2. **Observed Correlation**: Compute the Pearson correlation between the observed shift vector (difference in mean embeddings) and the reduced WALS difference vector.
 3. **Null Distribution (Label Permutation)**:
 - Permute the language labels of the frequency vectors (shuffling which frequency vector belongs to which language) multiple times.
 - For each permutation, recompute the shift vector and its correlation with the *fixed* WALS features.
 - This generates a null distribution of correlations under the hypothesis that "language identity is random".
 4. **P-Value**: Calculate the proportion of null correlations that are greater than or equal to the observed correlation.
- **Output**: Correlation coefficients and p-value.

### 3.5 Permutation Test (FR-004)
- **Input**: Observed similarity scores, language pairs.
- **Method**:
 1. **Null Distribution Generation**: Generate $N=1000$ samples by:
 - Comparing the observed subspace against **within-language similarity samples** (e.g., Llama-EN vs Mistral-EN).
 - Shuffling language pairs (swapping frequency labels) to create a null distribution of cross-lingual similarities.
 2. For each permutation, recompute the subspace similarity.
 3. Compute p-value: $P(\text{sim}_{\text{observed}} \le \text{sim}_{\text{null}})$.
- **Output**: p-value (standard decimal precision).

### 3.6 Token Overlap Baseline
- **Input**: Ranked token lists for English and non-English models.
- **Method**: Calculate the overlap ratio of the top-ranked tokens. Compare this ratio against a baseline generated from **randomly generated orthogonal bases** (geometric baseline) to ensure the overlap is not due to random chance.
- **Output**: Overlap percentage and baseline comparison.

## 4. Statistical Rigor & Assumptions

- **Multiple Comparisons**: Bonferroni correction applied for multiple language pairs (EN-FR, EN-ZH).
- **Power Analysis**: N=1000 permutations ensures high power for detecting shifts > 0.05.
- **Causal Claims**: No causal claims made. Results are associational (typological features correlate with subspace shift).
- **Measurement Validity**: WALS features are standard typological markers. SentEval STS is a standard benchmark.
- **Collinearity**: Acknowledge that token frequencies and model weights are correlated; report descriptive statistics.
- **Tautology Avoidance**: The Label Permutation null model ensures that the correlation between shift and WALS is not merely a function of language identity.

## 5. Compute Feasibility & Escape Hatch

- **CPU-First**: SVD of $W_U$ (4k x 4k) and permutation test (1000 iterations) are CPU-tractable.
- **GPU Escape**: Not required for SVD or permutation. If model loading fails due to VRAM limits (unlikely for CPU-only weights), use `device="cpu"` with `load_in_8bit`.
- **Streaming**: All large datasets (RedPajama, OSCAR) are streamed to avoid OOM.

## 6. Risk Mitigation

- **Missing Data**: If OSCAR is unavailable, use Wikipedia and log the limitation. Task T068 will quantify the bias.
- **Numerical Instability**: Use `scipy.linalg.svd` with `full_matrices=False` and check for small singular values.
- **Vocabulary Mismatch**: Implement a shared subword vocabulary mapping layer (FR-008) and compute similarity only on the intersection.
