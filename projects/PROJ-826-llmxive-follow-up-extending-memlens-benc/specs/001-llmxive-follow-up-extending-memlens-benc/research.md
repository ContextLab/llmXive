# Research: llmXive follow-up: extending "MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models"

## Dataset Strategy

| Dataset Name | Source URL (Verified) | Usage in Plan | Notes |
|:--- |:--- |:--- |:--- |
| **MemLens** | ` (Primary) <br> ` (Alternative) | **Primary Data Source**. Filtered for `task_type` in ["MSR", "TR"]. | The JSON source is preferred for direct access to question/answer pairs and metadata. |
| **MSR** | NO verified source found | N/A | Not a standalone dataset; a task type within MemLens. |
| **YOLOv8-Tiny** | NO verified source found | **Model Component**. Loaded via `ultralytics` library (CPU mode). | Not a dataset. The model weights are pulled from the HuggingFace Hub or PyTorch Hub during runtime. |
| **CPU-optimized** | ` | **Reference Only**. Not used for this project's core logic. | This dataset is listed in verified sources but is irrelevant to the MemLens benchmark extension. |

**Dataset Fit Verification**:
The MemLens dataset contains the required variables: `question`, `answer`, `task_type` (to filter MSR/TR), `images` (or image paths), and `session_id` (for temporal reasoning).
* **Image Accessibility**: The JSON source contains an `image_path` field (e.g., `images/session_001/img_01.jpg`) pointing to relative paths within the dataset repository. The `datasets` library will automatically download these binary assets when loading the dataset, ensuring accessibility for the CPU pipeline.
* **Predictors**: Indexing strategy (Coarse/Medium/Fine), retrieved context quality.
* **Outcome**: Answer accuracy (binary or string match).
* **Covariations**: Session length, visual complexity.
* **Gap Analysis**: The dataset does not explicitly provide "post-task anxiety" or "rumination" (irrelevant to this study). The required variables for the study (images, text, task type) are present.
* **Constraint**: If the filtered MSR/TR subset yields < 30 samples, statistical power is insufficient. The plan includes a fallback to report descriptive statistics only and flag the power limitation.

## Model & Methodology

### Memory Store Construction
1. **Coarse**: Extract text summaries from the dataset. Embed using `sentence-transformers/all-MiniLM-L6-v2` (CPU-optimized).
2. **Medium**: Combine text summaries with global CLIP image embeddings (`clip-ViT-B-32`).
3. **Fine**:
 * Run **YOLOv8-Tiny** (via `ultralytics`) on images to detect objects and generate bounding boxes.
 * **Captioning**: Generate natural language descriptions for each detected object using a lightweight, CPU-optimized Vision-Language Model (e.g., a distilled captioner or prompt-based Phi-3). **Template-based descriptions (e.g., 'Object at [x,y]') are explicitly forbidden** to avoid confounding text quality with granularity.
 * **Fallback**: If YOLO fails (timeout/error), store a global CLIP embedding for that image (same as Medium) and log the failure with `detection_status: fallback`.
 * **Validation**: Calculate **Semantic Relevance Score (SRS)**. Since MemLens lacks ground-truth bounding boxes (see Data Resources), we cannot compute Object Detection Recall. Instead, a frozen LLM rates the relevance of the retrieved object captions to the query (Scale 0-1). Target SRS ≥ 0.6.

### Retrieval Strategy
* **Fine Store**: **Text-only retrieval**. Use cosine similarity on text embeddings of the generated object captions.
 * *Correction*: Bounding box coordinates (x_min, y_min, etc.) are **retained in the data structure** as metadata for the 'Fine' representation definition but are **excluded from the similarity calculation**. Fusing raw spatial coordinates with semantic embeddings creates a mathematically invalid similarity space.
* **Coarse/Medium**: Text-only retrieval using cosine similarity on text embeddings. Top-k = 5.

### Inference Engine
* **Model**: `microsoft/Phi-3-mini-4k-instruct` (or `Llama-3-8B` 4-bit if CPU memory permits, but Phi-3 is safer for 7GB RAM).
* **Configuration**: Frozen weights. No fine-tuning.
* **Quantization**: Use `bitsandbytes` if available for CPU (rare) or native `torch` 4-bit/8-bit loading with `device="cpu"`. If 4-bit fails on CPU, fall back to 16-bit (FP16) with reduced batch size (1) to stay within RAM limits.
* **Context Window**: Truncate responses if they exceed limits; log truncation events.

### Statistical Analysis
* **Test**: Paired Wilcoxon signed-rank test comparing accuracy of Fine vs. Coarse strategies.
* **Stratification**: The 'Fine' group may contain 'success' (object-level) and 'fallback' (global-level) samples. The primary test will be performed **only on the subset where `detection_status` is 'success'**.
* **Fallback Handling**: If the 'success' subset has n < 30, the test is aborted. Descriptive statistics (mean, std) will be reported for the full mixed group with a `power_warning` flag.
* **Rationale**: Non-parametric test suitable for accuracy scores (bounded, potentially non-normal) and paired data (same questions, different strategies).
* **Correction**: Since only one primary comparison (Fine vs. Coarse) is the core hypothesis, family-wise error correction (e.g., Bonferroni) is not strictly required for the main test. If multiple comparisons are added (e.g., Medium vs. Coarse), apply Bonferroni correction.
* **Power**: Acknowledge that if N < 30, the test has low power to detect small effect sizes.
* **Causal Claims**: Claims will be framed as "associational" regarding the impact of indexing granularity, as this is a controlled experiment on a fixed dataset, not an observational study. Randomization is inherent in the task ordering.
* **Construct Validity**: The study acknowledges that 'visual fidelity' is proxied by 'Answer Accuracy'. If the model fails to reason despite high-fidelity retrieval, this is recorded as a 'Reasoning Failure' rather than 'Fidelity Failure'.

## Compute Feasibility & Rationale

* **Hardware Target**: GitHub Actions Free Tier (standard compute resources, ~7GB RAM, ~14GB Disk).
* **Memory Strategy**:
 * Process images in batches of 1.
 * Use `torch.no_grad()` for inference.
 * Load model in 4-bit (if supported on CPU) or 16-bit with `max_memory` constraints.
 * Discard intermediate embeddings after retrieval to free RAM.
* **Time Strategy**:
 * YOLOv8-Tiny is fast on CPU.
 * Phi-mini is ~GB in 16-bit, ~1.5GB in 4-bit. Fits in 7GB RAM.
 * If runtime approaches 4 hours, the system will auto-throttle or sample [deferred] of the dataset for the final run (logged as a limitation).
* **Rationale**: The selected stack (Phi-3, YOLOv8-Tiny, CLIP) is the minimal viable set to perform the required tasks. Larger models (Llama-3-70B) or GPU-dependent methods are explicitly excluded to ensure the project is runnable.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **OOM (Out of Memory)** | Pipeline crashes; no results. | Implement strict memory monitoring. Drop to 16-bit if 4-bit fails. Process data in chunks. |
| **Insufficient Samples (N < 30)** | Statistical test invalid. | Log warning. Report descriptive stats (mean, std) and effect size (Cohen's d) without p-value significance claims. |
| **YOLO Failures > 40%** | Fine store invalid (SRS < 0.6). | Fallback to global embeddings (Medium). Report SRS metric. If SRS < 0.6, flag "Visual Fidelity Not Validated". |
| **Model Not CPU Compatible** | Inference fails. | Fallback to smaller model (e.g., TinyLlama) or CPU-optimized quantization. |
| **Spec Contradiction (FR-003/SC-005)** | Plan requires coordinate exclusion, Spec requires fusion. | **Flagged for Kickback**: The plan implements the methodologically sound approach (text-only retrieval). The spec must be amended to reflect that spatial coordinates are metadata only, not retrieval features. |
| **Spec Contradiction (FR-009/SC-005)** | Plan uses SRS, Spec requires Recall. | **Flagged for Kickback**: MemLens lacks ground-truth boxes. The plan uses SRS as a proxy. The spec must be amended to replace 'Object Detection Recall' with 'Semantic Relevance Score'. |
| **Construct Validity (Floor Effect)** | Model fails to reason despite high fidelity. | Record as 'Reasoning Failure'. Frame outcome as 'Impact of Granularity on Reasoning Performance'. |
| **Template-based Confound** | Text quality confounds granularity. | **Explicitly forbid** template-based descriptions. Use LLM-based captioning only. |