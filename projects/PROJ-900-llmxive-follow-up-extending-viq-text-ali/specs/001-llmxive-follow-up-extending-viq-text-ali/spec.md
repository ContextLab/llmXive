# Specification: ViQ Resolution Invariance Study

## 1. Introduction

This document defines the requirements for the "ViQ: Text-Aligned Visual Quantized Representations at Any Resolution" study. It outlines the functional requirements, scope constraints, and statistical analysis plans required to validate the hypothesis that ViQ representations maintain semantic alignment across resolutions.

## 2. Functional Requirements

### FR-001: Codebook Training
The system must train a VQ-VAE codebook using low-resolution (64x64) COCO images.

### FR-002: High-Resolution Inference
The system must process 1024x1024 images using the trained codebook to measure reconstruction fidelity.

### FR-003: Dataset Exclusion (Amended)
The ChestX-ray14 dataset is explicitly excluded from this study to maintain domain consistency with natural images (COCO/ImageNet).
**Amendment per Decision Record 001**: ChestX-ray14 is excluded from all data loading and analysis steps.
**Amendment per Decision Record 002**: This exclusion is confirmed as a deviation from the initial draft scope, ensuring the study focuses solely on natural image resolution invariance.

### FR-004: Ground Truth Resolution (Amended)
The study requires ground truth images at the target inference resolution.
**Amendment per Decision Record 002**: The system shall use **native 1024x1024 ground truth** images for fidelity measurement, deviating from the original upsampled baseline approach. This ensures that fidelity metrics (PSNR/SSIM) reflect actual reconstruction quality at high resolution rather than interpolated artifacts.

## 3. Scope Constraints

### US-2: High-Resolution Fidelity Evaluation
Evaluate reconstruction quality on high-resolution images.
**Constraint**: As per Decision Record 001, ChestX-ray14 is excluded from US-2. Only COCO and ImageNet-1K validation sets are used.
**Constraint**: As per Decision Record 002, fidelity is measured against native 1024x1024 ground truth.

## 4. Statistical Analysis Plan

### SC-001: Correlation Analysis
Calculate Spearman correlation between texture complexity and reconstruction error.

### SC-002: Normality Testing
Perform Shapiro-Wilk test to determine distribution of errors.

### SC-003: Test Selection
Select statistical test based on normality results.

### SC-004: Statistical Significance Testing (Amended)
The study shall determine if reconstruction error significantly correlates with texture complexity.
**Amendment per Decision Record 002**: The analysis shall use a **Paired t-test or Wilcoxon signed-rank test** (depending on normality) to compare error distributions, replacing the previously drafted one-sample t-test (SC-005) which was deemed scientifically unsound for this specific hypothesis.

## 5. Decision Records

The following decision records document deviations from the initial draft specification:

- **DR-001**: Exclusion of ChestX-ray14 dataset (Domain Consistency).
- **DR-002**: Use of native 1024x1024 ground truth and adoption of paired t-test/Wilcoxon for statistical analysis.

## 6. Deliverables

- Trained codebook checkpoint (`data/results/codebook_v0.pth`)
- High-resolution embeddings (`data/results/embeddings_high_res.h5`)
- Fidelity metrics report (`data/results/fidelity_metrics.json`)
- Statistical analysis report (`data/results/analysis_results.json`)