# Research: Low-Rank RL for Foresight in LLM Training

## Research Question
Does the "foresight" phenomenon in language model reasoning emerge primarily from the geometric stability of parameter update subspaces, or is it an emergent property of the supervised distillation objective itself?

## Methodology

### 1. Dataset Strategy
The study utilizes the **GSM8K** dataset, a collection of grade-school math word problems, as the primary reasoning benchmark.
- **Primary Source**: GSM8K (main split, Parquet) from HuggingFace.
 - **URL**: `
 - **Usage**: A subset of problems is used for training and validation to ensure computational feasibility.
 - **Rationale**: GSM8K requires multi-step reasoning, making it a suitable proxy for "foresight" (planning ahead in reasoning chains).
- **Other Verified Sources** (for reference only, not used in primary analysis):
 - **GSM8K (JSONL)**: `
 - **GSM8K (Synth)**: `
 *Note: Only the 'main' split is used for the core experiment to ensure consistency.*

### 2. Experimental Design

Six experimental variants are executed to isolate the geometric signal:

#### Variant A: On-Policy Distillation (OPD) - Baseline for Geometry
- **Objective**: Generate a "stable subspace" defined by the top singular vectors of early parameter updates.
- **Procedure**:
 1. Initialize a pruned model (derived from `TinyLlama/TinyLlama-1.1B-Chat-v1.0` by reducing hidden_size to 512) with a parameter count in the hundreds-of-millions range.
 2. Train on GSMK subset using standard supervised fine-tuning (SFT) / distillation objective for a fixed number of steps (e.g., [deferred] of total trajectory).
 3. Record parameter update matrices ($\Delta W_t$) for each layer.
 4. Aggregate updates and perform Singular Value Decomposition (SVD).
 5. Extract top-$k$ singular vectors such that cumulative explained variance $\ge$ [deferred] (default $k=10$ if variance threshold not met).
- **Output**: A projection matrix $P$ (shape $k \times n_{params}$) representing the stable subspace.

#### Variant B: Standard RL (PPO) - Baseline for Objective
- **Objective**: Establish the convergence trajectory of standard reinforcement learning without geometric constraints.
- **Procedure**:
 1. Initialize the same model architecture (random weights).
 2. Train using PPO with a reward function based on GSM8K answer correctness.
 3. Log accuracy vs. steps and update directions.
- **Output**: Convergence curve and final update direction (used for performance comparison, not geometric ground truth).

#### Variant C: Low-Rank RL (Hybrid) - The Intervention
- **Objective**: Test if projecting RL gradients onto the OPD subspace induces foresight.
- **Procedure**:
 1. Initialize the model (random weights).
 2. Train using PPO, but before applying the update:
 - Compute the raw RL gradient $g$.
 - Project $g$ onto the subspace defined by $P$: $g_{proj} = P^T (P g)$.
 - Apply $g_{proj}$ as the update.
 3. **Relevance Monitoring**: At each step, compute the cosine similarity between the current RL update direction and the OPD subspace. If similarity < 0.5 for >10 consecutive steps, flag as "over-constrained" and trigger a sensitivity analysis (increase rank $k$).
 4. Log accuracy vs. steps and update directions.
- **Output**: Convergence curve, alignment scores (diagnostic), and early trajectory alignment metrics (diagnostic only).

#### Variant D: Random Projection Baseline - Control for Constraint
- **Objective**: Isolate the effect of the *specific* OPD geometry from the general effect of *any* low-rank constraint.
- **Procedure**:
 1. Initialize the model (random weights).
 2. Generate a random projection matrix $P_{rand}$ of rank $k$ (same as OPD).
 3. Train using PPO, projecting gradients onto $P_{rand}$.
 4. Log accuracy vs. steps.
- **Output**: Convergence curve. If Variant C outperforms Variant D, the specific OPD geometry is the driver of foresight.

#### Variant E: Random Walk Prior Baseline - Control for Supervision-Induced Geometry
- **Objective**: Distinguish between "geometry learned from supervision" vs "geometry as a constraint".
- **Procedure**:
 1. Initialize the model (random weights).
 2. Perform a random walk in parameter space (noise) for the same number of steps as OPD.
 3. Perform SVD on the random walk updates to derive a "noise subspace" $P_{noise}$.
 4. Train using PPO, projecting gradients onto $P_{noise}$.
- **Output**: Convergence curve. If Variant C outperforms Variant E, the OPD geometry is not merely a byproduct of supervised learning but a specific signal.

#### Variant F: OPD-Initialized RL - Control for Initialization
- **Objective**: Isolate the effect of the *projection constraint* from the *initialization* with OPD weights.
- **Procedure**:
 1. Initialize the model with the **final weights** from Variant A (OPD).
 2. Train using PPO **without** any gradient projection.
 3. Log accuracy vs. steps.
- **Output**: Convergence curve. If Variant C (Projected) outperforms Variant F (Initialized), the geometric constraint itself (not just the starting point) drives foresight.

### 3. Metrics & Analysis

- **Convergence Efficiency**: Steps to reach high accuracy (Primary Success Metric).
- **Final Task Accuracy**: Accuracy on a held-out test set after convergence (Primary Success Metric).
- **Subspace Specificity**: Comparison of performance (Steps/Accuracy) between Variants C, D, E, and F.
- **Relevance Monitoring**: Average cosine similarity between RL update direction and OPD subspace (diagnostic only).
- **Statistical Significance**: Wilcoxon signed-rank test on steps-to-convergence across 10 seeds (FR-006, SC-003).

**Note on Alignment Metrics**: Early Trajectory Alignment (cosine similarity between Low-Rank RL and OPD) is a *diagnostic* metric to verify the projection is active, not a primary success criterion. The primary hypothesis is tested via task performance (Steps to [deferred] Accuracy and Final Task Accuracy).

### 4. Statistical Rigor & Assumptions

- **Multiple Comparisons**: Since six variants are compared, a Bonferroni correction is applied for pairwise tests (e.g., C vs. B, C vs. D, C vs. E, C vs. F).
- **Sample Size & Power**: The study mandates **10 independent runs (seeds)** per variant. This provides sufficient power (>0.8) to detect a medium effect size (Cohen's $d \ge 0.5$) with a Wilcoxon signed-rank test at $\alpha = 0.05$. A power analysis will be performed post-hoc; if power < 0.8, the result will be flagged as "inconclusive".
- **Causal Inference**: The study is observational regarding the "geometry" variable (derived from OPD). Claims will be framed as associational unless the experimental design (randomized seeds, controlled subspace) allows for stronger causal inference.
- **Collinearity**: The projection is an external constraint. The analysis acknowledges that the subspace and the RL objective may be correlated, but the projection isolates the geometric component.
- **Measurement Validity**: GSM8K is a standard benchmark for reasoning. The "foresight" proxy (convergence speed) is derived from the hypothesis that stable subspaces correlate with efficient reasoning paths.

### 5. Compute Feasibility

- **Hardware**: CPU-only (2 vCPU, 7GB RAM).
- **Model**: ~300M parameters (pruned from TinyLlama-1.1B). Full 1.1B model is too large.
- **Precision**: FP16 mixed precision to reduce memory footprint.
- **SVD Strategy**: Layer-wise SVD (only attention projections) or randomized SVD to avoid OOM.
- **Runtime**: Total pipeline capped at a fixed duration. Data is subset to a representative sample of problems. A feasible number of seeds per variant is within this limit due to the small model size.

### 6. Risks & Mitigations

- **Risk**: SVD fails due to memory limits.
 - *Mitigation*: Use randomized SVD or restrict SVD to attention layers only.
- **Risk**: Low-Rank RL fails to converge (over-constraining).
 - *Mitigation*: Dynamic rank adaptation (increase $k$) if relevance drops. If convergence fails, report stagnation and adjust $k$.
- **Risk**: Flat SVD spectrum (no clear low-rank structure).
 - *Mitigation*: Default to fixed $k=10$ or variance threshold (e.g., 90%) to ensure a defined projection matrix.
- **Risk**: Random Baseline (Variant D) or Random Walk (Variant E) performs better than OPD Baseline (Variant C).
 - *Mitigation*: This would falsify the hypothesis that *specific* OPD geometry drives foresight. Report as negative result.
- **Risk**: OPD-Initialized RL (Variant F) performs as well as Low-Rank RL (Variant C).
 - *Mitigation*: This would suggest initialization is sufficient, and the constraint is not needed. Report as partial falsification.