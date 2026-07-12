# Feature Specification: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

**Feature Branch**: `001-llmxive-vae-geometric-analysis`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Qwen-Image-VAE-2.0 Technical Report'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Latent Space Disentanglement Analysis (Priority: P1)

As a researcher, I want to encode document images from the OmniDoc-TokenBench dataset into latent vectors and classify them by modality (text-only vs. image-only) using a lightweight linear model, so that I can determine if the Qwen-Image-VAE-2.0 latent space geometrically separates textual and visual features.

**Why this priority**: This is the core scientific inquiry. Without establishing linear separability, the subsequent editing capabilities (US-02) lack a theoretical foundation. It is the primary validation of the hypothesis.

**Independent Test**: The system can be fully tested by running the encoding and classification pipeline on a sampled subset of the dataset and reporting the classification accuracy and F1-score. A result > 90% accuracy confirms the hypothesis without needing the editing module.

**Acceptance Scenarios**:

1. **Given** a set of document images with ground-truth bounding boxes for text and image regions, **When** the system extracts latent vectors from *unlabeled* crops and trains a Linear SVM, **Then** the model must report a classification accuracy of ≥ 90% and an F1-score of ≥ 0.90 against the ground-truth labels (used only for evaluation) to confirm disentanglement. If the power analysis (US-03) indicates insufficient power (power < 0.8), the result is reported as "inconclusive" rather than a failure.
2. **Given** the encoded latent vectors, **When** PCA is applied to reduce dimensions to 2D, **Then** the resulting plot must visually display two distinct, non-overlapping clusters corresponding to text and image modalities.
3. **Given** the classification results, **When** a permutation test is performed (shuffling labels multiple times), **Then** the observed accuracy must be significantly higher (p < 0.05) than the distribution of random accuracies.

---

### User Story 2 - Zero-Shot Semantic Editing via Vector Arithmetic (Priority: P2)

As a user, I want to perform linear vector arithmetic on the latent representations to swap text content while preserving layout, so that I can verify the geometric structure supports efficient, non-diffusion-based editing.

**Why this priority**: This demonstrates the practical utility of the disentanglement found in US-01. It validates the "zero-shot semantic manipulation" claim. It depends on the existence of the distinct centroids identified in US-01.

**Independent Test**: The system can be tested by taking a document image, computing the "text mean" vector, subtracting it, adding a new text mean vector, decoding the result, and verifying the text content changed while the layout remained intact.

**Acceptance Scenarios**:

1. **Given** a source document image and a target text string, **When** the system computes $z_{new} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$ and decodes the result, **Then** the system MUST:
   - (a) Generate a baseline reconstruction of the original image ($z_{baseline} = \text{decode}(\text{encode}(z_{doc}))$) to serve as a control.
   - (b) Compute Masked SSIM between the edited image and the baseline reconstruction for non-text regions; the result must be ≥ 0.85.
   - (c) Compute a Keypoint Matching Score (using SIFT/ORB detection on non-text regions between edited and baseline images); the score must be ≥ 0.80.
   If both (b) and (c) pass, layout preservation is confirmed independent of the disentanglement hypothesis. If (b) fails but (c) passes, the failure is attributed to VAE texture artifacts, not layout distortion. If both fail, the hypothesis is rejected.
2. **Given** the edited image, **When** an OCR engine (PaddleOCR with English model and standard binarization) processes the text region, **Then** the recognized text must match the target string with ≥ 95% character accuracy, OR the system must flag the sample for manual verification of a random sample to confirm text swap success independent of OCR engine limitations.
3. **Given** the editing operation, **When** the process is executed on a 2 vCPU, 7 GB RAM environment, **Then** it must complete within 60 seconds per image to ensure feasibility.

---

### User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

As a reviewer, I want to see a sensitivity analysis of the disentanglement threshold and a report on multiple-comparison corrections, so that I can verify the methodological soundness of the findings.

**Why this priority**: This addresses the methodological panel's requirements for robustness. It ensures the results are not artifacts of specific hyperparameters or chance findings due to multiple tests.

**Independent Test**: The system can be tested by re-running the separability analysis with varying decision thresholds and reporting the stability of the accuracy metrics, and by applying a correction method (e.g., Bonferroni) to the statistical tests.

**Acceptance Scenarios**:

1. **Given** the linear separability results, **When** the decision threshold is swept over a range of values around the optimal boundary, **Then** the system must report the variation in false-positive and false-negative rates, confirming the result is robust to small threshold changes.
2. **Given** multiple hypothesis tests performed (e.g., accuracy, F1, SSIM, Keypoint Score), **When** individual significance tests are applied to each distinct metric, **Then** the p-values must be adjusted using the Bonferroni correction (or Holm-Bonferroni) to control the family-wise error rate at α ≤ 0.05. The adjusted p-values must indicate statistical significance for the primary findings.
3. **Given** the power analysis, **When** the sample size is evaluated, **Then** the system must report the achieved power; if power < 0.8, the hypothesis is considered "inconclusive" and the specific power value and limitation must be explicitly reported.

### Edge Cases

- What happens if the OmniDoc-TokenBench dataset is unavailable or the specific subset referenced in the report cannot be downloaded? (System must fail gracefully with a clear error message and fallback to a smaller, local sample if provided).
- How does the system handle latent vectors where the "text" and "image" regions overlap significantly in the source image, making ground-truth isolation ambiguous? (System must exclude ambiguous regions or flag them for manual review).
- What happens if the decoding of the edited latent vector produces artifacts or fails to reconstruct the image? (System must log the failure, report a low SSIM score, and flag the specific vector for exclusion from the final analysis).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the OmniDoc-TokenBench dataset (or the specific subset referenced in the Qwen-Image-VAE-2.0 report) containing document images with ground-truth bounding boxes for text and image regions. (See US-01)
- **FR-002**: System MUST load the pre-trained Qwen-Image-VAE-2.0 encoder and decoder in CPU-only mode on a 2 vCPU, 7 GB RAM environment, ensuring no CUDA or GPU dependencies are invoked. (See US-01, US-02)
- **FR-003**: System MUST extract latent vectors corresponding strictly to "text-only" and "image-only" regions using the provided bounding box annotations, ensuring the classifier is trained on *unlabeled* crops and labels are used only for evaluation. (See US-01)
- **FR-004**: System MUST train a lightweight Linear SVM or Logistic Regression classifier on CPU to predict the modality (text vs. image) of the latent vectors and output accuracy/F1 metrics. (See US-01)
- **FR-005**: System MUST compute centroid vectors for text and image clusters and perform vector arithmetic ($z_{new} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$) to generate edited latent representations. (See US-02)
- **FR-006**: System MUST decode edited latent vectors back to images and evaluate reconstruction fidelity using Masked SSIM against the baseline reconstruction (original image encoded and decoded without arithmetic) for non-text regions. (See US-02)
- **FR-007**: System MUST perform a permutation test to validate that observed separability is significantly higher than random chance (p < 0.05). (See US-01)
- **FR-008**: System MUST execute a sensitivity analysis sweeping the classification threshold over a range of low-probability values and report the impact on error rates. (See US-03)
- **FR-009**: System MUST apply Bonferroni (or Holm-Bonferroni) correction to the family of p-values derived from accuracy, F1, SSIM, and Keypoint Score tests to control the family-wise error rate at α ≤ 0.05. (See US-03)
- **FR-010**: System MUST detect keypoints (using SIFT or ORB) in non-text regions of the baseline and edited images, match them, and compute a Keypoint Matching Score ≥ 0.80 to provide an independent measure of layout preservation. (See US-02)

### Key Entities

- **LatentVector**: A high-dimensional numerical representation of an image region, containing the encoded semantic and visual features.
- **RegionAnnotation**: Metadata defining the bounding box coordinates and modality label (text/image) for a specific area of a document image.
- **Centroid**: The mean vector of a cluster of latent vectors, representing the central tendency of a specific modality (text or image), computed empirically from the dataset.
- **EditedImage**: An image generated by decoding a modified latent vector, intended to have swapped text content but preserved layout.
- **BaselineReconstruction**: An image generated by encoding and decoding the original image without any vector arithmetic, used as a control for layout preservation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The linear separability accuracy is measured against the baseline random chance and the target threshold of 90% defined in the research hypothesis; if the power analysis indicates insufficient power (power < 0.8), the result is reported as "inconclusive". (See US-01)
- **SC-002**: The reconstruction fidelity (Masked SSIM ≥ 0.85) and layout preservation (Keypoint Matching Score ≥ 0.80) of edited images are measured against the baseline reconstruction (original image encoded/decoded without arithmetic) to isolate editing success from disentanglement failure. (See US-02)
- **SC-003**: The statistical significance of the disentanglement and editing results is measured against a Bonferroni-corrected p-value threshold (α ≤ 0.05 / N_tests) for the family of dependent hypotheses. (See US-03)
- **SC-004**: The computational feasibility is measured against the constraint of ≤ 6 hours total runtime on a 2 vCPU, 7 GB RAM runner with the full OmniDoc-TokenBench subset (N images). (See Assumptions)
- **SC-005**: The robustness of the threshold is measured by the variation in false-positive rates across the sensitivity sweep. (See US-03)

## Assumptions

- The OmniDoc-TokenBench dataset is accessible via the repository link provided in the Qwen-Image-VAE-2.0 report and contains sufficient samples of distinct text and image regions for statistical power.
- The pre-trained Qwen-Image-VAE-2.0 model weights are available via HuggingFace or the paper's codebase and can be loaded into CPU memory (2 vCPU, 7 GB RAM) without requiring quantization or GPU acceleration.
- The ground-truth bounding box annotations in the dataset are accurate enough to isolate "text-only" and "image-only" regions without significant contamination from mixed modalities.
- The linear vector arithmetic approach is sufficient to achieve semantic editing without requiring fine-tuning or complex optimization, as hypothesized in the research question.
- The sample size of the dataset subset used is adequate to achieve a statistical power of ≥ 0.8 for detecting a large effect size (Cohen's d > 0.8) in the separability test; if not, the limitation will be explicitly reported as "inconclusive".
- The CPU-only environment (a small number of vCPUs, 7 GB RAM) is sufficient to run the encoder, decoder, and classification models on the sampled dataset within a fixed time limit.
- The "text mean" and "image mean" vectors are computed empirically from the dataset as part of the analysis, not assumed a priori; the hypothesis is that these empirically derived centroids will exhibit geometric structure (disentanglement).
- A reliable keypoint detector (SIFT/ORB) is available and capable of detecting stable features in non-text regions of the document images to support the Keypoint Matching Score metric.