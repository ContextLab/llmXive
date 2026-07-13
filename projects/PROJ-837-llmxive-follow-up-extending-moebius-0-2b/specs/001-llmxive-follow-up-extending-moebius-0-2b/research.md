# Research: llmXive follow-up: extending "Moebius: 0.2B Lightweight Image Inpainting Framework with 10B-Level Pe"

## 1. Problem Statement & Hypothesis

**Hypothesis**: The structural complexity of a masked region in an image dictates the minimum model rank required for perceptual fidelity. By dynamically adjusting the rank of linear matrices ($L\lambda MI$) based on this complexity, we can achieve significant latency reductions on low-complexity regions without degrading image quality (FID difference ≤ 0.5) compared to static high-capacity baselines.

**Core Challenge**: Defining "complexity" in a way that is both computationally tractable and human-grounded. Current methods often rely on model performance (circular validation). This project proposes a human-rated ground truth (N=50) to train a gating mechanism that predicts complexity from synthetic proxies (gradient variance, texture entropy).

**Mode Distinction**:
- **CI Simulation Mode**: Validates the *mechanism* using a "Decoupled Synthetic Ground Truth" (random labels) and a "Moebius-Tiny" model. Results are labeled "Simulation-Only".
- **Research Mode**: Validates the *hypothesis* using external human-annotated data and the full architecture. This is the only mode that supports the "Human-Grounded" claim.

## 2. Dataset Strategy

**Source**: The project relies on the **Places365** dataset, available via the official MIT Places repository on HuggingFace.

| Dataset Name | Source URL | Usage | Validation Status |
| :--- | :--- | :--- | :--- |
| Places365 (Standard) | `https://huggingface.co/datasets/mit-places/Places365` | Primary source for image content. Used to generate masked regions. | Verified (Official MIT/HF). |
| Human Complexity Annotations | *External (Manual Source)* | Ground truth for Research Mode. | **Not Verified in CI** (Must be manually sourced and checksummed). |

**Data Loading Strategy**:
- The `data/loader.py` script will use `torch.utils.data.Dataset` to load a subset of the Places dataset.
- Images will be resized to 256x256 or 512x512 (configurable) to fit RAM.
- **Memory Constraint**: The dataset will be streamed from disk; no full in-memory loading of the entire dataset.
- **Synthetic Masks**: Generated on-the-fly or pre-generated and stored in `data/processed/` with metadata (gradient variance, texture entropy).

**Human Annotation Simulation (CI Mode)**:
- Since the CI environment cannot host a live crowdsourcing platform, `code/data/annotator.py` will simulate the N=50 participant study.
- **Crucial Distinction**: The simulation generates a "Decoupled Synthetic Ground Truth" (random 1-5 Likert scores) that is **independent** of the synthetic metrics (gradient variance, entropy) used for training. This prevents circular validation (FR-007).
- **Validity**: This simulation is a placeholder for the *data structure* and *noise profile*. The *actual* ground truth for the research hypothesis relies on the assumption that human ratings follow a specific distribution relative to synthetic metrics. The plan explicitly flags that real human annotation is an external dependency for the final paper, but the pipeline must be testable with decoupled data for CI.

## 3. Methodology

### 3.1. Complexity Metrics (Synthetic Proxies)
- **Gradient Variance**: Measures the intensity of edges within the masked region's boundary.
- **Texture Entropy**: Measures the randomness of pixel intensities in the masked area.
- **Validation**: Pearson correlation ($r$) between these metrics and ground truth (human or decoupled). For CI Mode, low correlation is expected (random labels). For Research Mode, a sufficiently high value of $r$ is required..

### 3.2. Dynamic Rank Modulation
- **Architecture**: A lightweight Convolutional Gating Head (≤15M params total) ingests the masked context.
- **Output**: A scalar complexity score $C \in [1, 5]$.
- **Modulation**: The score $C$ is mapped to a target rank $R$ for the $L\lambda MI$ matrices.
 - $C \le 2 \implies R \le 64$ ([deferred] of max capacity 128).
  - $C \ge 4 \implies R = 128$ (Full capacity).
  - $C = 3 \implies$ Linear interpolation.
- **Fallback**: If mask coverage > 50%, force $R = 128$ to prevent hallucination.

### 3.3. Training Protocol
- **Loss Function**: Multi-task loss:
  $$ \mathcal{L}_{total} = \lambda_1 \mathcal{L}_{recon} + \lambda_2 \mathcal{L}_{reg} + \lambda_3 \mathcal{L}_{bin} $$
  - $\mathcal{L}_{recon}$: Reconstruction error (MSE/L1).
  - $\mathcal{L}_{reg}$: Regression loss against ground truth (Human or Decoupled).
  - $\mathcal{L}_{bin}$: Rank-bin classification loss.
- **Curriculum Learning**: Train gating head first (frozen base), then end-to-end fine-tuning.
- **Constraints**: No GPU. Default precision (float32). Batch size = 1 for inference, small batch (4-8) for training if RAM permits.

### 3.4. Evaluation Metrics
- **Efficiency**: Wall-clock latency (ms) on 2-core CPU.
- **Quality**: FID (Fréchet Inception Distance) and LPIPS (Learned Perceptual Image Patch Similarity).
- **Statistical Significance**: Paired t-test on quality metrics (low-complexity regions) vs. static baseline. Target $p > 0.05$ for "insignificant difference" (US-3).
- **Power Analysis**: Calculate statistical power for the latency reduction claim.
- **Spearman Correlation**: Correlation between ground truth and effective rank.
- **Permutation Test**: P-value for overfitting check.

## 4. Statistical Rigor & Assumptions

- **Multiple Comparisons**: When testing across multiple complexity bins, apply Bonferroni correction or False Discovery Rate (FDR) control.
- **Power Analysis**: The sample size (N=50 human annotations, ~1k images for CI) is [deferred] but must be justified to achieve power ≥ 0.8 for the latency reduction claim (SC-005).
- **Causal Inference**: Claims are associational. The gating mechanism *predicts* complexity; it does not *cause* it. The causal claim is that "using the predicted complexity to reduce rank *results in* efficiency gains," which is tested via controlled ablation (Phase 3.5).
- **Collinearity**: Synthetic metrics (gradient, entropy) may be correlated. The gating head will be trained to handle this, but the plan acknowledges that independent effects cannot be claimed if metrics are definitionally related.
- **Measurement Validity**: Human ratings are the ground truth (Research Mode). Synthetic metrics are proxies. The validity of the proxy is the critical control (US-4).
- **Circularity Mitigation**: CI Mode uses Decoupled Synthetic Ground Truth to ensure training targets are independent of validation metrics.

## 5. Compute Feasibility

- **Hardware**: GitHub Actions free-tier (multi-core CPU, substantial RAM).
- **Model Size**: The **small-scale** model is **too large** for CI training.
  - **Mitigation**: Use a **Moebius-Tiny** architecture (approx. -20M params) for the CI run. This model maintains the *structural* properties (dynamic rank) but fits in memory.
  - **Alternative**: The 0.2B claim is reserved for the paper's theoretical discussion or external GPU runs.
- **Runtime**: Training must complete in ≤ 6 hours. If not, the plan will reduce the dataset size or epochs.
- **Libraries**: `torch` (CPU), `scikit-learn`, `lpips` (CPU mode), `torchmetrics` (CPU).

## 6. Decision Rationale

- **Why CPU-only?**: Target deployment is edge devices. GPU benchmarks would be misleading (Constitution VII).
- **Why Human Ratings?**: To avoid circular validation (FR-007). Model performance cannot define complexity if complexity is used to optimize model performance.
- **Why Synthetic Proxies?**: Human annotation is slow/expensive. Proxies allow scalable training, provided they are validated (FR-009).
- **Why Decoupled Synthetic Ground Truth?**: To allow CI testing without circularity. The training target is random, breaking the link between synthetic metrics and labels.
- **Why Moebius-Tiny?**: To ensure reproducibility on free-tier CI. The *mechanism* (dynamic rank) is the innovation, not the absolute scale of the 0.2B model.
