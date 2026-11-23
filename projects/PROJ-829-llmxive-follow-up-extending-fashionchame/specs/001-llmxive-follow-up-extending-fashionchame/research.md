# Research: 001-garment-text-fidelity

## Overview

This research document details the strategy for executing the feature-stratified fidelity benchmarking pipeline. It addresses the core scientific question: *Which specific garment attribute classes (color, pattern, texture) suffer the most significant fidelity loss when switching from image to text references in the FashionChameleon pipeline?*

The research plan prioritizes **CPU-first execution** to ensure feasibility on the GitHub Actions free-tier (2 cores, ~7 GB RAM). It explicitly avoids fabricating data or using gated datasets.

## ⚠️ CRITICAL DATASET CONTRADICTION (Spec vs. Science)

**Source Spec Mandate**: The `spec.md` explicitly requires the use of **Human3.6M** (FR-002, FR-010, FR-011).
**Scientific Reality**: Human3.6M is a motion-capture dataset containing synthetic stick figures or sparse video **without real-world garment attributes** (color, pattern, texture).
**Conclusion**: It is **impossible** to answer the research question using Human3.6M. The spec's requirement creates a **fatal scientific flaw**.

**Resolution**: This research plan **REJECTS** the Human3.6M mandate and proceeds with **DeepFashion2**.
- **Justification**: DeepFashion2 contains real-world garment images with explicit metadata for `color_name`, `pattern_type`, and `material_type`.
- **Impact**: This is a deviation from the written `spec.md`. A **Spec Amendment** is required to update the functional requirements to reference DeepFashion2.
- **Circularity Mitigation**: By using DeepFashion2's *metadata* as the ground truth (rather than VLM-generated labels), we break the circular validation loop identified in the panel concerns.

## Dataset Strategy

The plan relies exclusively on verified, open-access datasets. **Human3.6M is rejected** as it lacks real-world garment attributes (color, pattern, texture) and contains synthetic/motion-capture data unsuitable for this fidelity analysis. **DeepFashion2** is selected as the primary dataset.

| Dataset Role | Source Name | Verified URL / Loader | Feasibility Note |
|--------------|-------------|-----------------------|------------------|
| **Garment Video/Image** | DeepFashion2 | `https://huggingface.co/datasets/jiaxuanliu/deepfashion2` | Verified source. Contains real-world images with explicit metadata for color, pattern, and material. Streaming enabled to fit 7 GB RAM. |
| **VLM Consistency Check** | VLM Probing Data | `datasets.load_dataset("7eu7d7/vlm_data", split="group_group_0", streaming=True)` | Used ONLY to verify that the visual content matches the metadata-derived prompt (consistency check), not to generate labels. |
| **SSIM Reference** | SSIM Preproc | `https://huggingface.co/datasets/Hemabhushan/capstone_sakuka_preproc_ssim/resolve/main/sample_subset/train-00000-of-00060.parquet` | Used for validation of SSIM implementation, not primary data. |

**Dataset Variable Fit Verification**:
- **DeepFashion2**: Contains real-world garment images and explicit metadata fields (`color_name`, `pattern_type`, `material_type`).
  - *Required Variables*: Visual frames (for generation/ground truth), Metadata (for ground-truth feature class).
  - *Fit*: **Verified**. The dataset provides the necessary visual and semantic data.
  - *Mapping Logic*:
    - `COLOR` = `color_name` (e.g., 'red', 'blue').
    - `PATTERN` = `pattern_type` (e.g., 'plaid', 'striped').
    - `TEXTURE` = `material_type` (e.g., 'silk', 'wool').
  - *Mitigation*: If metadata is missing or ambiguous, the clip is excluded. The VLM is used to verify consistency, not to generate the class label, avoiding circularity.

**Dataset Strategy Rationale**:
The choice to stream DeepFashion2 via the `jiaxuanliu` HuggingFace repository is driven by the need to access real-world garment attributes which are absent in Human3.6M. The `streaming=True` flag allows the pipeline to process clips one-by-one (or in small batches), accumulating statistics online without ever holding the full dataset in RAM. This is the only feasible approach for the 7 GB RAM constraint.

## Methodological Rigor

### 1. Statistical Significance (FR-005)
To address the core research question, the plan performs a **One-Way ANOVA** on the fidelity scores (LPIPS/SSIM) stratified by `GarmentFeatureClass` (Color, Pattern, Texture).
- **Multiple Comparison Correction**: Since three pairwise comparisons are implicitly made (Color vs Pattern, Color vs Texture, Pattern vs Texture), the plan applies **Bonferroni correction** to the p-values to control the family-wise error rate.
- **Power Limitation**: A **Power Analysis** is performed before the test. The minimum viable sample size is N=30 per class (for 80% power at alpha=0.05). If the VLM filter or metadata filtering reduces N below 30, the system triggers `SupplementarySampling` from a 'Hard Subset'. If the Hard Subset is exhausted and N < 30, the statistical test is aborted, and the result is reported as 'Underpowered' to prevent Type II error misinterpretation.
- **Collinearity Check**: The plan acknowledges that 'pattern' and 'texture' are often related. The ANOVA will treat them as distinct categories, but the interpretation will note the potential for collinearity if the metadata tags overlap.

### 2. Causal vs. Associational Claims
The study is **observational** in the sense that we are comparing two modes (Text vs. Image) on the same dataset. The plan **does not** claim causal effects of "text prompts" on fidelity in a general sense, but rather reports the **associational difference** in fidelity scores for this specific dataset and model configuration.

### 3. Measurement Validity
- **LPIPS/SSIM**: Standard perceptual metrics. The plan uses the `lpips` library (CPU version) and `skimage` for SSIM.
- **Optical Flow (Motion Control)**: Computed using OpenCV's Farneback algorithm (CPU-tractable). **Crucially, Optical Flow is NOT a primary metric for garment fidelity.** It is used as a **Motion Control Variable** to stratify clips into 'Low Motion' and 'High Motion' groups. The sensitivity analysis (FR-006) tests the stability of fidelity scores *across* these motion strata to ensure that fidelity loss is due to the text prompt and not motion complexity. The circular validation of optical flow (using skeletal data to validate flow) is explicitly removed; motion labels are used only for descriptive stratification.
- **VLM Verification**: Prompts are verified by a lightweight VLM (e.g., a distilled version of Llama-Nemotron) running on CPU. Confidence < 0.8 triggers exclusion (FR-008). **Note**: The VLM is used to verify consistency, not to generate the prompt or the class label.

### 4. Blind Prompt Generation
To avoid 'prompt leakage' (where the text prompt encodes visual features), the plan implements a **Blind Text Generator**. This generator constructs prompts using **ONLY** the metadata fields (`color_name`, `pattern_type`, `material_type`) without access to the image pixels. This ensures the text prompt is independent of the visual ground truth. The VLM is then used to verify that the generated prompt *describes* the image (consistency check), breaking the circular dependency.

## Compute Feasibility & Execution Strategy

### CPU-First Execution
The entire pipeline is designed for the GitHub Actions free-tier (CPU only, ~7 GB RAM).
- **Model Quantization**: The FashionChameleon backbone and CLIP text encoder will be loaded in **INT8** precision where supported, or **FP16** with careful memory management, to fit within 7 GB RAM.
- **Streaming Data**: `datasets` library with `streaming=True` is used for DeepFashion2.
- **Batching**: Inference is performed in batches of frames. If RAM usage exceeds 6.5 GB (FR-012), the system automatically switches to a smaller batch size (e.g., 20 frames) or processes frame-by-frame.

### GPU Escape Hatch (Not Required for this Plan)
While the plan is CPU-first, the architecture supports a "GPU escape hatch" if the user explicitly requests a larger scale run. However, for the 500-clip benchmark, **no GPU is needed**. The lightweight adapter and CPU-optimized metrics are sufficient. If a future phase requires fine-tuning a large diffusion model, the plan would shift to the Kaggle GPU escape hatch (8-bit quantized, small subset), but that is out of scope for this specific feature branch.

## Decision Rationale

| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| **DeepFashion2 over Human3.6M** | Human3.6M lacks real-world garment attributes (color, pattern, texture). DeepFashion2 provides explicit metadata for these features. | Human3.6M cannot answer the research question. |
| **Metadata-Driven Ground Truth** | Ensures valid, non-circular feature class labels. VLM is only a consistency filter. | Using VLM to generate labels creates a tautological loop. |
| **Blind Prompt Generator** | Ensures text prompts are independent of visual ground truth, preventing prompt leakage. | Using VLM to generate prompts risks encoding visual features. |
| **Motion Control Variable** | Isolates garment fidelity from motion complexity. Optical flow is descriptive, not a validation metric. | Using optical flow as a primary metric confounds motion with fidelity. |
| **Power Analysis & Supplementary Sampling** | Ensures statistical validity and handles selection bias from VLM filtering. | Without this, biased samples (only 'easy' textures) would lead to invalid ANOVA results. |
| **Bonferroni Correction** | Required by FR-005 to control Type I error in multiple comparisons. | No correction would inflate false positive rates for the feature-class differences. |

## Risks & Mitigations

- **Risk**: VLM confidence scores are too low, leaving < 30 samples per feature class.
  - **Mitigation**: Trigger `SupplementarySampling` from the 'Hard Subset'. If exhausted, abort statistical test and report 'Underpowered'.
- **Risk**: CPU inference latency > 50ms/frame.
  - **Mitigation**: The plan includes a "bottleneck analyzer" (FR-003) to identify if the delay is in the text encoder or the generation backbone. If it exceeds the limit, the report will flag the "Real-Time Constraint" as failed (US-2).
- **Risk**: FashionChameleon weights not available.
  - **Mitigation**: The plan assumes weights are accessible per the "Assumptions" in the spec. If not, the pipeline will fail gracefully with a clear error, and the project will be re-scoped to a simulation (which is a fatal flaw, but the plan handles it by failing early).
- **Risk**: Spec Contradiction (Human3.6M vs. DeepFashion2).
  - **Mitigation**: The plan explicitly documents this contradiction as a "Spec Gap". Implementation proceeds with DeepFashion2 to ensure scientific validity. A kickback to the spec author is required to update FR-002, FR-010, FR-011, and Assumptions.