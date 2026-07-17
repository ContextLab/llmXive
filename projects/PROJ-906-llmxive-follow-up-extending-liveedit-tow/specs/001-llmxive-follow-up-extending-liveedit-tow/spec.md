# Feature Specification: llmXive follow-up: extending "LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing"

**Feature Branch**: `001-optical-flow-temporal-coherence`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing'"

## User Scenarios & Testing

### User Story 1 - Baseline Replication and Metric Collection (Priority: P1)

**User Journey**: As a researcher, I need to execute the CPU-optimized LiveEdit baseline model on a stratified dataset of video clips to establish ground-truth metrics for memory usage, latency, and temporal consistency (SSIM) before introducing any modifications.

**Why this priority**: This is the foundational step. Without a validated baseline, any comparison of the proposed flow-based method lacks scientific validity. It ensures the experimental environment is correctly configured and the data pipeline functions within the 6-hour CI limit.

**Independent Test**: This can be tested by running the baseline pipeline on a subset of clips. Success is defined by the generation of a metrics report containing peak memory, average FPS, and SSIM scores for the background regions, without manual intervention.

**Acceptance Scenarios**:
1. **Given** the baseline LiveEdit configuration and the DAVIS/YouTube-VOS dataset subset, **When** the inference job completes on the CPU runner, **Then** the system outputs a JSON report containing peak memory usage, inference time per frame, and background SSIM scores for all processed clips.
2. **Given** a video clip with fast non-rigid motion, **When** processed by the baseline, **Then** the system records the specific optical flow magnitude and divergence for that clip to enable later correlation analysis.

---

### User Story 2 - Flow-Coherence Module Implementation and Execution (Priority: P2)

**User Journey**: As a researcher, I need to replace the region-tracking logic of the Mask Cache with a "Flow-Coherence" module that warps latent features using pre-computed optical flow (derived from the source video), then execute this modified model on the full dataset to measure memory reduction and artifact generation.

**Why this priority**: This implements the core hypothesis (that flow-based warping using source priors is a viable memory-efficient alternative). It directly addresses the research question regarding the limitations of optical flow priors in editing contexts where the flow does not match the edited content.

**Independent Test**: This can be tested by running the modified pipeline on the same dataset subset used in Story 1. Success is defined by the generation of a comparative metrics report showing a reduction in memory usage and the corresponding SSIM scores, including handling of invalid flow vectors via identity warp.

**Acceptance Scenarios**:
1. **Given** the pre-computed dense optical flow fields (from source video) and the modified model configuration (Flow-Coherence module), **When** inference is executed on a video clip, **Then** the system generates the edited video without utilizing the attention-based temporal layers or the original Mask Cache.
2. **Given** a video clip with high optical flow magnitude or invalid flow vectors, **When** processed by the Flow-Coherence module, **Then** the system records the specific frame-wise SSIM degradation and flickering metrics (temporal gradient variance) in the output report, applying identity warp for invalid vectors and flagging the frame.

---

### User Story 3 - Statistical Boundary Analysis and Threshold Identification (Priority: P3)

**User Journey**: As a researcher, I need to perform statistical analysis (Kolmogorov-Smirnov test and regression) on the collected metrics to identify the specific optical flow magnitude threshold where artifact generation becomes statistically significant and to quantify the memory/quality trade-off.

**Why this priority**: This transforms raw data into scientific insight, directly answering the research question about "under what specific motion characteristics" flow-based warping fails, using appropriate statistical methods for comparing distinct distributions.

**Independent Test**: This can be tested by running a post-processing script on the metric reports from Story 1 and Story 2. Success is defined by the generation of a statistical summary identifying the correlation between flow magnitude and SSIM drop, and the significance of the memory reduction using distribution-based tests.

**Acceptance Scenarios**:
1. **Given** the paired datasets of baseline and flow-based metrics, **When** the statistical analysis script runs, **Then** the system outputs a p-value from a Kolmogorov-Smirnov test for the difference in error distributions and identifies a specific flow-magnitude threshold where the SSIM degradation exceeds a defined significance level.
2. **Given** the identified threshold, **When** the sensitivity analysis is performed, **Then** the system reports how the false-positive artifact rate varies across a swept range of flow magnitude cutoffs {0.01, 0.05, 0.1}.

---

### Edge Cases

- **Invalid Flow Vectors**: If the optical flow estimation fails (e.g., extreme motion blur or occlusion) causing invalid warp vectors, the system MUST fall back to an identity warp for that frame and MUST flag the frame with an `invalid_flow` marker in the output report. This ensures the frame remains in the dataset for SSIM calculation (satisfying US-2) while preventing undefined behavior.
- **RAM Limit Exceeded**: How does the system handle video clips exceeding the GB RAM limit during preprocessing? The system must detect the clip size and automatically downsample or split the clip into smaller segments before processing, logging the action.
- **CI Time Limit**: What happens if the 6-hour CI time limit is approached? The system must implement a checkpointing mechanism to pause execution and resume, or gracefully terminate with a partial results report indicating the dataset coverage achieved.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and preprocess a diverse set of short video clips from DAVIS and YouTube-VOS, stratifying by motion complexity (static, slow rigid, fast non-rigid), and generate synthetic editing masks for each clip. (See US-1)
- **FR-002**: The system MUST compute dense optical flow fields for all video clips using a lightweight, CPU-optimized algorithm (e.g., RAFT-small or Farneback) to serve as the temporal coherence prior. (See US-2)
- **FR-003**: The system MUST implement a "Flow-Coherence" module that replaces the region-tracking logic of the Mask Cache, warping latent features from the previous frame using the pre-computed flow fields while removing all attention-based temporal layers. **If the flow field contains invalid vectors (e.g., NaN or infinity), the system MUST fall back to an identity warp for that frame and MUST flag the frame with an `invalid_flow` marker in the output report.** (See US-2)
- **FR-004**: The system MUST execute both the baseline LiveEdit model and the modified Flow-Coherence model on the CPU-only runner for a representative set of clips, recording inference time per frame, peak memory consumption, and total throughput (FPS). (See US-1, US-2)
- **FR-005**: The system MUST calculate the Structural Similarity Index Measure (SSIM) and temporal gradient variance between **consecutive frames ($t$ and $t-1$) within the edited output video** to quantify background stability and flickering, rather than comparing to the original ground-truth video. (See US-1, US-2)
- **FR-006**: The system MUST perform a **Kolmogorov-Smirnov (K-S) test** on the distributions of error magnitudes (SSIM/gradient variance) between the baseline and the proposed method, and conduct a regression analysis to determine the flow-magnitude threshold where artifact generation becomes statistically significant. (See US-3)
- **FR-007**: The system MUST perform a sensitivity analysis sweeping the decision cutoff for flow magnitude over a quantitative range defined as the set **{0.01, 0.05, 0.1}** and report how the inconsistency rate varies across these specific values. (See US-3)

### Key Entities

- **VideoClip**: Represents a single input video unit, containing attributes for source path, motion complexity category, pre-computed optical flow field, and associated synthetic mask.
- **MetricRecord**: Represents a single inference result, containing attributes for clip ID, model variant (baseline/flow), peak memory usage, FPS, SSIM score, temporal gradient variance, flow magnitude statistics, and an `invalid_flow` boolean flag.
- **AnalysisResult**: Represents the aggregated statistical output, containing attributes for p-values (K-S test), regression coefficients, identified flow-magnitude thresholds, and sensitivity analysis tables.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Memory usage reduction is measured against the baseline LiveEdit configuration's peak memory consumption, quantifying the trade-off curve between memory savings and quality degradation to identify the point of diminishing returns. (See FR-004)
- **SC-002**: Background stability (temporal consistency) is measured by the variance in SSIM and gradient variance between **consecutive frames ($t$ and $t-1$) in the edited output**, quantifying the trade-off and identifying the non-linear degradation point relative to optical flow magnitude. (See FR-005, FR-006)
- **SC-003**: Statistical significance of the difference in performance is measured against the null hypothesis using a **Kolmogorov-Smirnov (K-S) test** to compare error distributions, with a significance level of α=0.05 to confirm the validity of the observed trade-offs. (See FR-006)
- **SC-004**: Threshold robustness is measured by the variance in artifact rates across the swept cutoff values **{0.01, 0.05, 0.1}**, ensuring the identified boundary is not an artifact of a single arbitrary cutoff choice. (See FR-007)
- **SC-005**: Computational feasibility is measured against the 6-hour GHA execution limit, ensuring the total pipeline (data prep, inference, analysis) completes within the time budget without GPU acceleration. (See FR-001, FR-004)

## Assumptions

- **Assumption about data availability**: The DAVIS and YouTube-VOS datasets are publicly accessible and contain sufficient video clips with the required motion complexity (static, slow rigid, fast non-rigid) to populate a comprehensive test dataset.
- **Assumption about computational resources**: The GitHub Actions free-tier runner (multiple CPU cores, standard RAM allocation) is sufficient to run the lightweight optical flow algorithms (RAFT-small/Farneback) and the CPU-optimized diffusion model inference without exceeding memory limits, provided the dataset is processed in batches.
- **Assumption about model compatibility**: The LiveEdit model architecture can be modified to replace the Mask Cache with a flow-warping module without requiring a complete retraining of the diffusion model weights, relying instead on the existing pre-trained weights.
- **Assumption about measurement validity**: The Structural Similarity Index Measure (SSIM) and temporal gradient variance, calculated between consecutive frames in the edited output, are valid and accepted proxies for human-perceived background flickering and temporal consistency in this specific video editing context.
- **Assumption about flow estimation**: The selected lightweight optical flow algorithm (RAFT-small or Farneback) provides sufficiently accurate flow fields for the purpose of latent warping, despite potential errors in extreme motion blur scenarios which are treated as edge cases handled by identity warp.
- **Assumption about flow prior validity**: The flow field computed from the **source video** serves as a valid prior for latent warping in the edited video, acknowledging that discrepancies arising from the editing mask are the specific phenomenon under investigation (the "flow prior mismatch" hypothesis).
- **Assumption about statistical power**: The sample size of 500 clips is sufficient to achieve statistical power (>0.8) for detecting the expected effect size in the Kolmogorov-Smirnov tests, given the anticipated variance in the SSIM metrics.