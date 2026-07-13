# Feature Specification: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

**Feature Branch**: `001-llmxive-kairos-discrete-scaling`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "How does the minimum information density required for stable long-horizon forecasting in embodied agents scale as input modality shifts from continuous visual streams to sparse, discrete sensor streams, and what architectural properties are necessary to preserve error bounds under these constraints?"

## User Scenarios & Testing

### User Story 1 - Data Construction and Quantization Pipeline (Priority: P1)

The research system MUST convert the continuous LIBERO benchmark dataset (RGB frames and proprioceptive states) into discrete, JSON-serialized state vectors with configurable quantization levels (4-bit, 8-bit, 16-bit) to simulate sparse sensor inputs.

**Why this priority**: Without a reproducible, quantized dataset representing the "Sparse Physical World," no subsequent modeling or stability analysis can occur. This is the foundational input for the entire study.

**Independent Test**: The pipeline can be tested by running the conversion script on a subset of LIBERO data, verifying that the output JSON files contain discrete integer values within the specified bit-depth ranges, and confirming that the total dataset size fits within the 7GB RAM constraint.

**Acceptance Scenarios**:

1. **Given** the raw LIBERO dataset is downloaded, **When** the quantization script is executed with a target bit-depth of 4-bit, **Then** the output state vectors contain only integer values in the range [0, 15] and the file size is reduced by at least 75% compared to the raw float32 representation.
2. **Given** a raw continuous state vector, **When** the script applies Gaussian noise injection (std dev 0.1), **Then** the resulting noisy vector remains within the discrete quantization bins without floating-point leakage.
3. **Given** the full dataset, **When** the pipeline runs on a 2-core CPU runner, **Then** the entire conversion process completes in a timely manner and peak RAM usage does not exceed 7GB.

---

### User Story 2 - CPU-Only Model Training and Inference (Priority: P2)

The system MUST load the pre-trained Kairos Hybrid Linear Temporal Attention module, replace the visual embedding layers with a fixed, untrained discrete projection layer (to preserve architecture), and execute the full training and long-horizon prediction loop on a CPU-only environment without GPU acceleration.

**Why this priority**: The core research question depends on evaluating the architecture's stability under CPU constraints. If the model cannot run or train on the target hardware, the hypothesis regarding "resource-constrained deployment" cannot be tested.

**Independent Test**: The model can be tested by initiating a training run with a fixed random seed, verifying that the loss trend shows convergence (no single epoch loss increase > 5% relative to the previous epoch), confirming that the total training time is a target ≤ 4 hours (graceful exit if > 6h), and confirming that inference on a 500-step sequence completes without CUDA errors or out-of-memory exceptions.

**Acceptance Scenarios**:

1. **Given** the pre-trained Kairos weights are available, **When** the visual embedding layers are replaced with a fixed discrete projection layer, **Then** the model initialization completes successfully on a CPU-only PyTorch environment without any "CUDA device" or "bitsandbytes" errors.
2. **Given** a training loop configured for 100 epochs, **When** it runs on the 2-core CPU runner, **Then** the total training time for the sampled dataset is a target ≤ 4 hours (graceful exit if > 6h), and the loss curve shows convergence (no single epoch loss increase > 5% relative to the previous epoch).
3. **Given** a trained model, **When** it predicts a 500-step horizon sequence, **Then** the inference latency per step is ≤ 2 seconds, and the cumulative RAM usage remains < 6GB throughout the sequence generation.

---

### User Story 3 - Stability Analysis and Threshold Mapping (Priority: P3)

The system MUST compute the Mean Squared Error (MSE) between predicted and ground-truth discrete sequences across varying quantization levels and noise levels, performing statistical validation to identify the minimum information density threshold where stability guarantees break down.

**Why this priority**: This is the direct answer to the research question. It synthesizes the data and model outputs into the "scaling law" and "threshold" findings required for the paper.

**Independent Test**: The analysis can be tested by running the evaluation script on the model outputs, generating the error-vs-bandwidth curve, and verifying that the statistical tests (t-test/Wilcoxon) produce valid p-values and confidence intervals.

**Acceptance Scenarios**:

1. **Given** the prediction results for 4-bit, 8-bit, and 16-bit inputs, **When** the error accumulation rate is calculated, **Then** the system produces a clear non-linear scaling curve and reports the specific quantization threshold where MSE exceeds a 20% increase over the baseline visual-modality error.
2. **Given** 10 independent runs with different noise seeds, **When** a paired t-test is performed on the error rates between discrete and visual modalities, **Then** the system outputs a p-value and explicitly states whether the difference is statistically significant (p < 0.05) or indistinguishable.
3. **Given** the sensitivity analysis results, **When** the quantization threshold is swept (e.g., 4-bit vs 8-bit), **Then** the system reports the specific error rate change and identifies the stability boundary with a confidence interval.

### Edge Cases

- **What happens when** the quantization level is so low (e.g., 1-bit) that the state space collapses to a single value? The system MUST detect this degeneracy and flag the run as "Invalid Data" rather than producing a false stability metric.
- **How does system handle** a scenario where the CPU runner hits the 6-hour time limit during training? The system MUST checkpoint the model state every epoch and gracefully exit, logging the progress so the run can be resumed or the sample size reduced.
- **What happens when** the noise injection (std dev 0.5) causes the discrete state to flip to a completely invalid bin? The system MUST clamp the noise to the nearest valid discrete bin to prevent data corruption in the ground truth.

## Requirements

### Functional Requirements

- **FR-001**: System MUST convert continuous LIBERO dataset frames and proprioceptive states into discrete JSON-serialized vectors with user-defined quantization levels (4-bit, 8-bit, 16-bit) to simulate sparse sensor inputs (See US-1).
- **FR-002**: System MUST process discrete inputs through the *same* unpruned Kairos architecture, replacing the visual encoder with a *fixed, untrained* projection layer to isolate modality shift from architectural changes (See US-2).
- **FR-003**: System MUST execute the full training and inference pipeline on a CPU-only environment without requiring GPU, CUDA, or mixed-precision accelerators (See US-2).
- **FR-004**: System MUST calculate the Mean Squared Error (MSE) between predicted and ground-truth discrete sequences and compute the cumulative error growth rate over horizons of 100, 250, and 500 steps (See US-3).
- **FR-005**: System MUST perform statistical validation (paired t-test or Wilcoxon signed-rank test) across 10 independent runs with different noise seeds to determine significance of error accumulation (See US-3).
- **FR-006**: System MUST implement a sensitivity analysis that sweeps the quantization resolution (e.g., 4-bit, 8-bit, 16-bit) and reports the variation in headline error rates (See US-3).
- **FR-007**: System MUST log CPU utilization, peak RAM usage, and latency per time step to verify compliance with the 2-core/7GB RAM/6h GHA runner constraints (See US-2).
- **FR-008**: System MUST explicitly frame stability claims as "relative degradation due to quantization" against a continuous baseline, acknowledging the lack of an independent ground truth for the discrete modality (See US-3).

### Key Entities

- **DiscreteStateVector**: Represents the quantized state of the embodied agent at a single time step, containing integer values for object positions, velocities, and binary collision flags.
- **PredictionHorizon**: The number of future time steps (100, 250, and 500) the model attempts to predict from a given input sequence.
- **ErrorMetric**: A composite record containing the MSE, cumulative error growth rate, and statistical significance (p-value) for a specific quantization level and noise seed.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The minimum information density threshold (quantization level) required to maintain stable long-horizon forecasting is measured against the point where MSE exceeds a [deferred] increase over the baseline visual-modality error. (See US-3).
- **SC-002**: The error accumulation rate (MSE growth per time step) is measured against the continuous visual-modality baseline to determine the relative degradation caused by the discrete modality (See US-3).
- **SC-003**: The computational feasibility (training time and peak RAM) is measured against the 6h time limit and 7GB RAM constraint of the GitHub Actions free-tier runner to ensure the study is reproducible (See US-2).
- **SC-004**: The statistical significance of the difference in error rates between discrete and visual modalities is measured against the p < 0.05 threshold using a paired t-test or Wilcoxon test (See US-3).
- **SC-005**: The sensitivity of the stability threshold to quantization resolution is measured by the change in MSE when sweeping the bit-depth from 4-bit to 16-bit in 4-bit increments (See US-3).

## Assumptions

- **Assumption about data**: The LIBERO benchmark dataset is publicly available and contains sufficient variety of object states and collision events to generate a representative "Sparse Physical World" dataset after quantization.
- **Assumption about scope boundaries**: The study focuses exclusively on the Hybrid Linear Temporal Attention mechanism within the Kairos architecture; other architectural components (e.g., visual encoders, policy heads) are assumed to be irrelevant to the specific stability question of the attention module on sparse data.
- **Assumption about target hardware**: The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) is representative of the target "resource-constrained" edge environment, and the CPU-only training time will remain within a practical duration for the sampled dataset size.
- **Assumption about quantization**: The discrete state vectors generated by 4-bit, 8-bit, and 16-bit quantization will retain enough semantic information to allow the model to learn a valid predictive distribution, provided the information density is above the identified threshold.
- **Assumption about noise injection**: The injected Gaussian noise (0.1–0.5 std dev) accurately simulates the telemetry instability found in real-world industrial IoT and micro-controller sensors.
- **Assumption about statistical power**: The sample size of multiple independent runs with different noise seeds is sufficient to detect a statistically significant difference in error accumulation rates between modalities.
- **Assumption about model weights**: The pre-trained Kairos weights are available in a format compatible with the CPU-only PyTorch environment and do not require GPU-specific quantization (e.g., 8-bit/CUDA) to load.
- **Assumption about baseline comparison**: The 'visual-modality error' baseline is derived from a separate run of the *same* unpruned Kairos model on the continuous data, ensuring architectural consistency when comparing modality effects.
- **Assumption about independent ground truth**: An independent ground truth for the discrete modality (e.g., high-fidelity sensor logs from a physical robot) is unavailable; therefore, the study is scoped to measure relative degradation against the continuous baseline rather than absolute stability.