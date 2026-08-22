# Feature Specification: llmXive follow-up: extending "AlayaWorld: Long-Horizon and Playable Video World Generation"

**Feature Branch**: `001-llmxive-alayaworld-extend`  
**Created**: 2026-07-18  
**Status**: Draft  
**Input**: User description: "How does the integration of a lightweight, CPU-tractable symbolic logic layer influence the long-horizon semantic consistency of interactive video world models compared to autoregressive generation alone?"

## User Scenarios & Testing

### User Story 1 - Baseline Semantic Drift Quantification (Priority: P1)

**Description**: The system must generate 60-second interactive video sequences using the frozen AlayaWorld model under fixed user action inputs and calculate a "Semantic Drift Score" by comparing the generated video's object states against a ground-truth symbolic simulation of those same actions.

**Why this priority**: This establishes the baseline performance of the vanilla model. Without quantifying the extent of semantic drift in the absence of the proposed intervention, the efficacy of the hybrid approach cannot be measured. This is the foundational control experiment.

**Independent Test**: Can be fully tested by running the AlayaWorld inference pipeline on a subset of the dataset, running the symbolic engine, and comparing the two outputs to produce a single scalar drift score.

**Acceptance Scenarios**:

1. **Given** a pre-trained AlayaWorld model and a set of 10 user action sequences, **When** the system generates 60-second videos and runs the symbolic engine on the same inputs, **Then** the system outputs a valid Semantic Drift Score for each sequence (e.g., a float between 0 and 1) representing the deviation between visual and logical states.
2. **Given** a sequence where the symbolic engine predicts an object should be "dead" (HP=0), **When** the visual consistency checker analyzes the generated video frame at the corresponding timestamp, **Then** the system flags a "permanence violation" if the object is still visually present and moving, contributing to the drift score.

---

### User Story 2 - Hybrid Correction Mechanism Implementation (Priority: P2)

**Description**: The system must implement a lightweight, rule-based symbolic engine that tracks object states (HP, inventory) and injects "correction tokens" (via dynamic prompt re-conditioning) into the AlayaWorld inference loop when a discrepancy between the symbolic state and the visual generation is detected.

**Why this priority**: This is the core innovation. It tests the hypothesis that offloading logic to a symbolic layer can mitigate drift. It is dependent on the baseline (US-1) being functional but is the primary value-add of the research.

**Independent Test**: Can be tested by enabling the correction loop on a new set of action sequences, generating videos, and verifying that the symbolic engine's state log matches the visual output more closely than the baseline did.

**Acceptance Scenarios**:

1. **Given** the hybrid system is active and the symbolic engine detects that an object's logical HP is 0 while the video generator is producing frames where the object is alive, **When** the correction token (prompt update) is injected, **Then** the subsequent frames in the video sequence must reflect the object as "dead" or removed, reducing the visual-logical discrepancy.
2. **Given** a sequence of 20 distinct user actions, **When** the hybrid system runs, **Then** the total number of "state inconsistency" events (visual state != logical state) must be statistically significantly lower than the count observed in the baseline run (US-1) for the same action sequence, with p < 0.05 at a 95% confidence level across the 10 random seeds.

---

### User Story 3 - Resource Constraint Verification (Priority: P3)

**Description**: The system must execute the entire hybrid inference pipeline (generation + symbolic tracking + consistency checking) on a CPU-only environment, ensuring total wall-clock time per sequence remains within a practical operational timeframe and memory usage stays within acceptable operational limits.

**Why this priority**: The research question explicitly targets "CPU-tractable" and "resource-constrained edge devices." If the method requires GPU acceleration or excessive memory, the proposed solution fails its primary deployment constraint, rendering the semantic improvement moot for the target use case.

**Independent Test**: Can be tested by running the full pipeline on a standard 2-core, 7GB RAM runner and logging resource usage metrics.

**Acceptance Scenarios**:

1. **Given** a standard GitHub Actions free-tier runner (2 CPU cores, 7 GB RAM), **When** the system processes a single 60-second video sequence with the hybrid correction enabled, **Then** the total wall-clock execution time must be ≤ 30 minutes.
2. **Given** the same runner environment, **When** the system processes the sequence, **Then** the peak memory usage reported by the OS must not exceed 7 GB at any point during execution.

---

### Edge Cases

- **What happens when the symbolic engine detects a state that the visual model cannot physically render?** (e.g., an object is logically "teleported" but the video model expects a continuous trajectory). The system must log this as a "rendering failure" with a distinct JSON format: `{"error_code": "RENDER_FAILURE", "object_id": "...", "timestamp": ...}` rather than a standard drift error, and the correction token must be a "reset" or "fade" command rather than a direct state overwrite.
- **How does the system handle sequences where the visual model hallucinates an object that does not exist in the symbolic log?** The consistency checker must detect "phantom objects" and increment the drift score, ensuring the metric captures both missing and spurious entities.
- **What happens if the optical flow/template matching fails to detect an object due to occlusion?** The system must implement a fallback logic (e.g., "assume state persists if occlusion is detected") and flag the frame as "low-confidence" to avoid false-positive drift penalties.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST generate 60-second interactive video sequences using the frozen AlayaWorld model based on discrete user action inputs. (See US-1)
- **FR-002**: The system MUST implement a deterministic, rule-based symbolic engine in pure Python/C that tracks object states (HP, inventory, position) based on the same user action inputs. (See US-1)
- **FR-003**: The system MUST calculate a "Semantic Drift Score" by comparing the symbolic engine's state trajectory against object states detected in the generated video frames using classical computer vision primitives (template matching for static objects, optical flow for motion) with a verified detection accuracy floor of ≥ 85%. (See US-1)
- **FR-004**: The system MUST inject "correction tokens" (implemented as dynamic prompt re-conditioning updates) into the video generation process when the symbolic engine detects a state inconsistency with the visual output. (See US-2)
- **FR-005**: The system MUST log resource usage metrics (peak RAM, total wall-clock time) for every generated sequence to verify CPU-only feasibility. (See US-3)
- **FR-006**: The system MUST perform a statistical paired t-test comparing the Semantic Drift Scores of the baseline (vanilla) runs against the hybrid (corrected) runs across at least 10 random seeds, assuming stationary CV error validated by FR-007, and report the CV validation accuracy alongside the test results. (See US-1, US-2)
- **FR-007**: The system MUST perform a Ground Truth Validation step on a manually annotated subset of frames (≥ 50 frames) to verify that the CV pipeline's detection accuracy meets the ≥ 85% threshold; if accuracy falls below this, the Semantic Drift Score for that sequence MUST be flagged as invalid. (See US-1, US-2)

### Key Entities

- **Action Sequence**: A discrete list of user inputs (e.g., "summon", "hit", "die") driving the simulation.
- **Symbolic State Log**: A time-series record of logical object states (HP, existence) derived from the rule-based engine.
- **Visual State Log**: A time-series record of object states derived from computer vision analysis of the generated video.
- **Semantic Drift Score**: A scalar metric representing the divergence between the Symbolic State Log and the Visual State Log, contingent on valid CV validation.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The mean Semantic Drift Score for the hybrid approach must be at least 30% lower than the mean score of the vanilla AlayaWorld baseline across the test set. (See US-1, US-2)
- **SC-002**: The total wall-clock time for generating and analyzing a single 60-second sequence on a 2-core CPU must be ≤ 30 minutes. (See US-3)
- **SC-003**: The peak memory usage during the hybrid inference pipeline must remain ≤ 7 GB. (See US-3)
- **SC-004**: The statistical comparison (paired t-test) must yield a p-value < 0.05 at a 95% confidence level, indicating a significant reduction in drift, provided the CV validation accuracy is ≥ 85%. (See US-1, US-2)
- **SC-005**: The "correction token" mechanism must successfully reduce the rate of "permanence violations" (objects alive in video but dead in logic) by ≥ 25% compared to the baseline. (See US-2)
- **SC-006**: The Ground Truth Validation (FR-007) must confirm a detection accuracy of ≥ 85% on the annotated subset; otherwise, the experiment is deemed inconclusive. (See FR-007)

## Assumptions

- The AlayaWorld dataset contains sequences with specific, countable object interactions (e.g., "summon," "hit," "die") that can be reliably mapped to symbolic logic rules.
- The AlayaWorld model weights are available in a format compatible with CPU inference (e.g., standard PyTorch `.pth` or ONNX) without requiring CUDA-specific kernels or 8-bit quantization libraries that mandate GPU.
- Classical computer vision primitives (template matching, optical flow) are sufficient to detect object states in the generated video frames with ≥ 85% accuracy; if accuracy drops below this, the drift score may be noisy and is flagged as invalid per FR-007.
- The "correction tokens" or context injections can be implemented by modifying the input prompt or latent context of the AlayaWorld model via dynamic re-conditioning without retraining the model weights.
- The symbolic engine's logic rules (e.g., "hit reduces HP by 10") are consistent with the game mechanics implied by the AlayaWorld training data; any discrepancies found during Ground Truth Validation (FR-007) must be documented and may require rule adjustment.
- The dataset size is small enough to be processed in batches that fit within the available RAM limit; if the full dataset is larger, a random sample is assumed to be representative.
- The GitHub Actions free-tier runner provides stable 2-core performance without significant noise from neighboring containers that would invalidate the 30-minute time constraint.
- The AlayaWorld model architecture supports prompt conditioning (textual injection) as a mechanism for state correction, allowing the model to react to dynamic symbolic state updates.