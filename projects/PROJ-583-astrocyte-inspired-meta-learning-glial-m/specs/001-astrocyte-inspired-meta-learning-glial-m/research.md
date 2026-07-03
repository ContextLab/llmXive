# Research: Astrocyte-Inspired Meta-Learning: Glial Modulation of Neural Networks

## 1. Problem Statement & Hypothesis

**Problem**: Meta-learning algorithms like MAML struggle with the stability-plasticity trade-off: rapid adaptation to new tasks (plasticity) often leads to catastrophic forgetting of previous tasks (stability).
**Hypothesis**: An astrocyte-inspired homeostatic mechanism, modeled via a calcium-wave ODE (Polykretis et al.), can dynamically modulate the learning rate to balance this trade-off, resulting in a statistically significant improvement in Stability and Plasticity compared to vanilla MAML.

## 2. Theoretical Background

### 2.1 The Calcium-Wave ODE (Polykretis et al., 2018)
The core biological mechanism is the intracellular calcium concentration $Ca_t$, which acts as a memory of neural activity.
The ODE formulation (simplified for implementation) is:
$$ \frac{dCa_t}{dt} = -\frac{Ca_t}{\tau} + \alpha \cdot A_t + \beta \cdot \sum_{k=1}^{H} w_k \cdot A_{t-k} $$
Where:
- $A_t$: Current task activation signal (derived from gradient norms or loss).
- $\tau$: Decay time constant.
- $\alpha, \beta$: Scaling parameters.
- $H$: History buffer size (task-history memory).
- **$w_k$ (History Weights)**: **Fixed non-learnable parameters** using an exponential decay kernel $w_k = e^{-k/\tau_{hist}}$ with $\tau_{hist}=5$. These are explicitly **not learnable** to avoid confounding the optimization landscape and to strictly adhere to the biological mechanism (Constitution Principle VI). This ensures the system is a direct translation of the Polykretis model without introducing new optimization variables.

The **homeostatic factor** $h_t$ is derived from $Ca_t$:
$$ h_t = \sigma(\gamma \cdot Ca_t + \delta) $$
Where $\sigma$ is a sigmoid or similar squashing function to bound the factor, ensuring numerical stability. This $h_t$ multiplies the learning rate $\eta$ in the inner loop: $\eta' = h_t \cdot \eta$.

### 2.2 MAML Integration
Standard MAML updates parameters $\theta$ via:
$$ \theta' = \theta - \alpha \nabla_\theta \mathcal{L}_{task}(\theta) $$
Our modification replaces $\alpha$ with $\alpha \cdot h_t$ per layer or globally, depending on the aggregation method of $Ca_t$.

## 3. Dataset Strategy

**Constraint**: Must run on CPU-only GitHub Actions (7GB RAM) and ensure reproducibility (Constitution Principle I).
**Datasets**:
1.  **Omniglot (Primary)**: 1623 characters, A representative number of examples each. Ideal for few-shot (5-way 1-shot) on CPU.
    -   *Source*: `torchvision.datasets.Omniglot` (standard PyTorch loader).
    -   *Feasibility*: High. Low memory footprint.
    -   *Reproducibility*: Fully supported by standard loaders; no external URL fabrication required.
2.  **Mini-ImageNet (Conditional/Deferred)**: 100 classes, A balanced set of images, with an equal number per category..
    -   *Source*: **Deferred**. No verified, reproducible HuggingFace source found in the provided verification block. The plan will default to Omniglot-only for the MVP to ensure reproducibility. If a verified source is identified later, it will be added.
    -   *Feasibility*: **Conditional**. Requires careful batching and potential subsampling to fit 7GB RAM.
    -   *Fairness Constraint*: If used in the future, **both** Baseline and Astrocyte models MUST run on the **exact same** subsampled configuration (same `dataset_seed` for class selection, same resolution). This is non-negotiable to prevent confounding.

**Dataset Variable Fit**:
-   *Variables Required*: Images (RGB/Grayscale), Labels (Class ID).
-   *Fit*: Both Omniglot and Mini-ImageNet provide exactly these. No external cognitive variables are needed (per Spec Assumption).

## 4. Statistical Methodology

### 4.1 Metrics
-   **Plasticity**: Accuracy on the current task after $k$ inner-loop steps ($k \in \{1, 5, 10\}$).
-   **Stability**: Accuracy on a **Replay Buffer** of $B=5$ previous tasks.
    -   *Buffer Definition*: The 5 most recently completed tasks prior to the current episode.
    -   *Evaluation*: Evaluated on the model parameters **before** the current task's gradient update (pre-update snapshot). This ensures the metric reflects retention of past knowledge independent of the current task's learning trajectory, decoupling it from Plasticity and avoiding circular dependency.

### 4.2 Hypothesis Testing
-   **Test**: **Paired-sample t-tests** (Bonferroni corrected).
    -   *Rationale*: With $n=5$ seeds and $p=2$ dimensions, Hotelling's T-squared test is invalid due to singular covariance matrices ($n-p-1 = 2$ degrees of freedom). We decompose the vector into two univariate tests (one for Stability, one for Plasticity) to ensure statistical validity.
-   **Null Hypothesis ($H_0$)**: The mean Stability (or Plasticity) of the Astrocyte model is equal to the mean of the Vanilla MAML baseline.
-   **Alternative Hypothesis ($H_1$)**: The means differ.
-   **Significance Level**: $\alpha = 0.05$.
-   **Correction**: Bonferroni correction applied for 2 tests (Stability, Plasticity). Adjusted $\alpha = 0.025$.
-   **Power Analysis**: With a limited number of seeds, the test has low power. The plan will report effect sizes (Cohen's $d$) and explicitly state if the result is "inconclusive" due to low sample size, rather than claiming false negatives. This satisfies Constitution Principle VII's "t-test" requirement while addressing the n=5 constraint.

### 4.3 Sensitivity Analysis
-   Sweep homeostatic scale parameters: $\gamma \in$ a range of small positive values.
-   Ablation: Replace ODE with a constant scalar $h_t = 1.0$.

## 5. Compute Feasibility & Rationale

-   **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM, 6h limit).
-   **Strategy**:
    -   **No GPU**: All operations in `torch.float32` on CPU.
    -   **Batching**: Small batch sizes (e.g., 8 or 16) to fit memory.
    -   **Mini-ImageNet**: Deferred until verified source found.
    -   **ODE Solver**: Use `torch.autograd` for a simplified Euler integration or a fixed-step solver to avoid heavy ODE library overhead.
-   **Rationale**: This approach ensures the project reaches `research_complete` without failing due to resource constraints or statistical invalidity.

## 6. Risk Mitigation

-   **Risk**: ODE solver divergence.
    -   *Mitigation*: Clamp $Ca_t \in [0, 1]$ and log warnings.
-   **Risk**: Covariance matrix singularity in statistical tests.
    -   *Mitigation*: Using paired t-tests avoids covariance matrix inversion issues entirely.
-   **Risk**: Dataset download failure.
    -   *Mitigation*: Retry logic (multiple attempts, exponential backoff) as per Spec Edge Cases.
