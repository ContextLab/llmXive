# Research: Astrocyte-Inspired Meta-Learning: Glial Modulation of Neural Networks

## 1. Scientific Background

### 1.1 The Stability-Plasticity Dilemma
In meta-learning, models must adapt quickly to new tasks (plasticity) while retaining knowledge from previous tasks (stability). Standard MAML (Model-Agnostic Meta-Learning) often suffers from catastrophic forgetting when the task distribution shifts, as the inner-loop updates optimize for the current task at the expense of historical performance.

### 1.2 Astrocytic Homeostasis
Astrocytes in the brain regulate synaptic strength through calcium signaling. The Polykretis et al. (2018) model proposes that astrocytes integrate presynaptic activity over time to release gliotransmitters that modulate synaptic efficacy. This biological mechanism suggests a natural homeostatic control loop: high activity triggers a reduction in learning rate (stability), while low activity allows for faster adaptation (plasticity).

### 1.3 The Proposed Mechanism
We implement a differentiable approximation of the calcium-wave ODE. The homeostatic factor $h_t$ is computed as:
$$ h_t = \sigma(Ca_t) $$
where $Ca_t$ is the simulated calcium concentration derived from current and historical task activations. This factor multiplicatively scales the learning rate $\alpha$ in the MAML inner loop:
$$ \theta' = \theta - h_t \cdot \alpha \cdot \nabla_\theta \mathcal{L} $$

## 2. Dataset Strategy

### 2.1 Primary Datasets
The study relies on two standard few-shot learning benchmarks:
1.  **Omniglot**: A dataset of 1623 handwritten characters from 50 different alphabets. Ideal for testing rapid adaptation due to high similarity between characters.
2.  **Mini-ImageNet**: A subset of ImageNet with 100 classes, 600 images each. Used to test robustness on more complex, natural image distributions.

### 2.2 Verified Sources & Loading Strategy
Per the project's "Verified datasets" list and the requirement to cite only verified URLs:

| Dataset | Source | Loading Method | Notes |
| :--- | :--- | :--- | :--- |
| **Omniglot** | `torchvision.datasets.Omniglot` | `torchvision` loader | Standard library. No URL fabricated. |
| **Mini-ImageNet** | Canonical Split (ImageNet) | Custom Loader / `torchvision` | **No verified URL in list**. Implementation must define the canonical split procedure (e.g., `lukaemon` split) explicitly in code to ensure reproducibility. If a verified URL is unavailable, the code must fetch the raw ImageNet split and apply the canonical partition. |

**Decision**: We will use `torchvision.datasets.Omniglot` for Omniglot. For Mini-ImageNet, we will implement a loader that fetches the canonical split (e.g., the `lukaemon` split definition) from a verified source or defines the split procedure explicitly in code. We will **not** rely on a third-party HuggingFace repo without a verified URL.

### 2.3 Dataset Fit & Variable Verification
- **Omniglot**: Contains images and labels. Sufficient for 5-way 1-shot classification. No external variables (e.g., cognitive state) are needed.
- **Mini-ImageNet**: Contains images and labels. Sufficient for the task.
- **Fit**: The datasets contain the required variables (images, labels). No mismatch exists.

## 3. Methodological Rigor

### 3.1 Statistical Plan
- **Test**: **Non-Parametric Permutation Test** (10,000 permutations).
- **Null Hypothesis**: The joint distribution of [Stability, Plasticity] vectors is identical between the Astrocyte-MAML and Vanilla MAML.
- **Test Statistic**: Euclidean distance between the mean vectors of the two groups in the (Stability, Plasticity) space.
- **Significance Level**: $\alpha = 0.05$.
- **Sample Size**: 5 independent random seeds.
- **Power Justification**: With n=5, parametric tests (Hotelling's T-squared, t-test) are invalid due to singular covariance matrices and low power. The Permutation Test is the only valid method for this sample size.
- **Fallback Strategy**: If fewer than 5 seeds complete, the analysis will be aborted and reported as "Insufficient Seeds". The test will not be run with n < 5.

### 3.2 Multiple Comparison Correction
Since we are running a single multivariate test per seed set (comparing two models), no family-wise error correction is needed for the primary hypothesis. However, if ablation studies (Sensitivity Analysis) involve multiple pairwise comparisons (e.g., Astrocyte vs Baseline for each scale parameter), a Bonferroni correction will be applied to the p-values.

### 3.3 Causal Inference & Assumptions
- **Observational**: The study is computational; "causality" here refers to the causal effect of the homeostatic module on the metrics.
- **Identification**: The random assignment of seeds and the controlled experimental setup (same architecture, same data) allow us to attribute differences in metrics to the homeostatic module.
- **Collinearity**: The stability and plasticity metrics are inversely related by definition (trade-off). We treat them as a joint vector to capture the trade-off, rather than claiming independent effects of one over the other.

### 3.4 Measurement Validity & Disjoint Buffer Strategy
To address the tautology concern (where the outcome is a deterministic function of the predictor), the plan implements a **Disjoint Buffer Strategy**:
- **Calcium History**: The Calcium ODE uses activation history from episodes $t-k$ to the most recent preceding time step.
- **Stability Buffer**: The Stability metric is calculated on a **Meta-Test Buffer** consisting of the last 5 completed tasks that were **explicitly excluded** from the Calcium ODE's history calculation for the current step.
- **Independence**: By ensuring the Stability Buffer episodes are not part of the Calcium history used to compute $h_t$ for the current episode, the stability metric becomes an independent measure of generalization, breaking the circular dependency.
- **Validation**: These metrics are standard in the MAML literature, with the added rigor of the disjoint buffer.

## 4. Compute Feasibility & Constraints

### 4.1 Hardware Constraints
- **Runner**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, No GPU).
- **Memory**: 7 GB RAM is tight for Mini-ImageNet.
  - **Strategy**: Use `torchvision` transforms to resize images to a standardized resolution (standard for Mini-ImageNet) and load images on-the-fly (no pre-loading all data).
  - **Subset**: **Mandatory**: Mini-ImageNet will be subsetted to **50 classes** if memory is exceeded. DataLoader will use `num_workers=0`, `pin_memory=False`, and `batch_size=1` for inner-loop steps to minimize overhead.
- **Time**: 6 hours limit.
  - **Strategy**: Run 5 seeds on Omniglot (fast) and 5 seeds on a subset of Mini-ImageNet (50 classes). **Critical**: If fewer than 5 seeds complete successfully for Mini-ImageNet, the statistical analysis phase will be **aborted** and reported as "Insufficient Seeds for Statistical Validation" rather than proceeding with a statistically invalid test (n < 5).

### 4.2 Library Selection
- **PyTorch**: CPU-only version. No CUDA.
- **scipy**: For permutation test.
- **scikit-learn**: For data handling.
- **datasets**: For HuggingFace dataset loading (if applicable).

### 4.3 Risk Mitigation
- **ODE Divergence**: The calcium ODE solver will clamp $Ca_t$ to $[0, 1]$ and log a warning if divergence is detected.
- **Dataset Download Failure**: Retry logic with exponential backoff (a limited number of attempts).
- **Singular Covariance**: Not applicable due to use of Permutation Test.

## 5. Research Decisions & Rationale

| Decision | Rationale |
| :--- | :--- |
| **Use Permutation Test** | Captures the joint distribution of Stability and Plasticity without assuming a multivariate t-distribution. Mandatory due to n=5 sample size. |
| **Use 5 Seeds** | Balances statistical power with the 6-hour runtime limit on CPU. 5 seeds are a standard minimum in meta-learning literature. |
| **Clamp Calcium to [0, 1]** | Prevents numerical instability in the ODE solver, ensuring the training loop does not crash due to extreme values. |
| **No GPU / CPU Only** | Mandatory for CI feasibility. The ODE and MAML are computationally light enough for CPU if datasets are managed carefully. |
| **Subset Mini-ImageNet if needed** | Ensures the job completes within 6 hours. The scientific validity is maintained as long as the subset is representative. |
| **Abort Analysis if n < 5** | Prevents the execution of a statistically invalid test (n < 5) and ensures only valid results are reported. |
| **Disjoint Buffer Strategy** | Ensures the stability metric is independent of the calcium history, breaking the tautology of the validation. |

## 6. Dataset Strategy (Summary Table)

| Dataset | Source (Verified) | Loader | Variables Needed | Fit Check |
| :--- | :--- | :--- | :--- | :--- |
| **Omniglot** | `torchvision` | `torchvision.datasets.Omniglot` | Images, Labels | **PASS**: Contains required variables. |
| **Mini-ImageNet** | Canonical Split (ImageNet) | Custom Loader | Images, Labels | **PASS**: Contains required variables. **Note**: Implementation must define the split procedure explicitly. |

*Note: As per the "Verified datasets" constraint, no URLs are fabricated for Mini-ImageNet as they are not in the provided list. We rely on standard, stable loaders or explicit split definitions.*