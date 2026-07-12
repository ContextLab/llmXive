# Feature Specification: llmXive follow-up: extending "LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation"

**Feature Branch**: `001-llmxive-precision-threshold`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CPU-Only Precision Simulation Loop (Priority: P1)

A researcher can execute a complete training simulation loop on a standard CPU-only environment (2 cores, 7GB RAM) that models the theoretical memory footprint and numerical behavior of NVFP4 precision without requiring actual low-bit hardware instructions or CUDA.

**Why this priority**: This is the foundational capability. Without a CPU-tractable simulation that accurately models bit-width effects, the subsequent analysis of precision thresholds is impossible. It directly addresses the "Compute feasibility" constraint of the project.

**Independent Test**: Can be fully tested by running a single training epoch on a downsampled Kinetics-400 subset and verifying that the memory usage stays within 7GB and the simulated bit-masked values match the expected 32-bit floating-point arithmetic with explicit quantization noise injection.

**Acceptance Scenarios**:

1. **Given** a downsampled Kinetics-400 dataset subset (4-second clips), **When** the simulation loop is executed with a target bit-width of 4-bit, **Then** the system must complete the forward and backward pass using only standard 32-bit floats with explicit bit-masking, consuming ≤ 7GB RAM and ≤ 14GB disk, without triggering any GPU/CUDA errors.
2. **Given** the simulation loop is running, **When** the bit-width parameter is changed from 4-bit to 8-bit, **Then** the system must re-initialize the quantization masking logic without requiring a code restart, maintaining the same CPU-only execution path.

---

### User Story 2 - Narrative Consistency Evaluation Pipeline (Priority: P2)

A researcher can evaluate generated video sequences for temporal coherence using a frozen, independent video-language model (e.g., CLIP-ViT) to generate a quantitative narrative consistency score, ensuring validation independence from the training model.

**Why this priority**: This provides the dependent variable (outcome) necessary to answer the research question. It validates the "Methodological soundness" requirement for measurement validity and validation independence.

**Independent Test**: Can be fully tested by feeding a set of generated video clips into the evaluation pipeline and verifying that the output is a numeric consistency score derived solely from the frozen evaluator model, with no gradient flow back to the generator.

**Acceptance Scenarios**:

1. **Given** a set of 10 generated video clips from the simulation loop, **When** the evaluation pipeline is run using a frozen CLIP-ViT model, **Then** the system must output a single numeric score per video representing temporal coherence, calculated within 5 minutes on CPU.
2. **Given** a video clip with known temporal discontinuity (artificially injected), **When** evaluated by the pipeline, **Then** the system must assign a significantly lower consistency score compared to a continuous reference clip, demonstrating sensitivity to narrative breakdown.

---

### User Story 3 - Precision-Consistency Threshold Mapping (Priority: P3)

A researcher can aggregate results from multiple training runs across different simulated bit-widths (2-bit, 4-bit, 8-bit) to generate a precision-consistency curve and identify the specific threshold where narrative consistency degrades non-linearly.

**Why this priority**: This delivers the final scientific insight (the "threshold") requested by the research question. It synthesizes the simulation and evaluation components.

**Independent Test**: Can be fully tested by running the full experimental suite (3 bit-widths × 3 seeds) and verifying that the output includes a regression plot and a statistical test result identifying the point of non-linear degradation.

**Acceptance Scenarios**:

1. **Given** results from 9 training runs (3 bit-widths × 3 seeds), **When** the aggregation script is executed, **Then** the system must output a CSV containing bit-width, memory footprint, convergence speed, and consistency score for each run.
2. **Given** the aggregated CSV, **When** the statistical analysis module runs, **Then** it must identify a specific bit-width threshold (e.g., 4-bit) where the consistency score drops below a defined baseline, accompanied by a p-value < 0.05 from a paired t-test.

### Edge Cases

- What happens when the simulated bit-width (e.g., 2-bit) causes the model to collapse (outputting constant noise) and the consistency score becomes undefined? (System must handle NaN/Inf values gracefully and record a "Collapse" status).
- How does the system handle a video clip that is too large for the 7GB RAM limit even after downsampling? (System must trigger a fallback to a smaller subset size or abort with a clear error).
- What if the frozen evaluator model (CLIP-ViT) fails to load due to local environment issues? (System must fail fast with a specific error message indicating the missing dependency).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement a CPU-only training loop that simulates low-bit precision (2-bit, 4-bit, 8-bit) using explicit bit-width masking on 32-bit floating-point arithmetic, ensuring no CUDA or GPU-specific instructions are executed (See US-1).
- **FR-002**: System MUST utilize a downsampled subset of the Kinetics-400 dataset (4-second clips) via the HuggingFace Datasets API, ensuring the total dataset size fits within 7GB RAM (See US-1).
- **FR-003**: System MUST evaluate generated video outputs using a frozen, independent video-language model (e.g., CLIP-ViT or VideoMAE) to calculate a temporal coherence score, ensuring no gradient backpropagation to the generator (See US-2).
- **FR-004**: System MUST execute the entire training and evaluation pipeline within a single GitHub Actions free-tier job (≤ 6 hours, 2 CPU cores, ≤ 7GB RAM, ≤ 14GB disk) (See US-1, US-2, US-3).
- **FR-005**: System MUST perform statistical analysis (paired t-tests and regression) across multiple random seeds for each bit-width to validate the significance of the observed precision-consistency trade-offs (See US-3).
- **FR-006**: System MUST record and report the theoretical memory footprint derived from parameter counts alongside the empirical memory usage to verify simulation accuracy (See US-3).

### Key Entities

- **SimulatedModel**: The student diffusion model with quantization-aware masking logic.
- **VideoClip**: A 4-second segment from Kinetics-400, used as input/output.
- **ConsistencyScore**: A numeric metric derived from the frozen evaluator model representing temporal coherence.
- **ExperimentRun**: A single execution instance defined by bit-width, random seed, and resulting metrics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The memory usage of the training loop is measured against the 7GB RAM limit of the GitHub Actions free-tier runner to ensure feasibility (See FR-001, FR-004).
- **SC-002**: The narrative consistency score is measured against the baseline score obtained from a high-precision (32-bit) reference model to quantify the degradation caused by bit-width reduction (See FR-003, FR-005).
- **SC-003**: The statistical significance of the precision-consistency relationship is measured against a p-value threshold of 0.05 using paired t-tests across multiple seeds (See FR-005, FR-006).
- **SC-004**: The total execution time of the full experimental suite (all bit-widths and seeds) is measured against the 6-hour job limit of the CI runner (See FR-004).
- **SC-005**: The simulation accuracy is measured by comparing the empirical memory usage against the theoretical lower bound derived from parameter counts, with a tolerance of ≤ 10% variance (See FR-006).

## Assumptions

- **Assumption about data availability**: The Kinetics-400 dataset contains sufficient 4-second video clips relevant to narrative coherence analysis, and the HuggingFace API provides stable access without rate limiting that exceeds the 6-hour job window.
- **Assumption about hardware constraints**: The "CPU-only simulation" approach using explicit bit-masking on 32-bit floats is a valid proxy for actual low-bit hardware behavior regarding memory footprint and numerical noise, even if it does not perfectly replicate the exact inference speed of hardware-accelerated low-bit operations.
- **Assumption about evaluation validity**: The frozen CLIP-ViT (or similar) model provides a sufficiently correlated metric for "narrative coherence" in the context of short 4-second clips, serving as a valid proxy for human evaluation of long-horizon consistency.
- **Assumption about model convergence**: The "student" diffusion model will converge within the 6-hour window even at the most aggressive bit-width (2-bit), allowing for a complete data point to be collected; if convergence fails, the run will be marked as "collapsed" rather than discarded.
- **Assumption about quantization simulation**: Explicit bit-width masking on 32-bit floats will introduce noise comparable to actual low-bit quantization, allowing the study to isolate the *effect* of precision reduction without needing the actual hardware.
