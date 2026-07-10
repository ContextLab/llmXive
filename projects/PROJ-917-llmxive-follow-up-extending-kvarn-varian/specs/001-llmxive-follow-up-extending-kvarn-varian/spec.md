# Feature Specification: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

**Feature Branch**: `001-llmxive-kvarn-static-prior`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "To what extent is the mapping from input attention statistics to optimal variance-normalization scaling factors learnable via static priors, and what are the fundamental trade-offs between the accuracy of this approximation and the elimination of iterative optimization in long-horizon autoregressive generation?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Ground-Truth Scaling Factors for Synthetic Attention Blocks (Priority: P1)

The researcher needs to generate a dataset of synthetic attention matrices and compute the "ground truth" optimal scaling factors for each using the original KVarN Sinkhorn optimization step. This establishes the target variable for the learning task and creates the necessary training labels.

**Why this priority**: Without ground truth labels derived from the expensive iterative method, the static prior cannot be trained or evaluated. This is the foundational data generation step.

**Independent Test**: Can be fully tested by running the data generation script on a small subset and verifying that the output file contains valid scaling factors and that the computation time per matrix matches the expected overhead of the Sinkhorn solver.

**Acceptance Scenarios**:

1. **Given** a configuration for attention matrix dimensions (128x128) and sparsity levels, **When** the data generation script is executed, **Then** it produces a JSON/CSV file containing a substantial number of entries, each with the input moments (mean, variance) and the corresponding Sinkhorn-derived optimal scaling factors.
2. **Given** the generated dataset, **When** a validation check is run, **Then** the distribution of scaling factors shows variance consistent with the "high-variance vs. low-variance" block simulation parameters defined in the methodology.

---

### User Story 2 - Train and Evaluate the Static Prior Model (Priority: P2)

The researcher needs to train a lightweight 2-layer MLP on a CPU to map input attention moments to the ground-truth scaling factors, and then evaluate its prediction accuracy (MSE) against a held-out test set.

**Why this priority**: This implements the core hypothesis: that the mapping is learnable. It validates the feasibility of replacing the iterative step with a static inference.

**Independent Test**: Can be fully tested by training the model on the training split and reporting the Mean Squared Error (MSE) on the test split. If the MSE is below a specific threshold (e.g., 0.01), the mapping is considered learnable.

**Acceptance Scenarios**:

1. **Given** the training dataset from User Story 1, **When** the 2-layer MLP is trained for 50 epochs on a CPU, **Then** the training loss converges and the test MSE is recorded.
2. **Given** a held-out set of [deferred] matrices sampled from the training distribution, **When** the trained model predicts scaling factors, **Then** the Mean Squared Error (MSE) on this set does not exceed 2x the MSE of the closed-form baseline (s = 1/variance).

---

### User Story 3 - Simulate Long-Horizon Generation and Measure Latency/Accuracy Trade-off (Priority: P3)

The researcher needs to run a simulated autoregressive generation loop of [deferred] steps, replacing the KVarN optimizer with the trained static prior, and measure both the accumulated KL-divergence and the per-token latency.

**Why this priority**: This provides the final answer to the research question regarding the trade-off between error accumulation and latency reduction in a realistic long-horizon scenario.

**Independent Test**: Can be fully tested by running the simulation loop twice (once with KVarN optimizer, once with static prior) and comparing the final accumulated KL-divergence and average wall-clock time per token.

**Acceptance Scenarios**:

1. **Given** a standard transformer architecture and the static prior model, **When** the 1,000-step simulation completes, **Then** the accumulated KL-divergence is recorded and compared to the KVarN baseline.
2. **Given** the same hardware environment, **When** the latency is profiled, **Then** the per-token latency of the static prior method is measured against the original KVarN method to quantify the reduction in optimization overhead.

### Edge Cases

- What happens when the input attention matrix has near-zero variance (division by zero risk in normalization)? The system MUST handle this by applying a small epsilon floor (e.g., 1e-6) before computing moments.
- How does the system handle attention matrices with extreme outlier magnitudes not present in the training distribution? The static prior MUST either generalize or fail gracefully (e.g., fallback to KVarN) without crashing the simulation.
- What if the Sinkhorn solver fails to converge for a specific synthetic matrix? The data generation step MUST skip or flag these instances rather than producing NaN labels.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST generate 10,000 synthetic attention matrices (128x128) with controlled sparsity and outlier magnitudes, and compute ground-truth scaling factors using the KVarN Sinkhorn optimizer. (See US-1)
- **FR-002**: The system MUST train a multi-layer perceptron (MLP) on a CPU using the first two moments (mean, variance) of input attention matrices to predict the ground-truth scaling factors, minimizing Mean Squared Error. (See US-2)
- **FR-003**: The system MUST simulate an autoregressive decoding loop of [deferred] steps, where the static prior replaces the iterative Sinkhorn optimization for variance normalization. (See US-3)
- **FR-004**: The system MUST measure and record the accumulated KL-divergence between the quantized output distribution and the full-precision distribution at each step of the simulation. (See US-3)
- **FR-005**: The system MUST profile and report the wall-clock time per token for both the static prior method and the original KVarN method on the same CPU hardware. (See US-3)
- **FR-006**: The system MUST perform a paired t-test on the final accumulated KL-divergence (scalar value) across 30 independent runs (n=30) to determine statistical significance (p < 0.05). (See US-3)
- **FR-007**: The system MUST implement a sensitivity analysis that sweeps the epsilon floor for variance normalization over a set of values and reports how the accumulated KL-divergence error rate varies. (See US-2, US-3)
- **FR-008**: The system MUST compute and report the theoretical lower bound of KL-divergence based on the quantization noise model, and measure the static prior's performance against this independent ground truth to avoid circular validation. (See US-3)
- **FR-009**: The system MUST compare the MLP prediction error against a simple closed-form baseline (s = 1/variance) to verify that the learned mapping captures non-trivial, context-dependent relationships beyond the deterministic identity. (See US-2)

### Key Entities

- **AttentionMatrix**: Represents a 128x128 matrix of attention scores, characterized by its mean, variance, sparsity level, and outlier magnitude.
- **ScalingFactor**: A scalar value representing the optimal variance-normalization factor for a specific attention block, derived from the Sinkhorn optimization.
- **SimulationRun**: An instance of the [deferred]-step autoregressive generation, storing the sequence of KL-divergence values and timing metrics.
- **ModelError**: A record of the prediction error (MSE) for a specific attention matrix when using the static prior versus the ground truth.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The prediction accuracy (MSE) of the static prior is measured against the ground-truth scaling factors generated by the KVarN Sinkhorn optimizer. (See FR-002)
- **SC-002**: The accumulated KL-divergence [deferred] steps is measured against the baseline KVarN method, the theoretical lower bound, and standard uniform quantization methods. (See FR-004, FR-008)
- **SC-003**: The per-token latency of the static prior method is measured against the original KVarN method to quantify the reduction in optimization overhead. (See FR-005)
- **SC-004**: The statistical significance of the difference in final accumulated error is measured against a p-value threshold of 0.05 using a paired t-test on 30 independent runs. (See FR-006)
- **SC-005**: The sensitivity of the error rate to the variance floor threshold is measured across a sweep set of representative magnitudes to validate robustness. (See FR-007)
- **SC-006**: The improvement of the MLP over the closed-form baseline (s = 1/variance) is measured to confirm the non-triviality of the learned mapping. (See FR-009)

## Assumptions

- **Assumption about data/environment**: The synthetic dataset generation and the shallow MLP training will fit within the RAM and disk limits of the GitHub Actions free-tier runner without requiring sampling or chunking.
- **Assumption about scope boundaries**: The research is limited to CPU-only execution; no GPU acceleration, CUDA, or 8-bit/4-bit quantization libraries requiring GPU drivers are used.
- **Assumption about target users**: The primary user is a researcher evaluating the feasibility of static priors for KV-cache quantization; the output is a research artifact (spec, code, results) rather than a production API.
- **Assumption about methodological validity**: The relationship between input moments and optimal scaling factors is not deterministic; the study treats the mapping as an empirical learning problem, and the "ground truth" is defined strictly by the KVarN Sinkhorn output.
- **Assumption about threshold justification**: The epsilon floor for variance normalization is set to 1e-6 based on standard numerical stability practices in deep learning, and the sensitivity analysis (FR-007) will verify this choice.
- **Assumption about compute feasibility**: The total compute time for multiple independent simulation runs (each of a sufficient number of steps) will not exceed the time limit per GitHub Actions job.