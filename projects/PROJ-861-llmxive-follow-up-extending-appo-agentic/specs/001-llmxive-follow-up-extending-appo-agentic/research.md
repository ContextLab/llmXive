# Research: llmXive follow-up: extending "APPO: Agentic Procedural Policy Optimization"

## Problem Definition

The project investigates whether a "Static Branching Score" (computed via frozen LLM next-token entropy at semantic steps) can serve as a valid proxy for "Dynamic Branching Score" (computed via online APPO Advantage values) in reasoning tasks. If valid, this would allow researchers to estimate the value of decision points without expensive online rollouts, democratizing agentic RL on CPU-only infrastructure.

## Dataset Strategy

The study utilizes reasoning traces from GSM8K and MATH datasets. The following verified sources are used:

| Dataset | Description | Verified Source | Usage |
|---------|-------------|--------------|-------|
| **GSM8K** | Grade school math word problems (reasoning traces with CoT). | `openai/gsm8k` (via `load_dataset`) | Primary source for static and dynamic scoring. Contains `question`, `answer`, and `cot` (reasoning steps). |
| **MATH** | Mathematical problem solving dataset (text-only). | `hendrycks/math` (via `load_dataset`) | Secondary source for binary reward validation. **Note**: Raw MATH lacks CoT traces; used only if GSM8K is insufficient or for reward check. |
| **APPO Baseline** | CleanRL PPO Implementation | ` | The "Dynamic Branching Score" is generated dynamically via the APPO algorithm adapted from CleanRL. |

**Variable Fit Verification**:
- **Predictor**: Next-token probability distribution at semantic steps (available from any decoder-only LLM inference).
- **Outcome**: "Final answer correctness" (binary: 1 if correct, 0 otherwise). This is derived from the ground-truth solution in the GSM8K/MATH datasets.
- **Covariates**: Task difficulty (inferred from dataset split), reasoning length.
- **Fit**: GSM8K contains the necessary question, ground-truth answer, and reasoning traces (CoT). The "Dynamic Score" is not a pre-existing column but a derived metric from the APPO rollout (Advantage values), which is feasible given the dataset structure. MATH is used only for reward validation if GSM8K is insufficient.

**Constraint**: The datasets are loaded via the HuggingFace `datasets` library using their canonical IDs (`openai/gsm8k`, `hendrycks/math`). No direct file URLs are used to ensure reproducibility and version stability.

## Methodology

### Phase 1: Static Score Generation
- **Model**: Phi-2 (or similar small decoder-only model) loaded in CPU-only mode (`torch_dtype=torch.float32`).
- **Metric**: KL Divergence between model's next-token distribution and a uniform distribution over the top-5 tokens, computed at each **semantic step** (parsed via `step_parser.py`).
- **Formula**: $D_{KL}(P || U) = \sum P(x) \log \frac{P(x)}{U(x)}$.
- **Handling Zeros**: Apply $\epsilon = 10^{-9}$ smoothing to $P(x)$ to prevent $\log(0)$.
- **Throughput**: Stream data in chunks to stay within available RAM.
- **Semantic Step Parser**: Uses a fixed regex grammar (e.g., `Step \d+:`, `Therefore:`, `Conclusion:`) to identify step boundaries. Only tokens following a valid step header are scored.

### Phase 2: Dynamic Score Generation
- **Algorithm**: APPO (Agentic Procedural Policy Optimization) adapted from **CleanRL** (PPO implementation).
- **Environment**: GSM8K/MATH tasks as the environment.
- **Reward**: Binary correctness (1 if final answer matches ground truth, 0 otherwise).
- **Metric**: **Advantage Values (A(s,a))** computed via Generalized Advantage Estimation (GAE).
 - **Formula**: $A(s_t, a_t) = \sum_{l=0}^{\infty} (\gamma \lambda)^l \delta_{t+l}$, where $\delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)$.
 - **Value Function**: $V(s)$ is the value function learned jointly with the policy by the APPO agent. This ensures the Advantage metric reflects the *outcome quality* (reward) relative to the state baseline, not just policy confidence.
- **Scope**: A subset of tasks (to account for [deferred] dropout and alignment noise) to ensure completion within the designated time window.
- **Failure Handling**: If a rollout exceeds token limits or fails to converge, the task is excluded from the final correlation analysis.

### Phase 3: Statistical Analysis
- **Alignment**: **Semantic Step Alignment**. Both static and dynamic traces are parsed into semantic steps using the fixed regex grammar. Scores are aligned based on matching step identifiers (e.g., "Step 1: Define variables"). If a step in the static trace has no matching identifier in the dynamic trace (or vice versa), the score is marked 'unalignable' and **excluded** from the correlation analysis. **No token-level DTW or Levenshtein distance is used**, as this would align noise rather than logical decision points.
- **Correlation**: Compute Pearson ($r$) and Spearman ($\rho$) coefficients on the aligned score vectors.
- **Significance**: Permutation test (sufficient iterations to generate a null distribution and p-value).
- **Residuals**: Ljung-Box test on residuals to detect systematic patterns (e.g., algebraic vs. arithmetic failures).

### Sensitivity Analysis
- **Dropout Impact**: Assuming a [deferred] failure rate and [deferred] alignment noise, the initial subset of 85 tasks ensures an effective $n \approx 60$.
- **Power**: A power analysis for correlation ($r=0.7$) at $\alpha=0.05$ and power=0.8 requires $n \approx 20$. With $n \ge 60$, the study is robust to attenuation from alignment noise.
- **Attenuation**: If the observed correlation is weaker than expected, the plan includes a directional check (testing for negative correlation) to identify if high-value paths are unexpectedly low-predictability.
- **Alignment Noise**: The plan explicitly models the reduction in effective sample size due to step mismatches. If >20% of steps fail to align, the analysis reports the reduced power and interprets the result as a lower-bound estimate.

## Decision Rationale

### CPU-Only Constraint
- **Rationale**: The project aims to democratize agentic RL. GPU resources are not available on the target CI runner.
- **Trade-off**: Inference speed is slower; however, the static pass is lightweight (just log-probs), and the dynamic pass is limited to a subset of tasks.
- **Fallback**: If the model is too slow, the plan will reduce the subset size or switch to a smaller model (e.g., TinyLlama) while maintaining the architecture.

### Metric Selection (KL Divergence)
- **Rationale**: KL divergence measures the "surprise" or "predictability" of the next token. High predictability (low KL) implies the model is confident, which may correlate with high-value decision points in a well-trained policy.
- **Alternative**: Entropy was considered, but KL divergence against a uniform baseline provides a normalized "distance from randomness" metric.

### Advantage Value Selection (vs. Likelihood Gain)
- **Rationale**: "Likelihood gain" can be tautological (correlating a policy with itself). "Advantage values (A(s,a))" derived from GAE and external rewards provide an independent measure of *outcome quality* at each step, ensuring the dynamic score is a valid ground truth. This breaks the circular validation risk where the static score (model probabilities) correlates with the dynamic score (model probabilities).

### Sample Size (85 Tasks)
- **Rationale**: 85 tasks is a compromise between statistical power and the 5-hour runtime limit, accounting for a [deferred] dropout rate and alignment noise.
- **Power Analysis**: A power analysis for correlation ($r=0.7$) at $\alpha=0.05$ and power=0.8 typically requires $n \approx 20$. $n=85$ provides a buffer for task dropouts and alignment noise.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **APPO rollout timeout** | High (missing dynamic scores) | Limit to a fixed number of tasks; enforce hard token limits; log failures and exclude from analysis. |
| **Memory overflow** | High (job killed) | Stream data; use `torch.no_grad()`; monitor memory and fallback to a predefined number of permutations (5,000 or 2,500) if >6.5 GB. |
| **Zero probability in static trace** | Medium (NaN errors) | Apply $\epsilon$ smoothing (1e-9) as per spec. |
| **Weak correlation** | Low (scientific result) | Report negative result; analyze residuals to understand *why* (e.g., static score misses long-horizon dependencies). |
| **Spec Conflict** | High (Methodology mismatch) | Flagged for kickback to update `spec.md` FR-002/FR-003 to match Advantage/Step Alignment definitions. |

## Hypothesis Nuance

The hypothesis that "predictability correlates with value" is not a standard identity. High-value paths in complex reasoning may be *less* predictable (high entropy) because they require exploring non-obvious branches. The analysis plan explicitly tests for both positive and negative correlations and analyzes residuals to identify if the static score systematically fails on high-entropy/high-value paths. The Dynamic Score is defined as Advantage (outcome quality), not likelihood gain, to ensure independence from the static predictor.
