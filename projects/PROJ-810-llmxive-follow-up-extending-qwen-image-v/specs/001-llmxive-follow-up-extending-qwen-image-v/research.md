# Research: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

## Executive Summary
This research investigates the geometric disentanglement of the Qwen-Image-VAE-2.0 latent space. We hypothesize that "text-only" and "image-only" regions in document images map to linearly separable clusters in the latent space. We will validate this using a Linear SVM on the OmniDoc-TokenBench dataset. If separability is confirmed (Accuracy ≥ 90%), we will perform zero-shot semantic editing via vector arithmetic ($z_{new} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$) and verify layout preservation using Masked SSIM and Edge Alignment Score (EAS).

**Key Methodological Updates**:
1. **Triviality Check**: A 'Pixel-Only' baseline is used on unlabeled crops to ensure separation is not due to trivial pixel statistics.
2. **Linearity Validation**: A consistency check for the 'text direction' vector is performed before arithmetic.
3. **Region Purity Filter**: Mixed modalities (IoU > 0.1) are explicitly excluded.
4. **CPU Feasibility**: If the model fails on CPU, the 'CPU-First' hypothesis is formally REJECTED.
5. **Statistical Scope**: Bonferroni correction is applied only to separability p-values (Accuracy, F). SSIM and Keypoint are evaluated against thresholds.
6. **Baseline Comparison**: Layout preservation metrics (SSIM, EAS) are computed against the *Baseline Reconstruction* (original image encoded/decoded without arithmetic) as per FR-006.
7. **Runtime Power Analysis**: If runtime > 6 hours, the result is reported as "Inconclusive".

## Hypotheses & Statistical Framework

### Primary Hypothesis (H1)
The latent representations of text-only regions and image-only regions are linearly separable.
- **Null Hypothesis (H0)**: The classification accuracy of a Linear SVM on latent vectors is no better than random chance.
- **Metric**: Classification Accuracy, F1-Score.
- **Significance**: Permutation test (p < 0.05) and Bonferroni-corrected p-values for separability tests only.
- **Power Analysis**: We will calculate the required sample size (N) to detect a large effect size (Cohen's d > 0.8) with power ≥ 0.8. If the available dataset subset yields power < 0.8, the result is reported as "inconclusive" (US-01).
- **Triviality Check**: A 'Pixel-Only' classifier (raw pixels or edge density) is trained on *unlabeled* crops. If its accuracy > 90%, the result is flagged as "Trivial" and the latent space disentanglement claim is rejected.

### Secondary Hypothesis (H2)
Vector arithmetic allows for text swapping while preserving layout.
- **Metric**: Masked SSIM (non-text regions) ≥ 0.85; Edge Alignment Score (EAS) ≥ 0.80.
- **Validation**: Comparison against the *Baseline Reconstruction* (original image encoded/decoded without arithmetic) and OCR verification of text change.

## Dataset Strategy

### Primary Dataset: OmniDoc-TokenBench
- **Source**: Verified Hugging Face dataset.
- **URL**: `https://huggingface.co/datasets/omnineura/Omni-Doc-1`
- **Relevance**: Contains document images with ground-truth bounding boxes for text and image regions, essential for extracting "text-only" and "image-only" crops. This dataset includes the specific 'OmniDoc-TokenBench' benchmark subset required for the analysis.
- **Access Strategy**: Use `datasets.load_dataset(..., streaming=True)` to iterate over the dataset without loading the entire file into RAM. This ensures compatibility with the RAM constraint.
- **Verification Step**: Before processing, verify the presence of 'modality' and 'bbox' fields. If missing, report "Data Unavailable".
- **Preprocessing**:
  1. Filter for images containing both text and image bounding boxes.
  2. Crop regions based on bounding box annotations.
  3. **Region Purity Filter**: Exclude regions where text and image overlap (IoU > 0.1) or where OCR confidence is low.

### Dataset Variable Fit Check
- **Required Variables**: Image pixels, Bounding Box coordinates, Modality Labels (Text/Image).
- **Availability**: The OmniDoc-TokenBench dataset provides these fields.
- **Risk**: If the dataset lacks explicit modality labels for every bounding box, the study is reported as "Data Unavailable" rather than fabricating data.

## Methodology & Statistical Rigor

### 1. Data Loading & Sampling
- Stream the dataset.
- **Verification**: Confirm 'modality' and 'bbox' fields exist.
- **Power Analysis**: Calculate required N for Power ≥ 0.8.
- **Runtime Analysis**: Estimate runtime per image on CPU. If max N (within 6h) < required N, report "Inconclusive".

### 2. Latent Extraction (FR-003)
- Load Qwen-Image-VAE-2.0 encoder (Source: Hugging Face).
- **Model Availability Check**: Verify the model exists and fits CPU memory before proceeding.
- Encode cropped regions.
- **CPU Constraint**: Attempt loading on CPU. If OOM, trigger 'Model Unavailable' or GPU escape hatch (with hypothesis rejection).

### 3. Disentanglement Analysis (US-01)
- **Triviality Check**: Train a 'Pixel-Only' classifier (raw pixels or edge density) on *unlabeled* crops. If accuracy > 90%, flag as "Trivial".
- **Classifier**: Linear SVM (`sklearn.svm.LinearSVC`).
- **Training**: Train on a split of the latent vectors. Labels are ground-truth modality.
- **Evaluation**: Accuracy, F1-Score.
- **Permutation Test**: Shuffle labels repeatedly to generate a null distribution. Calculate p-value.
- **Multiple Comparison Correction**: Apply Bonferroni correction to the p-values of Accuracy and F1 (separability tests only). SSIM and EAS are evaluated against thresholds, not p-values.

### 4. Vector Arithmetic & Editing (US-02)
- **Linearity Validation**: Test consistency of 'text direction' vector across multiple pairs of text regions.
- Compute centroids: $\mu_{text} = \text{mean}(Z_{text})$, $\mu_{image} = \text{mean}(Z_{image})$.
- Operation: $z_{edited} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$.
- Decode $z_{edited}$.
- **Metrics**:
  - **OCR Verification**: Confirm text content changed (≥95% accuracy).
  - **Masked SSIM**: Compare edited image vs. **Baseline Reconstruction** for non-text regions; result ≥ 0.85.
  - **Edge Alignment Score (EAS)**: Detect SIFT/ORB keypoints in non-text regions; match between edited and baseline; score ≥ 0.80.

### 5. Sensitivity Analysis (US-03)
- Sweep classification threshold around the decision boundary.
- Report False Positive Rate (FPR) and False Negative Rate (FNR) variations.

## Compute Feasibility & Decision Rationale

### CPU-First Strategy
- **Method**: `torch` CPU, `scikit-learn`, `opencv`, `paddlepaddle` (CPU wheel 2.7.0).
- **Justification**: The VAE encoder/decoder for document images is typically a convolutional network (U-Net or similar) which can run on CPU for small batches or single images. The classification (Linear SVM) is trivial on CPU. PaddleOCR (CPU wheel) is <1GB and fits within 7 GB RAM.
- **Memory Accounting**: VAE (~3GB) + PaddleOCR (~1GB) + OS/Data (~2GB) < 7GB. The CPU-only wheel is used to minimize overhead.
- **Risk Mitigation**: 
  1. **Model Availability Check**: Verify 'Qwen/Qwen-Image-VAE-2.0' exists and fits CPU before proceeding. If not, report 'Model Unavailable'.
  2. **Runtime Power Analysis**: Estimate runtime per image. If max N (within 6h) < required N for power, report 'Inconclusive'.
  3. **GPU Escape Hatch**: If CPU fails (OOM), the 'CPU-First Feasibility' hypothesis is REJECTED. A scaled-down run (N=100) on Kaggle GPU is performed only to demonstrate editing capability, with a note that the CPU feasibility claim is invalid.

### GPU Escape Hatch
- **Condition**: Only if `ImportError` or `OOM` on CPU.
- **Configuration**: Kaggle GPU (T4/P100), `device="cuda"`, `load_in_8bit` if applicable.
- **Scale**: Run on a subset of N=100 images (as per US-02 Assumptions) to demonstrate feasibility within the kernel time limit.
- **Reproducibility**: The N=100 subset is fixed-seed (seed=42) and documented in the output.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Unavailable** | Fatal | Fallback to a smaller local sample if provided; otherwise, report "Data Unavailable". |
| **Model Unavailable** | Fatal | If 'Qwen/Qwen-Image-VAE-2.0' is not found or too large for CPU, report "Model Unavailable". |
| **Ambiguous Regions** | Medium | Exclude regions where text/image overlap significantly (IoU > 0.1) or flag for manual review. |
| **CPU OOM** | High | Trigger GPU escape hatch (N=100) but mark 'CPU-First Feasibility' as REJECTED. |
| **Low Statistical Power** | Medium | Report "Inconclusive" with the specific power value (SC-001). |
| **Runtime Exceeds 6h** | Medium | Report "Inconclusive" due to hardware constraints. |
