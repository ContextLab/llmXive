# Research: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

## 1. Problem Statement & Theoretical Background

The core problem is to determine how the sample complexity required to identify a Pareto-optimal policy scales as the number of reward objectives $N$ increases, specifically under the assumption of independent, identically distributed (i.i.d.) noise $\epsilon_i$ in each reward signal.

Existing work (e.g., DVAO) suggests variance-adaptive mechanisms, but a rigorous theoretical lower bound for the *multi-reward* case with independent noise has not been formally derived in closed form. This project aims to:
1.  Derive the variance of the weighted advantage function $V(\hat{A})$ as a function of $N$.
2.  Invert this relationship to find the sample complexity $M(N, \delta)$ required to achieve an error tolerance $\delta$.
3.  Validate this bound empirically using a "Moving-Window Heuristic" in synthetic environments.

## 2. Dataset Strategy

**Dataset Type**: Synthetic Tabular MDPs (Generated in-memory).  
**Source**: `src/environment/synthetic_mdp.py`.  
**Rationale**: External datasets (e.g., real LLM reward logs) are not available with the specific ground-truth noise parameters ($\sigma^2$) required for FR-013 and FR-014. Synthetic generation allows precise control over $N$, noise distribution, and correlation structure ($\rho$), satisfying the need for a "known ground truth" for validation.

**Verified Datasets**:
- **N/A**: No external datasets are used. All data is generated programmatically to ensure reproducibility and exact ground-truth knowledge of noise parameters.

**Data Generation Strategy**:
- **State Space**: $|S|$ states, $|A|$ actions.
- **Rewards**: $N$ reward functions generated as random linear combinations of state features.
- **Noise**: Independent Gaussian noise $\epsilon_i \sim \mathcal{N}(0, \sigma^2)$ added to each objective (for the primary test).
- **Reward Distributions (FR-010)**:
  - **Linear**: Standard random linear combinations.
  - **Sparse**: Random linear combinations where a substantial majority of weights are zero.
  - **Non-Convex**: Mix of linear terms and quadratic state terms ($x_i^2$).
- **Correlation**: Controlled correlation matrices will be injected for the sensitivity analysis (US-5).
- **Validation Independence (FR-012)**: A separate "held-out" set will be generated using a **Student's t-distribution (df=3)** for noise, distinct from the Gaussian training set, to test construct validity.

## 3. Methodology & Statistical Rigor

### 3.1 Theoretical Derivation (FR-001, FR-002)
The system will use `sympy` to derive the variance of the weighted advantage function:
$$ \text{Var}(\hat{A}) = \sum_{i=1}^N w_i^2 \text{Var}(\epsilon_i) + \sum_{i \neq j} w_i w_j \text{Cov}(\epsilon_i, \epsilon_j) $$
Under the assumption of independence ($\text{Cov}=0$) and equal weights ($w_i = 1/N$):
$$ \text{Var}(\hat{A}) = \frac{1}{N^2} \sum_{i=1}^N \sigma^2 = \frac{\sigma^2}{N} $$
The sample complexity $M$ will be derived by inverting the confidence interval formula for the mean advantage estimate, yielding a theoretical slope $\beta_{theo}$ in a log-log regression of $M$ vs $N$.

### 3.2 Moving-Window Heuristic (FR-004)
The heuristic estimates variance using only the last $k$ steps of a rollout.
- **Input**: Sequence of advantage estimates $A_t$.
- **Window**: $W_t = \{A_{t-k+1}, \dots, A_t\}$.
- **Estimate**: $\hat{\sigma}^2_t = \text{Var}(W_t)$.
- **Constraint**: $k \ll \text{rollout\_group\_size}$.

### 3.3 Statistical Validation (FR-006, FR-009, FR-015)
- **Core Validation (Scaling Law)**: Perform a **Log-Log Linear Regression** of Empirical Sample Count ($M$) vs. Number of Objectives ($N$).
  - Model: $\log(M) = \alpha + \beta \log(N) + \epsilon$.
  - Test: Check if the 95% Confidence Interval of $\beta$ contains the theoretical slope $\beta_{theo}$.
  - This replaces the incorrect KS test on distributions, directly validating the functional relationship.
- **Sensitivity Analysis**: Sweep $k \in \{0.01, 0.05, 0.1\} \times \text{rollout\_size}$.
  - Apply **Benjamini-Hochberg False Discovery Rate (FDR)** control to the p-values from multiple $k$ tests to reduce Type II error risk.
- **Coincidence Check (SC-002)**:
  - Identify the "failure point N" where empirical sample count > 1.5 * theoretical bound.
  - Identify the "Pareto distance point" where distance > 5%.
  - Calculate `coincidence_delta` = |failure_point_N - pareto_distance_point|.
- **False Positive Rate (SC-004)**:
  - Count steps where heuristic ratio $\in [0.9, 1.1]$ BUT distance to frontier > 5%.
  - FPR = (Count of such steps) / (Total steps).
- **Sanity Check (FR-014/FR-015)**: One-sample t-test on the mean deviation of heuristic variance from known $\sigma^2$ (H0: $\mu=0$). This is a sanity check, not the primary validation.

### 3.4 Approximate Pareto Oracle (FR-017)
Since computing the exact Pareto frontier for $N \ge 5$ is NP-hard, we use an **Approximate Pareto Oracle**:
- **Method**: Weighted-sum scalarization sweep.
- **Procedure**: Generate random weight vectors $w \in \Delta^{N-1}$, solve the scalarized MDP for each, and collect the resulting reward vectors.
- **Distance Metric**: Euclidean distance from the policy's reward vector to the convex hull of the collected scalarized rewards.
- **Justification**: This provides a consistent, reproducible proxy for the "true" frontier, satisfying the need for a ground truth without requiring infeasible computation.

### 3.5 Power Analysis & Limitations
- **Sample Size**: The plan mandates **100 independent runs** per configuration (increased from a baseline level) to ensure sufficient statistical power to detect the 1.5x deviation factor at the failure point, acknowledging the high variance of RL sample counts.
- **Power Limitation**: If the effect size is small, 100 runs may still lack power. This will be explicitly acknowledged in the results.
- **Causal Assumption**: The study is observational regarding the synthetic environment; claims are about the *consistency* of the heuristic with the theoretical bound, not causal effects of $N$ on performance in the real world.

## 4. Compute Feasibility & Resource Strategy

### 4.1 CPU-First Approach
- **Method**: All computations (MDP generation, variance estimation, statistical tests) are performed using `numpy` and `scipy` on CPU.
- **Memory**: Tabular MDPs store rewards as $|S| \times |A| \times N$ arrays.
  - For $N=50$, $|S|=100$, $|A|=4$: $100 \times 4 \times 50 \times 8$ bytes $\approx 160$ KB.
  - Even with $|S|=10,000$, memory usage is well under 7GB.
- **Degradation Strategy (FR-016)**: If $N > 50$, the system will automatically reduce $|S|$ by a factor of 2 to maintain the memory footprint $< 7$GB. This is logged and reported.

### 4.2 GPU Escape Hatch
- **Not Required**: The problem is purely tabular and statistical. No deep learning or CUDA kernels are needed. The plan does not invoke the GPU escape hatch.

## 5. Data Availability & Integrity

- **Reproducibility**: All random seeds are pinned in `src/utils/seeding.py`.
- **Checksums**: Generated data files in `data/processed/` will be checksummed (SHA-256) and recorded in the project state.
- **No External Dependencies**: No external API calls or downloads. The system is self-contained.

## 6. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Synthetic MDPs** | Real LLM environments lack ground-truth noise parameters ($\sigma^2$), making FR-013 and FR-014 impossible. Synthetic generation provides exact control. |
| **Tabular Representation** | Deep RL would exceed the 7GB RAM limit and introduce architectural noise, confounding the specific noise-scaling law being tested. |
| **Moving-Window Heuristic** | A small window $k$ is required to estimate variance in real-time without storing the full history, fitting the "online" nature of the DVAO extension. |
| **Log-Log Regression** | Required to validate the scaling law (slope) rather than just variance accuracy. KS test is inappropriate for functional relationships. |
| **Benjamini-Hochberg FDR** | More appropriate than Bonferroni for exploratory sensitivity analysis to avoid masking true trends (Type II error). |
| **Approximate Pareto Oracle** | Exact Pareto frontier is NP-hard for N=50. Weighted-sum sweep provides a consistent, reproducible proxy. |
| **100 Runs** | Increased sample size to ensure statistical power for detecting the 1.5x deviation factor at the failure point. |
| **No GPU** | The problem is computationally light (matrix operations on small arrays). GPU usage would add unnecessary complexity and cost. |