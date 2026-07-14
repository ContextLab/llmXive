# Research: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Executive Summary

This research validates the "Symbolic-Latent" hypothesis: that a frozen Geometric Foundation Model (GFM) combined with a differentiable symbolic solver can achieve zero-shot generalization to novel object topologies (kinematic chains, deformable materials) where a learned neural predictor fails. The study utilizes a CPU-only pipeline to ensure feasibility on standard CI infrastructure, comparing a symbolic approach against a baseline GAM on a synthetic "topology-shift" test set.

## Dataset Strategy

The study relies on three distinct data components: (1) the original GFM weights and **training distribution statistics** (mean/covariance), (2) a synthetic "topology-shift" test set generated via PyBullet, and (3) the baseline GAM implementation.

| Component | Description | Source / Verification | Usage in Plan |
|-----------|-------------|-----------------------|---------------|
| **GFM Weights & Training Stats** | Original Geometric Foundation Model parameters and **latent distribution statistics** (mean/covariance) for drift detection. | **Verified Source**: ` (for training context); **Weights/Stats**: Must be provided as `data/raw/gfm_weights.pt` and `data/raw/training_stats.json`. If `training_stats.json` is missing, the "Latent Drift" check is disabled (see Methodology). | Used to load frozen encoder/decoder (FR-002) and compute Mahalanobis distance. Metadata used to define "novel" topologies (avoiding overlap). |
| **PyBullet Physics Engine** | CPU-based physics simulator for generating novel topologies. | **Verified Source**: ` (Format Reference: video/trajectory logging standard); ` (Format Reference: task format). | **Tool for Generation**: The `data_generation.py` script uses PyBullet (library) to *generate* the **Topology-Shift Test Set** (FR-001). The cited datasets are used *only* as format references for logging, not as data sources for novel topologies. |
| **Baseline GAM Data** | Standard manipulation tasks for baseline comparison. | **Verified Source**: ` (Format Reference: generic trajectory format); ` (Format Reference: trajectory format). | **Format Reference Only**: Used to define the "Baseline GAM" control condition (FR-005) structure. The actual baseline execution uses the *same* synthetic topologies generated in Phase 1. |

**Note on Data Sources**: The core "Topology-Shift Test Set" is **generated de novo** by the `data_generation.py` script using the PyBullet physics engine. No external dataset provides the specific novel topologies (5-link hinges, soft ropes) required by FR-001. The cited URLs serve only as format references for logging standards.

## Methodology

### 1. Synthetic Topology-Shift Test Set Generation (FR-001)
- **Tool**: PyBullet (CPU).
- **Process**:
 1. Define a set of **Novel Topologies**: Kinematic chains with hinge counts (e.g., 5, 7, 10) and deformable mesh densities (soft ropes, cloth) strictly *not* present in the GFM training metadata (verified via hash comparison if available, otherwise via random seed separation).
 2. Generate a diverse set of unique manipulation tasks (start state, target zone) for these topologies.
 3. Simulate trajectories to produce ground-truth latent inputs and physical actions.
 4. **Validation**: Compute a SHA-256 hash of the metadata; ensure no collision with the original GAM training set hash (if available).
- **Output**: `data/generated/topology_shift_test_set_v1.jsonl` (or parquet).

### 2. Symbolic Latent Planner Execution (FR-002, FR-003, FR-004)
- **GFM Interface**: Load frozen GFM encoder/decoder weights. Ensure `model.eval()` and `requires_grad=False` for GFM parameters.
- **Symbolic Solver**:
 - **Operation Space**: **Exclusively in the frozen 3D latent space** (Constitution VI). The solver optimizes the latent action vector $z_{action}$.
 - **Constraint Formulation**: Constraints (rigid-body, soft-body) are defined in physical 3D space but are enforced by decoding $z_{action}$ to physical space and checking validity.
 - **Solver**: Use a differentiable convex optimization layer (e.g., `cvxpy` with `diffcp`) to solve for $z_{action}$ that minimizes a loss function based on *decoded* physical constraint violations.
 - **Differentiability Check**: The solver is differentiable *internally*. **Validation** is performed by executing the decoded action in PyBullet and verifying constraint satisfaction. **No gradients flow through the frozen GFM decoder** to update solver parameters; the decoder is a fixed function.
- **Pipeline**:
 1. Encode observation $o_t \rightarrow z_t$.
 2. Solve $z_{action} = \text{Solver}(z_t, \text{constraints})$.
 3. Decode $z_{action} \rightarrow \text{Physical Action}$.
 4. Execute in PyBullet.
- **Constraint Handling**:
 - If solver fails (infeasible): Return "infeasible" flag; record trial as failure.
 - If solver exceeds 300s: Timeout; record as failure.
 - **Latent Drift**: Compute Mahalanobis distance of $z_t$ from training distribution. **Requirement**: `data/raw/training_stats.json` (mean/covariance) MUST be present. If missing, the check is disabled and the trial is flagged as "Unverified Drift".

### 3. Comparative Statistical Analysis (FR-005, FR-006)
- **Strict Pairing Protocol**: The 50 trials for Symbolic and Baseline MUST run on the **exact same 50 topology IDs** in the **same order**.
- **Metrics**:
 - **Success Rate**: Binary (1 = target reached within 5cm for 1.0s; 0 = failure).
 - **Latency**: Inference time (ms) per step.
- **Statistical Tests**:
 - **Success Rates**: Fisher's Exact Test (appropriate for low counts/small N).
 - Null Hypothesis ($H_0$): No difference in success rates between Symbolic and Baseline.
 - Output: p-value, confidence interval.
 - **Latency**: **Wilcoxon Signed-Rank Test** (non-parametric, robust to skewness and outliers).
 - *Censoring Protocol*: Trials with "Timeout" or "Infeasible" (where latency is undefined or censored) are **excluded** from the latency test. A separate **Kaplan-Meier Survival Analysis** is performed to compare the time-to-failure (timeout) rates.
 - Null Hypothesis ($H_0$): No difference in latency distribution.
 - Output: Median difference, p-value, effect size (Cliff's Delta).
- **Significance**: $\alpha = 0.05$.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Only two primary hypotheses (Success Rate, Latency) are tested. No family-wise error correction (e.g., Bonferroni) is strictly required for just two tests, but the report will explicitly state the number of tests performed.
- **Power Analysis & Mitigation**:
 - **Assumption**: $N=50$ per condition is sufficient to detect a moderate effect size (Cohen's d ≈ 0.5) for latency and a [deferred] absolute difference in success rates.
 - **Limitation**: If preliminary runs show success rates <20% or variance too high, the power to detect differences may be lower.
 - **Mitigation Strategy**: If preliminary runs indicate insufficient power, the plan triggers an **Adaptive Extension**: generate additional topologies to increase power. This is explicitly noted as a conditional step.
- **Causal Inference**: The study is experimental (controlled simulation). The "cause" is the planner architecture (Symbolic vs. Neural). Randomization of topology order ensures no confounding from sequence effects.
- **Collinearity**: Predictors (topology complexity) are distinct from the outcome (success). The symbolic solver's constraints are mathematically defined, avoiding data-driven collinearity issues common in neural nets.
- **Measurement Validity**:
 - **PyBullet**: Widely used physics engine; constraints (joint limits, collision) are standard.
 - **Latent Space**: GFM is assumed to provide a valid geometric representation (Constitution VI).

## Feasibility & Compute Constraints

- **Hardware**: GitHub Actions 2-core x86_64 (no GPU).
- **Memory**: Target < 7GB RAM.
 - *Strategy*: Process trials sequentially; discard intermediate states; use `torch.no_grad()` for GFM inference.
- **Time**: Target < 6 hours for 100 trials.
 - *Strategy*: Timeout solver at a fixed duration per step. If a single step takes too long, the trial is marked failed, preventing a single complex topology from blocking the entire time window.
- **Libraries**:
 - `torch` (CPU version): Standard inference.
 - `cvxpy`/`diffcp`: CPU-compatible differentiable solvers.
 - `pybullet`: CPU-native.
 - **Excluded**: `bitsandbytes`, `deepspeed`, `cuda` specific libs.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Solver Timeout** | Trial fails, reducing effective N. | Implement 300s timeout; log complexity; analyze if failures are systematic (e.g., only for >8 hinges). |
| **Latent Drift** | GFM decoder produces invalid 3D states for novel topologies. | Mahalanobis distance check (requires `training_stats.json`); if drift > threshold, flag trial; treat as "out-of-distribution" failure. |
| **Memory Overflow** | PyBullet simulation consumes >7GB. | Use single-process simulation; clear PyBullet instances between trials; monitor memory usage. |
| **Non-Convergence** | Symbolic solver fails to find any solution. | Solver returns "infeasible"; trial recorded as failure (valid data point). |