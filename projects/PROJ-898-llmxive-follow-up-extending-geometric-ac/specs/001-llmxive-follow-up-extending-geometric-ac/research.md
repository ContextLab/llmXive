# Research: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Background & Motivation

The Geometric Action Model (GAM) demonstrates success in robot policy learning by leveraging a Geometric Foundation Model (GFM) to map 3D observations to a latent space. However, its learned causal predictor may fail to generalize to novel object topologies (e.g., variable hinge counts, deformable materials) not seen during training. This project hypothesizes that replacing the neural predictor with a **differentiable symbolic solver operating in the frozen 3D latent space** will enable zero-shot generalization while maintaining inference speed.

## Methodology

### 1. Synthetic Topology-Shift Test Set Generation (FR-001)
To test zero-shot generalization, a synthetic dataset of manipulation tasks is generated using **PyBullet**.
- **Novel Topologies**: Kinematic chains with hinge counts $N \in [3, 10]$ and deformable meshes with varying stiffness ($k \in [0.1, 0.5]$).
- **Process**: Randomized initial states, target zones, and material properties.
- **Validation**: Hash-based uniqueness check. **Retry Logic**: If <50 unique topologies are generated after 10 retries, the system logs a CRITICAL error and **halts** the inference phase to ensure FR-001 compliance.
- **Edge Case Handling**: If generation fails to produce 50 unique topologies, the system logs a critical failure and halts, preventing invalid results.

### 2. Symbolic Latent Planner Execution (FR-002, FR-003, FR-004)
- **GFM Freezing**: Encoder and decoder weights are loaded frozen. No fine-tuning.
- **Symbolic Solver**: A differentiable optimization layer (implemented as a **custom `torch.autograd.Function`** wrapping `scipy.optimize.minimize` with SLSQP) solves for **latent vectors** that satisfy:
  - Latent constraints (velocity limits, distance to target in latent space).
  - **Physical Validation**: The decoded physical action is checked for rigid-body constraints (non-penetration, joint limits). The error from this validation is backpropagated **through the decoder** to the latent solver parameters to verify differentiability (FR-003).
- **Differentiability Verification**: The solver computes gradients of constraint violation loss w.r.t. solver parameters, backpropagating *through* the GFM decoder (which acts as a differentiable map from latent to physical space) to ensure the interface is differentiable.
- **CPU Execution**: All operations (PyBullet simulation, GFM inference, solver optimization) are optimized for CPU. `torch` is used in CPU mode.
- **Convex Relaxation**: Rigid-body contact constraints are approximated using **soft-penalty distance constraints** (convex) in the post-hoc validation loss to ensure tractability on CPU. This is a known approximation in differentiable physics.

### 3. Comparative Statistical Analysis (FR-005, FR-006)
- **Metrics**: 
  - Binary success (task completed vs. failed) – defined as reaching the target zone within 5cm for at least 60 consecutive frames at 60Hz.
  - Inference latency (ms per step).
  - Time-to-Failure (steps survived).
- **Tests**:
  - **Fisher's Exact Test**: For success rates (handles low counts) – reports p-value, Odds Ratio, and **95% Confidence Interval** (Wilson score interval).
  - **Latency Test**: Aggregate per-trial mean latency. Check normality (Shapiro-Wilk). If normal, Paired t-test (mean diff, p-value, Cohen's d). If not, Wilcoxon Signed-Rank (Cliff's Delta).
  - **Survival Analysis**: Kaplan-Meier curves and Log-Rank test for Time-to-Failure.
- **Significance**: $\alpha = 0.05$.

## Dataset Strategy

| Dataset | Source | Access Method | Notes |
|---------|--------|---------------|-------|
| **PyBullet Physics Engine** | `pybullet` (PyPI) | `pip install pybullet` | CPU-based simulator. No external dataset URL. |
| **Geometric Foundation Model (GFM)** | Internal Project (llmXive) | Local weights (`data/raw/gfm_weights.pt`) | Dependency: Weights are expected to be provided by the upstream llmXive project. If not available, the pipeline will fall back to standard normal distribution for drift detection. |
| **Synthetic Topology Test Set** | Generated Locally | `code/generate_topology.py` | Generated on-the-fly; no external download. |
| **Baseline GAM**: Internal Project (llmXive) | Local weights (`data/raw/baseline_gam.pt`) | Assumed accessible per project context. |

**Note**: No external datasets (e.g., ADNI, HCP) are used. The project relies on **synthetic data generation** and **local model weights** to ensure reproducibility on the CI runner.