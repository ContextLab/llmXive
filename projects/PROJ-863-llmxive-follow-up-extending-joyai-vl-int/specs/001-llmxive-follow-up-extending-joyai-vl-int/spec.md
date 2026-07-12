# Feature Specification: llmXive Follow-up: Extending "JoyAI-VL-Interaction"

**Feature Branch**: `001-llmxive-vl-intuition`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'JoyAI-VL-Interaction: Real-Time Vision-Language Interaction Intelligen'"

## User Scenarios & Testing

### User Story 1 - Synthetic Data Generation and Ground-Truth Labeling (Priority: P1)

**Description**: As a researcher, I need to generate a synthetic dataset of video streams simulating security/elder care scenarios, where each frame is paired with a ground-truth "optimal intervention" label (critical vs. silence) derived strictly from the visual content (e.g., falls, alarms) as a proxy for high-load events, independent of any model output.

**Why this priority**: This is the foundational step. Without a valid, non-circular dataset where the ground truth is decoupled from the model's internal states or final outputs, no subsequent analysis regarding "latent intuition" can be scientifically valid. Note: The ground truth is a visual proxy for high-load events, not a direct measurement of cognitive load.

**Independent Test**: The data pipeline can be executed in isolation to produce a JSONL file containing video frames and labels. The test verifies that the labeling logic relies solely on the video content (e.g., object detection of a "fall") and not on the VLM's hidden states, and that an execution log confirms zero VLM API calls.

**Acceptance Scenarios**:
1. **Given** a raw video stream containing a simulated fall event, **When** the data synthesis script processes the frame, **Then** the generated label MUST be "critical" regardless of whether the VLM would have responded.
2. **Given** a raw video stream showing a calm conversation, **When** the script processes the frame, **Then** the generated label MUST be "silence".
3. **Given** the generated dataset and its execution log, **When** a validator checks the label source, **Then** the log MUST show zero calls to the VLM inference API or internal state access during label construction.

---

### User Story 2 - Feature Extraction from Internal States (Priority: P2)

**Description**: As a researcher, I need to extract feature vectors from the internal hidden states and attention maps of the JoyAI-VL-Interaction model for every time step in the synthetic dataset, ensuring that the final token logits and explicit response decisions are explicitly excluded.

**Why this priority**: This step isolates the specific signal ("latent intuition") hypothesized to predict cognitive load. It ensures the experiment tests the hypothesis about internal representations rather than the model's explicit reasoning.

**Independent Test**: The extraction module can be run on a subset of the dataset. The test verifies that the output feature matrix dimensions match the internal state dimensions and that the feature set contains no data from the final output layer.

**Acceptance Scenarios**:
1. **Given** a video frame and the loaded JoyAI-VL-Interaction model, **When** the feature extractor runs, **Then** the output MUST consist ONLY of hidden state embeddings and attention vectors.
2. **Given** the extracted features, **When** a schema validator checks the feature keys, **Then** keys corresponding to final token logits or generated text MUST be absent.
3. **Given** a sequence of frames, **When** features are extracted, **Then** the resulting feature sequence length MUST match the input video frame count (1:1 temporal alignment).

---

### User Story 3 - CPU-Optimized Scheduler Training and Evaluation (Priority: P3)

**Description**: As a researcher, I need to train a Transformer classifier with a moderate parameter count on a CPU-only environment using the extracted features to predict the "optimal intervention" labels (visual proxies), and evaluate its ability to reduce interruptions while maintaining safety recall.

**Why this priority**: This validates the core research question: whether the internal states contain sufficient signal to drive a lightweight, CPU-tractable scheduler. It directly addresses the "compute feasibility" and "methodological soundness" constraints.

**Independent Test**: The training and evaluation script can be run end-to-end on a hardware profile equivalent to an AWS c6i.large instance with enforced resource limits. The test verifies that the model converges and produces a confusion matrix against the held-out test set.

**Acceptance Scenarios**:
1. **Given** the training features and labels, **When** the 15M-parameter model trains on a runner with cgroup constraints limiting RAM to ≤ 7GB and CPU to 2 vCPUs (AWS c6i.large equivalent), **Then** the process MUST complete within 6 hours without exceeding these limits.
2. **Given** the trained model and a held-out test set, **When** predictions are made, **Then** the model MUST output a "trigger" or "suppress" decision for each frame.
3. **Given** the predictions and ground truth, **When** metrics are calculated, **Then** the system MUST report the "Interruption Reduction Rate" and "Safety Recall" separately.

---

### Edge Cases

- **What happens when** the synthetic video contains ambiguous events (e.g., a person sitting down vs. falling)?
  - *Resolution*: The labeling logic MUST apply a deterministic rule (e.g., "if bounding box velocity < threshold, label as silence") to ensure consistent ground truth, and the ambiguity rate must be logged.
- **How does the system handle** if the VLM's internal state dimension changes between model versions?
  - *Resolution*: The feature extraction script MUST validate input dimensions against a hardcoded schema and fail gracefully with a clear error if a mismatch occurs, rather than silently dropping data.
- **What happens when** the CPU memory limit is approached during feature extraction for long video segments?
  - *Resolution*: The system MUST implement a streaming/batching mechanism that processes video in fixed-size chunks (e.g., 100 frames) to ensure RAM usage remains < 6GB.

## Requirements

### Functional Requirements

- **FR-001**: The data synthesis module MUST generate a dataset of at least 50 hours of simulated video content with ground-truth labels derived exclusively from visual events (e.g., falls, alarms) as a proxy for high-load events, independent of model outputs (See US-1).
- **FR-001.1**: The data synthesis module MUST emit a structured execution log that records every data source accessed; this log MUST be verifiable to contain zero entries for VLM inference API calls during label generation (See US-1).
- **FR-002**: The feature extraction module MUST capture hidden state embeddings and attention maps from the VLM at every time step while explicitly excluding final token logits and generated text (See US-2).
- **FR-003**: The training pipeline MUST utilize a Transformer classifier with a moderate parameter count optimized for CPU execution, ensuring no CUDA or GPU-specific operations are invoked (See US-3).
- **FR-004**: The evaluation module MUST calculate and report two distinct metrics: "Interruption Reduction Rate" (percentage of non-critical events suppressed) and "Safety Recall" (percentage of critical events correctly triggered) (See US-3).
- **FR-005**: The system MUST perform a Mutual Information calculation and partial correlation analysis between the internal state features and the final output logits, conditioned on the ground truth, to verify that the internal states provide a unique predictive signal distinct from the visual proxy (See US-3).

### Key Entities

- **SyntheticVideoFrame**: Represents a single frame of the generated video stream, containing visual data and a ground-truth intervention label.
- **InternalStateVector**: Represents the extracted hidden state and attention map data from the VLM for a specific frame, used as input features.
- **SchedulerDecision**: The binary output (trigger/suppress) generated by the lightweight classifier for a specific time step.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between the scheduler's predictions and the video-derived ground truth is measured against a random baseline using Spearman rank correlation; the p-value MUST be < 0.05 to establish statistical significance (See FR-001, FR-005).
- **SC-002**: The "Interruption Reduction Rate" is measured against the baseline of the VLM's default behavior (assuming it triggers on all events) to quantify efficiency gains (See FR-004).
- **SC-003**: The "Safety Recall" is measured against a minimum threshold of ≥ 99.5% to ensure no safety degradation (See FR-004).
- **SC-004**: The peak RAM utilization and inference latency of the scheduler are measured against the edge environment constraints (≤ 7GB RAM, ≤ 2 CPU cores) to confirm feasibility (See FR-003).
- **SC-005**: The independence of the internal state signal is measured by comparing the scheduler's performance to a deterministic rule-based visual detector; the scheduler's F1-score MUST be within 5% of the rule-based detector to confirm the internal states contain sufficient signal beyond simple visual heuristics (See FR-005).

## Assumptions

- The synthetic video generation tool can produce realistic visual events (falls, conversations) with sufficient temporal resolution to simulate large-scale data volumes within the 6-hour CI time limit.
- The JoyAI-VL-Interaction model is available in a version compatible with CPU-only inference and its internal state dimensions are stable for feature extraction.
- A sufficiently large Transformer architecture is sufficient to learn the mapping from internal states to intervention labels without requiring deeper or larger models that exceed CPU memory limits.
- The ground-truth labeling logic based on visual events (e.g., object detection) accurately reflects "optimal intervention" timing for the purpose of this study, acknowledging that visual events are proxies for high-load events rather than direct cognitive load measurements.
- The dataset size provides sufficient samples to train the 15M-parameter model without overfitting, given the simplicity of the binary classification task.