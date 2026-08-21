# Feature Specification: llmXive follow-up: extending "Guava: An Effective and Universal Harness for Embodied Manipulation"

**Feature Branch**: `001-symbolic-guava-perception`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Guava: Does replacing high-fidelity multimodal vision encoders with lightweight, symbolic perception modules preserve long-horizon task success rates, or does the seeing-to-doing gap necessitate raw pixel-level semantic grounding?"

## User Scenarios & Testing

### User Story 1 - Symbolic Pipeline Construction & Dataset Transformation (Priority: P1)

The research team MUST be able to ingest the original Guava visual trajectory data and transform it into a "Symbolic-Guava" dataset where raw image tensors are replaced by structured JSON observations (object classes, 2D bounding boxes, centroids, color histograms) generated via a CPU-only perception module (OpenCV + ONNX YOLO-tiny).

**Why this priority**: Without a valid symbolic dataset, the core hypothesis (testing the "seeing-to-doing gap") cannot be tested. This is the foundational data engineering step that enables the entire downstream experiment.

**Independent Test**: The pipeline can be run on a subset of trajectories. The output JSON must contain valid bounding boxes and class labels for every frame where an object is present, and the processing time per frame must be [deferred] on a standard CPU.

**Acceptance Scenarios**:

1. **Given** a raw video frame from the Guava dataset containing a red block and a blue drawer, **When** the symbolic pipeline processes the frame, **Then** the output JSON contains an entry for "red_block" with a bounding box and "blue_drawer" with a bounding box, and no raw pixel data is included in the output.
2. **Given** a frame with no manipulable objects, **When** the pipeline processes it, **Then** the output JSON contains an empty object list or a specific "scene_empty" flag, without raising a runtime error.
3. **Given** the full Guava training set (<2,000 trajectories), **When** the transformation script runs, **Then** it completes within 4 hours on a CPU-only runner, producing a transformed dataset of equivalent trajectory count.

---

### User Story 2 - Model Re-distillation on Symbolic States (Priority: P2)

The research team MUST be able to fine-tune a 4B parameter open-source LLM using the "Symbolic-Guava" dataset and the original Guava prompt templates, ensuring the model learns to reason over symbolic states rather than visual tokens.

**Why this priority**: This validates whether the "harness" architecture (reasoning loops) can adapt to reduced-fidelity inputs. It tests the core claim that the harness is the primary driver of performance.

**Independent Test**: The fine-tuning job must converge (loss decrease) within the available free-tier CPU time limit. The resulting model must accept the symbolic JSON input format without crashing.

**Acceptance Scenarios**:

1. **Given** the transformed symbolic dataset and the base 4B LLM, **When** the fine-tuning script executes, **Then** the training loss decreases by at least 10% within the first 2 hours of CPU compute, indicating the model is learning the symbolic mapping.
2. **Given** a new symbolic observation JSON, **When** the fine-tuned model receives it as input, **Then** it generates a valid action plan string following the Guava action abstraction schema (e.g., "GRAB_OBJECT", "MOVE_TO").
3. **Given** a training run that exceeds 5.5 hours, **When** the job is terminated, **Then** the partially trained model checkpoint is saved and loadable for further evaluation.

---

### User Story 3 - Evaluation & Statistical Comparison (Priority: P3)

The research team MUST be able to execute the Symbolic-Guava agent on a held-out set of long-horizon tasks, measure the task success rate and step efficiency, and perform a statistical comparison (two-proportion z-test) against the original Guava baseline.

**Why this priority**: This delivers the final answer to the research question: "Does symbolic perception suffice?" It provides the quantitative evidence needed to validate or refute the hypothesis.

**Independent Test**: The evaluation script must run the agent on 50 tasks, record binary success/failure for each, and output a p-value indicating statistical significance (or lack thereof).

**Acceptance Scenarios**:

1. **Given** the fine-tuned Symbolic-Guava model and 50 held-out tasks, **When** the evaluation loop runs, **Then** it produces a success rate (e.g., [deferred]) and a step count for each task, completing within 6 hours.
2. **Given** the success rates of the Symbolic-Guava agent and the original Guava baseline, **When** the statistical analysis module runs, **Then** it outputs a p-value and a conclusion (e.g., "Significant drop" or "No significant difference") with p < 0.05 as the threshold.
3. **Given** a failed task, **When** the failure analysis module runs, **Then** it categorizes the failure as either "geometric" (misalignment) or "semantic" (wrong object/texture) based on the symbolic state log.

---

### Edge Cases

- **What happens when** the symbolic perception module fails to detect an object that is clearly visible in the ground truth? The system must log this as a "perception failure" and categorize the subsequent task failure as "semantic" to distinguish it from a reasoning failure.
- **How does the system handle** a task where the environment changes dynamically (e.g., an object moves unexpectedly)? The symbolic state must be updated in real-time; if the update latency exceeds the action timeout, the task is recorded as a timeout failure.
- **What happens when** the 4B model generates an action that is syntactically valid but physically impossible (e.g., "GRAB_OBJECT" when the object is out of reach)? The simulation environment must catch this, log it as a "planning error," and the agent must retry up to a maximum of 3 attempts before marking the task as failed.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a CPU-only perception module using OpenCV and an ONNX Runtime YOLO-tiny model to generate structured JSON observations (class, bbox, centroid, color histogram) from raw image inputs (See US-1).
- **FR-002**: System MUST transform the original Guava training trajectories (<2,000) into a symbolic dataset format compatible with the LLM input schema, replacing pixel tensors with JSON objects (See US-1).
- **FR-003**: System MUST fine-tune a 4B parameter open-source LLM on the symbolic dataset using the original Guava prompt templates and action abstraction schemas, ensuring convergence within 6 hours on a CPU-only runner (See US-2).
- **FR-004**: System MUST evaluate the fine-tuned Symbolic-Guava agent on a held-out set of 50 long-horizon tasks from standard embodied benchmarks (e.g., ALFWorld) to measure task success rate and step efficiency (See US-3).
- **FR-005**: System MUST perform a two-proportion z-test to compare the success rates of the Symbolic-Guava agent against the original Guava baseline, reporting a p-value with a significance threshold of p < 0.05 (See US-3).
- **FR-006**: System MUST categorize task failures into "geometric" (misalignment, collision) and "semantic" (wrong object, texture confusion) categories based on the symbolic state logs (See US-3).

### Key Entities

- **SymbolicObservation**: A JSON object representing the state of the environment, containing lists of objects with attributes: `class_label`, `bounding_box_2d`, `centroid`, `color_histogram`.
- **Trajectory**: A sequence of `SymbolicObservation` and `Action` pairs derived from the original Guava dataset, used for training and evaluation.
- **TaskOutcome**: A record containing `task_id`, `success` (boolean), `steps_taken` (integer), `failure_category` (geometric/semantic/timeout), and `execution_time` (float).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The success rate of the Symbolic-Guava agent on geometric tasks is measured against the success rate of the original Guava baseline on the same tasks (See FR-005).
- **SC-002**: The step efficiency (average steps per task) of the Symbolic-Guava agent is measured against the baseline agent's step efficiency to determine if symbolic abstraction introduces planning overhead (See FR-004).
- **SC-003**: The statistical significance of the performance difference is measured using a two-proportion z-test with a p-value threshold of < 0.05 (See FR-005).
- **SC-004**: The proportion of failures categorized as "semantic" vs. "geometric" is measured to identify the specific failure modes of symbolic perception (See FR-006).
- **SC-005**: The total compute time for the fine-tuning and evaluation phases is measured against the 6-hour CPU-only runner limit to ensure feasibility (See FR-003, FR-004).

## Assumptions

- The original Guava dataset (<2,000 trajectories) is publicly available and contains sufficient visual data to train a YOLO-tiny model for object detection in the simulated environment.
- The small-parameter open-source LLM (e.g., Llama-3-8B or similar quantized variant) can be fine-tuned and run for inference on a standard CPU-only GitHub Actions runner (2 cores, ~7 GB RAM) within the 6-hour limit without requiring GPU acceleration or 8-bit quantization libraries that depend on CUDA.
- The simulated environment (e.g., ALFWorld or Franka) used for evaluation is compatible with CPU-only execution and provides a deterministic physics engine for measuring task success.
- The symbolic representation (bounding boxes + color histograms) is sufficient to describe the state of tasks involving geometric primitives (stacking, opening drawers) but may lack the fidelity required for texture-based tasks.
- The YOLO-tiny model, when quantized and run via ONNX Runtime on CPU, achieves inference speeds sufficient to process the trajectory frames within the simulation's time constraints.
- The original Guava prompt templates and action abstraction schemas are compatible with symbolic JSON inputs without requiring structural modification.
