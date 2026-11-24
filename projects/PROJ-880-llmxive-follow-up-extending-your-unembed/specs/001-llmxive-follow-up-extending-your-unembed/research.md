# Research: llmXive cross‑lingual edge‑spectrum analysis

## Objective
Determine whether the “edge spectrum” subspace (top-100 singular vectors of the unembedding matrix $W_U$) encodes a universal, language-agnostic 'common sense' prior or reflects language-specific syntactic noise.

## Decision / Rationale
- **Compute Strategy**: **CPU-first**. The unembedding matrix $W_U$ is small enough to fit in RAM. SVD via `scipy.sparse.linalg.svds` and permutation tests via vectorized NumPy are tractable within the 6h GitHub Actions limit. No GPU is required.
- **Dataset Strategy**:
  | Role | Dataset | Verified URL(s) | Notes |
  |------|---------|-----------------|-------|
  | Token Frequencies | RedPajama (EN), Common Crawl (others) | `https://huggingface.co/datasets/allenai/redpajama-1b` (EN), and respective HF paths for Common Crawl. | Streamed via `datasets` to fit RAM. $\ge$ 1M token guard enforced. |
  | Typological Features | WALS | *No valid verified URL provided in block* | The provided URL in the verified block refers to a "bankless" dataset; the project will use the official WALS repository/CSV as described in spec, but will flag the verified-URL mismatch. |
  | Performance Bench | XTREME / XNLI | `google/xtreme` (via HF `datasets`) | Used for independent validation of shift across multiple languages. |

- **Statistical Rigor**:
  - **Ambient Space Alignment**: Because Llama/Mistral and BLOOM have different hidden dimensions, direct comparison of the right singular vectors $V$ is undefined. 
    1. **Vocab Alignment**: $U$ matrices are aligned to a common 11,200-dimensional space based on the shared subword vocabulary (Q136293754).
    2. **Hidden Space Alignment**: To compare $V$ subspaces (hidden-side anisotropy) across models, we compute an orthogonal Procrustes transformation $P$ that maps the hidden space of model $A$ to model $B$, derived from the embeddings of the shared 11,200-token vocabulary.
  - **Mean Embedding Projection**: To avoid ambient space mismatches, the mean embedding $\hat{\mathbf{h}}$ (which lives in the model's hidden space $D$) is projected onto the $V$ matrix (the right singular vectors of $W_U$, also in space $D$). This yields coordinates in the 100-dimensional edge-spectrum subspace.
  - **Multiple Comparisons**: Bonferroni correction ($\alpha = 0.05/3$) is applied to the three components of the permutation test to prevent Type I errors.
 - **Power Analysis**: For a Pearson $r=0.5$ at [deferred] power, $\ge$ 29 languages are needed. With a limited number of languages, the study is acknowledged as under-powered; results will be framed as associational/exploratory.
  - **Causal Inference**: This is an observational study. All claims are framed as associations between subspace orientation and linguistic typology.
  - **Collinearity**: Token frequencies and model weights are treated as distinct; we use the Moore-Penrose pseudo-inverse $W_U^+$ to isolate the effect of the frequency distribution $f$ on the mean embedding.

## Expected Deliverables
- `edge_spectrum.json`: Top-100 singular vectors ($U$ and $V$) per model/language.
- `frequency_list_{lang}.json`: Normalized token distributions.
- `token_attribution_{model}.json`: Ranked tokens by logit weight.
- `mean_embedding_{lang}.json`: $\hat{\mathbf{h}}$ and uniform baseline vectors.
- `cross_projection.json`: Coordinates of $\hat{\mathbf{h}}$ in the $V$-basis.
- `baseline_report.json`: Projections of uniform baseline vectors.
- `similarity_matrix.json`: Pairwise subspace similarity (sum of squared cosines).
- `similarity_metric.json`: Delta similarity values vs controls.
- `permutation_test.json`: P-values and significance flags.
- `control_analysis.json`: Null distribution statistics.
- `validation.json`: Pearson $r$ for WALS and XTREME correlations.
- `feasibility_report.json`: Runtime, memory, and dataset verification timestamps.
- `sensitivity_analysis.json`: Results from mask-off pipeline.
