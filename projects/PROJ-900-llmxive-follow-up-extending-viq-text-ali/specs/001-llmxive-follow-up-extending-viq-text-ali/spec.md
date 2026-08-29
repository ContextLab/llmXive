# Specification: ViQ Resolution Invariance

## Overview
This project investigates the resolution invariance of Visual Quantized (ViQ) representations. We train a low-resolution codebook on 64x64 images and evaluate its ability to reconstruct and maintain semantic alignment when processing high-resolution (1024x1024) images without resizing.

## Functional Requirements

### FR-001: Codebook Training
The system must train a VQ-VAE codebook on 64x64 images using CPU resources within a 6-hour time limit.

### FR-002: Low-Resolution Reconstruction
The system must reconstruct 64x64 images with a PSNR meeting the threshold defined in the baseline validation (Claim: c_ea18f858).

### FR-003: Dataset Scope
The system must utilize the COCO and ImageNet-1K datasets for training and evaluation.
**Update**: ChestX-ray14 is **excluded** from scope per Decision Record 001.

### FR-004: High-Resolution Fidelity Measurement
The system must evaluate reconstruction fidelity on 1024x1024 images.
**Update**: Fidelity metrics (PSNR, SSIM) must be calculated against **native 1024x1024 ground truth** images, not upsampled low-resolution versions, per Decision Record 002.

## Statistical Constraints

### SC-001: Statistical Validity
All statistical comparisons must use appropriate tests for the data structure.

### SC-005: Resolution Comparison Test
The system must compare reconstruction errors between low and high resolutions.
**Update**: The comparison must use a **paired t-test** (if normality holds) or **Wilcoxon signed-rank test** (if normality fails), not a one-sample t-test, per Decision Record 002.

## User Stories

### US-1: Low-Resolution Training
As a researcher, I want to train a codebook on 64x64 images so that I can establish a baseline for quantization.

### US-2: High-Resolution Inference
As a researcher, I want to evaluate the trained codebook on 1024x1024 images to measure fidelity degradation.
**Update**: This user story relies on ImageNet-1K and COCO only. ChestX-ray14 is **excluded** per Decision Record 001.

### US-3: Semantic Alignment
As a researcher, I want to verify that semantic alignment remains stable across resolutions.

## Data Model
- **Codebook**: Discrete latent representation.
- **Embeddings**: Projected visual vectors.
- **Metrics**: PSNR, SSIM, Cosine Similarity, Texture Complexity.

## Appendix: Decision Records
- [DR-001: ChestX-ray14 Exclusion](decisions/001-chestx14-exclusion.md)
- [DR-002: Native Ground Truth & Paired Test](decisions/002-native-ground-truth-test.md)