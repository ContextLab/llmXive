# Research: llmXive cross-lingual edge-spectrum analysis

## Objective
Determine if the "edge spectrum" subspace (dominant singular vectors of $W_U$) is a universal common-sense prior or a language‑specific artifact by quantifying the geometric rotation across multiple linguistic typologies.

## Decision / Rationale

- **Compute Strategy**: **CPU‑first**. SVD on the unembedding matrix ($W_U$) for the target models is computationally tractable on a modest‑core CPU if we load only the `lm_head` weights rather than the full model. All subsequent linear algebra (pseudo‑inverse, projection) and statistical tests (bootstrap, permutation) are CPU‑native.
- **Dataset Strategy**: 
    - **Token Frequencies**: We use the `datasets` library to programmatically load Common Crawl language‑filtered subsets. We enforce a strict $\ge 1\,\text{M}$ token minimum to ensure stability of the mean embedding $\hat{\vh}$.
    - **Typological Features**: We use the verified WALS dataset from the Hugging Face hub: `https://huggingface.co/datasets/linguistics/wals` (verified 2026‑08‑20). This replaces the previously mismatched Taiko URL.
    - **Performance Validation**: We use the verified SentEval‑CR JSONL source: `https://huggingface.co/datasets/SetFit/SentEval-CR/resolve/main/test.jsonl` (verified 2026‑08‑20).
- **Statistical Rigor**:
    - **Permutation**: 10 000 iterations are required to establish a robust null distribution. To fit the 6 h CI window, we will use vectorized NumPy operations for the cosine similarity calculations and apply a Bonferroni correction ($\alpha=0.05/3$) across the three null components (within‑language, across‑model, model‑specific). This directly satisfies **FR‑004** and the reviewer’s **methodology-08b0aa04** concern.
    - **Bootstrap**: Two complementary bootstraps are performed:
        1. *Parametric bootstrap of singular vectors*: perturb $W_U$ with small Gaussian noise and recompute SVD to obtain a CI for subspace cosine similarity (addresses the mathematical concern that token‑frequency resampling does not affect SVD).
        2. *Token‑frequency bootstrap*: resample the token‑frequency observation set to generate CIs for mean‑embedding and baseline‑adjusted shift metrics (as required by FR‑015).
    - **Correction**: Bonferroni correction ($\alpha = 0.05/3$) is applied to the combined p‑values from the three null distribution components.
- **Cosine Similarity Computation (FR‑002)**: For every pair of language‑model subspaces we compute the cosine similarity between their top‑k singular vector matrices. Specifically, given matrices $U_i$ and $U_j$ (each $k \times d$), we flatten each row‑wise, normalize, and compute `cos_sim = (U_i_flat · U_j_flat) / (||U_i_flat|| * ||U_j_flat||)`. This yields a single similarity score per pair, stored in `similarity_matrix_*.json`. This explicit method addresses **methodology-16c4d829**.

### Dataset Strategy Table

| Role | Dataset | Verified URL(s) | Access notes |
|------|---------|-----------------|--------------|
| Token Frequencies | Common Crawl | `datasets.load_dataset("common_crawl", name="<lang>")` | Programmatic streaming via HF. |
| Typological Features | WALS | `https://huggingface.co/datasets/linguistics/wals` | Verified; contains binary typological feature matrix. |
| Performance Bench | Multilingual SentEval | `https://huggingface.co/datasets/SetFit/SentEval-CR/resolve/main/test.jsonl` | Verified. |

## Experimental Pipeline Overview

1. **Weight Extraction**: Load `lm_head` for Llama‑3, Mistral, BLOOM. 
2. **Masked SVD**: Apply language‑specific token masks (FR‑032) to $W_U$. Compute top‑100 singular vectors using `scipy.sparse.linalg.svds`.
3. **Frequency Guard**: Stream Common Crawl subsets. If tokens $< 1{,}000{,}000$, abort with `DataInsufficiencyError`.
4. **Vocab Alignment**: Map model‑specific IDs to the shared subword vocabulary (size 11 200, see Q136293754).
5. **Mean Embedding Projection**: Compute the Moore‑Penrose pseudo‑inverse $W_U^{+}$ (regularized $\lambda=1e-5$) and calculate $\hat{\vh}=W_U^{+}\times f$.
6. **Baseline Adjustment**: Compute $\hat{\vh}_{\text{uniform}}$ using a flat token distribution. The shift vector is $\Delta\vh = \hat{\vh}_{\text{lang}} - \hat{\vh}_{\text{uniform}}$. **Note:** $\Delta\vh$ remains a linear function of the raw token frequencies; we will report this dependence explicitly in the validation narrative (addresses concern 7c1e1b28).
7. **Geometric Comparison**: Pairwise cosine similarity of subspace bases (FR‑002). Calculate $\Delta$‑similarity by subtracting matched‑architecture control pairs (FR‑028).
8. **Significance Testing**: Run the 10 k‑iteration permutation test against the combined null distribution (within‑language, across‑model, model‑specific) with Bonferroni correction (FR‑004, methodology‑08b0aa04).
9. **External Correlation**: Pearson $r$ between $\Delta\vh$ (baseline‑adjusted) and WALS feature differences / SentEval STS gaps, reporting 95 % CIs.
10. **Ablation**: Randomize $f$ within each language (preserving total count) and repeat the full pipeline; loss of correlation (p > 0.05) validates that the original relationship is not artefactual.

## Expected Deliverables
- `edge_spectrum_{model}_{lang}_{hash}.json`: Subspace bases.
- `frequency_list_{lang}_{hash}.json`: Token frequency distributions.
- `similarity_matrix_{hash}.json`: Pairwise cosine similarity matrix with bootstrap CIs.
- `similarity_report_{hash}.json`: Detailed similarity metrics and CIs.
- `permutation_test_{hash}.json`: Combined p‑values and significance flag.
- `validation_{hash}.json`: WALS and SentEval correlations.
- `ablation_report_{hash}.json`: Ablation outcomes.
- `feasibility_report_{hash}.json`: Resource usage and runtime logs.

All artifacts are validated against their JSON‑Schema contracts (see `contracts/`). 

