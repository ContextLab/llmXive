# Feature Specification: llmXive follow-up: extending "EvalVerse" with CPU-tractable Feature Distillation

**Feature Branch**: `001-llmxive-feature-distillation`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "To what extent do low-level visual parameters (motion consistency, lighting distribution, composition geometry) suffice to explain human expert judgments of cinematic quality, and which specific qualitative dimensions of "professionalism" inherently require high-level semantic reasoning beyond these physical descriptors?"

## User Scenarios & Testing

### User Story 1 - Dimensional Viability Analysis (Priority: P1)

**Journey**: A researcher needs to determine which specific technical sub-dimensions of cinematic quality (e.g., "camera smoothness," "lighting consistency") can be accurately predicted using only low-level, hand-crafted computer vision features (optical flow, HOG, histograms) without relying on heavy VLM inference.

**Why this priority**: This is the core research question. If the system cannot identify which dimensions are "feature-sufficient," the entire project fails to address the literature gap regarding the trade-off between accuracy and compute efficiency.

**Independent Test**: The system can be fully tested by running the feature extraction and regression pipeline on the EvalVerse dataset and outputting a ranked list of dimensions with their correlation coefficients against the VLM reference scores.

**Acceptance Scenarios**:
1. **Given** the EvalVerse dataset with expert-annotated sub-dimension scores, **When** the system extracts hand-crafted features and trains a regularized regression model, **Then** the system outputs a correlation coefficient for each dimension with a 95% confidence interval.
2. **Given** a dimension where the lower bound of the 95% confidence interval for the Pearson correlation is < 0.70, **When** the analysis completes, **Then** the system explicitly flags this dimension as "VLM-required" in the results report. This threshold is justified by community standards in video quality assessment (VQA) literature where r > 0.7 is considered "strong" correlation for perceptual metrics.
3. **Given** a dimension where the correlation is > 0.85, **When** the analysis completes, **Then** the system explicitly flags this dimension as "feature-sufficient" in the results report. This threshold aligns with requirements for "professional" grading applications where higher fidelity is needed.

---

### User Story 2 - Compute Feasibility Profiling (Priority: P2)

**Journey**: A resource-constrained researcher needs to verify that the proposed lightweight evaluation pipeline runs entirely on a standard CPU within the constraints of a GitHub Actions free-tier runner (limited cores, limited RAM, 6h time limit) before deploying it to their own workflow.

**Why this priority**: The project's motivation is explicitly to enable "real-time agentic workflows" and "resource-constrained researchers." If the method requires GPU or exceeds memory limits, the solution is non-viable for the target audience.

**Independent Test**: The system can be fully tested by executing the full pipeline on a representative subset of the dataset within a CPU-only environment and reporting peak memory usage and total inference time per clip.

**Acceptance Scenarios**:
1. **Given** a video clip from the EvalVerse dataset, **When** the feature extraction and prediction pipeline runs on a 2-core CPU instance, **Then** the peak memory usage must not exceed 7 GB.
2. **Given** a batch of 100 video clips, **When** the pipeline processes them, **Then** the total inference time must be less than 30 minutes, ensuring the time-per-clip metric scales linearly to fit within a 6-hour job limit for the full dataset size (N=10,000 clips).
3. **Given** the pipeline execution, **When** it completes, **Then** the system must log the exact CPU time and memory peak to a structured report file.

---

### User Story 3 - Sensitivity Analysis of Feature Thresholds (Priority: P3)

**Journey**: A methodologist needs to ensure that the decision boundaries used to classify a dimension as "feature-sufficient" (e.g., correlation > 0.85) are robust and not artifacts of a single arbitrary cutoff.

**Why this priority**: To ensure methodological soundness, the study must demonstrate that the findings hold across a range of reasonable thresholds, preventing false positives in the classification of "feature-sufficient" dimensions.

**Independent Test**: The system can be fully tested by re-running the classification logic with slightly varied thresholds and verifying that the set of "feature-sufficient" dimensions remains stable.

**Acceptance Scenarios**:
1. **Given** a dimension identified as "feature-sufficient" at a correlation threshold of 0.85, **When** the threshold is swept across {0.80, 0.85, 0.90}, **Then** the system reports the classification stability (the proportion of dimensions that flip status between "feature-sufficient" and "VLM-required").
2. **Given** the sensitivity analysis results, **When** the variation in classification stability (flip rate) exceeds 5% across the threshold sweep, **Then** the system flags the dimension as "threshold-sensitive" and recommends manual review.
3. **Given** the final report, **When** it is generated, **Then** it must include a table showing the classification outcome for each dimension at all tested thresholds.

---

### Edge Cases

- **What happens when** a video clip in the EvalVerse dataset has no audio track? **How does system handle**: The audio feature extraction module (Librosa) must gracefully skip audio feature extraction for that clip and return a null vector for audio features without crashing the pipeline, logging a warning.
- **How does system handle** a video clip where optical flow calculation fails (e.g., all black frames or extreme motion blur)? **How does system handle**: The feature extraction pipeline must catch the exception, return a default "zero-motion" vector, and flag the sample as "low-quality data" in the preprocessing report. If the global error rate across the dataset exceeds a predefined threshold, the system must exclude these samples from the final correlation calculation.
- **What happens when** the correlation coefficient is exactly 0.85? **How does system handle**: The system must treat the boundary condition inclusively (≥ 0.85) for the "feature-sufficient" classification, as per the defined acceptance criteria.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract low-level visual features (optical flow magnitude/variance, HOG density, global histogram statistics) from video clips using CPU-native libraries (OpenCV) without GPU acceleration. (See US-1)
- **FR-002**: System MUST extract audio features (spectral centroid, zero-crossing rate) from video clips using CPU-native libraries (Librosa) and handle missing audio tracks gracefully. (See US-1)
- **FR-003**: System MUST train regularized linear regression (Ridge/Lasso) and shallow tree-based models (XGBoost) to map extracted feature vectors to EvalVerse sub-dimension scores. (See US-1)
- **FR-004**: System MUST calculate Pearson and Spearman correlation coefficients between model predictions and the VLM reference scores for each dimension. (See US-1)
- **FR-005**: System MUST perform a sensitivity analysis by sweeping the classification threshold (e.g., correlation cutoff) across a defined set of values {0.80, 0.85, 0.90} and report the resulting variation in classification outcome. (See US-3)
- **FR-006**: System MUST profile and log peak memory usage and inference time per video clip to verify compliance with the 7 GB RAM and 6-hour time limit constraints. (See US-2)
- **FR-007**: System MUST apply bootstrapping to generate 95% confidence intervals for all reported correlation coefficients. (See US-1)
- **FR-008**: System MUST explicitly flag dimensions where the lower bound of the 95% confidence interval drops below 0.70 as "VLM-required" in the final output. (See US-1)
- **FR-009**: System MUST perform a preliminary validation step by correlating VLM reference scores with a subset of human expert ratings (n ≥ 30) to confirm alignment (r ≥ 0.70) before proceeding with the main distillation study. (See US-1)

### Key Entities

- **VideoClip**: Represents a single entry from the EvalVerse dataset, containing raw pixel data, an optional audio track, and the associated ground truth sub-dimension scores.
- **FeatureVector**: A numerical representation of a video clip derived from hand-crafted algorithms (e.g., optical flow magnitude, HOG density), distinct from raw pixels.
- **DimensionScore**: The ground truth value for a specific cinematic attribute (e.g., "camera smoothness") as provided by EvalVerse experts/VLMs.
- **ModelPerformance**: A record containing the correlation coefficients, confidence intervals, and inference metrics for a specific dimension and model combination.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Pearson correlation coefficient between the lightweight model predictions and the EvalVerse VLM reference scores is measured against the threshold of 0.85 to determine "feature-sufficiency." (See FR-004)
- **SC-002**: The peak memory usage of the feature extraction and prediction pipeline is measured against the 7 GB RAM constraint of the GitHub Actions free-tier runner. (See FR-006)
- **SC-003**: The inference time per video clip is measured against the requirement to process the full dataset (N=10,000 clips) within a 6-hour window on a 2-core CPU. (See FR-006)
- **SC-004**: The variation in the classification outcome (stability) is measured across the threshold sweep {0.80, 0.85, 0.90} to assess the robustness of the decision boundary. (See FR-005)
- **SC-005**: The width of the 95% confidence interval for the correlation coefficients is measured against the stability requirement (lower bound must be > 0.70 for a dimension to be considered reliably predictable). (See FR-007)
- **SC-006**: The alignment between VLM reference scores and human expert ratings is measured (Pearson r) to validate the proxy target, requiring r ≥ 0.70. (See FR-009)

## Assumptions

- **Dataset Availability**: The EvalVerse dataset (a large-scale collection of clips with expert annotations) is publicly accessible via the official repository or Zenodo archive with a stable DOI, and the sub-dimension scores are explicitly labeled in the metadata.
- **CPU-tractability**: The OpenCV and Librosa feature extraction methods, along with Ridge/Lasso and XGBoost models, are computationally feasible on a 2-core CPU with 7 GB RAM for the specified dataset size (N=10,000 clips) without requiring downsampling that would invalidate the statistical power.
- **Ground Truth Validity**: The VLM reference scores are treated as the target variable for the main distillation study ONLY AFTER FR-009 validates their alignment with human expert judgments (r ≥ 0.70) on a pilot subset.
- **No GPU Dependency**: The implementation will strictly avoid any libraries or methods that require CUDA, 8-bit/4-bit quantization, or GPU-specific acceleration, relying solely on standard CPU instruction sets.
- **Variable Completeness**: The EvalVerse dataset contains the necessary raw video and audio data to derive all required low-level features (optical flow, HOG, spectral centroid) without missing critical metadata fields.