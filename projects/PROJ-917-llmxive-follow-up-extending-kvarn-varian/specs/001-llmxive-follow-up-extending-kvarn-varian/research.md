# Research: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

## Problem Statement

The KVarN method uses an iterative Sinkhorn optimization step to compute variance-normalization scaling factors for KV-cache quantization, which mitigates error accumulation in long-horizon autoregressive generation. This research investigates whether the mapping from input attention statistics (mean, variance) to these optimal scaling factors is learnable via a static prior (a lightweight MLP). The core question is: *To what extent can a static prior approximate the iterative Sinkhorn solution, and what are the trade-offs between accuracy (accumulated KL-divergence) and latency (per-token time) in a [deferred]-step generation scenario?*

## Methodology

### 1. Data Generation (US-1, FR-001)
- **Source**: Synthetic generation. No external dataset is used.
- **Process**:
  - Generate 10,000 synthetic attention matrices (128x128).
  - Parameters: Controlled sparsity (0.1, 0.5, 0.9), outlier magnitudes (1x, 5x, 10x), and variance levels (high, low).
  - **Ground Truth**: Compute optimal scaling factors using the KVarN Sinkhorn optimizer for each matrix.
  - **Output**: JSONL file containing `attention_matrix_moments` (mean, variance) and `optimal_scaling_factor`.
- **Feasibility**: [deferred] matrices of 128x128 fit comfortably in ~7 GB RAM (each matrix of moderate size in float32, total substantial raw data, plus overhead for moments and labels).
- **Construct Validity**: For the specific objective of **variance normalization** in KVarN, the optimal scaling factor is theoretically a function of the first two moments (mean and variance) alone. The Sinkhorn solver in KVarN targets variance matching; thus, higher-order moments (skewness, kurtosis) or spatial structure (outlier locations) are redundant for this specific constraint. This justifies the 2-feature input and avoids model under-specification.

### 2. Model Training (US-2, FR-002)
- **Model**: 2-layer MLP (Input: 2 features [mean, variance] -> Hidden: a hidden layer -> Output: a single feature [scaling factor]).
- **Theoretical Justification**: For the specific objective of **variance normalization** in KVarN, the optimal scaling factor is theoretically a function of the first two moments (mean and variance) alone. The Sinkhorn solver in KVarN targets variance matching; thus, higher-order moments (skewness, kurtosis) or spatial structure (outlier locations) are redundant for this specific constraint. This justifies the 2-feature input and avoids model under-specification.
- **Training**:
  - Loss: Mean Squared Error (MSE).
  - Optimizer: Adam.
  - Epochs: A sufficient number of training iterations will be determined during the implementation phase to ensure model convergence.
  - Split: A standard majority-minority train-test split.
- **Baseline**: Closed-form `s = 1/variance` (FR-009).
- **Success Metric**: Test MSE < 2x baseline MSE (SC-006).

### 3. Simulation & Evaluation (US-3, FR-003-006)
- **Simulation**: A multi-step autoregressive loop.
  - **Baseline**: Iterative Sinkhorn at each step.
  - **Proposed**: Static prior (MLP) at each step.
- **Quantization Scheme**: **Uniform INT8 Quantization** with symmetric range centered on the mean.
  - This defines the specific mechanism to induce quantization error.
- **Metric**: **Accumulated KL-divergence** between the full-precision distribution and the quantized distribution at each step.
  - The KL-divergence is calculated based on the analytical noise model of the defined quantization scheme, ensuring the metric is well-defined and causally linked to the scaling factor.
- **Statistical Validation**:
  - 30 independent runs (n=30) to ensure statistical power (Source: arXiv:1509.09174).
  - Paired t-test on final accumulated KL-divergence (p < 0.05) (FR-006, SC-004).

### 4. Theoretical Validation (FR-008, SC-002)
- **Theoretical Lower Bound**: Calculate the analytical lower bound of KL-divergence based on the uniform quantization noise model.
  - This bound represents the minimum possible error for the given quantization scheme, serving as an **independent ground truth**.
  - **Calculation**: Derived from the minimum possible error for the given quantization scheme (Uniform INT8), based on the variance of the quantization noise (step size squared divided by a constant factor).
- **Two-Tier Validation**:
  - **Tier 1**: Compare static prior vs. KVarN baseline (standard comparison).
  - **Tier 2**: Compare both methods against the **Theoretical Lower Bound**.
  - This breaks the circular validation loop by validating the static prior against an independent physical bound, not just the KVarN solver's internal consistency.

### 5. Robustness & Sensitivity (FR-007)
- **Sensitivity Analysis**: Sweep epsilon floor values across a range of small magnitudes. and measure impact on accumulated KL-divergence.
- **Edge Case Handling**:
  - Near-zero variance: Apply epsilon floor before normalization.
  - Outliers: Ensure MLP generalizes or falls back to KVarN (graceful degradation).

## Dataset Strategy

| Dataset Name | Source/URL | Access Method | Justification |
|--------------|------------|---------------|---------------|
| **Synthetic Attention Matrices** | N/A (Generated) | `code/data_generation/synthetic_matrix_generator.py` | No external dataset exists for "optimal KVarN scaling factors." Synthetic generation allows controlled experimentation with sparsity, outliers, and variance levels required to test the learning hypothesis. |
| **KVarN Sinkhorn Solver** | N/A (NO verified source) | `code/data_generation/sinkhorn_solver.py` | The KVarN algorithm is implemented from the methodology described in the parent project. No external dataset URL is available or needed for the solver itself. |

> **Note**: The "Verified datasets" block indicates "KVarN: NO verified source found." This project relies on **synthetic data generation** and **algorithmic implementation** of the KVarN Sinkhorn step, not an external dataset download. This is the only feasible approach given the lack of a public dataset for "optimal scaling factors."

## Theoretical Background & Citations

- **KVarN Methodology**: The variance-normalization and Sinkhorn optimization steps are derived from the KVarN paper (parent project). The implementation will follow the described algorithm.
- **Statistical Power (n=30)**: The requirement for 30 independent runs is based on standard statistical power analysis for paired t-tests in computational experiments, as referenced in arXiv:1509.09174 (Source: "batch generate independent must run runner simulation = 30").
- **KL-Divergence in Quantization**: The use of KL-divergence to measure quantization error is standard in quantization literature (e.g., QAT, AWQ). The specific analytical noise model for Uniform INT8 is derived from standard quantization theory.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Sinkhorn Solver Non-Convergence** | Data generation fails; missing labels. | Implement retry logic with max iterations; skip/flag non-convergent matrices; verify convergence rate in `research.md`. |
| **MLP Overfitting** | Poor generalization to unseen attention matrices. | Use early stopping; monitor train/test gap; keep model simple (2-layer MLP). |
| **Accumulated Error Divergence** | Static prior fails in long-horizon simulation. | Implement fallback to KVarN if error exceeds threshold; analyze error accumulation patterns. |
| **CPU Time Limit Exceeded** | A large number of runs of extended steps exceed the 6h CI limit. | Profile single run; optimize vectorized operations; if needed, reduce step count (e.g., 500 steps) and note power limitation. |
| **Circular Validation** | Study only proves MLP mimics Sinkhorn. | **Tier 2 Validation**: Compare against independent Theoretical Lower Bound (FR-008). |

## Decision Rationale

- **CPU-First**: The entire pipeline (synthetic generation, MLP training, 1,000-step simulation) is designed to run on CPU. The Sinkhorn solver and MLP are lightweight; no GPU is required. This aligns with the GitHub Actions free-tier constraints.
- **Synthetic Data**: Since no external dataset provides "optimal KVarN scaling factors," synthetic generation is the only viable path. This allows full control over input distributions (sparsity, outliers) to stress-test the static prior.
- **Statistical Rigor**: The n=30 runs and paired t-test ensure that observed differences in accumulated KL-divergence are statistically significant, not due to random variance.
- **Construct Validity**: The use of mean and variance as inputs is theoretically justified by the variance-matching objective of KVarN, ensuring the learning task is not trivial or under-specified.
- **Independent Ground Truth**: The inclusion of a Theoretical Lower Bound (FR-008) ensures the study validates against a physical ground truth, avoiding circular validation.