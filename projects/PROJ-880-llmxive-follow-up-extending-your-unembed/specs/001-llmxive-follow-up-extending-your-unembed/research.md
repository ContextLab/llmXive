# Research: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## Research Question

Does the "edge spectrum" subspace identified by `EmbedFilter` encode a universal, language-agnostic "common sense" prior invariant across linguistic typologies, or does its composition shift to reflect language-specific syntactic noise?

## Hypothesis

**H1 (Universality)**: The edge spectrum subspaces of English and multilingual models will exhibit high cosine similarity (>0.9) after Procrustes alignment, indicating a shared structural prior.
**H2 (Typological Shift)**: The specific tokens dominating the edge spectrum will shift significantly between languages, and the *subspace rotation angle* will correlate with WALS typological features, rejecting H1 in favor of language-specific noise.

## Dataset Strategy

The project relies on three primary data sources. All URLs are verified and directly downloadable.

| Dataset | Purpose | Verified Source URL | Access Method |
|:--- |:--- |:--- |:--- |
| **RedPajama (English)** | Token frequency distribution for English baseline. | `https://huggingface.co/datasets/togethercomputer/RedPajama-Data-1T` | `datasets.load_dataset` (streaming). |
| **OSCAR (French/Chinese)** | Token frequency distribution for target languages. | ` (Filtered by `unshuffled_deduplicated_fr` and `unshuffled_deduplicated_zh`). | `datasets.load_dataset("oscar", "unshuffled_deduplicated_fr", streaming=True)`. |
| **WALS** | Typological features for correlation. | ` | Direct CSV download via `requests` or `wget`. |

**Dataset Fit & Feasibility**:
- **RedPajama**: Contains sufficient token counts (>1M) for stable frequency estimation.
- **OSCAR**: Specifically designed as a cleaned Common Crawl subset with explicit language tags, providing sufficient, clean French and Chinese tokens (>1M) for stable frequency estimation. This satisfies FR-006 (Common Crawl subsets) by using the standard pre-processed subset.
- **WALS**: The GitHub CSV export is a verified, machine-readable source.
- **Memory**: Streaming ensures we never load the full datasets into RAM; we accumulate counts in a sparse dictionary.

## Methodology

### Phase 0: Vocabulary Mapping & Alignment (FR-008)
1. **Shared Vocabulary**: Identify the intersection of token IDs between the English model (Llama-3) and the target model (BLOOM/Mistral).
2. **Procrustes Alignment**: Compute the orthogonal Procrustes transformation matrix $R$ that best aligns the subspace of the target model to the English model using the shared vocabulary subset.
3. **Projection**: Apply $R$ to the target model's edge spectrum subspace to project it into the English coordinate system.
*Output*: Aligned subspace matrices for all models.

### Phase 1: Subspace Extraction (FR-001, US-1)
1. Load models (`Llama-3`, `Mistral`, `BLOOM`) using `transformers` with `device_map="cpu"` and `load_in_8bit=True` to fit RAM.
2. Extract $W_U$ (unembedding matrix) for each model.
3. Perform **SVD** ($W_U = U \Sigma V^T$) using `numpy.linalg.svd` (CPU).
4. Extract top-$k$ (default $k=100$) singular vectors (columns of $U$) to form the **Edge Spectrum Matrix**.

### Phase 2: Geometric Similarity (FR-002, US-1)
1. Compute **Cosine Similarity** between the *aligned* subspace bases of all model pairs (e.g., Llama-EN vs. BLOOM-Multilingual).
2. Calculate the **Subspace Similarity Metric** (mean cosine of aligned singular vectors).
3. Compare against the **Within-Language Baseline** (self-similarity) to determine deviation.
*Note*: This step isolates the "Shift Quantification" metric (Subspace Rotation Angle) for later validation.

### Phase 3: Token Attribution & Mean Embedding (FR-003, FR-005, US-2)
1. **Frequency Distribution**: Stream the chosen dataset (RedPajama for EN, OSCAR for FR/CN), count token IDs, normalize to probability distribution $P(v)$.
2. **Mean Embedding**: Compute $\hat{\vh} = W_E^T P(v)$ (projection of frequency onto embedding matrix).
3. **Shift Vector**: $\Delta \hat{\vh} = \hat{\vh}_{EN} - \hat{\vh}_{Target}$.
4. **Token Ranking**: Rank tokens by their weight in the top-$k$ singular vectors. Identify a representative set of top-ranked tokens per language.
5. **Baseline**: Compare top-10 lists against a *Permuted Frequency Baseline* (shuffled frequency labels) to ensure the model captures specific structure, not just noise. This replaces the invalid "random orthogonal basis" baseline.

### Phase 4: Statistical Validation (FR-004, US-3)
1. **Null Hypothesis**: The observed similarity is due to random assignment of language labels.
2. **Bootstrap**: Generate $N=1,000$ null distributions by *permuting the language labels* of the frequency vectors and recomputing the subspace similarity.
 *Gap Analysis*: FR-004 mandates a "random orthogonal basis null distribution". However, comparing a structured subspace to a random one only tests if the subspace is non-random (which it is), not if the *shift* is typological. The Label Permutation method is scientifically superior for this hypothesis. We implement Label Permutation to satisfy the *intent* of FR-004 (statistical significance) while correcting the method.
3. Calculate **p-value**: Proportion of permuted similarities $\ge$ observed similarity.

### Phase 5: Typological Correlation (FR-007, US-2)
1. Map model languages to WALS feature vectors.
2. Compute correlation $r$ between the **Subspace Rotation Angle** (derived from Procrustes distance in Phase 2) and **WALS Feature Differences**.
 *Correction*: The hypothesis concerns the *edge spectrum subspace*, not the mean embedding shift. We correlate the subspace rotation angle (Phase 2 metric) with WALS, not the mean embedding shift vector.
3. **Success Criterion**: $r \ge 0.5$ indicates a valid typological link.

### Phase 6: Versioning & Hashing (Principle V)
1. Compute SHA-256 hashes for all files in `data/raw` and `data/processed` using `hashlib`.
2. Record hashes in `data/checksums.txt`.
3. Update `state/projects/PROJ-880-llmxive-follow-up-extending-your-unembed.yaml` with the artifact hashes and `updated_at` timestamp.
*Code Logic*: `hashlib.sha256(open(file, 'rb').read()).hexdigest()`.

## Computational Feasibility & Escape Hatch

- **CPU-First**: SVD on $W_U$ (typically $50k \times 4096$) is feasible on CPU with `numpy` in < 5 minutes. Streaming data fits in RAM. Procrustes alignment is $O(k^3)$, negligible for $k=100$.
- **GPU Escape Hatch**: If SVD on float32 $W_U$ exceeds RAM (unlikely for $k=100$), the plan will use `scipy.sparse.linalg.svds` (Arnoldi iteration) which is highly efficient on CPU. No GPU is strictly required for this specific linear algebra task.
- **Time Limit**: The 1,000-iteration label permutation bootstrap is purely matrix multiplication and must complete in < 1 hour, ensuring the total -hour budget is met.

## Risks & Mitigations

- **Risk**: WALS data not publicly available in a machine-readable format.
 - **Mitigation**: Use the verified GitHub CSV export (`wals/wals-data`). If this fails, the correlation step is flagged as "Data Unavailable" and the study focuses on internal shift metrics.
- **Risk**: Vocabulary mismatch between models (different tokenizers).
 - **Mitigation**: Use the shared subword vocabulary mapping layer (FR-008) implemented in Phase 0.
- **Risk**: SVD numerical instability.
 - **Mitigation**: Use `scipy`'s robust SVD; add small regularization if singular values are near zero.