# Feature Specification: llmXive follow-up: extending "LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation"

**Feature Branch**: `001-llmxive-precision-threshold`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CPU-Only Numerical Stability Simulation (Priority: P1)

A researcher can execute a complete training simulation loop on a standard CPU-only environment (a minimal core count, limited RAM) that models the **numerical behavior** (gradient noise, convergence stability) of NVFP4 precision using stochastic rounding to simulate low-bit arithmetic. This simulation explicitly does **not** model hardware memory bandwidth or physical memory footprint, which are derived theoretically from the NVFP4 architecture definition.

**Why this priority**: This is the foundational capability. Without a CPU-tractable simulation that accurately models bit-width effects and numerical noise, the analysis of precision thresholds for convergence is impossible. It addresses the "Numerical Stability" constraint, while infrastructure efficiency is validated via the theoretical model (US-3).

**Independent Test**: Can be fully tested by running a single training epoch on a downsampled Kinetics-400 subset and verifying that the simulated stochastic rounding noise matches the expected uniform distribution over the range [-0.5 * LSB, 0.5 * LSB] (where LSB = 2^(-bit_width+1)) within 5% KL-divergence, using a sample size of ≥ 10,000 values binned into 50 bins.

**Acceptance Scenarios**:

1. **Given** a downsampled Kinetics-400 dataset subset (4-second clips), **When** the simulation loop is executed with a target bit-width of 4-bit, **Then** the system must complete the forward and backward pass using standard 32-bit floats with stochastic rounding, consuming ≤ 7GB runner memory and ≤ 14GB disk, without triggering any GPU/CUDA errors.
2. **Given** the simulation loop is running, **When** the bit-width parameter is changed from 4-bit to 8-bit, **Then** the system must re-initialize the quantization rounding logic without requiring a code restart, maintaining the same CPU-only execution path.

---

### User Story 2 - Temporal Coherence Evaluation Pipeline (Priority: P2)

A researcher can evaluate generated video sequences for **temporal coherence** using a frozen, independent video-language model (e.g., CLIP-ViT) to generate a quantitative score. **Scope Note**: This metric measures *local temporal coherence* on 4-second clips as a proxy for the continuity of action sequences. **Operational Definition**: "Temporal Coherence" is defined as "aggregated frame-to-frame consistency" measured across the generated sequence. Validation against human labels is replaced by validation against synthetic discontinuity labels (generated via frame-swapping) due to the lack of ground-truth narrative data in Kinetics-400.

**Why this priority**: This provides the dependent variable (outcome) necessary to answer the research question. It validates the "Methodological soundness" requirement for measurement validity and validation independence.

**Independent Test**: Can be fully tested by feeding a set of generated video clips into the evaluation pipeline and verifying that the output is a numeric consistency score derived solely from the frozen evaluator model, with no gradient flow back to the generator.

**Acceptance Scenarios**:

1. **Given** a set of 10 generated video clips from the simulation loop, **When** the evaluation pipeline is run using a frozen CLIP-ViT model, **Then** the system must output a single numeric score per video representing temporal coherence, calculated within 5 minutes on CPU.
2. **Given** a video clip with known temporal discontinuity (artificially injected via frame-swapping), **When** evaluated by the pipeline, **Then** the system must assign a consistency score at least 15% lower than the continuous reference clip, or a p-value < 0.05 from a one-tailed t-test against 30 noise-injected controls, demonstrating sensitivity to narrative breakdown.

---

### User Story 3 - Precision-Consistency Threshold Mapping & Infrastructure Validation (Priority: P3)

A researcher can aggregate results from multiple training runs across different simulated bit-widths to generate a precision-consistency curve and identify the specific threshold where temporal coherence degrades non-linearly. Additionally, the researcher validates the NVFP4 infrastructure efficiency claims by comparing the **theoretical memory footprint** (calculated via NVFP4 architecture parameters) against the theoretical footprint of standard FP32, confirming the ≥ 75% reduction claim without needing runtime hardware profiling.

**Why this priority**: This delivers the final scientific insight (the "threshold") requested by the research question. It synthesizes the simulation and evaluation components with sufficient statistical power for non-linear modeling and confirms the theoretical efficiency gain.

**Independent Test**: Can be fully tested by running the full experimental suite across multiple bit-widths and seeds, and verifying that the output includes a regression plot, a statistical test result identifying the point of non-linear degradation, and a theoretical memory comparison report.

**Acceptance Scenarios**:

1. **Given** results from multiple training runs (multiple bit-widths × multiple seeds), **When** the aggregation script is executed, **Then** the system must output a CSV containing bit-width, memory footprint (theoretical), convergence speed, and consistency score for each run.
2. **Given** the aggregated CSV, **When** the statistical analysis module runs, **Then** it must identify a specific bit-width threshold (e.g., 4-bit) where the consistency score drops below the defined baseline (32-bit reference, seed=42), accompanied by a p-value < 0.05 from a non-linear regression fit, confirmed by a ΔAIC > 10 or curvature p-value < 0.05.
3. **Given** the NVFP4 architecture parameters, **When** the theoretical memory calculator runs, **Then** it must report a memory reduction of ≥ 75% compared to FP32 for the same parameter count, consistent with the source paper's claims.

### Edge Cases

- What happens when the simulated bit-width (e.g., 2-bit) causes the model to collapse (outputting constant noise) and the consistency score becomes undefined? (System must handle NaN/Inf values gracefully and record a "Collapse" status).
- How does the system handle a video clip that is too large for the 7GB runner memory limit even after downsampling? (System must trigger a fallback to a smaller subset size or abort with a clear error).
- What if the frozen evaluator model (CLIP-ViT) fails to load due to local environment issues? (System must fail fast with a specific error message indicating the missing dependency).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement a CPU-only training loop that simulates low-bit precision (2-bit to 8-bit) using stochastic rounding on 32-bit floating-point arithmetic to model gradient distortion and numerical noise, ensuring no CUDA or GPU-specific instructions are executed (See US-1).
- **FR-002**: System MUST utilize a downsampled subset of the Kinetics dataset (4-second clips) via the HuggingFace Datasets API, ensuring the total dataset size fits within 7GB runner memory (See US-1).
- **FR-003**: System MUST evaluate generated video outputs using a frozen, independent video-language model (e.g., CLIP-ViT or VideoMAE) to calculate a temporal coherence score, ensuring no gradient backpropagation to the generator (See US-2).
- **FR-004**: System MUST execute the entire training and evaluation pipeline within a single GitHub Actions free-tier job (≤ 6 hours, 2 CPU cores, ≤ 7GB runner memory, ≤ 14GB disk) (See US-1, US-2, US-3).
- **FR-005**: System MUST perform statistical analysis (non-linear regression and paired t-tests) across random seeds for a range of bit-widths to validate the significance of the observed precision-consistency trade-offs (See US-3).
- **FR-006**: System MUST calculate and report the **theoretical** memory footprint derived strictly from parameter counts and bit-widths using the formula: `(Parameter Count × Bit Width / 8) + 1.5GB` (Python runtime overhead, conservative upper-bound estimate for containerized CI). This calculation is used to validate the **theoretical efficiency** of NVFP4 (≥ 75% reduction vs FP32), independent of runtime profiling (See US-3).
- **FR-007**: System MUST validate the CLIP-ViT proxy metric by computing a correlation coefficient ≥ 0.8 between the model's score and synthetic discontinuity labels (generated via frame-swapping) on a held-out subset of clips to ensure the metric measures temporal structure, not semantic content (See US-2).
- **FR-008**: System MUST fit a piecewise linear or logistic regression model to the precision-consistency data to identify the non-linear degradation threshold, defined as a model fit where ΔAIC > 10 or curvature p-value < 0.05 (See US-3).
- **FR-009**: System MUST verify that the noise distribution introduced by stochastic rounding matches the theoretical uniform distribution over the range [-0.5 * LSB, 0.5 * LSB] within 5% KL-divergence, using ≥ 10,000 samples and 50 bins (See US-1).
- **FR-010**: System MUST perform a sensitivity analysis on the temporal coherence metric by injecting synthetic noise (Gaussian noise with varying low-to-moderate standard deviations) into the video frames and reporting the resulting change in consistency scores to demonstrate robustness against minor perturbations (See US-2).

### Key Entities

- **SimulatedModel**: The student diffusion model with stochastic rounding logic.
- **VideoClip**: A 4-second segment from Kinetics-400, used as input/output.
- **ConsistencyScore**: A numeric metric derived from the frozen evaluator model representing temporal coherence.
- **ExperimentRun**: A single execution instance defined by bit-width, random seed, and resulting metrics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The memory usage of the training loop is measured against the 7GB runner memory limit of the GitHub Actions free-tier runner to ensure feasibility (See FR-001, FR-004).
- **SC-002**: The temporal coherence score is measured against a baseline score obtained from a specific reference run (32-bit precision, 4-second clips, seed=42) to quantify the degradation caused by bit-width reduction (See FR-003, FR-005).
- **SC-003**: The statistical significance of the precision-consistency relationship is measured against a standard p-value threshold using non-linear regression across multiple seeds (See FR-005, FR-008).
- **SC-004**: The total execution time of the full experimental suite (all bit-widths and seeds) is measured against the job limit of the CI runner. (See FR-004).
- **SC-005**: The simulation accuracy is measured by comparing the calculated theoretical memory footprint (using the formula in FR-006) against the Python runtime overhead model, with a tolerance of ≤ 15% variance (See FR-006).
- **SC-006**: The NVFP4 theoretical efficiency is measured against the FP32 baseline, confirming a memory reduction of ≥ 75% (See FR-006, US-3).

## Assumptions

- **Assumption about data availability**: The Kinetics-400 dataset contains sufficient 4-second video clips relevant to **temporal coherence** analysis (action continuity), and the HuggingFace API provides stable access without rate limiting that exceeds the 6-hour job window.
- **Assumption about hardware constraints**: The "CPU-only simulation" approach using stochastic rounding on 32-bit floats is a valid proxy for the **numerical noise** of low-bit hardware behavior, even if it does not perfectly replicate the exact inference speed or memory bandwidth of hardware-accelerated low-bit operations. Infrastructure memory efficiency is validated theoretically, not via simulation.
- **Assumption about evaluation validity**: The frozen CLIP-ViT (or similar) model provides a sufficiently correlated metric for "temporal coherence" (frame-to-frame consistency) in the context of short 4-second clips, serving as a valid proxy for human evaluation of continuity, subject to the validation in FR-007 using synthetic labels.
- **Assumption about model convergence**: The "student" diffusion model will converge within the 6-hour window even at the most aggressive bit-width (2-bit), allowing for a complete data point to be collected; if convergence fails, the run will be marked as "collapsed" rather than discarded.
- **Assumption about quantization simulation**: Stochastic rounding on 32-bit floats will introduce noise comparable to actual low-bit quantization, allowing the study to isolate the *effect* of precision reduction on convergence, subject to validation in FR-009.