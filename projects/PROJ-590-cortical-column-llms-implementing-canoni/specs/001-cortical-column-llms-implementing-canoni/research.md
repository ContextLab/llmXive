# Research: Cortical Column LLMs

## 1. Problem Statement & Hypothesis

**Problem**: Standard Transformers are computationally universal but biologically implausible. It is unknown whether the specific laminar structure and excitatory-inhibitory loops of cortical columns impose a significant "cost" on universal approximation capabilities, or if these motifs provide inherent stability/efficiency advantages.

**Hypothesis**: Replacing standard MLP layers with a parameterized cortical column microcircuit will result in a measurable increase in approximation error (MAE) on chaotic time-series tasks, quantifiable as a "cost of biological plausibility" curve. However, the homeostatic scaling mechanism will mitigate training instability compared to un-constrained recurrent networks.

**Scope Refinement**: The claim of "universal approximation" is reframed as **"generalization across distinct dynamical regimes"**. The validation set (Polynomials/Fourier) tests generalization from chaotic to smooth dynamics, but does not constitute a rigorous proof of mathematical universality (approximating *any* continuous function). Future work may include discontinuous or high-frequency functions.

## 2. Dataset Strategy

The project relies on **synthetic function generation** rather than external static datasets to ensure exact control over the data manifold and to satisfy the "Independent Distribution Validation" requirement (Constitution Principle VII).

| Dataset Name | Description | Source/Generation | Verified URL | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Lorenz Attractor** | Chaotic time-series data (3D) generated via numerical integration. | `code/src/data/benchmarks.py` (SciPy `odeint`) | N/A (Synthetic) | Used for **Training**. Represents chaotic, non-linear dynamics. |
| **Fourier Surfaces** | Synthetic 2D/3D surfaces constructed from sum of sinusoids. | `code/src/data/benchmarks.py` (NumPy) | N/A (Synthetic) | Used for **Testing** (Independent distribution). |
| **Polynomial Surfaces** | Synthetic high-degree polynomial functions. | `code/src/data/benchmarks.py` (NumPy) | N/A (Synthetic) | Used for **Testing** (Independent distribution). |

**Rationale for Synthetic Data**:
1.  **Reproducibility**: No external download failures; checksums are deterministic.
2.  **Independence**: Training on chaotic dynamics (Lorenz) and testing on smooth polynomials/Fourier series rigorously tests "generalization across regimes" rather than curve fitting.
3.  **Feasibility**: Generating a large batch of samples takes milliseconds, avoiding I/O bottlenecks on the GitHub Actions runner.

*Note: No verified external URL exists for "FunctionBenchmark" as it is a custom generator defined in the spec. The implementation will strictly use the internal generator.*

## 3. Methodology

### 3.1. Baseline Architecture (Control)
A standard Transformer encoder (no positional encoding, as time-series is handled via input windowing) with:
-   Embedding dimension: 64
-   Attention heads: 4
-   MLP layers: Standard 2-layer feedforward (GELU activation).
-   **Constraint**: Parameter count fixed to $P_{base}$.

### 3.2. Microcircuit Architecture (Experimental)
A hybrid network where the MLP layers of the Transformer are replaced by `MicrocircuitModule` (FR-001).
-   **Laminar Structure**: Explicit sub-layers for L2/3, L4, L5, L6.
-   **Connectivity**: Fixed masks enforcing local E/I loops (L4 Excitatory $\to$ L2/3 Inhibitory $\to$ L5/6).
-   **E/I Ratio**: Enforced via `homeostasis.py` (FR-002) to maintain 4:1 ratio.
-   **Parameter Parity**: The microcircuit module uses a **padding and masking** strategy to match $P_{base} \pm 1\%$. Specifically, if the 4:1 ratio requires a non-integer number of neurons, the layer is padded to the nearest integer, and a binary mask zeros out the "dummy" connections. This ensures parameter count parity while explicitly measuring the cost of the mask (a structural constraint).

### 3.3. Ablation Studies (FR-003)
Three variants will be trained to isolate critical motifs:
1.  **Full Microcircuit**: All laminar connections + Homeostasis.
2.  **Ablated Recurrence**: Local recurrent connections disabled (feedforward only within column).
3.  **Ablated Inhibition**: Inhibitory connections disabled (E-I ratio constraint relaxed).

### 3.4. Scaling Law Analysis (FR-008)
To estimate a scaling exponent, we require at least 3 data points. We will train:
1.  **1x Columns** (Baseline microcircuit width).
2.  **2x Columns** (Double width).
3.  **4x Columns** (Quadruple width).
-   **Metric**: Scaling exponent $\alpha$ where $Performance \propto N^{\alpha}$.
-   **Constraint**: The 4x variant will be run only if the 2x variant completes within 3 hours. If the 4x variant exceeds the 6-hour total budget, the analysis will report a "scaling trend" based on 2 points, explicitly acknowledging the limitation.
-   **Normalization**: Performance will be normalized by parameter count to distinguish between "capacity gains" and "efficiency gains".

### 3.5. Statistical Rigor

#### 3.5.1. Pilot Study & Power Analysis
Before the main experiments, a **Pilot Study** will be conducted with $N=1,000$ samples to estimate the variance ($\sigma^2$) of the MAE difference between the Baseline and Full Microcircuit models.
- **Power Calculation**: Using the observed $\sigma$ from the pilot, we will calculate the required $N$ to achieve [deferred] power ($1-\beta=0.8$) to detect a [deferred] relative MAE increase at $\alpha=0.05$.
- **Adjustment**: If the pilot suggests $N > 10,000$ is needed, we will report the power limitation and proceed with the maximum feasible $N$ ([deferred]), explicitly stating the reduced statistical power.

#### 3.5.2. Hypothesis Testing
-   **Family of Tests**: The Bonferroni correction is applied **only** to the family of ablation comparisons (Baseline vs. Full, vs. Ablation Recurrence, vs. Ablation Inhibition). The Scaling analysis is treated as a separate, exploratory axis and is **not** included in this correction family.
-   **Test Type**: Since ablation variants are trained on the **same** synthetic dataset with the **same** random seeds, the data is **paired**. We will use a **paired t-test** (or Wilcoxon signed-rank test if normality is violated) to compare MAE distributions. A two-sample t-test is explicitly rejected as it assumes independence.
-   **Causal Claims**: All claims are framed as **associational** (performance vs. architecture). No causal inference regarding "intelligence" is made.

## 4. Compute Feasibility & Resource Management

The implementation is strictly designed for the GitHub Actions Free Tier (limited CPU, memory, and time quotas).

| Component | Strategy | Justification |
| :--- | :--- | :--- |
| **Hardware** | CPU-only (PyTorch default) | No GPU available. CUDA libraries excluded. |
| **Model Size** | Small (Embedding dim 64, ~100k params) | Ensures training < 6h. Large models would timeout. |
| **Data** | In-memory NumPy arrays | Avoids I/O latency; fits easily in 7GB RAM. |
| **Batching** | Dynamic batch size (max 256) | Prevents OOM errors; reduces memory footprint. |
| **Precision** | Float32 | Float16/BF16 may not be stable on CPU; Float32 is safe. |
| **Time Limit** | 100 epochs max | Hard stop at a predetermined maximum duration; early stopping if convergence reached. |

**Risk Mitigation**:
-   *Vanishing Gradients*: Implemented gradient clipping (norm < 1.0) and homeostatic scaling.
-   *Memory Overflow*: If RSS > 6GB, batch size is halved dynamically.
-   *Timeout*: If training > 5.5h, job is terminated, and partial results are saved.

## 5. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Rate-based neurons** instead of Spiking Neural Networks (SNN) | SNN training on CPU is computationally prohibitive for extended training durations. Rate-based approximation preserves the laminar topology logic without the simulation overhead. |
| **Synthetic Data** instead of Real-world Neuro Data | Real data lacks ground truth for "universal function approximation." Synthetic data allows precise control over the "Independent Distribution" requirement. |
| **Hybrid Architecture** (Microcircuit in Transformer) | Replacing the entire Transformer with a microcircuit would lose the attention mechanism's global context. The hybrid approach isolates the "MLP" component's contribution. |
| **Padding for Parameter Parity** | Necessary to maintain exact parameter counts despite 4:1 E/I constraints. The "cost" of the mask is part of the biological constraint measurement. |
| **Paired Statistical Tests** | Required because ablation variants share the same random seeds and dataset. Two-sample tests would be invalid. |
| **Separate Scaling Analysis** | Scaling variants (2x, 4x) violate parameter parity and are analyzed separately from the "Cost of Plausibility" ablation family to avoid statistical confounding. |