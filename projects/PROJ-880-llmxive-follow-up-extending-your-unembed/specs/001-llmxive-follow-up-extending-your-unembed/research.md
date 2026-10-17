# Research: llmXive cross‑lingual edge‑spectrum analysis

## Objective
Determine whether the “edge spectrum” subspace (the top‑100 singular vectors of the unembedding matrix $W_U$) encodes a universal, language‑agnostic prior **or** reflects language‑specific syntactic noise. **Only correlational (observational) conclusions are drawn.**

## Decision / Rationale
- **Compute Strategy**: **CPU‑first**. All linear‑algebra operations (SVD, pseudo‑inverse, bootstrap, permutation) are tractable on a multi‑core CPU when we load only the `lm_head` weights. No GPU is required.
- **Dataset Strategy**:
  | Role | Dataset | Verified URL(s) | Notes |
  |------|---------|-----------------|-------|
  | Token Frequencies (language‑specific) | Common Crawl language‑filtered splits | `https://huggingface.co/datasets/common_crawl/en`<br>`https://huggingface.co/datasets/common_crawl/fr`<br>`https://huggingface.co/datasets/common_crawl/zh`<br>`https://huggingface.co/datasets/common_crawl/ar`<br>`https://huggingface.co/datasets/common_crawl/sw`<br>`https://huggingface.co/datasets/common_crawl/de`<br>`https://huggingface.co/datasets/common_crawl/es`<br>`https://huggingface.co/datasets/common_crawl/hi`<br>`https://huggingface.co/datasets/common_crawl/ja`<br>`https://huggingface.co/datasets/common_crawl/pt` | Verified on HuggingFace; each download is logged with a verification timestamp (SC‑008). |
  | Typological Features | WALS (binary typology matrix) | `https://huggingface.co/datasets/linguistics/wals` | Verified HuggingFace dataset; PCA‑reduced before correlation (see below). |
  | Performance Bench | Multilingual SentEval STS | `https://huggingface.co/datasets/SetFit/SentEval-CR/resolve/main/test.jsonl` | Verified; provides STS accuracy per language. |
- **Statistical Rigor**:
  - **Permutation Test**: 10 000 iterations, three null components (within‑language, across‑model, model‑specific). Bonferroni‑corrected α = 0.05/3. Vectorized NumPy ensures runtime ≤ 5 h; if exceeded, a warning is logged and the run aborts (FR‑004).
  - **Bootstrap**: Two bootstraps – (1) parametric perturbation of $W_U$ (σ = 1e‑4) for subspace similarity CI; (2) token‑frequency resampling (≥ 1 000 replicates) for mean‑embedding metrics (FR‑015). Both report 95 % CI.
  - **Similarity (FR‑002)**: Compute the **rotation‑invariant subspace similarity** as the sum of squared cosines of the principal angles between two subspace bases $U_i$ and $U_j$. This metric is invariant to orthogonal rotations, eliminating confounds from arbitrary basis ordering, and directly measures the *shared subspace geometry* that underlies the hypothesized prior (see Construct‑Validity Rationale in plan.md).
  - **Power Analysis**: With 10 languages, a two‑tailed Pearson test at α = 0.05 has ≈80 % power to detect |r| ≈ 0.60. Effects smaller than this are reported as under‑powered (SC‑005).
  - **Covariate Controls**: In Phase 8 we regress each shift vector on three covariates—corpus‑size (token count per language), tokenization granularity (average subword length), and model‑size (parameter count). This mitigates confounds from differing training data or architecture (addresses methodology‑1c65c6d2).
  - **WALS PCA**: Binary WALS feature vectors are reduced via PCA (explaining ≥ 80 % variance) before Pearson correlation, satisfying continuity assumptions.
- **Validation**: Correlate baseline‑adjusted shift vectors $\Delta\mathbf{h}$ with (a) WALS typological differences **after PCA reduction** (FR‑007) and (b) Multilingual SentEval STS performance drops using Pearson $r$ (95 % CI). Perform an ablation that randomizes token frequencies while preserving total counts; loss of correlation (p > 0.05) confirms non‑artefactual relationship (FR‑032). Include paired‑architecture controls (FR‑027) and uniform‑frequency baseline comparison (FR‑029).

## Expected Deliverables
- `edge_spectrum_{model}_{lang}_{hash}.json` – edge‑spectrum bases (FR‑014).  
- `frequency_list_{lang}_{hash}.json` – token‑frequency vectors (FR‑006).  
- `token_attribution_{model}_{hash}.json` – top‑logit tokens (FR‑003).  
- `mean_embedding_{lang}_{hash}.json` – $\hat{\mathbf{h}}$ and uniform baseline (FR‑005, FR‑029).  
- `similarity_matrix_{hash}.json` – pairwise rotation‑invariant similarity scores with bootstrap CI (FR‑002, FR‑015).  
- `similarity_report_{hash}.json` – detailed similarity metrics (FR‑023).  
- `permutation_test_{hash}.json` – combined p‑value, component p‑values, Bonferroni flag (FR‑004, FR‑026).  
- `validation_{hash}.json` – WALS & SentEval correlations (FR‑007).  
- `control_analysis_{hash}.json` – paired‑architecture and covariate regression results (FR‑027, new covariate analysis).  
- `ablation_report_{hash}.json` – ablation outcomes (FR‑032).  
- `feasibility_report_{hash}.json` – runtime, memory, CPU usage, and any abort warnings (FR‑024).  
- `checksum_manifest_{hash}.json` – SHA‑256 checksums for all derived artifacts (FR‑020).  

All artifacts will be validated against their JSON‑Schema contracts in `contracts/`.

---


