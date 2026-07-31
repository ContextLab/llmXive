# Research: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Summary

This research investigates whether replacing the learned neural predictor in the Geometric Action Model (GAM) with a differentiable symbolic solver improves zero-shot generalization to novel kinematic topologies. The hypothesis is that symbolic constraint satisfaction in physical 3D space (via the frozen GFM decoder) is more robust to topology shifts than a neural predictor trained on a fixed distribution.

## Methodology

### 1. Synthetic Topology-Shift Test Set Generation (P1)
- **Tool**: PyBullet physics simulator.
- **Process**:
  - Define a parameterized kinematic chain generator (variable hinge counts, link lengths).
  - Define a deformable material generator (soft ropes, cloth with variable mesh density).
  - **Exclusion Logic**: Generate candidate topologies and compute a cryptographic hash of their structural parameters. Compare against a hash set of the original GAM training distribution.
  - **Termination Condition**: If < 50 unique novel topologies are generated within 1000 attempts, the script will **HALT** and output `error_code: 1` with a report of the attempted count. It will **NOT** proceed to downstream phases. (Resolves Unresolved Concern: T009-verify-uniqueness).
- **Output**: `data/raw/novel_topology_set.json` containing 50+ distinct topology definitions and initial simulation states.

### 2. Symbolic Latent Planner Execution (P2)
- **Model**: Frozen Geometric Foundation Model (GFM) Encoder/Decoder.
- **Solver**: Differentiable symbolic solver (`cvxpylayers`).
- **Pipeline**:
  1. **Encode**: Input 3D observation -> GFM Encoder -> Latent Vector $z$.
  2. **Plan**: Latent Vector $z$ + Task Constraints -> Symbolic Solver -> Action $a_{phys}$.
     - *Constraint Enforcement*: Rigid-body non-penetration, joint limits, soft-body elasticity.
     - *Differentiability Check*: The GFM decoder is **frozen**. The gradient flow verification is a **numerical check on the composite map** (Solver -> Decoder -> Physical Space) to ensure the solver can propagate constraint violations through the decoder's Jacobian. This does not involve training the GFM or backpropagating through it to update weights. Log results to `data/results/gradient_flow_log.json`.
  3. **Decode**: Action $a_{phys}$ -> GFM Decoder -> Physical Action.
  4. **Simulate**: Execute in PyBullet.
  5. **Safety**: Implement a per-step timeout (e.g., a reasonable duration). If exceeded, log `timeout=true` and record failure.
- **Compute Strategy**: CPU-first. The solver and GFM inference are designed to run on standard x86_64 cores. No CUDA required.

### 3. Comparative Statistical Analysis (P3)
- **Metrics**:
  - **Physical Success Rate**: Binary (1 if target reached without collision, 0 otherwise). **Crucial**: Trials with `timeout=true` (computational failure) are **excluded** from this metric to prevent conflation of solver speed with generalization capability. They are reported separately as "Computational Failure Rate".
  - **Inference Latency**: Time (ms) per step (Encoding + Solving + Decoding) for *converged* trials only.
- **Statistical Tests**:
  - **Success Rate**: Fisher's Exact Test (appropriate for low counts/binary outcomes) on the subset of *converged* trials.
    - Null Hypothesis ($H_0$): No difference in success rates between Symbolic and Baseline.
    - Significance Level: $\alpha = 0.05$.
  - **Latency**:
    - **Condition**: If latency data contains censored values (timeout events), use **Log-Rank test** (survival analysis) or **Wilcoxon signed-rank test** on the uncensored subset (with bias acknowledgment).
    - **Condition**: If no censored data exists, use **Paired t-test**.
    - Null Hypothesis ($H_0$): No difference in latency distribution.
    - Output: p-value, 95% CI, effect size (Hazard Ratio or Cliff's Delta).
- **Sample Size & Power**: 50 trials per condition (Symbolic, Baseline).
 - *Power Note*: This sample size is sufficient to detect a moderate effect size with [deferred] power for the t-test. For Fisher's test, power depends on the expected baseline success rate. **Adaptive Protocol**: If the observed baseline success rate is < 15%, the system will automatically extend the trial count to 100 per condition to maintain statistical power.

## Power Analysis & Sensitivity

To address the concern regarding underpowered studies for low baseline success rates, the following sensitivity analysis is provided for the 50-trial sample size:

| Baseline Success Rate | Minimum Detectable Effect Size (MDES) at [deferred] Power | Power if Effect Size = 20% |
|-----------------------|----------------------------------------------------|----------------------------|
| [deferred] (Pre-defined) | [deferred] (Absolute difference) | [deferred] |
| [deferred] | [deferred] (Absolute difference) | [deferred] |
| [deferred] | [deferred] (Absolute difference) | [deferred] |

**Adaptive Sampling Protocol**:
- If the observed baseline success rate in the initial 50 trials is **< 15%**, the system will **automatically extend** the trial count to 100 per condition.
- This ensures that the study maintains sufficient power (>70%) to detect a meaningful effect size (e.g., 15-20% improvement) even in low-success-rate scenarios.
- The final report will explicitly state the final sample size used for the Fisher's Exact Test.

## Dataset Strategy

The project relies on **synthetic data generation** for the test set and **local model weights** for the GFM. No external datasets are downloaded for the *test* phase, as the hypothesis requires *novel* topologies not present in existing datasets.

| Dataset/Resource | Source | Usage | Verification |
|------------------|--------|-------|--------------|
| **PyBullet Assets** | `pybullet` library (bundled) | Physics simulation engine, default rigid/deformable bodies. | Verified via `pip install pybullet`. |
| **GFM Weights** | Local `data/raw/gfm_weights.pth` (from original GAM repo) | Frozen encoder/decoder for latent mapping. | Assumption: Weights are accessible and compatible (Spec Assumption). |
| **Original GAM Training Set** | `data/raw/gam_reference_stats.json` (checksummed) | Used to generate exclusion hashes for topology uniqueness. | Must be present; if missing, generation halts. |
| **Synthetic Novel Topologies** | Generated by `topology_generator.py` | The primary test dataset. | Validated by hash uniqueness check against GAM training stats. |

**Note on "Verified datasets" block**: The user-provided list contains PyBullet video/image datasets and GFM benchmarks. These are **not** used for the *topology-shift test set* because they represent existing distributions. The project generates its own *novel* distribution to satisfy FR-001. The PyBullet library itself is the verified tool for generation.

## Decision Rationale: Compute Feasibility

- **CPU-First**: The symbolic solver (convex optimization) and GFM inference (small transformer/MLP) are computationally tractable on a standard CPU.
  - *Solver*: Convex problems (e.g., quadratic programming for soft-body constraints) are highly optimized and run efficiently on CPU.
  - *GFM*: The encoder/decoder are frozen and run in inference mode.
- **GPU Escape Hatch**: Not required. The plan explicitly avoids large transformer fine-tuning or diffusion models that would necessitate a GPU. If the solver complexity exceeds a predefined time limit, the timeout mechanism (FR-Edge) will catch it, and the trial will be recorded as a failure, preserving the integrity of the dataset rather than fabricating a result.

## Statistical Rigor

- **Multiple Comparisons**: Only two primary comparisons are made (Success Rate, Latency). No family-wise error correction is strictly required for these two independent tests, but the report will note the number of tests performed.
- **Causal Assumptions**: The study is observational in the sense of comparing two methods on the same data. The "causal" claim is that the *method* (Symbolic) causes the *outcome* (Generalization). This is supported by the controlled experimental design (same topologies, same seeds, same hardware).
- **Measurement Validity**: PyBullet is the standard for robotic simulation. The success metric (target reach + no collision) is a standard robotics benchmark.
- **Collinearity**: N/A (Comparing two distinct algorithms, not predictor variables within a single model).
- **Censored Data Handling**: The plan explicitly distinguishes between 'physical infeasibility' (true failure) and 'timeout' (computational failure). The statistical test for latency is selected based on the presence of censored data (Log-Rank/Wilcoxon if censored, t-test if not) to ensure scientific validity. **Crucially**, the primary success rate comparison (Fisher's Exact Test) excludes censored timeouts to avoid conflating solver speed with generalization capability.
- **Complexity-Stratified Analysis**: To address the concern of systematic censoring (methodology-8f1ce941), the analysis will stratify results by topological complexity (e.g., number of links, mesh density). This ensures that the symbolic solver is not just tested on "easy" cases. The "Generalization Rate" (success among converged) and "Robustness Rate" (success among all trials) will be reported separately to distinguish algorithmic failure from computational intractability.

## Edge Case Handling

1. **Solver Infeasibility**: If constraints cannot be satisfied, the solver returns a specific `infeasible` flag. The trial is recorded as a failure (`success=0`), and the reason is logged.
2. **Topology Complexity Timeout**: If the solver exceeds the time limit (e.g., a predefined threshold), a timeout flag is set. The trial is recorded as a failure (`success=0`, `timeout=true`), and the complexity metric is logged. **Note**: These trials are excluded from the primary success rate comparison to avoid conflating computational limits with algorithmic generalization.
3. **Latent Drift**: If the Mahalanobis distance of the latent vector $z$ from the training distribution exceeds a threshold, the trial is flagged as `out_of_distribution`. This does not automatically fail the trial but is recorded for manual review.

## References

- **Omnibus Test**: Used for null rejection state status = 0.000 (Source: Wikipedia, Omnibus test).
- **Fisher's Exact Test**: Standard method for 2x2 contingency tables with small sample sizes.
- **Paired t-test**: Standard method for comparing means of paired observations.
- **Log-Rank Test**: Standard method for comparing survival distributions with censored data.
- **Wilcoxon Signed-Rank Test**: Non-parametric test for paired data, robust to outliers and non-normality.