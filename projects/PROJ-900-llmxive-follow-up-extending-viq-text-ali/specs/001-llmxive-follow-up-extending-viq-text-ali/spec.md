# Specification: ViQ Resolution Invariance Study

## 1. Introduction
This document specifies the requirements for the ViQ (Visual Quantized) resolution invariance study. The goal is to evaluate whether a visual quantization model trained on low-resolution images can maintain semantic alignment and acceptable fidelity when processing high-resolution inputs without retraining.

## 2. Functional Requirements

### FR-001: Low-Resolution Training
The system must be able to train a VQ-VAE codebook using low-resolution (64x64) images from the COCO dataset on CPU-only hardware within a 6-hour time limit.

### FR-002: High-Resolution Inference
The system must be able to process high-resolution (1024x1024) images from ImageNet-1K and COCO using the trained low-resolution codebook without resizing the input images.

### FR-003: Dataset Scope
**AMENDED PER DECISION RECORD 001**: The system must utilize the ImageNet-1K (validation split) and COCO (train split) datasets for evaluation.
- **Exclusion**: The ChestX-ray14 dataset is explicitly **excluded** from this project due to lack of verified programmatic access and CI compatibility risks.
- The system must fail loudly if the specified datasets cannot be accessed.

### FR-004: Fidelity Measurement
**AMENDED PER DECISION RECORD 002**: The system must calculate reconstruction fidelity metrics (PSNR, SSIM) by comparing the model's output against the **native 1024x1024 ground truth** images.
- **Correction**: The requirement to use "upsampled ground truth" is rejected. Comparisons must be made against the original high-resolution source to ensure scientific validity.

### FR-005: Semantic Alignment
The system must compute the cosine similarity between projected high-resolution visual embeddings and frozen CLIP text embeddings to verify semantic stability.

## 3. Statistical & Analysis Requirements

### SC-001: Texture Complexity
The system must calculate texture complexity using the variance of the Laplacian operator on grayscale images.

### SC-002: Correlation Analysis
The system must compute the Spearman rank correlation between texture complexity and reconstruction error (PSNR).

### SC-003: Normality Testing
Before parametric testing, the system must perform a Shapiro-Wilk test on the error distribution.

### SC-004: Hypothesis Testing
**AMENDED PER DECISION RECORD 002**: The system must perform a **paired t-test** if the error distribution is normal (p > 0.05), or a **Wilcoxon signed-rank test** if it is not.
- **Correction**: The requirement for a "one-sample t-test" (SC-005 in original draft) is rejected as it is statistically inappropriate for paired data.

## 4. User Stories

### US-1: Low-Resolution Training
As a researcher, I want to train the codebook on 64x64 COCO images so that I can establish a baseline quantization model on CPU.
- **Acceptance Criteria**: Codebook converges; checkpoint saved to `data/results/codebook_v0.pth`.

### US-2: High-Resolution Evaluation
As a researcher, I want to evaluate the model on 1024x1024 images from ImageNet and COCO so that I can measure fidelity degradation.
- **Acceptance Criteria**: Metrics calculated against **native ground truth**; ChestX-ray14 **excluded** per FR-003.
- **Note**: This story is restricted to natural images (ImageNet, COCO).

### US-3: Semantic Stability
As a researcher, I want to compare high-res and low-res semantic similarities so that I can verify the model's resolution invariance.
- **Acceptance Criteria**: Difference in similarity scores computed and logged.

## 5. Non-Functional Requirements
- **Reproducibility**: All random seeds must be fixed; data sources must be verified.
- **Performance**: Training must complete within 6 hours on CPU.
- **Data Integrity**: Raw data checksums must be verified (T040).
- **Fail Loudly**: Scripts must raise errors if real data fetch fails; no synthetic fallbacks.

## 6. Decision Records
- [001-chestx14-exclusion.md](decisions/001-chestx14-exclusion.md): Exclusion of ChestX-ray14.
- [002-native-ground-truth-test.md](decisions/002-native-ground-truth-test.md): Adoption of native ground truth and paired tests.