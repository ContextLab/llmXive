# Feature Specification: llmXive Follow-up: Extending Asynchronous RL Staleness Bounds for Sub-1B Models

**Feature Branch**: `[001-llmxive-staleness-scaling]`  
**Created**: 2026-08-04  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending https://arxiv.org/abs/2607.07508"

## User Scenarios & Testing

### User Story 1 - Reproducible CPU-Only Training Loop with Configurable Staleness (Priority: P1)

**User Journey**: A researcher needs to execute an asynchronous reinforcement learning training loop on a standard GitHub Actions runner (2 CPU, 7GB RAM) without GPU acceleration. The researcher must be able to configure the "staleness" of gradient updates (simulating network latency) and observe whether the model converges or diverges based on the parameter count and staleness magnitude.

**Why this priority**: This is the foundational capability. Without a stable, reproducible training loop that respects hardware constraints and correctly simulates staleness, no empirical data regarding the relationship between model capacity and divergence can be collected. It directly addresses the "Methodology sketch" requirement to implement the controlled loop.

**Independent Test**: The system can be tested by running a single training job with a fixed staleness value and verifying that the training log outputs a sequence of reward values and gradient norms without crashing due to OOM (Out Of Memory) or CUDA errors.

**Acceptance Scenarios**:

1. **Given** a quantized sub-1B model (e.g., Qwen1.5-1.8B) and the GSM8K dataset loaded on a 2-CPU runner, **When** the training loop is initiated with `staleness=0` (synchronous), **Then** the system completes 500 steps within 45 minutes and logs a non-divergent reward curve.
2. **Given** the same environment, **When** the training loop is initiated with `staleness=10` (simulating 10-step delay) and `device="cpu"`, **Then** the system executes without attempting to load `bitsandbytes` CUDA kernels and completes the run, logging the final gradient norm.
3. **Given** a configuration with `batch_size=8` and `steps=1000`, **When** the run is executed, **Then** the memory usage remains below 6.5 GB throughout the execution, preventing runner termination.

---

### User Story 2 - Divergence Detection and Threshold Mapping (Priority: P2)

**User Journey**: A researcher needs to automatically detect when a training run has "diverged" based on a defined metric (sustained reward drop) and map the specific staleness threshold at which this occurs for different model sizes.

**Why this priority**: This implements the core scientific measurement. It transforms raw training logs into the specific data points (staleness bound vs. convergence status) required to answer the research question about the non-linear scaling law.

**Independent Test**: The system can be tested by feeding a pre-generated log file with a known divergence point and verifying that the analysis script correctly flags the run as "diverged" and records the specific step number where the threshold was breached.

**Acceptance Scenarios**:

1. **Given** a training log where the reward drops below 0.5 for 50 consecutive steps after step 200, **When** the divergence analysis script is run, **Then** the script outputs `status: DIVERGED` and `divergence_point: 200`.
2. **Given** a training log where the reward fluctuates but remains above the baseline threshold of 0.5, **When** the analysis script is run, **Then** the script outputs `status: STABLE`.
3. **Given** a set of 5 runs with varying staleness values (0, 5, 10, 15, 20), **When** the aggregation script is executed, **Then** it produces a summary table identifying the maximum staleness value that resulted in a `STABLE` status for the specific model configuration.

---

### User Story 3 - Statistical Comparison of Convergence Stability Across Regimes (Priority: P3)

**User Journey**: A researcher needs to statistically validate whether the observed difference in convergence stability between "low staleness" and "high staleness" regimes is significant, accounting for random seed variance.

**Why this priority**: This addresses the "Expected results" requirement to perform a two-sample t-test. It ensures the findings are not due to chance and provides the rigorous statistical backing required for the paper.

**Independent Test**: The system can be tested by running a mock dataset with known means and variances for two groups and verifying that the statistical module returns a p-value consistent with the input distribution.

**Acceptance Scenarios**:

1. **Given** two sets of final reward variances (Set A: low staleness, Set B: high staleness) derived from 5 seeds each, **When** the t-test module is executed, **Then** it outputs a p-value and a boolean indicating if the difference is significant at alpha=0.05.
2. **Given** a dataset where the variance of Set B is significantly higher than Set A, **When** the analysis is run, **Then** the output explicitly states "High staleness regime shows statistically significant instability (p < 0.05)".
3. **Given** a dataset with identical means but high variance, **When** the analysis is run, **Then** the output correctly reports a non-significant result, preventing false claims of divergence.

---

### Edge Cases

- **What happens when the model fails to load on CPU?** The system MUST log a specific error code `ERR_CPU_LOAD_FAIL` and abort immediately, rather than hanging or attempting a GPU fallback which is prohibited.
- **How does the system handle extreme staleness?** If `staleness` is set to a value exceeding the queue size (e.g., `staleness > buffer_size`), the system MUST clamp the staleness to `buffer_size - 1` and log a warning, ensuring the queue does not underflow or crash.
- **What happens if the dataset is truncated?** If the GSM8K or SWE-Bench subset is incomplete, the system MUST raise a `DATA_INTEGRITY_ERROR` and stop, rather than training on partial data which would invalidate the statistical power.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load and quantize a sub-1B parameter language model (e.g., Qwen1.5-1.8B) using CPU-only inference primitives to ensure execution on 2-CPU, 7GB RAM runners. (See US-1)
- **FR-002**: System MUST implement a configurable "staleness queue" that delays gradient updates by a user-specified integer number of steps to simulate asynchronous latency. (See US-1)
- **FR-003**: System MUST monitor the reward signal and gradient norm in real-time, flagging a run as "diverged" if the reward drops below a baseline threshold for ≥ 50 consecutive steps. (See US-2)
- **FR-004**: System MUST execute 5 independent training runs per experimental regime (low, high, adaptive staleness) using different random seeds to ensure statistical robustness. (See US-3)
- **FR-005**: System MUST perform a two-sample t-test on the final reward variance between the low-staleness and high-staleness regimes and output the p-value. (See US-3)
- **FR-006**: System MUST validate that the GSM8K test split used for evaluation is strictly independent of the training staleness mechanism and gradient updates. (See US-2)

### Key Entities

- **TrainingRun**: Represents a single execution of the RL loop, containing attributes for `model_id`, `staleness_level`, `seed`, `convergence_status`, and `divergence_point`.
- **StalenessQueue**: A buffer holding delayed gradient updates, defined by `max_size` and `current_delay`.
- **ConvergenceMetric**: A derived value representing the variance of the reward signal over the last 50 steps, used to determine stability.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Convergence stability (measured as final reward variance) is compared against the baseline synchronous training regime (See US-2).
- **SC-002**: The critical staleness threshold (measured as the maximum integer delay before divergence) is mapped against model parameter count (See US-2).
- **SC-003**: Statistical significance of the stability difference is measured against the alpha=0.05 threshold using a two-sample t-test (See US-3).
- **SC-004**: Memory footprint is measured against the 7 GB RAM constraint to ensure no OOM termination (See US-1).
- **SC-005**: Total runtime per job is measured against the 6-hour limit to ensure feasibility on free-tier CI (See US-1).

## Assumptions

- The HuggingFace `datasets` library can successfully download and preprocess GSM8K and SWE-Bench-lite within the 14 GB disk constraint of the free-tier runner.
- The `bitsandbytes` library supports CPU-only quantization without requiring CUDA, allowing the 1.5B model to fit within 7 GB RAM.
- The "baseline threshold" for divergence is defined as the mean reward of the first 50 steps of a synchronous run, assuming initial stability.
- The relationship between staleness and divergence is monotonic within the tested range (0 to 20 steps), allowing for a clear identification of a "critical threshold."
- The computational cost of the two-sample t-test on 5 data points is negligible compared to the training loop execution time.
- The GitHub Actions free-tier runner provides consistent CPU performance (no significant thermal throttling) across all 5 seed runs.
