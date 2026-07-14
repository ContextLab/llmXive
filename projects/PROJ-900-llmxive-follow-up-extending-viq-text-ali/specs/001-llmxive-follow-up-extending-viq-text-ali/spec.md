# Feature Specification: llmXive follow-up: extending "ViQ: Text-Aligned Visual Quantized Representations at Any Resolution"

**Feature Branch**: `001-viq-resolution-invariance`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'ViQ: Text-Aligned Visual Quantized Representations at Any Resolution'"

## User Scenarios & Testing

### User Story 1 - Low-Resolution Training & Codebook Initialization (Priority: P1)

A researcher needs to initialize and train a visual quantization codebook using only low-resolution (64x64) image-text pairs from the COCO dataset to establish a baseline "low-res" manifold without requiring high-resolution compute resources.

**Why this priority**: This is the foundational step. Without a successfully trained codebook on the low-resolution data, no high-resolution evaluation can occur. It validates the "training" phase of the hypothesis on CPU-only hardware.

**Independent Test**: The system can be tested by running the training loop on a representative sample of COCO pairs., verifying that the codebook converges (loss decreases) and that the resulting quantized tokens can be reconstructed into 64x64 images with a PSNR > 15 dB, all within the 6-hour CPU time limit on a 2-core, 7GB RAM runner.

**Acceptance Scenarios**:
1. **Given** the COCO dataset is downloaded and resized to 64x64, **When** the training loop executes on the CPU with frozen ViQ encoder weights, **Then** the codebook loss converges and the model saves a valid checkpoint.
2. **Given** a trained low-res codebook, **When** a 64x64 image is passed through the encoder, **Then** the output is a discrete token sequence that reconstructs the image with a PSNR > 15 dB.

---

### User Story 2 - High-Resolution Inference & Fidelity Measurement (Priority: P2)

A researcher needs to evaluate the trained low-resolution codebook on high-resolution (1024x1024) images from the ImageNet-1K and ChestX-ray14 datasets to measure the degradation in reconstruction fidelity (PSNR/SSIM) and correlate it with texture complexity.

**Why this priority**: This directly tests the core hypothesis regarding "resolution shift" and the trade-off between semantic invariance and pixel fidelity. It is the primary experimental validation.

**Independent Test**: The system can be tested by processing a batch of 50 high-resolution images (1024x1024) from ImageNet-1K and ChestX-ray14, generating reconstructions, and calculating the mean PSNR and SSIM. The test passes if the metrics are computed and the correlation with texture complexity (high-frequency energy) is plotted.

**Acceptance Scenarios**:
1. **Given** a trained low-res codebook and a 1024x1024 image from ImageNet-1K or ChestX-ray14, **When** the image is encoded and decoded without resizing (validating resolution-invariant architecture), **Then** the system outputs a reconstructed image and calculates a PSNR value.
2. **Given** a set of high-resolution images with varying texture complexity, **When** the correlation analysis is run, **Then** the system outputs a correlation coefficient indicating the relationship between texture complexity and reconstruction error.

---

### User Story 3 - Semantic Alignment Validation (Priority: P3)

A researcher needs to verify that the semantic alignment between visual tokens and text embeddings remains stable (within 5% of baseline) despite the resolution shift, using a frozen CLIP text encoder, in compliance with Constitution Principle VII (Non-Circular Semantic Validation).

**Why this priority**: This validates the "semantic coherence" aspect of the hypothesis. While fidelity may drop, the core value proposition of ViQ is that the *meaning* (alignment) is preserved.

**Independent Test**: The system can be tested by computing the cosine similarity between the projected visual embeddings of high-resolution images and their corresponding text embeddings (from frozen CLIP). The test passes if the similarity scores are computed and compared against the low-resolution baseline scores.

**Acceptance Scenarios**:
1. **Given** a high-resolution image and its caption, **When** the projected visual embeddings are extracted and compared to the frozen CLIP text embedding, **Then** the cosine similarity is calculated.
2. **Given** the similarity scores for high-res inputs, **When** compared to the low-res baseline, **Then** the difference in mean similarity is calculated and reported.

### Edge Cases

- What happens when the high-resolution image contains extreme high-frequency noise that exceeds the codebook's capacity to represent? (Expected: High reconstruction error, low SSIM).
- How does the system handle images from the medical subset (ChestX-ray14) where texture complexity is structurally different from natural images (COCO)?
- What occurs if the frozen CLIP encoder fails to load or the text embedding dimension mismatches the projection head?
- What occurs if the ViQ encoder architecture is not resolution-invariant and fails to process 1024x1024 inputs? (Expected: Shape mismatch error, experiment terminates).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load and freeze the pre-trained ViQ encoder weights (assumed resolution-invariant architecture, e.g., global pooling) and initialize a new quantization codebook and text-aligned projection head for training on 64x64 COCO data (See US-1).
- **FR-002**: System MUST execute the training loop on CPU-only hardware (no GPU/CUDA) using VQ-VAE loss and contrastive text alignment loss, completing within 6 hours on a 2-core, 7GB RAM GitHub Actions free-tier runner using a sample of images (See US-1).
- **FR-003**: System MUST process 1024x1024 images from the ImageNet-1K and ChestX-ray14 datasets without resizing (validating resolution-invariant architecture), generating discrete token sequences via the trained low-res codebook (See US-2).
- **FR-004**: System MUST calculate reconstruction fidelity metrics (PSNR and SSIM) by comparing high-resolution reconstructions (upsampled to 1024x1024) against a bilinearly upsampled 64x64 ground truth to control for interpolation bias (See US-2).
- **FR-005**: System MUST compute semantic alignment scores by calculating the cosine similarity between the *projected visual embeddings* (output of the Projection Head) and frozen CLIP text embeddings, adhering to Constitution Principle VII (Non-Circular Semantic Validation) (See US-3).
- **FR-006**: System MUST perform a statistical correlation analysis between image texture complexity (high-frequency energy) and the reconstruction error (PSNR/SSIM) using Spearman rank correlation (See US-2).
- **FR-007**: System MUST output a report comparing the semantic similarity of high-res inputs against the low-res baseline, calculating the percentage difference in mean similarity and flagging if it exceeds a predefined threshold (See US-3).

### Key Entities

- **Codebook**: The discrete vocabulary of visual tokens learned during the low-resolution training phase.
- **Projection Head**: The neural layer mapping visual features to the text embedding space for alignment; outputs the projected visual embeddings used for semantic similarity.
- **Texture Complexity Metric**: A derived scalar value representing the high-frequency energy of an input image.
- **Reconstruction Error**: The pixel-wise difference (PSNR/SSIM) between the original high-res image (or its bilinearly upsampled low-res equivalent) and the decoded output.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in mean cosine similarity between high-resolution and low-resolution inputs is measured against a predefined degradation threshold defined in the research question (See US-3).
- **SC-002**: The correlation coefficient between image texture complexity and reconstruction error (PSNR) is measured to quantify the trade-off hypothesis (See US-2).
- **SC-003**: The total training and inference runtime is measured against the CPU-only time limit to ensure compute feasibility (See US-1).
- **SC-004**: The memory usage during high-resolution inference is measured against the RAM limit of the free-tier runner (See US-2).
- **SC-005**: The statistical significance of the fidelity drop is measured using a one-sample t-test against the low-resolution baseline mean (See US-2).

## Assumptions

- **Assumption about data availability**: The COCO, ImageNet-1K, and ChestX-ray14 datasets and the pre-trained ViQ encoder weights are available via standard Hugging Face or direct download links without requiring proprietary access.
- **Assumption about compute constraints**: The 64x64 training and 1024x1024 inference will fit within the available RAM and disk limits of the GitHub Actions free runner by processing data in batches; if not, the dataset will be subsampled to fit.
- **Assumption about model behavior**: The frozen ViQ encoder weights are compatible with the PyTorch version available in the CI environment and do not require CUDA-specific kernels.
- **Assumption about text alignment**: The frozen CLIP text encoder provides a stable, independent reference for semantic similarity that does not require re-training or fine-tuning.
- **Assumption about resolution invariance**: The ViQ architecture's "any resolution" claim is a hypothesis to be validated; if the encoder is not actually resolution-invariant (e.g., requires fixed input size), the high-resolution inference (US-2) will fail with a shape mismatch error, and the experiment will terminate. This assumption is specific to the ViQ encoder weights.
- **Assumption about texture metric**: High-frequency energy (e.g., via Laplacian variance or FFT magnitude) is a sufficient proxy for "texture complexity" for the purpose of this correlation analysis.