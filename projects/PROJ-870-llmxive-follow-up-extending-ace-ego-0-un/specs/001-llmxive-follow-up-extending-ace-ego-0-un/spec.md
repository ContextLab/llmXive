# Feature Specification: llmXive follow-up: extending "ACE-Ego-0: Unifying Egocentric Human and Robotic Data for VLA Pretrain"

**Feature Branch**: `001-llmxive-static-proxy`  
**Created**: 2026-09-07  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'ACE-Ego-0: Unifying Egocentric Human and Robotic Data for VLA Pretrain'"

## User Scenarios & Testing

### User Story 1 - Static Feature Extraction and Baseline Variance Quantification (Priority: P1)

**User Story ID**: US-1

As a researcher, I want to extract static visual features (entropy, hand visibility, lighting) from egocentric video segments and train a lightweight CPU-only regression model to predict pseudo-action reliability scores, so that I can determine the upper bound of variance explainable by static cues alone without requiring GPU resources.

**Why this priority**: This is the core hypothesis test. If static features cannot explain a significant portion of variance, the entire premise of a CPU-only filter fails. This step provides the baseline against which all dynamic context improvements are measured.

**Independent Test**: Can be fully tested by running the feature extraction pipeline on a subset of the ACE-Ego-0 dataset and reporting the $R^2$ score of the static-only model against the ground-truth (dynamic) reliability labels.

**Acceptance Scenarios**:

1. **Given** a dataset of 100 egocentric video segments with ground-truth (dynamic) reliability scores, **When** the system extracts static features and trains a Random Forest regressor, **Then** the model outputs a predicted reliability score for each segment and calculates an $R^2$ variance explained metric.
2. **Given** the trained static model, **When** it is applied to a held-out test set, **Then** the system reports the percentage of variance in reliability scores explained by static features alone.

---

### User Story 2 - Temporal Context Diminishing Returns Analysis (Priority: P2)

**User Story ID**: US-2

As a researcher, I want to systematically augment the static feature set with temporal windows of increasing length (short, medium, longer, longest) and measure the marginal reduction in residual error, so that I can identify the specific window length where adding more frames yields diminishing returns on predictive accuracy.

**Why this priority**: This determines the optimal trade-off point for the "static proxy" strategy. It answers the specific research question regarding the temporal window length required for significant marginal information.

**Independent Test**: Can be fully tested by running the temporal sweep analysis and generating a plot of residual error reduction versus window length, identifying the "elbow" point.

**Acceptance Scenarios**:

1. **Given** the static model residuals, **When** the system augments features with 1-second temporal windows and retrains the model, **Then** the system records the new residual error.
2. **Given** the series of models trained with 1s, 3s, 5s, and 10s windows, **When** the system compares their residual errors, **Then** it identifies the window length where the marginal gain in $R^2$ drops below a defined threshold of 0.01 (1 % improvement per added second).

---

### User Story 3 - Downstream VLA Model Performance Validation (Priority: P3)

**User Story ID**: US-3

As a researcher, I want to train three distinct VLA models (Dynamic Baseline, Uniform Weighting, Static-Proxy Filtered) and evaluate them on RoboCasa and RoboTwin benchmarks, so that I can confirm whether the static-filtered dataset yields models within a 2-3% performance margin of the full dynamic baseline.

**Why this priority**: This validates the practical utility of the findings. It confirms that the computational savings from using the static proxy do not come at an unacceptable cost to downstream task performance.

**Independent Test**: Can be fully tested by training the three VLA variants (using a small OpenVLA variant compatible with CPU-only training) and comparing their success rates on the specified benchmarks.

**Acceptance Scenarios**:

1. **Given** the static-filtered dataset subset, **When** a small OpenVLA model is trained on it, **Then** the system evaluates the model on the RoboCasa benchmark **and** the RoboTwin benchmark and reports the success rates for each.
2. **Given** the success rates of the Dynamic Baseline, Uniform Weighting, and Static-Proxy models across multiple shared evaluation episodes, **When** a paired t‑test is performed over multiple random training seeds, **Then** the system determines if the performance difference is statistically significant (p < 0.05) and quantifies the percentage drop.

---

### Edge Cases

- What happens when the static feature extraction fails for a specific frame (e.g., extreme darkness causing zero hand visibility confidence)? The system must first attempt imputation with the dataset mean; if imputation is not possible (e.g., NaN propagation), the segment is excluded and the exclusion count is logged.
- How does the system handle the scenario where the static model predicts high reliability but the ground‑truth dynamic reliability is low (false positive)? The system must flag these segments in the residual analysis to identify specific visual conditions where static cues are misleading.
- What happens if the temporal window sweep requires more memory than available on the CI runner? The system must automatically downsample the frame rate or reduce the dataset size to fit within the available memory constraints.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract static visual features (image entropy, YOLOv8 hand detection confidence, lighting metrics, **camera metadata (timestamp, exposure, focal length)**) from every frame in the input egocentric video segments using CPU‑only libraries. (See US-1)
- **FR-002**: System MUST train a lightweight regression model (Random Forest or shallow MLP) using only the extracted static features to predict the **ground‑truth (dynamic) reliability scores**. (See US-1)
- **FR-003**: System MUST calculate the residual error between the static model predictions and the **ground‑truth (dynamic) reliability scores** to identify the unexplained variance. (See US-1)
- **FR-004**: System MUST iteratively augment the feature set with temporal windows of 1s, 3s, 5s, and 10s using lightweight optical flow or frame‑difference features to measure marginal information gain. (See US-2)
- **FR-005**: System MUST train three distinct VLA models (Dynamic Baseline, Uniform Weighting, Static-Proxy Filtered) using a small OpenVLA variant and evaluate them on RoboCasa and RoboTwin benchmarks. (See US-3)
- **FR-006**: System MUST perform a paired t‑test on the benchmark success rates to determine statistical significance (p < 0.05) between the Dynamic Baseline and Static‑Proxy models, using per‑episode binary outcomes across 100 shared episodes and 5 random training seeds. (See US-3)
- **FR-007**: System MUST implement a hard threshold to create a “high‑reliability” subset, excluding segments that either (a) have a predicted reliability score below **0.4** *or* (b) exhibit model‑derived uncertainty (standard deviation across Random Forest trees or MC‑dropout variance for MLP) with a normalized std > 0.2. (See US-3)
- **FR-008**: System MUST verify that static visual features are not highly correlated with the dynamic reliability labels by computing Pearson correlation for each feature; any feature with |r| ≥ 0.2 triggers a warning and is excluded from the explanatory analysis. (See US-1)
- **FR-009**: System MUST process data in streaming batches of ≤ 500 video segments; if RAM usage approaches 5 GB, the pipeline automatically down‑samples the frame rate to ≤ 0.5 fps to keep total memory ≤ 6 GB and wall‑clock time ≤ 8 h for processing 10 h of video on the free‑tier GitHub Actions runner (2 CPU cores, ~7 GB RAM). (See US-1)
- **FR-010**: System MUST provide schema files `contracts/RegressionPrediction.schema.yaml`, `contracts/TemporalWindowFeatures.schema.yaml`, `contracts/StaticResidual.schema.yaml`, and `contracts/VLAExperimentResult.schema.yaml` that define the structure of `data/static_predictions.csv`, `data/temporal_features_{w}s.csv`, and `results/vla_*.csv` respectively. (See US-3)
- **FR-011**: System MUST ensure that the dataset download script `code/download_datasets.py` exits with status 0 and logs any errors; the script will be re‑executed until successful before any downstream processing. (General robustness)
- **FR-012**: System MUST assess the overall independence between static visual features and the dynamic reliability labels by computing the Pearson correlation between each static feature and the label; if any feature shows |r| ≥ 0.2, a detailed analysis must be performed and the static‑only explanatory analysis (FR‑002) must be qualified accordingly. (See US-1)
- **FR-013**: System MUST provide the missing contract schema file `contracts/static_features.schema.yaml` in addition to the four schemas listed in FR‑010, ensuring full plan‑to‑contract coverage. (Plan‑contract consistency)

### Key Entities

- **VideoSegment**: A discrete unit of egocentric video with associated ground‑truth (dynamic) reliability score and extracted static features.
- **StaticFeatureVector**: A numerical representation of a frame's visual properties (entropy, hand confidence, lighting, camera metadata) used as input for the regression model.
- **TemporalWindow**: A sequence of frames (1s, 3s, 5s, 10s) augmented with dynamic features (optical flow) to augment the static baseline.
- **VLAModel**: A trained Vision‑Language‑Action model variant evaluated on downstream benchmarks.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage of variance in pseudo‑action reliability scores explained by static features alone is measured against the total variance of the ground‑truth (dynamic) reliability scores, using k‑fold cross‑validation and bootstrap 95 % confidence intervals. (See US-1)
- **SC-002**: The marginal reduction in residual error for each temporal window length (1s, 3s, 5s, 10s) is measured against the static‑only residual error; a window is deemed diminishing‑return if the increase in cross‑validated $R^2$ is < 0.01 per added second. (See US-2)
- **SC-003**: The success rate of the Static‑Proxy Filtered VLA model on RoboCasa and RoboTwin benchmarks is measured against the Dynamic Baseline model's success rate to quantify the performance gap, with **at least 100 shared evaluation episodes per benchmark**. (See US-3)
- **SC-004**: The statistical significance (p‑value) of the performance difference between the Static‑Proxy and Dynamic Baseline models is measured against the threshold of p < 0.05, using paired t‑test across 5 random seeds. (See US-3)
- **SC-005**: The computational cost (CPU time and memory usage) of the static feature extraction and filtering pipeline must not exceed **5 minutes CPU time per hour of video** and **6 GB RAM** on the CI runner, and is measured against the published ACE‑Ego‑0 dynamic pipeline cost of **≤ 5 minutes CPU time per hour of video**. (See US-1)
- **SC-006**: Independence assessment outcome: The maximum absolute Pearson correlation between any static feature and the dynamic reliability label must be **< 0.2**, confirming label independence before reporting $R^2$ (See US-1).

## Assumptions

- The public repository linked to the original ACE‑Ego preprint contains the egocentric video segments with associated pseudo‑action labels and ground‑truth (dynamic) reliability scores required for this analysis.
- **Independence justification**: The ACE‑Ego‑0 reliability scores are derived from a dynamic heuristic pipeline that **exclusively uses temporal motion cues** (optical flow, temporal consistency) and **does not incorporate any of the static visual cues** (entropy, hand confidence, lighting, camera metadata) listed in FR‑001. This orthogonality is documented in Section 3.2 of the ACE‑Ego‑0 paper (). Consequently, the dynamic labels can be treated as independent of the static feature set for the purpose of explanatory variance analysis.
- The independence of static features from dynamic reliability labels will be verified as per FR‑008 before explanatory analysis.
- The "small OpenVLA variant" specified for downstream training is computationally tractable on a CPU‑only GitHub Actions runner (2 cores, ~7 GB RAM) within the short‑duration job limit, provided that at least **5 000 video segments** (≈10 h video) are used for training and **≥1 000 episodes** per benchmark are evaluated.
- The YOLOv8 model used for hand visibility detection can run in CPU mode with acceptable latency for processing a large corpus of video (on the order of thousands of hours).
- The RoboCasa and RoboTwin benchmarks can be evaluated in a CPU‑only environment without requiring GPU acceleration for the inference phase.
- The dataset contains no significant missing data for the required static features; if missing, the system will **impute with the dataset mean** as the primary strategy and **exclude the segment** only if imputation fails, logging the exclusion count.
- The pipeline will operate in streaming batches as described in FR‑009 to respect memory and wall‑clock constraints on the free‑tier CI runner.
