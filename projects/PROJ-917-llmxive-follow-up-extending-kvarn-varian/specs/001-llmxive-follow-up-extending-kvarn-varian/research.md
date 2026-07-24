# Research: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

## Research Question

To what extent is the mapping from input attention statistics (mean, variance) to optimal variance-normalization scaling factors learnable via static priors, and what are the fundamental trade-offs between the accuracy of this approximation and the elimination of iterative optimization in long-horizon autoregressive generation?

## Methodology

### 1. Data Generation Strategy (Addressing FR-001, US-1)

We generate a synthetic dataset of attention matrices ($128 \times 128$) to simulate diverse attention patterns.
- **Distribution**: Matrices are sampled from a mixture of Gaussians to control sparsity and outlier magnitudes.
- **Parameters**:
  - Sparsity levels: Uniformly sampled from $[0.1, 0.9]$.
  - Outlier magnitudes: Scaled by factors $[0.5, 2.0]$ of the base variance.
  - **Distributional Assumption**: To better approximate real attention distributions, the mixture includes heavy-tailed outliers (power-law components) alongside Gaussian components.
  - Variance normalization: $\epsilon = 1e-6$ floor applied to prevent division by zero (Edge Case 1).
- **Ground Truth**: For each matrix $A$, the optimal scaling factor $s^*$ is computed using the **KVarN Sinkhorn solver**.
  - *Note*: KVarN is an iterative algorithm. We implement a CPU-optimized version with early stopping criteria (tolerance=1e-4, max_iter=50) to ensure feasibility within the 6-hour CI limit.
  - *Verification*: We verify that the generated $s^*$ distribution aligns with the "high-variance vs. low-variance" simulation parameters.
  - *Edge Case*: Non-convergent matrices are flagged and excluded from the training set.

### 2. Model Architecture & Training (Addressing FR-002, US-2)

We train a lightweight **2-layer Multi-Layer Perceptron (MLP)** to approximate the mapping $f: (\mu, \sigma^2) \rightarrow s^*$.
- **Inputs**: First two moments of the attention matrix: Mean ($\mu$) and Variance ($\sigma^2$).
  - **Predictor Justification**: While the baseline $s=1/\sigma^2$ is variance-driven, the hypothesis tests if the **mean** provides additional context-dependent information (e.g., bias in the Sinkhorn solution) that variance alone cannot capture. The MLP is trained to minimize MSE; if the mean is redundant, its weights will converge to zero.
  - *Correction*: The spec explicitly mandates using **only** the first two moments. Higher-order moments (skewness, kurtosis) are excluded to strictly adhere to the hypothesis test scope.
- **Architecture**:
  - Input: 2 neurons ($\mu, \sigma^2$).
  - Hidden Layer 1: A moderate number of neurons with ReLU activation.
  - Hidden Layer 2: A hidden layer with a moderate number of neurons and ReLU activation.
  - Output: 1 neuron (predicted scaling factor $s_{pred}$).
- **Loss Function**: Mean Squared Error (MSE) between $s_{pred}$ and $s^*$.
- **Training**:
  - Optimizer: Adam ($lr=1e-3$).
  - Epochs: A sufficient number of training epochs will be determined based on convergence criteria.
  - Hardware: CPU (PyTorch `device='cpu'`).
- **Baseline Comparison**: We compare the MLP's MSE against a closed-form baseline $s_{base} = 1/\sigma^2$ to verify non-trivial learning (FR-009).

### 3. Long-Horizon Simulation (Addressing FR-003, FR-004, US-3)

We simulate an autoregressive decoding loop of a sufficient number of steps to measure error accumulation.
- **Dynamic Data Generation**: Unlike the static training set, the simulation generates **new** attention matrices at each step $t$ using a **DriftModel**.
  - **DriftModel**: A random walk process with bounded variance that evolves the mean and variance of the attention matrix over time, simulating the changing context of autoregressive generation.
  - This ensures the "accumulated KL-divergence" metric measures error propagation over a dynamic process, not a static distribution.
- **Procedure**:
  1. Initialize a synthetic transformer state.
  2. For $t = 1 \dots 1000$:
     - Compute attention matrix $A_t$ via DriftModel.
     - Derive scaling factor:
       - **Static Prior**: $s_t = f(A_t)$ (via trained MLP).
       - **KVarN Baseline**: $s_t = \text{Sinkhorn}(A_t)$ (iterative).
     - Apply normalization and quantization.
     - Compute KL-divergence between the **quantized output distribution** and the **full-precision (unquantized) distribution**.
       - *Clarification*: The "full-precision" reference is the state *before* quantization, ensuring the KL-divergence measures the quantization error, not the scaling error.
     - Accumulate KL-divergence: $KL_{total} = \sum KL_t$.
     - **Fallback**: If the MLP predicts an extreme outlier or fails, fall back to KVarN solver (Edge Case 2).
- **Latency Profiling**: Measure wall-clock time per token for both methods on the same CPU hardware.

### 4. Statistical Analysis (Addressing FR-006, FR-007, FR-008)

- **Seed Strategy**: Multiple independent runs use seeds from a predefined range. Each run generates its own unique set of [deferred] matrices via the DriftModel with a unique seed offset, ensuring statistical independence.
- **Significance Testing**: Perform a **paired t-test** on the final accumulated KL-divergence across 30 independent runs ($n=30$).
  - *Pairing Logic*: Run $i$ (Static Prior) is paired with Run $i$ (KVarN Baseline) using the same random seed.
  - *Hypothesis*: $H_0: \mu_{diff} = 0$ vs $H_1: \mu_{diff} \neq 0$ ($p < 0.05$).
  - *Robustness Check*: If error accumulation is non-stationary, a Wilcoxon signed-rank test will be used as a backup.
- **Sensitivity Analysis**: Sweep $\epsilon$ floor values $[1e-9, 1e-8, 1e-7, 1e-6, 1e-5]$ to validate robustness (FR-007).
- **Theoretical Lower Bound**: Compute the theoretical minimum KL-divergence based on the quantization noise model ($\Delta^2/12$) to avoid circular validation (FR-008).

## Dataset Strategy

| Dataset | Source | Usage | Notes |
| :--- | :--- | :--- | :--- |
| **Synthetic Attention Matrices** | Generated In-Code | Training & Simulation | 10,000 matrices, 128x128. No external URL required. |
| **KVarN Solver** | Internal Implementation | Ground Truth Labeling | CPU-optimized Sinkhorn implementation verified against primary paper. |
| **No External Datasets** | N/A | N/A | Spec strictly limits scope to synthetic data. KVarN paper has no verified public dataset URL. |

## Decision Rationale (Compute Feasibility)

- **CPU-First**: All components (Sinkhorn, MLP, Simulation) are designed for CPU execution.
- **Feasibility Analysis**: 
 - Sinkhorn: A large-scale set of matrices * moderate dimensions * 50 iterations (worst case) * vectorized ops [deferred] on 2-core CPU.
  - Simulation: Multiple runs * a sufficient number of steps * multiple methods ~ 10^6 operations, well within limits.
  - Total estimated runtime: < 4 hours, safely within the 6-hour CI limit.
- **No GPU Required**: The hypothesis does not require fine-tuning large transformers or 8-bit inference. The "GPU escape hatch" is not needed as the CPU form is faithful to the research question.
- **Data Streaming**: Not required as the synthetic dataset (10k matrices) is small enough to fit in memory.

## Risk Mitigation

- **Non-Convergence**: The Sinkhorn solver includes a maximum iteration limit and convergence tolerance. Non-convergent matrices are flagged and excluded from the training set (US-1 Edge Case).
- **Numerical Instability**: An $\epsilon$ floor of $1e-6$ is applied to variance calculations. Sensitivity analysis validates this choice.
- **Outlier Generalization**: The training distribution includes controlled outlier magnitudes and heavy-tailed components to ensure the MLP generalizes to edge cases.
- **Distributional Validity**: The DriftModel includes heavy-tailed components to better approximate real attention distributions, mitigating the risk of synthetic data not generalizing to real scenarios.