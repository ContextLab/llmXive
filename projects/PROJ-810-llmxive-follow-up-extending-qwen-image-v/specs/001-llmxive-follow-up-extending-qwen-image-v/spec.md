# Feature Specification: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

**Feature Branch**: `001-llmxive-vae-geometric-analysis`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Qwen-Image-VAE-2.0 Technical Report'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Latent Space Disentanglement Analysis (Priority: P1)

As a researcher, I want to encode document images from the Omni-Doc-1 (TokenBench subset) dataset into latent vectors and analyze their organization using unsupervised clustering and disentanglement metrics, so that I can determine if the Qwen-Image-VAE-2.0 latent space geometrically separates textual and visual features without relying on trivial pixel statistics.

**Why this priority**: This is the core scientific inquiry. Without establishing true disentanglement (independence of factors) rather than simple linear separability, the subsequent editing capabilities (US-02) lack a theoretical foundation. It is the primary validation of the hypothesis.

**Independent Test**: The system can be fully tested by running the encoding, clustering, and disentanglement metric pipeline on a sampled subset of the dataset and reporting the DCI scores and cluster purity. A result > 0.8 DCI score and > 90% cluster purity (against ground truth) confirms the hypothesis without needing the editing module.

**Acceptance Scenarios**:

1. **Given** a set of document images with ground-truth bounding boxes for text and image regions, **When** the system extracts latent vectors from *unlabeled* crops (filtered for purity), applies K-Means clustering (k=2), and evaluates cluster purity against ground-truth labels, **Then** the system must report:
   - (a) Cluster purity ≥ 90% (evaluated against ground truth, not used for training).
   - (b) DCI (Disentanglement, Completeness, Informativeness) score ≥ 0.8.
   - (c) Classification accuracy significantly exceeds the mean(permutation_accuracy) from a 1000-permutation test, rejecting the null hypothesis of random texture separation.
   If the pre-experiment power analysis (US-03) indicates insufficient power (power < 0.8) or the sample size N exceeds the 6-hour runtime limit, the result is reported as "inconclusive" or "infeasible" rather than a failure.
2. **Given** the encoded latent vectors, **When** PCA is applied to reduce dimensions to 2D, **Then** the resulting plot must visually display two distinct, non-overlapping clusters corresponding to text and image modalities.
3. **Given** the classification results, **When** a permutation test is performed (shuffling labels 1000 times), **Then** the observed accuracy must be significantly higher (p < 0.05, Bonferroni corrected) than the distribution of random accuracies.

---

### User Story 2 - Zero-Shot Semantic Editing via Vector Arithmetic (Priority: P2)

As a user, I want to perform linear vector arithmetic on the latent representations to swap text content while preserving layout, so that I can verify the geometric structure supports efficient, non-diffusion-based editing.

**Why this priority**: This demonstrates the practical utility of the disentanglement found in US-01. It validates the "zero-shot semantic manipulation" claim. It depends on the existence of the distinct centroids identified in US-01 and the verification of linearity.

**Independent Test**: The system can be tested by taking a document image, computing the "text mean" vector, subtracting it, adding a new text mean vector, decoding the result, and verifying the text content changed while the layout remained intact via OCR and geometry metrics.

**Acceptance Scenarios**:

1. **Given** a source document image and a target text string, **When** the system computes $z_{new} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$ and decodes the result, **Then** the system MUST:
   - (a) **First**, verify via OCR (PaddleOCR v2.7.0, ch_PP-OCRv4) that the text content has changed (≥ 95% character accuracy match to target). If this fails, the sample is excluded from layout metrics.
   - (b) Generate a baseline reconstruction of the original image ($z_{baseline} = \text{decode}(\text{encode}(z_{doc}))$) to serve as a control.
   - (c) Compute Masked SSIM between the edited image and the baseline reconstruction for non-text regions; the result must be ≥ 0.85.
   - (d) Compute an Edge Alignment Score (Canny edge detection, IoU of edge maps) between edited and baseline images; the result must be ≥ 0.80.
   - (e) Compute a Keypoint Matching Score (SIFT detector, RANSAC inlier ratio ≥ 0.6, matching ratio 0.75) on non-text regions; the score must be ≥ 0.80.
   If (c), (d), and (e) pass, layout preservation is confirmed independent of the disentanglement hypothesis. If (d) fails but (e) passes, the failure is attributed to VAE texture artifacts, not layout distortion. If all fail, the hypothesis is rejected.
2. **Given** the edited image, **When** an OCR engine (PaddleOCR v2.7.0 with ch_PP-OCRv4 model, standard Otsu binarization, and Hough Line Transform deskewing) processes the text region, **Then** the recognized text must match the target string with ≥ 95% character accuracy.
3. **Given** the editing operation, **When** the process is executed on a 2 vCPU, 7 GB RAM environment, **Then** it must complete within 60 seconds per image to ensure feasibility. If the model fails to load or run on CPU (requiring GPU), the "CPU feasibility" hypothesis is explicitly rejected.

---

### User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

As a reviewer, I want to see a sensitivity analysis of the disentanglement threshold, a linearity validation, and a report on multiple-comparison corrections, so that I can verify the methodological soundness of the findings.

**Why this priority**: This addresses the methodological panel's requirements for robustness. It ensures the results are not artifacts of specific hyperparameters, chance findings, or invalid statistical assumptions.

**Independent Test**: The system can be tested by re-running the separability analysis with varying decision thresholds, verifying linearity on a pilot set, and applying a correction method (e.g., Bonferroni) to the valid hypothesis tests.

**Acceptance Scenarios**:

1. **Given** the linear separability results, **When** the decision threshold is swept over a range of values around the optimal boundary, **Then** the system must report the variation in false-positive and false-negative rates, confirming the result is robust to small threshold changes.
2. **Given** multiple hypothesis tests performed (e.g., accuracy, F1), **When** individual significance tests are applied to each distinct metric, **Then** the p-values must be adjusted using the Bonferroni correction (or Holm-Bonferroni) to control the family-wise error rate at α ≤ 0.05. The adjusted p-values must indicate statistical significance for the primary findings. SSIM and Keypoint Score metrics are excluded from this family as they are continuous metrics without defined p-values.
3. **Given** the power analysis, **When** the sample size is evaluated, **Then** the system must report the achieved power; if power < 0.8 or if the required N exceeds the 6-hour runtime limit on 2 vCPU, 7 GB RAM, the hypothesis is considered "inconclusive" or "infeasible" and the specific power value and limitation must be explicitly reported.
4. **Given** the linearity assumption, **When** the system tests the vector difference consistency on a pilot set of 10 diverse samples, **Then** the R² value must be ≥ 0.9. If R² < 0.9, the editing hypothesis is rejected before proceeding to full-scale editing.

### Edge Cases

- What happens if the Omni-Doc-1 (TokenBench subset) dataset is unavailable or the specific subset referenced in the report cannot be downloaded? (System must fail gracefully with a clear error message and fallback to a smaller, local sample if provided, or report "infeasible").
- How does the system handle latent vectors where the "text" and "image" regions overlap significantly in the source image, making ground-truth isolation ambiguous? (System must exclude ambiguous regions with >10% overlap or low purity scores from the training set).
- What happens if the decoding of the edited latent vector produces artifacts or fails to reconstruct the image? (System must log the failure, report a low SSIM/Edge Alignment score, and flag the specific vector for exclusion from the final analysis).
- What happens if the model requires GPU to run (e.g., memory overflow)? (System must explicitly report "CPU feasibility hypothesis rejected" and terminate the experiment).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the Omni-Doc-1 (TokenBench subset) dataset from `https://huggingface.co/datasets/omnineura/Omni-Doc-1` and validate that it contains the required 'text-only' and 'image-only' label keys before proceeding. (See US-01)
- **FR-002**: System MUST load the pre-trained Qwen-Image-VAE-2.0 model (HuggingFace ID: `Qwen/Qwen-Image-VAE-2.0`) and PaddleOCR v2.7.0 CPU wheel (ch_PP-OCRv4 model) in CPU-only mode on a 2 vCPU, 7 GB RAM environment, ensuring no CUDA or GPU dependencies are invoked. If the model fails to load or run on CPU, the "CPU feasibility" hypothesis is rejected. (See US-01, US-02)
- **FR-003**: System MUST extract latent vectors corresponding strictly to "text-only" and "image-only" regions using the provided bounding box annotations, applying a purity filter to exclude crops with >10% overlap or ambiguous modalities. The system MUST train a K-Means clustering model (unsupervised) on *unlabeled* crops and use ground-truth labels *only* for evaluation (purity metrics). (See US-01)
- **FR-004**: System MUST compute DCI (Disentanglement, Completeness, Informativeness) metrics and orthogonality checks on the latent clusters to validate true disentanglement beyond simple separability. (See US-01)
- **FR-005**: System MUST verify the linearity assumption on a pilot set of 10 diverse samples (R² ≥ 0.9 for vector arithmetic consistency) before performing full-scale editing. (See US-02)
- **FR-006**: System MUST decode edited latent vectors back to images and evaluate reconstruction fidelity using Masked SSIM (≥ 0.85) and Edge Alignment Score (≥ 0.80) against the baseline reconstruction for non-text regions, *after* verifying text change via OCR. (See US-02)
- **FR-007**: System MUST perform a permutation test (1000 permutations) to validate that observed separability is significantly higher than random chance (p < 0.05). (See US-01)
- **FR-008**: System MUST execute a sensitivity analysis sweeping the classification threshold over a range of low-probability values and report the impact on error rates. (See US-03)
- **FR-009**: System MUST apply Bonferroni (or Holm-Bonferroni) correction to the family of p-values derived from accuracy and F1 tests (generated via permutation test) to control the family-wise error rate at α ≤ 0.05. SSIM and Keypoint Score metrics are excluded from this family. (See US-03)
- **FR-010**: System MUST detect keypoints (using SIFT detector with RANSAC inlier ratio ≥ 0.6 and matching ratio 0.75) in non-text regions of the baseline and edited images, match them, and compute a Keypoint Matching Score ≥ 0.80 to provide an independent measure of layout preservation. (See US-02)

### Key Entities

- **LatentVector**: A high-dimensional numerical representation of an image region, containing the encoded semantic and visual features.
- **RegionAnnotation**: Metadata defining the bounding box coordinates and modality label (text/image) for a specific area of a document image.
- **Centroid**: The mean vector of a cluster of latent vectors, representing the central tendency of a specific modality (text or image), computed empirically from the dataset.
- **EditedImage**: An image generated by decoding a modified latent vector, intended to have swapped text content but preserved layout.
- **BaselineReconstruction**: An image generated by encoding and decoding the original image without any vector arithmetic, used as a control for layout preservation.
- **PurityFilter**: A mechanism to exclude crops with >10% overlap or ambiguous modalities from the training set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The linear separability accuracy is measured against the baseline random chance distribution (mean + 3*std from 1000 permutations) to reject the null hypothesis of random texture separation; if the power analysis indicates insufficient power (power < 0.8) or the sample size exceeds the runtime limit, the result is reported as "inconclusive" or "infeasible". (See US-01)
- **SC-002**: The reconstruction fidelity (Masked SSIM ≥ 0.85, Edge Alignment Score ≥ 0.80) and layout preservation (Keypoint Matching Score ≥ 0.80) of edited images are measured against the baseline reconstruction (original image encoded/decoded without arithmetic) to isolate editing success from disentanglement failure, *only after* OCR verification confirms text change. (See US-02)
- **SC-003**: The statistical significance of the disentanglement and editing results is measured against a Bonferroni-corrected p-value threshold (α ≤ 0.05 / N_tests) for the family of dependent hypotheses (accuracy, F1). SSIM and Keypoint Score are excluded from this family. (See US-03)
- **SC-004**: The computational feasibility is measured against the constraint of ≤ 6 hours total runtime on a 2 vCPU, 7 GB RAM runner with the sample size N determined by power analysis (power ≥ 0.8). If N * 60s > 6 hours, the hypothesis is "infeasible". (See US-03)
- **SC-005**: The robustness of the threshold is measured by the variation in false-positive rates across the sensitivity sweep. (See US-03)

## Assumptions

- The Omni-Doc-1 (TokenBench subset) dataset is accessible via `https://huggingface.co/datasets/omnineura/Omni-Doc-1` and contains sufficient samples of distinct text and image regions with valid 'text-only' and 'image-only' label keys for statistical power.
- The pre-trained Qwen-Image-VAE-2.0 model (HuggingFace ID: `Qwen/Qwen-Image-VAE-2.0`) is available and can be loaded into CPU memory (2 vCPU, 7 GB RAM) without requiring quantization or GPU acceleration. If it fails, the "CPU feasibility" hypothesis is rejected.
- The ground-truth bounding box annotations in the dataset are accurate enough to isolate "text-only" and "image-only" regions, and the purity filter (>10% overlap exclusion) is sufficient to remove mixed-modality noise.
- The linear vector arithmetic approach is sufficient to achieve semantic editing without requiring fine-tuning or complex optimization, provided the linearity assumption is verified (R² ≥ 0.9) on a pilot set.
- The sample size N required to achieve a statistical power of ≥ 0.8 for detecting a large effect size (Cohen's d > 0.8) is feasible within the 6-hour runtime limit on 2 vCPU, 7 GB RAM. If not, the result is "infeasible".
- The CPU-only environment (2 vCPU, 7 GB RAM) is sufficient to run the encoder, decoder, and classification models on the sampled dataset within a fixed time limit.
- The "text mean" and "image mean" vectors are computed empirically from the dataset as part of the analysis, not assumed a priori; the hypothesis is that these empirically derived centroids will exhibit geometric structure (disentanglement).
- A reliable keypoint detector (SIFT) and OCR engine (PaddleOCR v2.7.0, ch_PP-OCRv4) are available and capable of detecting stable features and text in document images within the 7 GB RAM constraint.
- If the model fails to load or run on CPU (requiring GPU), the "CPU feasibility" hypothesis is explicitly rejected, not treated as a fallback.
