# Research: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

## Executive Summary

This research validates the hypothesis that **prompt semantic entropy** (derived from MS-COCO image captions) correlates with **activation variance** in Diffusion Transformers (DiT) **during the generative process**. If confirmed, a dynamic router using pre-optimized rotation matrices (derived from clustering prompts by entropy and analyzing their corresponding **generated** activation histograms) will reduce quantization error (W2A4) for high-entropy prompts without exceeding a minimal runtime overhead.

## Dataset Strategy

| Dataset | Source URL | Usage | Verification Status |
|:--- |:--- |:--- |:--- |
| **MS-COCO 2017** | ` | Source for **image data** (ground truth) and **prompt text (captions)**. Captions serve as the **sole conditioning input** for the DiT generation. | Verified: Direct parquet link. |
| **MS-COCO (Alt)** | ` | Fallback source if primary link fails or rate-limited. | Verified: Direct parquet link. |

**Note**: No access-gated datasets (e.g., ADNI, HCP) are used. All data is programmatically downloadable via Hugging Face `datasets` library. The **FLUX Prompts** dataset is **not used**; the study relies on the native captions of the MS-COCO validation set to ensure a 1:1 pairing between prompt and ground-truth image.

## Methodological Rigor & Statistical Plan

### 1. Data Point Definition & Pairing Strategy (Corrected)
To validate the hypothesis that prompt complexity drives activation variance, every data point $(x, y)$ is a paired observation derived from a **text-to-image generation** process:
- **$x$ (Prompt Entropy)**: Semantic entropy of the MS-COCO image caption.
- **$y$ (Activation Variance)**: Variance of intermediate activation tensors from the DiT **during the generation of a latent sequence** conditioned **only** on the caption.
- **Pairing Mechanism**:
 1. Load MS-COCO parquet: `(image_id, caption, ground_truth_image)`.
 2. Use `caption` as the **prompt** for the DiT.
 3. Run DiT **generation** (text-to-image) using the `caption`.
 4. Measure **Activation Variance** from the intermediate latents of this **generative trajectory**.
 5. Store the pair `(caption_entropy, activation_variance)` linked by `image_id`.
 6. Use `ground_truth_image` **only** for the final FID/CLIP evaluation against the generated image.
- **Rationale**: This ensures the activation variance is a direct function of the prompt's semantic complexity, not an unrelated property of the ground-truth image.

### 2. Semantic Entropy Proxy (Corrected)
- **Problem**: `facebook/bart-large-cnn` is a summarization model and cannot generate diverse paraphrases required for semantic entropy estimation.
- **Solution**: Use a **generative** proxy model to produce $S$ semantic variations of the prompt.
- **Proxy Tool**: `sentence-transformers/all-MiniLM-L6-v2` (for clustering) + a small generative model (e.g., `google/t5-v1_1-small` or `mistralai/Mistral-7B-Instruct-v0.2` via `text-generation` with low temperature) to generate $S=5$ paraphrases.
- **Procedure**:
 1. Input: Caption $C$.
 2. Generate $S$ paraphrases $\{P_1,..., P_S\}$ using the generative proxy.
 3. Embed all $S+1$ texts (including $C$) using `sentence-transformers`.
 4. Cluster the embeddings using `sklearn.cluster.KMeans` with $K$ (e.g., 3-5) to capture semantic clusters.
 5. Compute **Semantic Entropy** as the entropy of the cluster distribution: $H = -\sum p_k \log p_k$.
- **Rationale**: This measures the diversity of semantic meanings the model associates with the prompt, which is the correct definition of semantic entropy for this hypothesis.

### 3. Correlation Analysis (FR-001, FR-002, SC-001)
- **Hypothesis**: $H_0: \rho = 0$ (No correlation between prompt entropy and activation variance). $H_1: \rho \neq 0$.
- **Method**:
 1. Sample $N=200$ diverse images from the MS-COCO 2017 validation set.
 2. Split data: **[deferred] Train (160)** for clustering/router derivation, **[deferred] Test (40)** for final validation (to avoid circularity).
 3. Compute **Semantic Entropy** for each caption using the generative proxy (Step 2).
 4. Run **Float32 Generative Pass** on a DiT (Stable Diffusion 2.1 on CPU; FLUX.1-dev/Wan 2.1 on GPU escape hatch) **conditioned ONLY on the caption**.
 5. Extract **Activation Variance** from intermediate layers (e.g., attention output, MLP output) of the **generated trajectory**.
 6. Compute **Pearson Correlation Coefficient ($r$)** and **p-value** between the set of entropy scores and the set of variance scores.
- **Rigor Check**:
 - **Multiple Comparisons**: If testing multiple layers, apply Bonferroni correction to the p-value threshold.
 - **Collinearity**: If multiple layers are analyzed, report Variance Inflation Factor (VIF) to ensure predictors are not definitionally identical.
 - **Causal Framing**: Claims are strictly associational. No causal inference is made.

### 4. Dynamic Router Construction (FR-003, FR-004) - Non-Circular
- **Training Phase ([deferred] Data)**:
 1. **Cluster by Predictor**: Cluster the 160 training prompts into $K=16$ bins based **solely on their Semantic Entropy ($x$)** using K-Means on the entropy values. This defines the router's decision boundaries.
 2. **Derive Matrices**: For each entropy bin, collect the activation histograms of the **generated trajectories** corresponding to that bin. Compute the cluster centroid of these histograms and derive the orthogonal rotation matrix $M_i$ for each bin $i$.
 3. **Lookup Table**: Build a table mapping Entropy Range $[min_i, max_i]$ to Matrix $M_i$.
- **Inference Phase (Test Data)**:
 - Map new prompt entropy (from the [deferred] test set) to the nearest bin index (clamping to [0, 15]).
 - Apply selected rotation matrix before W2A4 quantization.
- **Validation**: Evaluate the router's performance on the **held-out [deferred] test set** to ensure the mapping is predictive and not memorized.

### 5. Evaluation & Overhead (FR-006, FR-007, FR-008, SC-002, SC-003, SC-004)
- **Metrics**: FID, CLIP Score, MSE (quantization error).
- **Statistical Test**: Paired t-test (Dynamic vs. Static) on metric distributions. Threshold: $p < 0.05$.
- **Overhead**: Measure wall-clock time. Target: $\le 2\%$ increase.
- **Sensitivity Analysis (SC-005)**: Sweep entropy cut-offs by $\pm 5\%$ and report FID variance.

## Compute Feasibility & Hardware Strategy

### CPU-First Approach
- **Routing & Analysis**: All entropy calculation, clustering, correlation, and metric computation (FID/CLIP via CPU-optimized libraries) will run on the GitHub Actions CPU runner (multi-core, multi-GB RAM).
- **Data Streaming**: MS-COCO parquet files will be streamed (`datasets.load_dataset(..., streaming=True)`) to avoid loading the full dataset into RAM. Statistics will be accumulated online.

### GPU Escape Hatch (Kaggle)
- **Trigger**: If the selected DiT (FLUX.1-dev or Wan 2.1) fails to load or run on CPU due to memory constraints, the execution stage will automatically offload to a Kaggle GPU.
- **Scaled Down**:
 - Model: 8-bit quantized loading (`load_in_8bit`) if available, or full precision but limited to a small subset (e.g., a representative sample) for the correlation study.
 - Steps: Minimal diffusion steps (e.g., a small number) if full generation is required for FID, or use a proxy metric if full generation is too slow.
 - **Rationale**: A faithful CPU approximation of a large-scale parameter DiT generation pass is impossible. The GPU escape hatch allows the *real* computation on a scaled dataset, avoiding fabrication.

## Edge Case Handling
- **Entropy Out-of-Range**: Clamp to nearest boundary (Index 0 or 15).
- **Activation Outliers**: Log and default to median rotation matrix.
- **Proxy Failure**: Fallback to static OrbitQuant (median index).

## Data Hygiene & Versioning
- **Artifact Tracking**: All raw and processed data files are checksummed (SHA-256) and recorded in `state/artifact_hashes.json`.
- **Clustering Report**: A `data/processed/clustering_report.json` file will be generated containing the exact layers, subsets, and boundaries used for the 16 matrices. This file is a mandatory gate for Phase 2.