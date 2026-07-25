# Spec: ViQ Resolution Invariance
# Project: PROJ-900-llmxive-follow-up-extending-viq-text-ali
# Version: 1.1.0 (Updated per Decision Records 001 & 002)
# Status: Active

## Overview
This document specifies the requirements for validating the resolution invariance of
the ViQ (Visual Quantized) representation. The system trains a VQ-VAE codebook on
low-resolution images and evaluates fidelity and semantic alignment on high-resolution
inputs.

## Functional Requirements

### FR-001: Low-Resolution Training
The system shall train a VQ-VAE codebook using 64x64 resolution images from the COCO
dataset. The training loop must be CPU-optimized and complete within a 6-hour wall-clock
limit.

### FR-002: Codebook Initialization
The system shall initialize the codebook using the frozen ViQ encoder weights (or a
ResNet-based fallback if weights are unavailable) to ensure semantic alignment from
the start.

### FR-003: Dataset Scope (AMENDED per Decision Record 001)
The system shall utilize the COCO and ImageNet-1K datasets for training and evaluation.
**Exclusion**: The ChestX-ray14 dataset is explicitly EXCLUDED from this project due
to lack of a verified, programmatic data source compatible with CI environments.
Requirements referencing ChestX-ray14 are hereby voided.

### FR-004: High-Resolution Evaluation (AMENDED per Decision Record 002)
The system shall evaluate reconstruction fidelity on **native 1024x1024** images.
**Correction**: The previous requirement to upsample ground truth to 1024x1024 is
rejected. Metrics (PSNR, SSIM) must be calculated against the native high-resolution
ground truth to accurately measure fidelity degradation caused by the resolution shift
in the encoder, not interpolation artifacts.

### FR-005: Semantic Alignment
The system shall compute cosine similarity between projected visual embeddings and
frozen CLIP text embeddings to verify semantic stability across resolutions.

## Success Criteria

### SC-001: Codebook Convergence
The VQ-VAE training loss must decrease monotonically over the training steps, and the
final checkpoint must reconstruct 64x64 images with a PSNR > 20dB.

### SC-002: Resolution Invariance Check
The frozen ViQ encoder must successfully process 1024x1024 inputs without raising
a `RuntimeError` or shape mismatch, validating the "any resolution" hypothesis.

### SC-003: Fidelity Correlation
A statistical correlation (Spearman) must be established between image texture complexity
and reconstruction error (PSNR drop).

### SC-004: Semantic Stability
The mean cosine similarity between low-res and high-res visual embeddings must remain
within a configurable threshold (e.g., < 5% relative difference).

### SC-005: Statistical Validation (AMENDED per Decision Record 002)
**Correction**: The previous requirement for a one-sample t-test is rejected as
scientifically unsound for paired data.
**New Requirement**: The system shall perform a **paired t-test** (if data is normally
distributed per Shapiro-Wilk) or a **Wilcoxon signed-rank test** (if non-normal) to
compare reconstruction errors and semantic similarities between low-res and high-res
conditions.

## Data Models
- **ImageBatch**: Tensor [B, C, H, W]
- **TextBatch**: List[str]
- **Embedding**: Tensor [B, D]
- **MetricResult**: Dict[str, float]

## Configuration
- `batch_size`: 8 (default, adjustable for RAM)
- `learning_rate`: 1e-4
- `seed`: 42
- `max_train_samples`: Configurable
- `semantic_threshold`: 0.05

## Execution Flow
1. `code/data_loader.py --download-only` (Fetch COCO/ImageNet)
2. `code/validate_viq_invariance.py` (Check SC-002)
3. `code/train.py` (Execute FR-001, produce codebook)
4. `code/eval_high_res.py` (Execute FR-004, produce embeddings)
5. `code/aggregate_fidelity_metrics.py` (Compute PSNR/SSIM on native 1024x1024)
6. `code/correlation_analysis.py` (Execute SC-005, paired t-test/Wilcoxon)
7. `code/eval_semantic.py` (Verify SC-004)