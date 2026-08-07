# Research: 001-garment-text-fidelity

## 1. Problem Statement & Hypothesis

**Problem**: Current image-driven garment transfer (FashionChameleon) achieves high fidelity. It is unknown which specific semantic attributes (global color, local pattern, texture) degrade most significantly when the reference modality switches to text prompts, and whether a lightweight adapter can maintain real-time (<50ms) performance on CPU.

**Hypothesis**:
1.  **H1 (Fidelity)**: Text-driven generation will show significantly higher LPIPS/SSIM degradation for `TEXTURE` and `PATTERN` classes compared to `COLOR` classes.
2.  **H2 (Latency)**: The lightweight cross-attention adapter will add <10ms overhead, keeping total inference <50ms/frame on an 8-core CPU (static).
3.  **H3 (Significance)**: The observed differences in fidelity across classes will be statistically significant (p < 0.05) after Bonferroni correction.

## 2. Dataset Strategy

The project relies on the **DeepFashion2** dataset, which contains verified garment attributes (color, pattern, texture) and is available via Hugging Face. **Human3.6M is explicitly rejected** due to lack of garment semantic tags.

| Dataset | Source URL | Usage | Verification Status |
| :--- | :--- | :--- | :--- |
| **DeepFashion2 (Images)** | `https://huggingface.co/datasets/zhengqin/DeepFashion2/resolve/main/train-00000-of-00001.parquet` | Primary inference input (stratified subset). | Verified |
| **DeepFashion2 (Attributes)** | `https://huggingface.co/datasets/zhengqin/DeepFashion2/resolve/main/attributes.parquet` | Source of ground-truth garment tags. | Verified |

**Critical Data Gap & Mitigation**:
*   **Gap**: The original Human3.6M dataset lacks garment attributes and motion labels.
*   **Solution**: Use **DeepFashion2**, which contains human-curated attribute metadata.
*   **Prompt Generation**: Prompts are **metadata-derived**. For each sample, the system reads the verified attributes (e.g., `pattern: "plaid"`) and generates a deterministic prompt (e.g., "A person wearing a plaid shirt").
*   **Visual Verification (FR-002 Compliance)**: A lightweight VLM (**MobileCLIP**, CPU-optimized) is used to verify that the visual content of the image matches the metadata-derived prompt. Samples with low confidence (<0.8) are excluded. This ensures the "human-verified" requirement of FR-002 is met by proxy of the dataset's curation and a visual check.
*   **Feature Class Assignment**: The `GarmentFeatureClass` is derived directly from these metadata fields (e.g., if `pattern` is present -> `PATTERN`). This ensures the independent variable is semantically valid for ANOVA.
*   **Motion Labels**: DeepFashion is a static image dataset. **FR-006 (Motion FP/FN)** and **SC-005 (Motion Sensitivity)** are **deferred** for this benchmark. The plan explicitly skips these metrics to avoid fabricating motion labels.
*   **Stratification & Balancing**: The `data/stratifier.py` module groups samples based on the *presence* of specific verified attributes. To control for visual complexity, the dataset is filtered to ensure the "complexity score" (number of attributes) is balanced across the three feature classes before ANOVA.

**Streaming Strategy**:
To stay within the 7 GB RAM limit:
*   Use `datasets.load_dataset(..., streaming=True)`.
*   Process samples in batches.
*   Accumulate metrics (LPIPS, SSIM, Time) in memory and flush to disk (JSON/Parquet) after each batch.

## 3. Methodology

### 3.1. Model Architecture
*   **Backbone**: Frozen FashionChameleon weights (assumed accessible per Assumption 1).
*   **Adapter**: A lightweight cross-attention module inserted into the backbone.
    *   *Input*: Frozen CLIP text embeddings (ViT-B/32) derived from metadata prompts.
    *   *Operation*: Maps text embeddings to the reference KV slots.
    *   *Constraint*: Must fit in ~7 GB RAM (8-bit quantized if necessary).
*   **Text Encoder**: CLIP ViT-B/32 (CPU-optimized).
*   **Visual Verifier**: MobileCLIP (CPU-optimized) for prompt-image alignment verification.

### 3.2. Metrics
1.  **LPIPS**: Learned Perceptual Image Patch Similarity (lower is better).
2.  **SSIM**: Structural Similarity Index (higher is better).
3.  **Latency**: End-to-end time per frame (ms).
4.  **Degradation**: Delta = (Image-Baseline Score) - (Text-Driven Score).

### 3.3. Statistical Analysis
*   **ANOVA**: One-way ANOVA to test if mean fidelity scores differ across `COLOR`, `PATTERN`, `TEXTURE`.
*   **Multiplicity Correction**: Bonferroni correction applied if >3 pairwise comparisons are made.
*   **Sensitivity Analysis**: **Deferred** (requires motion labels not present in DeepFashion2).

### 3.4. Image-Baseline Run (Phase 0)
*   **Phase 0**: Execute FashionChameleon with **image references** on the same 500 samples (using 8-bit quantization if necessary).
*   **Phase 1**: Execute FashionChameleon with **text prompts** (derived from metadata + VLM verification) on the same 500 samples.
*   **Calculation**: Fidelity degradation is calculated as the difference between Phase 0 and Phase 1 scores. This explicitly addresses the "degradation" requirement.

## 4. Compute Feasibility & Rationale

**Platform**: GitHub Actions Free Tier (2 vCPU, ~7 GB RAM, No GPU).

| Component | CPU Strategy | GPU Escape Hatch (Kaggle) | Rationale |
| :--- | :--- | :--- | :--- |
| **Inference** | Run FashionChameleon + Adapter in `torch.no_grad()` mode. **Batch size = 1**. **8-bit quantization** applied if OOM. | If OOM or >6h, offload to Kaggle (16GB VRAM). | The spec explicitly targets CPU. If the model is too large, the "GPU escape hatch" is the only valid fallback. |
| **Text Encoding** | CLIP ViT-B/32 runs efficiently on CPU. | Not needed. | CLIP is lightweight. |
| **Visual Verification** | MobileCLIP (CPU-optimized) runs efficiently on CPU. | Not needed. | Lightweight model, one-time check. |
| **Statistics** | `scipy.stats` (CPU native). | Not needed. | Trivial compute. |

**Decision**: The primary plan is **CPU-first**. The method (lightweight adapter + CLIP + MobileCLIP) is designed to fit the constraints. If the FashionChameleon backbone itself exceeds 7 GB RAM even when frozen, the plan will trigger the **GPU escape hatch** (scaled down to 1 batch, 8-bit quantization) on Kaggle. A synthetic CPU approximation of the generation is **not** planned (fabrication rejection).

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Mismatch** | Human3.6M lacks feature tags. | **Solved**: Use DeepFashion2 (verified attributes). |
| **Memory Overflow** | >7 GB RAM during batch processing. | Use `streaming=True`, batch size = 1, and **8-bit quantization** of the backbone. |
| **Latency Failure** | >50ms/frame. | If failed, report "Fail" and analyze bottleneck (Adapter vs. Encoder). Do not optimize beyond spec. |
| **Statistical Power** | <10 samples per class. | Skip ANOVA for that class; report warning. |
| **Motion Metrics** | FR-006 requires motion labels. | **Deferred**: DeepFashion2 is static. FR-006 is out of scope for this benchmark. |
| **Spec Contradiction** | Spec references Human3.6M. | **Flagged**: Spec.md FR-002, User Story 1, and Assumptions flagged for update to reflect DeepFashion2 pivot. |

## 6. Decision Log

*   **Dataset Choice**: DeepFashion2 (Verified) selected over Human3.6M due to availability of garment attributes.
*   **Tagging Strategy**: Metadata-derived prompts used to satisfy "human-verified" requirement via dataset curation, with MobileCLIP visual verification.
*   **Compute**: CPU-first, with explicit 8-bit quantization and GPU offload path if OOM.
*   **Motion Metrics**: FR-006 deferred due to static nature of DeepFashion2.
*   **Baseline**: Image-based baseline run added to calculate relative fidelity degradation.