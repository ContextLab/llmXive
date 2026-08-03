# Research: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## 1. Problem Statement & Hypothesis

**Hypothesis**: The "edge spectrum" subspace (top-$k$ singular vectors of $W_U$) is not a universal, language-agnostic "common sense" prior. Instead, its composition shifts to reflect language-specific syntactic noise and typological differences.

**Null Hypothesis ($H_0$)**: The geometric alignment (cosine similarity) of edge spectrum subspaces between English and non-English models is indistinguishable from the alignment observed within English models (within-language variation).

**Alternative Hypothesis ($H_1$)**: The cross-lingual alignment is significantly lower than the within-language alignment, indicating a typological shift in the bias encoded by the edge spectrum.

## 2. Dataset Strategy

We strictly adhere to the `# Verified datasets` block. No fabricated or unverified URLs are used.

| Dataset | Purpose | Source / Verification | Access Method |
| :--- | :--- | :--- | :--- |
| **RedPajama-Data-1T** | English token frequency distribution ($f_{EN}$) | `togethercomputer/RedPajama-Data-1T` (Hugging Face) | `datasets.load_dataset(..., streaming=True)` |
| **OSCAR (French)** | French token frequency distribution ($f_{FR}$) | `oscar` (Hugging Face, filtered by `fr`) | `datasets.load_dataset("oscar", "unshuffled_deduplicated_fr", streaming=True)` |
| **OSCAR (Chinese)** | Chinese token frequency distribution ($f_{ZH}$) | `oscar` (Hugging Face, filtered by `zh`) | `datasets.load_dataset("oscar", "unshuffled_deduplicated_zh", streaming=True)` |
| **WALS** | Typological features for EN, FR, ZH | `wals/wals` (Hugging Face / GitHub) | Direct download of CSV/JSON from verified repo |
| **SentEval** | Performance validation (STS task) | `facebookresearch/SentEval` (GitHub) + **SICK-R/STS-B** | Clone repo; download SICK-R/STS-B test sets; run evaluation code |
| **Model Weights** | $W_U$, $W_E$ matrices | Hugging Face Hub (Llama-3, Mistral, BLOOM) | `transformers.AutoModel.from_pretrained(..., device_map="cpu")` |

**Data Availability Note**:
- **OSCAR**: We replace raw Common Crawl with OSCAR, a cleaned, language-filtered subset. This ensures the frequency distribution reflects linguistic typology rather than web noise (HTML, code-switching).
- **Feasibility Check**:
 - **RedPajama/OSCAR**: Stream the dataset and count the first $N$ tokens (where $N \ge [deferred]$) to estimate $f$. If the corpus is exhausted before $N$, log the limitation and proceed with the maximum available.
  - **Model Weights**: BLOOM-large (~large), MistralB (~large), Llama-8B (~16GB). Loading all three simultaneously exceeds the RAM limit of the CI runner.
    - **Strategy**: Load one model at a time. Perform SVD and save the subspace matrix to disk (`data/processed/{model}_svd.npy`). Unload model. Repeat for next model. This ensures memory safety.

## 3. Methodology

### 3.1. Edge Spectrum Extraction & Shared-Vocabulary Projection (FR-001, FR-002, FR-008)
1. **Shared-Vocabulary Intersection**:
   - Load tokenizers for all target models (Llama-3, Mistral, BLOOM).
   - Compute the intersection of token IDs: $V_{shared} = V_{Llama} \cap V_{Mistral} \cap V_{BLOOM}$.
   - Create a mapping index that re-indexes rows of $W_U$ and $W_E$ to the shared vocabulary.
2. **Load Model**: Load model $M$ into CPU memory. Extract $W_U$, project to $W_U^{shared}$ using the shared index.
3. **Perform SVD**: Compute $W_U^{shared} = U \Sigma V^T$ using `scipy.sparse.linalg.svds` (Arnoldi iteration) to extract top-$k$ singular vectors ($U_{shared} \in \mathbb{R}^{d_{model} \times k}$).
4. **Procrustes Alignment**: If models have different embedding dimensions, apply orthogonal Procrustes alignment to $U_{shared}$ matrices to a common reference frame before computing similarity.
5. **Save & Unload**: Save $U_{shared}$ to disk. Unload model to free memory.
6. **Compute Similarity**: Calculate cosine similarity between aligned $U_{shared}^{M1}$ and $U_{shared}^{M2}$ for all model pairs.

### 3.2. Mean Embedding & Token Attribution (FR-003, FR-005, FR-008)
1. **Re-tokenization**:
   - Stream RedPajama/OSCAR for target language.
   - Re-tokenize the corpus using the target model's tokenizer to generate a frequency vector $f$ of size $|V|$.
2. **Frequency Count**: Count tokens until $\ge [deferred]$ tokens are processed. If the corpus is exhausted before $N$, log a limitation and proceed with the maximum available.
3. **Mean Embedding**: Compute $\hat{h} = W_E^{shared} \times f^{shared}$ (using the shared-vocab projected embedding matrix).
4. **Shift Vector**: Compute $\Delta = \hat{h}_{EN} - \hat{h}_{Target}$. This vector is now in the shared coordinate system.

### 3.3. Validation (FR-007)
1. **WALS Correlation**:
   - Retrieve WALS feature vectors for EN, FR, ZH.
   - **Dimensionality Reduction**: Apply PCA to the high-dimensional shift vector $\Delta$ to reduce it to $N$ components, where $N$ matches the number of WALS features.
   - Compute Pearson correlation between the reduced shift vector and the WALS feature difference vector.
2. **SentEval Performance**:
   - Download SICK-R/STS-B test sets explicitly.
   - Execute SentEval code against these test sets to generate performance metrics (STS accuracy) for each language.

### 3.4. Statistical Significance (FR-004, US-3)
1. **Permutation Test**:
   - **Null Distribution**: Generate $N=1000$ samples by:
     a. **Within-Language Baseline**: Compare subspaces of same-language model pairs (e.g., Llama-EN vs Mistral-EN).
     b.  Shuffle the language labels of the frequency vectors to generate null distribution
   - **Observed Statistic**: Compute the similarity between observed cross-lingual subspaces (from 3.1).
   - **P-Value**: Calculate $P(\text{Sim}_{obs} \le \text{Sim}_{null})$.

### 3.5. Feasibility & Alignment Checks (T060, T065)
1. **Feasibility Check (T060)**: Implement `check_svd_feasibility` in `code/main.py`. Log detailed warnings if memory usage exceeds limits. Mark T012b as SKIPPED if necessary. Write Output: Generate `data/processed/feasibility_report.json` with memory/time metrics.
2. **Vocabulary Alignment Check (T065)**: Implement shared-vocabulary intersection check in `model_analyzer.py`. Log warnings if overlap ratio is low. Write Output: Generate `data/processed/vocab_alignment_warning.json` with overlap metrics and recommended actions.

## 4. Compute Feasibility & Escape Hatch

**CPU-First Strategy**:
- **SVD**: `scipy.sparse.linalg.svds` is CPU-optimized and memory efficient.
- **Permutation**: 1,000 iterations of dot products on $4096 \times k$ matrices. Trivial for CPU.
- **Data Streaming**: `datasets` library with `streaming=True` avoids loading 1T tokens into RAM.

**GPU Escape Hatch**:
- If `scipy.sparse.linalg.svds` fails due to numerical instability or memory fragmentation on the 7GB limit runner, the execution stage will detect the error.
- **Fallback**: Re-run on Kaggle GPU (free tier). Load model in `float16` or `8-bit` (if available) to reduce memory footprint, allowing simultaneous processing of two models. The plan remains the same; only the execution environment changes.

## 5. Decision Rationale

- **Why Shared-Vocabulary Projection?** To resolve the category error of comparing subspaces from different vocabularies. This ensures the similarity metric is defined and meaningful.
- **Why OSCAR?** OSCAR is a cleaned, language-filtered subset of Common Crawl, providing stable, representative token frequencies without the noise of raw web crawls.
- **Why Within-Language Null?** To test the specific hypothesis of typological shift, the null must represent "expected variation within the same language," not random geometric noise.
- **Why Streaming?** The RedPajama/OSCAR datasets are too large for the CI runner. Streaming ensures we use *real* data without fabricating a smaller synthetic subset.
- **Why Separate Model Loading?** Loading multiple large models simultaneously requires substantial RAM. Loading one-by-one respects the 7GB limit.
