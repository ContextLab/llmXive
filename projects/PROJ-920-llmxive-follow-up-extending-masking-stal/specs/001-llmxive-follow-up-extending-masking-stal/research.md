# Research: llmXive follow-up: extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

## Research Question

How does the semantic density of retrieved context modulate the optimal masking horizon for long-horizon search agents, and does high-density information retain "critical evidence" status for significantly longer temporal windows than low-density information?

## Methodology

### 1. Synthetic Trajectory Generation (US-1)
A rule-based simulator will generate a set of search trajectories.
- **Evidence Injection**: At a random turn $t \in [1, T]$, a "critical evidence" block is injected.
- **Density Control**: The evidence block is constructed to have a target semantic density ($D$) defined by:
  $D = 0.6 \times H_{token} + 0.4 \times R_{tech}$
  Where:
  - $H_{token}$: Shannon entropy per UTF-8 byte token.
  - $R_{tech}$: Ratio of tokens matching a predefined list of technical terms.
  - **Tokenization**: Tokens are extracted using the regex pattern `\w+` (whitespace and punctuation splitting) on the UTF-8 text.
  - **Technical Token List**: A curated list of 50+ technical terms (e.g., "function", "variable", "algorithm") defined in `code/config.py`.
- **Density Levels**: Three levels will be simulated: Low ($D \le 2.0$), Medium ($2.0 < D \le 4.0$), High ($D > 4.5$).
- **Validation**: A validation script (`validate_trajectories.py`) will verify that the generated entropy matches the target within $\pm 0.01$ bits/token. If `abs(calculated - target) > 0.01` for any critical block, the script logs the error and exits with code 1.

### 2. Agent Simulation (US-2)
A rule-based agent processes each trajectory with a configurable retention horizon $H \in [1, T]$.
- **Sampling Strategy**: To ensure statistical power without combinatorial explosion, for each trajectory, we sample $K=10$ random horizons from the range $[1, T]$ rather than testing all horizons. This yields a balanced design with a sufficient number of samples per (Density, Horizon) bin.
- **Masking Logic**: Only the last $H$ turns are visible.
- **Success Condition (Decoupled)**:
  $Success = 1$ if ($t_{evidence} \ge t_{current} - H + 1$) AND ($random() < 0.9$)
  $Success = 0$ otherwise.
  - **Correction**: The outcome is now determined *solely* by visibility and a fixed random coin flip (simulating agent capability with $p=0.9$). The semantic density $D$ is **not** used in the success logic. This breaks the tautological loop where the predictor defined the outcome. The hypothesis is tested by observing if the *empirical* decay of success with horizon differs by density.
  - **Note on FR-009**: The density-dependent Heuristic Solver defined in the original spec (FR-009) is **DEPRECATED** for this experiment. The parameters $\alpha=2.0$ and $\theta=0.05$ (source: P-value, https://en.wikipedia.org/wiki/P-value) are defined in `code/config.py` for reference only and are **not** used to determine the outcome.
- **Output**: A CSV log containing `trajectory_id`, `density`, `horizon`, `evidence_age`, `success`.

### 3. Statistical Analysis (US-3)
A Generalized Additive Model (GAM) will be performed to quantify the interaction effect.
- **Model**: $\text{logit}(P(Success)) = \beta_0 + s(Density) + s(Horizon) + \beta_3 \cdot (Density \times Horizon)$
  - $s(\cdot)$: Natural splines with degrees of freedom selected via Generalized Cross Validation (GCV) or AIC.
  - $\beta_3 \cdot (Density \times Horizon)$: Explicit linear interaction term to test the modulation hypothesis.
- **Hypothesis**: The interaction term $\beta_3$ will be statistically significant ($p < 0.05$), indicating that the effect of horizon on success depends on density.
- **Visualization**: A 3D surface plot will be generated with axes:
  - X: Masking Horizon
  - Y: Semantic Density
  - Z: Predicted Success Rate

## Dataset Strategy

| Dataset Name | Source URL | Loader Method | Notes |
| :--- | :--- | :--- | :--- |
| **Synthetic Trajectories** | N/A (Generated) | `generate_trajectories.py` | Fully synthetic. No external URL. Generated on-the-fly. |

> **Note**: No external datasets are used. The "dataset" is the output of the generator. This ensures reproducibility and eliminates access-gated data issues.

## Statistical Rigor

- **Multiple Comparisons**: Not applicable (single primary interaction test).
- **Sample Size**: 500 trajectories $\times$ 10 sampled horizons = 5,000 observations. With 3 density levels and 10 horizon levels, this yields ~ samples per bin, well above the required 16-17 for [deferred] power ($f^2 \approx 0.15$).
- **Causal Inference**: The simulation is a controlled experiment. The "cause" (density/horizon) is manipulated by the generator. Causal claims are valid *within the simulation environment*.
- **Measurement Validity**: Entropy is calculated directly from UTF-8 bytes. Technical token ratio is based on a deterministic list.
- **Collinearity**: Density and Horizon are independent variables in the design (density is fixed at generation, horizon is sampled). No collinearity issues expected.

## Compute Feasibility Decision

- **CPU-First**: All methods (entropy calculation, logistic regression, 3D plotting) are CPU-tractable.
- **No GPU Required**: No neural networks or large model inference is involved.
- **Memory Management**: Streaming to CSV ensures RAM usage remains within acceptable system limits.

## Constitution Alignment

- **Principle VI**: Density is dynamically derived from entropy, not just turn count.
- **Principle VII**: Simulation is rule-based and non-circular (outcome decoupled from predictor).
- **Principle I**: Seeds are pinned; code is reproducible.