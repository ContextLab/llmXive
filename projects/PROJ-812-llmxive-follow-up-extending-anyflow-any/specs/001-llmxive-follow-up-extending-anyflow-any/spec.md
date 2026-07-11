# Feature Specification: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

**Feature Branch**: `001-gene-regulation` (Note: Branch name inherited from mechanical step; semantic content refers to video flow stability)
**Created**: 2026-07-11
**Status**: Draft
**Input**: User description: "llmXive follow-up: extending 'AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil'"

## User Scenarios & Testing

### User Story 1 - Automated Flow-Map Divergence Measurement (Priority: P1)

**As a** video model researcher, **I want** to automatically compute the "flow-map divergence" (L2 distance between predicted latent states and high-resolution Euler rollouts) for a batch of video clips, **so that** I can quantify the numerical instability of the AnyFlow model on specific input sequences without manual inspection.

**Why this priority**: This is the core scientific measurement. Without an automated, reproducible way to calculate the divergence metric, the study cannot proceed. It directly addresses the research question's dependent variable.

**Independent Test**: A script can be run on a single video clip file. The system outputs a single floating-point number representing a divergence metric. This can be verified by manually computing the Euler rollout and the model prediction for the same clip and checking the distance.

**Acceptance Scenarios**:

1. **Given** a video clip file in the input directory, **When** the divergence calculator script is executed, **Then** the system outputs a precise L2 divergence value and logs the intermediate latent states.
2. **Given** a video clip with a known "hard cut" (high discontinuity), **When** the calculation runs, **Then** the resulting divergence value is significantly higher (e.g., > 0.5) than that of a smooth continuous motion clip processed in the same run.

---

### User Story 2 - Statistical Feature Extraction & Correlation Analysis (Priority: P2)

**As a** data analyst, **I want** to extract statistical features (optical flow variance, frame-to-frame MSE) from the input clips and correlate them with the computed divergence values, **so that** I can identify which specific input properties predict model instability.

**Why this priority**: This transforms raw measurements into scientific insight. It answers the "which statistical properties correlate" part of the research question.

**Independent Test**: A dataset of clips with pre-computed divergence values can be fed into the analysis module. The module outputs a correlation matrix and a regression model. The results can be verified by running a standard Python `scipy` or `statsmodels` correlation on the same CSV data.

**Acceptance Scenarios**:

1. **Given** a CSV containing input statistical features and divergence labels, **When** the correlation analysis runs, **Then** the system outputs a Pearson correlation coefficient and p-value for each feature.
2. **Given** a dataset where optical flow variance is artificially inflated, **When** the analysis runs, **Then** the system reports a strong positive correlation (r > 0.7) between optical flow variance and divergence.

---

### User Story 3 - Instability Threshold Validation & Sensitivity Sweep (Priority: P3)

**As a** dataset curator, **I want** to determine a specific divergence threshold that separates "stable" from "unstable" clips and verify its robustness via sensitivity analysis, **so that** I can reliably filter unsuitable datasets before training.

**Why this priority**: This provides the practical "tool for dataset screening" mentioned in the motivation. The sensitivity analysis ensures the threshold isn't an arbitrary artifact.

**Independent Test**: The system can be run with three different threshold values. The output should show how precision and recall metrics shift, confirming the stability of the classification boundary.

**Acceptance Scenarios**:

1. **Given** a labeled dataset of "stable" and "unstable" clips, **When** the threshold validator runs, **Then** it outputs the optimal threshold, precision, and recall.
2. **Given** the optimal threshold, **When** the sensitivity sweep is executed, **Then** the system reports the variation in false-positive and false-negative rates across a range of ±0.05 around the threshold.

### Edge Cases

- **What happens when** a video clip contains a complete black frame or corrupted data? The system must handle the optical flow calculation failure gracefully and log the clip as "skipped" rather than crashing the pipeline.
- **How does the system handle** a video clip where the Euler rollout (ground truth) fails to converge due to extreme discontinuity? The system must flag this as a "failed ground truth" and exclude the clip from the correlation analysis to avoid noise.
- **What happens when** the input dataset has fewer than 10 clips? The system must warn that statistical significance is low and potentially skip the regression analysis, outputting only descriptive statistics.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute the distance between the AnyFlow predicted latent state and the high-resolution Euler rollout state for every input video clip. (See US-1)
- **FR-002**: System MUST extract at least three statistical features (optical flow magnitude variance, frame-to-frame MSE, temporal gradient sparsity) from raw pixel data. (See US-2)
- **FR-003**: System MUST perform multiple linear regression and Pearson correlation analysis between the extracted features and the flow-map divergence. (See US-2)
- **FR-004**: System MUST determine a divergence threshold that maximizes the F1-score for classifying clips as "stable" vs "unstable" using a held-out validation set ([deferred] of data) and execute a sensitivity sweep over a range of ±0.05. (See US-3)
- **FR-005**: System MUST log CPU utilization and total execution time for every processed clip. (See US-1)
- **FR-006**: System MUST handle missing or corrupted video files by logging an error and skipping the file without terminating the entire batch process. (See Edge Cases)
- **FR-007**: System MUST support a manual annotation interface or import mechanism where two independent raters label clips as "stable" or "unstable" based on visible artifacts, requiring an inter-annotator agreement (Cohen's kappa) ≥ 0.8. (See US-3)
- **FR-008**: System design MUST enforce a total execution time limit of 6 hours for 500 clips; if a single clip's 100-step Euler rollout exceeds 15 minutes, the system MUST fallback to a 20-step surrogate rollout, flag the clip as "fallback," and exclude it from the primary statistical analysis to preserve metric integrity. (See US-1)

### Key Entities

- **VideoClip**: Represents a single input unit (16 frames), containing raw pixel data, computed statistical features, and the resulting divergence metric.
- **StatisticalFeature**: A vector of numerical properties (e.g., optical flow variance) derived from a VideoClip.
- **DivergenceMetric**: A scalar value representing the L2 distance between model prediction and ground truth rollout.
- **ThresholdModel**: A derived entity containing the optimal cutoff value and its associated sensitivity analysis results.
- **HumanLabel**: A label assigned by a human rater indicating "stable" or "unstable" status based on visual artifacts.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system successfully computes and reports a non-NaN Pearson correlation coefficient and a confidence interval for the relationship between optical flow magnitude variance and flow-map divergence. (See US-2)
- **SC-002**: The total execution time for processing a representative set of video clips is measured against the 6-hour GitHub Actions free-tier limit. (See FR-008)
- **SC-003**: The sensitivity analysis reports a variation in false-positive rate of less than 10% across the tested threshold range (±0.05), measured against the human-annotated ground truth defined in FR-007. (See US-3)
- **SC-004**: Peak memory usage during Euler rollout is measured against the RAM limit of the free-tier runner. (See FR-005)
- **SC-005**: The precision and recall of the "stable/unstable" classifier are measured against the human-annotated subset of 50 clips defined in FR-007. (See US-3)

## Assumptions

- **Assumption about data availability**: The public repositories (Kinetics-400 subset, UCF101) contain a sufficient number of clips (≥500) with a balanced distribution of continuous motion and hard cuts.
- **Assumption about model compatibility**: The frozen AnyFlow model can be successfully converted to ONNX format and run in CPU-only mode without requiring CUDA or specific GPU quantization libraries (e.g., bitsandbytes).
- **Assumption about ground truth**: The high-resolution Euler rollout (100 steps) is the primary metric definition; clips exceeding the 15-minute timeout (FR-008) are excluded from the primary analysis to maintain the strict 100-step standard.
- **Assumption about statistical validity**: The sample size of 500 clips (excluding fallbacks) provides sufficient statistical power to detect a moderate correlation (r ≈ 0.3) with 80% power at α=0.05.
- **Assumption about threshold justification**: The threshold for "stable" vs "unstable" will be derived from the data's F1-score maximization on the held-out set, and the sensitivity sweep will use a fixed range of ±0.05 as a community-standard baseline for this metric scale.