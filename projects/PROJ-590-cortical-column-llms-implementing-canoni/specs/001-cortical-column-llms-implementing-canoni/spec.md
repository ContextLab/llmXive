# Feature Specification: Cortical Column LLMs: Implementing Canonical Microcircuits for Universal Computation

**Feature Branch**: `001-cortical-column-llms`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Cortical Column LLMs: Implementing Canonical Microcircuits for Universal Computation"

## User Scenarios & Testing

### User Story 1 - Baseline Transformer Training and Validation (Priority: P1)

A researcher needs to establish a computationally universal baseline using a standard Transformer architecture on a diverse set of synthetic function approximation tasks to serve as the control for subsequent microcircuit comparisons.

**Why this priority**: Without a verified, universal baseline trained under identical resource constraints (CPU-only, <6h), any degradation observed in microcircuit models cannot be attributed to the architectural changes. This establishes the "maximum possible performance" reference point.

**Independent Test**: Can be fully tested by executing the training pipeline on a held-out set of synthetic functions (e.g., Lorenz attractor, Fourier series) and verifying that the baseline model achieves a mean absolute error (MAE) below 0.05 within the 6-hour time limit on 4 CPU cores.

**Acceptance Scenarios**:

1. **Given** a standard Transformer architecture with a parameter count in the hundreds of thousands, **When** trained on [deferred] samples of a chaotic time-series function for 100 epochs on a CPU-only runner (4 cores), **Then** the model must achieve a validation MAE < 0.05 and complete training within 6 hours.
2. **Given** the trained baseline model, **When** evaluated on a statistically independent test set (e.g., synthetic polynomial surfaces), **Then** the model must demonstrate < 10% performance degradation compared to the training set, confirming generalization and functional approximation capability.

---

### User Story 2 - Microcircuit Module Implementation and Integration (Priority: P1)

A researcher needs to implement a parameterized "Cortical Column" module in PyTorch that mimics laminar structure (L2/3, L4, L5, L6) with local excitatory-inhibitory loops and homeostatic scaling, and integrate it into a hybrid network replacing standard MLP/Attention layers.

**Why this priority**: This is the core innovation. The ability to swap standard layers for biologically constrained modules while maintaining parameter count parity is the prerequisite for the ablation study and trade-off analysis.

**Independent Test**: Can be fully tested by instantiating the microcircuit module, verifying its internal connectivity matrix matches the specified laminar topology (e.g., L4 excitatory to L2/3 inhibitory), and confirming it can be forward-passed through the hybrid network without shape mismatches or execution errors on a CPU runner.

**Acceptance Scenarios**:

1. **Given** the parameterized microcircuit module definition, **When** initialized with standard weight distributions, **Then** the module must enforce a fixed excitatory-inhibitory ratio of 4:1 (approximating cortical balance) throughout training via homeostatic scaling, and prevent any connection weights from exceeding [-1.0, 1.0] during initialization.
2. **Given** a hybrid network architecture, **When** replacing a standard Transformer MLP layer with the microcircuit module, **Then** the total parameter count must remain within ±1% of the baseline model, and the forward pass must execute without execution errors on a CPU runner.

---

### User Story 3 - Ablation and Scaling Law Analysis (Priority: P2)

A researcher needs to run a systematic ablation study where specific microcircuit features (e.g., local recurrence, specific layer connections) are removed or modified to identify the minimal architectural features required for universal approximation, and to analyze scaling laws as column count increases.

**Why this priority**: This directly addresses the research question regarding "cost of biological plausibility" and the necessity of specific motifs. It also addresses the reviewer comment regarding scaling laws (Geoffrey West) by quantifying performance vs. column count.

**Independent Test**: Can be fully tested by training three variants (full microcircuit, ablated recurrence, ablated inhibition) and a scaling variant (2x columns) on the same dataset, then comparing their approximation errors and training times to generate the "cost curve."

**Acceptance Scenarios**:

1. **Given** the full microcircuit hybrid model, **When** the local recurrent connections are removed (ablation), **Then** the model must show a statistically significant increase in validation MAE (a two-sample t-test with p-value < 0.05 showing a relative increase > 15%) compared to the full model, indicating recurrence is critical for maintaining approximation efficiency.
2. **Given** a scaling experiment where the number of microcircuit columns is doubled, **When** the model is trained on the same function approximation task, **Then** the system must report the scaling exponent of performance vs. parameter count, and the total training time must remain under the 6-hour limit to confirm CPU feasibility.

---

### Edge Cases

- What happens when the homeostatic scaling mechanism drives weights to zero (vanishing gradients) during early training? The system must implement a gradient clipping threshold with a defined maximum norm to prevent collapse.
- How does the system handle function families that are inherently non-differentiable or discontinuous? The system must report a specific error code or fallback to a "failed approximation" flag rather than crashing the training loop.
- What if the CPU memory limit is exceeded during the scaling experiment? The system must implement a data batching strategy that dynamically reduces batch size to keep memory usage below a safe operational threshold.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a parameterized PyTorch module representing a canonical microcircuit with explicit laminar connectivity (L2/3, L4, L5, L6) and local excitatory-inhibitory loops, replacing standard Transformer MLP layers while maintaining parameter count parity. (See US-002)
- **FR-002**: System MUST enforce a fixed excitatory-inhibitory neuron ratio of 4:1 within the microcircuit module to approximate biological balance, maintained dynamically via homeostatic scaling mechanisms during training. (See US-002)
- **FR-003**: System MUST perform a systematic ablation study by programmatically disabling specific microcircuit features (e.g., local recurrence, specific inter-layer connections) across at least three distinct model variants to assess impact on approximation efficiency. (See US-003)
- **FR-004**: System MUST execute training and evaluation on a CPU-only environment (no CUDA/GPU) using a maximum of 4 CPU cores and 7 GB RAM, completing all experiments within a 6-hour time window, verified via /usr/bin/time -v for peak RSS memory and taskset for CPU core pinning. (See US-001)
- **FR-005**: System MUST generate a "cost of biological plausibility" curve quantifying the trade-off between approximation error (MAE) and the degree of biological constraint (e.g., presence of recurrence, inhibition ratio). (See US-003)
- **FR-006**: System MUST validate "functional approximation capability" claims using a held-out test set generated from a statistically independent distribution (e.g., training on chaotic Lorenz systems, testing on synthetic polynomial surfaces) to prevent overfitting artifacts. (See US-001)
- **FR-007**: System MUST implement a homeostatic scaling mechanism based on activity-dependent principles (e.g., synaptic scaling) to maintain stable learning dynamics in the rate-based hybrid model. (See US-002)
- **FR-008**: System MUST perform a scaling law analysis by varying the number of microcircuit columns (e.g., 1x, 2x, 4x) and measuring the resulting change in performance and resource consumption. (See US-003)

### Key Entities

- **MicrocircuitModule**: A PyTorch `nn.Module` representing the canonical cortical column, containing sub-layers for specific laminae and defined connectivity masks.
- **FunctionBenchmark**: A dataset generator producing synthetic high-dimensional non-linear functions (e.g., Lorenz, Fourier, polynomial) for training and testing.
- **AblationVariant**: A configuration object defining which specific microcircuit features are disabled for a specific experimental run.
- **ScalingExperiment**: A configuration object defining the number of microcircuit columns and the resulting parameter count for scaling analysis.

## Success Criteria

### Measurable Outcomes

> Design constraints (sample size, time limits, thresholds) are fixed requirements. Observed empirical values (actual MAE, actual training time) are measured and deferred to the report.

- **SC-001**: Approximation error (MAE) of the microcircuit hybrid model is measured against the baseline Transformer model on the same held-out test set to quantify the "cost of biological plausibility." (See US-001, US-003)
- **SC-002**: Training stability (presence of vanishing/exploding gradients) is measured against the baseline model's gradient norm distribution to verify the efficacy of the homeostatic scaling mechanism. (See US-002)
- **SC-003**: Performance degradation (relative % increase in MAE) of ablated models is measured against the full microcircuit model to identify critical structural motifs. (See US-003)
- **SC-004**: Scaling exponent of approximation performance (MAE) vs. parameter count is measured across the scaling experiment variants to determine if performance scales linearly or sublinearly with column count. (See US-003)
- **SC-005**: Computational feasibility is measured by verifying total wall-clock training time for the largest configuration remains < 6 hours on the specified CPU-only runner. (See US-001)

## Assumptions

- The pre-trained baseline Transformer (e.g., from HuggingFace) can be loaded and adapted for function approximation tasks without requiring GPU acceleration for the initial weight loading or fine-tuning.
- The synthetic function generation scripts (e.g., Lorenz, Fourier) can produce datasets of sufficient size (N = 10,000) to train the models within the 6-hour limit while fitting in GB RAM.
- The "canonical microcircuit" topology can be approximated using rate-based neurons in PyTorch rather than requiring a full spiking neural network (SNN) framework, as SNN training on CPU is computationally prohibitive for this scope.
- The homeostatic scaling mechanism described in the spiking model can be adapted to a rate-based continuous domain without losing its stabilizing properties.
- The GitHub Actions free-tier runner (standard CPU, 7 GB RAM) will not experience significant resource contention that exceeds the 6-hour job timeout.
- The "functional approximation capability" of the baseline Transformer is assumed to hold for the specific synthetic function families chosen, serving as a valid upper bound for comparison.