# Feature Specification: llmXive follow-up: extending "ACE-Ego-0: Unifying Egocentric Human and Robotic Data for VLA Pretrain"

**Feature Branch**: `001-llmxive-static-proxy`  
**Created**: 2026-09-07  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'ACE-Ego-0: Unifying Egocentric Human and Robotic Data for VLA Pretrain'"

## User Scenarios & Testing

### User Story 1 - Static Feature Extraction and Baseline Variance Quantification (Priority: P1)

As a researcher, I want to extract static visual features (entropy, hand visibility, lighting) from egocentric video segments and train a lightweight CPU-only regression model to predict pseudo-action reliability scores, so that I can determine the upper bound of variance explainable by static cues alone without requiring GPU resources.

**Why this priority**: This is the core hypothesis test. If static features cannot explain a significant portion of variance, the entire premise of a CPU-only filter fails. This step provides the baseline against which all dynamic context improvements are measured.

**Independent Test**: Can be fully tested by running the feature extraction pipeline on a subset of the ACE-Ego-0 dataset and reporting the $R^2$ score of the static-only model against the ground-truth reliability labels.

**Acceptance Scenarios**:

1. **Given** a dataset of 100 egocentric video segments with ground-truth reliability scores, **When** the system extracts static features and trains a Random Forest regressor, **Then** the model outputs a predicted reliability score for each segment and calculates an $R^2$ variance explained metric.
2. **Given** the trained static model, **When** it is applied to a held-out test set, **Then** the system reports the percentage of variance in reliability scores explained by static features alone.

---

### User Story 2 - Temporal Context Diminishing Returns Analysis (Priority: P2)

As a researcher, I want to systematically augment the static feature set with temporal windows of increasing length (1s, 3s, 5s, 10s) and measure the marginal reduction in residual error, so that I can identify the specific window length where adding more frames yields diminishing returns on predictive accuracy.

**Why this priority**: This determines the optimal trade-off point for the "static proxy" strategy. It answers the specific research question regarding the temporal window length required for significant marginal information.

**Independent Test**: Can be fully tested by running the temporal sweep analysis and generating a plot of residual error reduction versus window length, identifying the "elbow" point.

**Acceptance Scenarios**:

1. **Given** the static model residuals, **When** the system augments features with 1-second temporal windows and retrains the model, **Then** the system records the new residual error.
2. **Given** the series of models trained with 1s, 3s, 5s, and 10s windows, **When** the system compares their residual errors, **Then** it identifies the window length where the marginal gain in $R^2$ drops below a defined threshold (e.g., <1% improvement per added second).

---

### User Story 3 - Downstream VLA Model Performance Validation (Priority: P3)

As a researcher, I want to train three distinct VLA models (Dynamic Baseline, Uniform Weighting, Static-Proxy Filtered) and evaluate them on RoboCasa and RoboTwin benchmarks, so that I can confirm whether the static-filtered dataset yields models within a 2-3% performance margin of the full dynamic baseline.

**Why this priority**: This validates the practical utility of the findings. It confirms that the computational savings from using the static proxy do not come at an unacceptable cost to downstream task performance.

**Independent Test**: Can be fully tested by training the three VLA variants (using a small OpenVLA variant compatible with CPU-only training) and comparing their success rates on the specified benchmarks.

**Acceptance Scenarios**:

1. **Given** the static-filtered dataset subset, **When** a small OpenVLA model is trained on it, **Then** the system evaluates the model on the RoboCasa benchmark and reports the success rate.
2. **Given** the success rates of the Dynamic Baseline and Static-Proxy models, **When** a paired t-test is performed, **Then** the system determines if the performance difference is statistically significant (p < 0.05) and quantifies the percentage drop.

---

### Edge Cases

- What happens when the static feature extraction fails for a specific frame (e.g., extreme darkness causing zero hand visibility confidence)? The system must handle missing feature vectors by imputing with dataset mean or excluding the segment, logging the exclusion count.
- How does the system handle the scenario where the static model predicts high reliability but the ground-truth dynamic reliability is low (false positive)? The system must flag these segments in the residual analysis to identify specific visual conditions where static cues are misleading.
- What happens if the temporal window sweep requires more memory than available on the CI runner? The system must automatically downsample the frame rate or reduce the dataset size to fit within the available memory constraints.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract static visual features (image entropy, YOLOv8 hand detection confidence, lighting metrics) from every frame in the input egocentric video segments using CPU-only libraries. (See US-1)
- **FR-002**: System MUST train a lightweight regression model (Random Forest or shallow MLP) using only the extracted static features to predict the ACE-Ego-0 ground-truth reliability scores. (See US-1)
- **FR-003**: System MUST calculate the residual error between the static model predictions and the actual dynamic reliability scores to identify the unexplained variance. (See US-1)
- **FR-004**: System MUST iteratively augment the feature set with temporal windows of 1s, 3s, 5s, and 10s using lightweight optical flow or frame-difference features to measure marginal information gain. (See US-2)
- **FR-005**: System MUST train three distinct VLA models (Dynamic Baseline, Uniform Weighting, Static-Proxy Filtered) using a small OpenVLA variant and evaluate them on RoboCasa and RoboTwin benchmarks. (See US-3)
- **FR-006**: System MUST perform a paired t-test on the benchmark success rates to determine statistical significance (p < 0.05) between the Dynamic Baseline and Static-Proxy models. (See US-3)
- **FR-007**: System MUST implement a hard threshold based on the static model's confidence to create a "high-reliability" subset, excluding segments with low predicted fidelity. (See US-3)

### Key Entities

- **VideoSegment**: A discrete unit of egocentric video with associated ground-truth reliability score and extracted static features.
- **StaticFeatureVector**: A numerical representation of a frame's visual properties (entropy, hand confidence, etc.) used as input for the regression model.
- **TemporalWindow**: A sequence of frames (1s, 3s, 5s, 10s) augmented with dynamic features (optical flow) to augment the static baseline.
- **VLAModel**: A trained Vision-Language-Action model variant evaluated on downstream benchmarks.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage of variance in pseudo-action reliability scores explained by static features alone is measured against the total variance of the ground-truth reliability scores. (See US-1)
- **SC-002**: The marginal reduction in residual error for each temporal window length (1s, 3s, 5s, 10s) is measured against the static-only residual error to identify the diminishing returns point. (See US-2)
- **SC-003**: The success rate of the Static-Proxy Filtered VLA model on RoboCasa and RoboTwin benchmarks is measured against the Dynamic Baseline model's success rate to quantify the performance gap. (See US-3)
- **SC-004**: The statistical significance (p-value) of the performance difference between the Static-Proxy and Dynamic Baseline models is measured against the threshold of p < 0.05. (See US-3)
- **SC-005**: The computational cost (CPU time and memory usage) of the static feature extraction and filtering pipeline is measured against the baseline GPU-bound dynamic heuristic to quantify efficiency gains. (See US-1)

## Assumptions

- The public repository linked to the original ACE-Ego preprint contains the egocentric video segments with associated pseudo-action labels and ground-truth reliability scores required for this analysis.
- The ACE-Ego-0 reliability scores are derived from a pipeline that incorporates temporal dynamics, making them a valid target for measuring the information content of static vs. dynamic features.
- The "small OpenVLA variant" specified for downstream training is computationally tractable on a CPU-only GitHub Actions runner (2 cores, ~7 GB RAM) within the 6-hour job limit.
- The YOLOv8 model used for hand visibility detection can run in CPU mode with acceptable latency for processing 1.48K hours of video.
- The RoboCasa and RoboTwin benchmarks can be evaluated in a CPU-only environment without requiring GPU acceleration for the inference phase.
- The static features (entropy, hand visibility, lighting) are sufficient proxies for the visual complexity of the scene and do not require additional, unlisted variables.
- The dataset contains no significant missing data for the required static features; if missing, the system will impute with the dataset mean.
