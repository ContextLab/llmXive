# Research: Astrocyte-Inspired Meta-Learning: Glial Modulation of Neural Networks

## 1. Scientific Background & Hypothesis

### 1.1 Biological Inspiration
The project draws from **Polykretis et al. (2018)** ("Neural-astrocytic architecture for homeostatic plasticity"), which models astrocyte calcium signaling as a dynamic system regulating neuronal excitability. In biological systems, astrocytes release gliotransmitters in response to calcium waves, modulating synaptic strength to maintain stability (preventing runaway excitation) while allowing plasticity (learning).

### 1.2 The Hypothesis
We hypothesize that injecting a **homeostatic factor** $h_t$, derived from a simulated calcium-wave ODE, into the MAML inner-loop learning rate will improve the **stability-plasticity trade-off** in few-shot meta-learning. Specifically, the modulated model should exhibit:
1.  **Higher Stability**: Reduced catastrophic forgetting of tasks in the Meta-Test Buffer (N-1, N-2, N-3).
2.  **Preserved Plasticity**: Comparable or improved adaptation speed on the current task (N) at 1, 5, and 10 inner-loop steps.

### 1.3 Mathematical Formulation
The core mechanism is defined as follows (per FR-001):
*   **Calcium ODE**: $dCa_t/dt = -\alpha \cdot Ca_t + \beta \cdot A_t + \gamma \cdot \text{Buffer}(A_{t-k})$, where $A_t$ is the current task activation signal and $\text{Buffer}$ represents task-history memory (excluding tasks N-1 and N).
*   **Homeostatic Factor**: $h_t = \exp(-\lambda \cdot Ca_t)$, where $\lambda$ is a scaling parameter.
*   **Modulated Update**: $\theta' = \theta - h_t \cdot \alpha_{inner} \cdot \nabla_\theta \mathcal{L}_{support}$.

### 1.4 Buffer Independence (Preventing Circular Validation)
- **Calcium History Buffer**: Contains activation signals from tasks N-2, N-3, and earlier. **Explicitly excludes** tasks N-1 and N.
- **Meta-Test Buffer for Stability**: Contains query sets from tasks N-1, N-2, N-3. **Separate from** calcium history buffer.
- **Rationale**: This separation ensures $h_t$ is independent of the Stability metric (N-1) and the current task activation (N), breaking potential tautological loops and ensuring the mechanism is an emergent property, not a mathematical artifact.

## 2. Dataset Strategy

The study requires image classification datasets suitable for few-shot learning (N-way 1-shot).

| Dataset | Purpose | Source / Loader | Verification Status | Feasibility |
| :--- | :--- | :--- | :--- | :--- |
| **Omniglot** | Primary benchmark for few-shot learning. High number of classes, low sample count per class. | `torchvision.datasets.Omniglot` (built-in) | **Verified**: Stable, CPU-compatible, standard in MAML literature. | **YES**: 28×28 grayscale, ~500 MB for 100 episodes/seed, fits in CI. |
| **Mini-ImageNet** | Secondary benchmark for scalability and complexity. | Standard split (not available in verified datasets block; ImageNet-1K is a different dataset). | **NOT VERIFIED**: The verified block lists ImageNet-1K (1M images, 1000 classes), not Mini-ImageNet (a large-scale dataset of images across 100 classes). These are incompatible datasets. | **NO**: 84×84 RGB, even 10-class subset ≈ 2–3 GB; exceeds CI RAM and time limits. |

**Dataset Variable Fit**:
*   **Required Variables**: Images (grayscale for Omniglot, RGB for Mini-ImageNet), Labels (class IDs).
*   **Fit Check (Omniglot)**: Omniglot provides raw images and labels sufficient for the 5-way 1-shot task. No external variables (e.g., cognitive state) are needed as the study is purely algorithmic.
*   **Fit Check (Mini-ImageNet)**: Not applicable for CI validation due to feasibility constraints.

**Decision & Spec Gap**:
- **Primary Validation**: Omniglot (verified, CPU-feasible).
- **Mini-ImageNet Status**: **DEFERRED** to local/cloud execution. 
- **Spec Gap**: The source spec (FR-004) requires execution on both Omniglot and Mini-ImageNet. However, Mini-ImageNet is **not feasible** on the GitHub Actions free-tier (2 CPU, 7 GB RAM, 6 h limit). 
- **Resolution**: The CI validation is **strictly scoped to Omniglot**. The plan explicitly acknowledges that FR-004's Mini-ImageNet requirement cannot be satisfied in the current CI environment. This is a **blocking feasibility constraint** that requires either a spec amendment to exclude Mini-ImageNet from CI or the provisioning of external resources (local/cloud) for full validation. The hypothesis is validated on Omniglot; Mini-ImageNet is flagged as essential for future full-scale validation.

## 3. Methodology

### 3.1 Training Protocol (Task-Incremental)
1.  **Initialization**: Model weights $\theta$ are initialized. Random seed determines task sequence and model initialization.
2.  **Task Sequence**: Tasks $T_1, T_2, \dots, T_N$ are presented sequentially in a fixed, deterministic order (seeded by the random seed).
3.  **Inner Loop (Per Task $T_i$)**:
    *   Sample Support Set ($S$) and Query Set ($Q$) for $T_i$.
    *   Compute meta-gradient $\nabla_\theta \mathcal{L}_{S}$.
    *   **Retrieve Calcium History Buffer**: Activation signals from tasks N-2, N-3, and earlier (EXCLUDING N-1 and N).
    *   Calculate $Ca_t$ using the ODE module (incorporating $S$ activation and history buffer).
    *   Compute $h_t = \exp(-\lambda \cdot Ca_t)$.
    *   Update: $\theta' = \theta - h_t \cdot \alpha_{inner} \cdot \nabla_\theta \mathcal{L}_{S}$.
4.  **Metrics Calculation**:
    *   **Plasticity**: Accuracy on $Q$ of $T_i$ after 1, 5, and 10 inner-loop steps. All three are logged per Constitution Principle VII. Primary metric for statistical test: 5-step value.
    *   **Stability**: Mean accuracy on query sets of tasks $T_{i-1}$, $T_{i-2}$, $T_{i-3}$ (Meta-Test Buffer, held-out from calcium history) after the update for $T_i$. This 3-task buffer reduces task-instance variance while maintaining Task-Incremental regime.
5.  **Iteration**: Repeat for 100 episodes per seed.

### 3.2 Statistical Analysis

#### Unit of Analysis
- **One [Stability, Plasticity] vector per seed** (n=5), derived by aggregating all 100 episodes per seed into a single mean pair.
- Episodes within a seed are correlated (same initialization, task sequence); only the 5 seed-level vectors are independent observations.
- This ensures n > p (5 > 2) for test validity.

#### Primary Test: Permutation Test
- **Test**: Non-parametric permutation test on Euclidean distance between mean [Stability, Plasticity] vectors.
- **Vectors**: $\vec{v}_{\text{baseline}} = [\text{mean Stability}_{\text{baseline}}, \text{mean Plasticity}_{\text{baseline}}]$ and $\vec{v}_{\text{astrocyte}} = [\text{mean Stability}_{\text{astrocyte}}, \text{mean Plasticity}_{\text{astrocyte}}]$ for each of the 5 seeds.
- **Null Hypothesis**: No difference in the joint distribution of [Stability, Plasticity] between Baseline and Astrocyte models.
- **Test Statistic**: Euclidean distance: $D = \sqrt{(\Delta \text{Stability})^2 + (\Delta \text{Plasticity})^2}$.
- **Permutations**: 10,000.
- **Rationale**: Permutation tests are non-parametric, robust to small N, do not require covariance matrix inversion, and do not assume multivariate normality. With N=5, this is more reliable than Hotelling's T-squared.

#### Secondary Test: Hotelling's T-squared (Reference)
- **Test**: Hotelling's T-squared statistic (implemented via scipy.stats.f or custom NumPy).
- **Formula**: $T^2 = n \cdot (\vec{\mu}_1 - \vec{\mu}_2)^T \cdot S^{-1} \cdot (\vec{\mu}_1 - \vec{\mu}_2)$, where $S$ is the pooled covariance matrix.
- **Degrees of Freedom**: df = n - p - 1 = 5 - 2 - 1 = 2.
- **Power**: Approximately 0.60–0.70 for large effects (Cohen's d ≥ 0.8), below the 0.80 threshold.
- **Covariance Singularity**: If singular, apply ridge penalty (λ=1e-4); if still singular, report "undefined".
- **Status**: Secondary reference; not the primary test due to low power with N=5.

#### Power Analysis
- **Study Type**: Exploratory validation due to N=5 constraint.
- **Minimum Detectable Effect Size**: Cohen's d ≥ 0.8 (large effect), assumed from the biological hypothesis of homeostatic plasticity.
- **Pre-Study Power**: With N=5 and p=2, estimated power ≈ 0.60–0.70 for Hotelling's T-squared; permutation tests are more robust but still limited by N.
- **Post-hoc Power**: After results, calculate actual power using observed effect size.
- **Inconclusive Verdict**: If power < 0.80 is confirmed, report:
  - `verdict: 'inconclusive'`
  - `reason: 'insufficient_power'`
  - `confidence_interval: null`
  - `n_seeds: 5`

#### Ablation & Sensitivity
- **Sweep Parameters**: $\lambda \in \{0.01, 0.05, 0.1\}$ (default community-standard range for homeostatic scale factors).
- **Constant Homeostatic Mode**: Replace dynamic calcium ODE with fixed $h_t = 1.0$ to isolate the effect of dynamic signaling.
- **Reporting**: Summary table showing [Stability, Plasticity] for each parameter value and mode.

### 3.3 Type I vs Type II Error Trade-off
- **Permutation Test**: Controls Type I error (false positive) via exact p-value computation; robust to small N but has lower power (Type II error risk).
- **Justification**: With N=5, controlling Type I error (avoiding spurious claims of improvement) is prioritized over maximizing power to detect real effects. The exploratory nature of the study acknowledges this trade-off.

## 4. Compute Feasibility Plan

### Hardware Constraints
- **GitHub Actions Free-tier**: 2 CPU cores, 7 GB RAM, ~14 GB disk, ≤6 h per job, NO GPU.

### Dataset & Memory Strategy
- **Omniglot**: Primary dataset. 28×28 grayscale images.
  - **Memory Estimate**: ~500 MB for 100 episodes per seed (5 seeds ≈ 2.5 GB total with overhead).
  - **Feasible**: YES, within 6 hours on CPU.
- **Mini-ImageNet**: Secondary dataset. 84×84 RGB images.
  - **Memory Estimate**: Full dataset ≈ several GB; even 10-class subset ≈ 2–3 GB.
  - **Feasible**: NO, exceeds CI RAM limit and 6-hour time constraint.
  - **Status**: **DEFERRED** to local/cloud execution. **Spec Gap**: FR-004 requires Mini-ImageNet, but CI cannot support it. The plan executes **only** on Omniglot for CI validation. Mini-ImageNet is flagged as essential for future full-scale validation on local/cloud resources.

### ODE Solver
- **Implementation**: Custom Euler integration in PyTorch (no external `scipy.integrate` dependency for the ODE itself).
- **Differentiability**: All operations use `torch.autograd` for gradient computation.
- **Clamping**: Calcium concentration $Ca_t$ clamped to [0, 1] to prevent divergence.

### Validation Subset
- **Episodes per Seed**: 100 (sufficient for statistical significance testing with 5 seeds; full-scale runs use [deferred] episodes on local/cloud resources).
- **Total Runtime**: Estimated 3–4 hours on 2 CPUs for 5 seeds (100 episodes each).
- **Disk Usage**: ~2 GB for logs and results.

## 5. Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **ODE Divergence** | Clamp $Ca_t$ to $[0, 1]$. Log warning. |
| **Covariance Singularity** | Apply ridge penalty ($\lambda=1e-4$) in Hotelling's test. If still singular, report "undefined". |
| **Insufficient Power** | Report "inconclusive" with `reason: 'insufficient_power'`, `confidence_interval: null`. Study is exploratory; full-scale validation requires N ≥ 20. |
| **Calcium History Circular Dependency** | Calcium buffer explicitly excludes N-1 and N. Meta-Test Buffer separate from calcium history. |
| **Task-Instance Variance in Stability** | Stability measured as mean over 3-task Meta-Test Buffer (N-1, N-2, N-3) instead of single-task N-1. |
| **Mini-ImageNet Infeasibility** | **Spec Gap**: FR-004 requires Mini-ImageNet, but CI cannot support it. **Mitigation**: Execute **only** on Omniglot for CI. Flag Mini-ImageNet as "Deferred to Local/Cloud" in all reports. Do not claim CI validation on Mini-ImageNet. |

## 6. Decision Rationale

### Why Permutation Test as Primary?
Hotelling's T-squared with N=5 has degrees of freedom df=2 and low power. Permutation tests are non-parametric, robust to small N, and do not require covariance matrix inversion. This is the recommended approach for exploratory studies with limited samples.

### Why 3-Task Buffer for Stability?
Single-task Stability (N-1 only) is high-variance and sensitive to task difficulty. Averaging over N-1, N-2, N-3 reduces variance while maintaining the Task-Incremental regime and preventing the buffer from including the current task N.

### Why Omniglot Only for CI?
Mini-ImageNet (84×84 RGB) with Task-Incremental regime (retaining query sets in memory) exceeds the GitHub Actions free-tier RAM and time limits. Omniglot (28×28 grayscale) is CPU-feasible and sufficient for validating the core hypothesis. Mini-ImageNet is flagged as essential for future full-scale validation on local/cloud resources. **Spec Gap Note**: The requirement in FR-004 for Mini-ImageNet is acknowledged but cannot be met in the current CI environment; it is deferred to external execution.