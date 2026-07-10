# Research: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

## Problem Statement

The KVarN method mitigates error accumulation in KV-cache quantization by using an iterative Sinkhorn optimization step to compute optimal variance-normalization scaling factors for each attention block. While effective, this iterative step introduces significant latency in long-horizon autoregressive generation. This research investigates whether the mapping from input attention statistics (mean, variance, skewness, kurtosis) to these optimal scaling factors is learnable via a static prior (a lightweight 2-layer MLP), thereby eliminating the iterative optimization step without sacrificing accuracy.

Crucially, this research addresses the **long-horizon dynamics** of error accumulation. Unlike previous static analyses, we model the temporal evolution of attention statistics and the feedback loop of quantization noise to ensure the static prior is robust to distribution shifts [deferred]+ steps.

## Dataset Strategy

Since KVarN is a novel method without a pre-existing public dataset of "optimal scaling factors," and the spec requires generating ground truth via the Sinkhorn optimizer, the dataset strategy is **synthetic trajectory generation** augmented by **real-world proxy validation**.

### 1. Synthetic Attention Trajectories (Primary Training Data)
Instead of generating [deferred] independent static matrices, we generate [deferred] **trajectories** (sequences of [deferred] steps).
- **Generation Method**: `code/data_generation/synthetic_attention.py` (Trajectory Mode).
- **Dynamics**: Each trajectory simulates a sequence of attention matrices where variance, sparsity, and higher-order moments (skewness, kurtosis) evolve according to a controlled **drift model**. This drift model mimics the accumulation of quantization noise and the changing attention patterns in autoregressive generation.
- **Ground Truth**: For each step in the trajectory, the "ground truth" scaling factor is computed using a **Sequential Sinkhorn Solver**. This solver maintains a cumulative error state from previous steps, ensuring the ground truth reflects the true long-horizon optimization problem, not just an independent step.
- **Verification**: Verified by checking that the variance drift matches the theoretical noise accumulation model and that the Sequential Sinkhorn solver converges within the step limit.

### 2. Non-Triviality Regimes
To ensure the MLP learns more than the closed-form baseline ($s = 1/\sigma^2$), we explicitly generate "Hard Regimes":
- **High-Order Moment Regimes**: Matrices with controlled skewness and kurtosis (via mixture distributions) where the optimal scaling factor is known to deviate from the variance-only prediction.
- **Verification**: We verify that in these regimes, the closed-form baseline error is significantly higher than the Sinkhorn ground truth, creating a learnable signal for the MLP.

### 3. Real-World Proxy (Validation Data)
To address the "sim-to-sim" domain shift risk:
- **Source**: We will extract attention matrices from a small, public, pre-trained transformer (e.g., `distilbert-base-uncased` or a small LLM) on a fixed dataset (e.g., WikiText-2).
- **Usage**: The trained MLP will be evaluated on these real-world attention maps to test generalization beyond synthetic distributions.
- **Verification**: Verified by checking the distribution of moments against the synthetic training data to quantify the domain shift.

**Note on External Datasets**: The "Verified datasets" block provided no URL for KVarN. The MLP, MSE, and other listed datasets are irrelevant to this specific research task (synthetic attention matrices). Therefore, **no external dataset URLs are cited**. The entire dataset is generated procedurally within the project, with the exception of the Real-World Proxy which uses a standard public model.

## Methodology

### 1. Data Generation: Dynamic Trajectories (FR-001)
- **Input**: Configuration for attention matrix dimensions (128x128), drift parameters, and non-triviality regimes.
- **Process**:
 1. **Trajectory Generation**: Generate a substantial set of sequences of [deferred] steps. At each step $t$, the attention matrix $A_t$ is derived from $A_{t-1}$ plus a noise term that simulates quantization error accumulation.
  2. **Moment Extraction**: Compute mean ($\mu_t$), variance ($\sigma^2_t$), skewness ($\gamma_t$), and kurtosis ($\kappa_t$) for each step.
  3. **Sequential Ground Truth**: Run a **Sequential Sinkhorn Solver** to derive the optimal scaling factor $s^*_t$. This solver updates its internal state based on the quantization error from step $t-1$, modeling the feedback loop.
  4. **Edge Cases**: Apply epsilon floor ($\epsilon = 10^{-6}$) to $\sigma^2_t$. Flag/Skip trajectories where the Sequential Sinkhorn fails to converge.
- **Output**: A Parquet/CSV file containing sequences of $[\mu_t, \sigma^2_t, \gamma_t, \kappa_t, s^*_t]$ tuples.

### 2. Model Training (FR-002, FR-009)
- **Model**: 2-layer Multi-Layer Perceptron (MLP).
  - **Input**: $[\mu_t, \sigma^2_t, \gamma_t, \kappa_t]$ (4 features, to capture non-trivial dependencies).
  - **Hidden layers**: 2 layers with ReLU activation.
  - **Output**: Predicted scaling factor $\hat{s}_t$.
- **Training**:
  - **Loss**: Mean Squared Error (MSE) between $\hat{s}_t$ and $s^*_t$ across the entire trajectory.
  - **Optimizer**: Adam.
  - **Hardware**: CPU-only.
- **Baselines**:
  - **Closed-form**: $s_{closed} = 1 / \sigma^2_t$.
  - **Comparison**: MLP MSE vs. Closed-form MSE (FR-009). We specifically analyze performance in the "High-Order Moment Regimes" to verify the MLP captures non-trivial relationships.

### 3. Simulation & Evaluation (FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-010)
- **Setup**: Simulate an autoregressive decoding loop for [deferred] steps.
- **Methods**:
 1. **KVarN Baseline (Sequential)**: Use the Sequential Sinkhorn optimizer at each step, maintaining cumulative error state.
 2. **Static Prior**: Use the trained MLP to predict $s_t$ at each step.
 3. **Closed-form**: Use $s_t = 1/\sigma^2_t$ at each step.
- **Metrics**:
  - **Accumulated KL-Divergence**: Sum of KL-divergence between quantized and full-precision distributions at each step (FR-004).
  - **Latency**: Wall-clock time per token (FR-005).
  - **Statistical Significance**: Paired t-test on final accumulated KL-divergence across 30 independent runs (FR-006).
  - **Sensitivity Analysis**: Sweep $\epsilon \in \{10^{-8}, 10^{-6}, 10^{-4}\}$ and report error rate variation (FR-007).
  - **Theoretical Lower Bound**: Compute theoretical KL-divergence lower bound based on an **analytical quantization noise model** (independent of Sinkhorn, derived from $\sigma^2_{quant} = \Delta^2/12$) to provide an external ground truth (FR-008).
  - **Real-World Proxy**: Evaluate the Static Prior on attention maps from a public pre-trained model to test generalization (see Dataset Strategy).

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: The simulation compares three methods (KVarN, Static Prior, Closed-form). A Bonferroni correction or similar adjustment will be applied if multiple hypothesis tests are performed on the same data to control family-wise error rate.
- **Sample Size / Power**: The plan specifies 30 independent runs (n=30) for the t-test. This is a standard minimum for robust statistical inference in computational experiments. Power analysis is deferred to the implementation phase if initial variance estimates suggest low power.
- **Causal Inference**: This is a controlled simulation (synthetic data), not an observational study. Causal claims are limited to the causal effect of the method (Static Prior vs. KVarN) on the outcome (KL-divergence/Latency) within the simulation environment.
- **Collinearity**: Input features (mean, variance, skewness, kurtosis) are distinct statistical moments. However, if the distribution of attention matrices implies a deterministic relationship between mean and variance in certain regimes, the plan will report this descriptive relationship rather than claiming independent effects.
- **Compute Feasibility**:
 - **Memory**: [deferred] trajectories (128x128 float32) $\approx 640$ MB (if stored as sequences) or streamed. The Sequential Sinkhorn solver is iterative but operates on single matrices. MLP training is trivial. Simulation of a moderate number of steps is memory-light. Total RAM usage will remain within acceptable system limits.
 - **Time**: [deferred] Sequential Sinkhorn solves (CPU) + Multiple epochs MLP training

The research question remains: How does the number of training epochs affect the convergence and performance of the MLP model?
The method remains: We will train a Multi-Layer Perceptron (MLP) using a standard backpropagation algorithm, varying the number of epochs to evaluate learning curves.
References remain: [Citation preserved as in original source] + 30 runs of [deferred] steps. The Sequential Sinkhorn step is the bottleneck. Optimized NumPy/SciPy implementation is required. If the 6-hour limit is tight, the number of simulation steps or runs may be reduced (documented in `research.md` decision log).

## Decision Log (Deferred)

| Decision | Rationale |
| :--- | :--- |
| **Sequential Sinkhorn Implementation** | Will use `scipy.optimize` with a cumulative error state. If convergence is too slow, a fixed iteration limit will be enforced. |
| **MLP Architecture** | 2-layer MLP with 64 units per layer (default). Will be adjusted if training loss does not converge. |
| **Simulation Steps** | Target a substantial number of steps. If runtime exceeds 6h, will reduce to 500 steps and extrapolate, or reduce n=30 to n=10 (with power analysis note). |
| **Epsilon Floor** | The specific value is set to 1e-6 as a standard numerical stability constant. Sensitivity analysis (FR-007) will determine the optimal value and robustness range. |
| **Real-World Proxy Model** | Will use a small, publicly available model (e.g., `distilbert-base-uncased` or a small LLM) to extract attention maps for validation. |