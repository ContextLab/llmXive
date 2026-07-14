# Feature Specification: Low-Rank RL for Foresight in LLM Training

**Feature Branch**: `001-low-rank-rl-foresight`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "Does the 'foresight' phenomenon in language model reasoning emerge primarily from the geometric stability of parameter update subspaces, or is it an emergent property of the supervised distillation objective itself?"

## User Scenarios & Testing

### User Story 1 - Establish Geometric Baseline via On-Policy Distillation (Priority: P1)

The researcher must be able to run an On-Policy Distillation (OPD) baseline on a GSM8K subset to generate a "stable subspace" defined by the top singular vectors of early parameter updates. This is the foundational step required to define the geometric constraint for the hybrid experiment.

**Why this priority**: Without the stable subspace derived from OPD, the "Low-Rank RL" hybrid cannot be constructed. This step isolates the geometric signal from the RL process.

**Independent Test**: Can be fully tested by running the OPD training loop for a fixed number of steps, extracting the accumulated update matrices, performing SVD, and verifying the existence of a defined subspace (top-k vectors) without running any RL.

**Acceptance Scenarios**:

1. **Given** a GSM8K subset of [deferred] problems and a 300M parameter model, **When** the system runs OPD for the first [deferred] of the training trajectory (capped at [deferred] steps), **Then** the system must output a matrix of shape (k, n_params) containing the top-$k$ singular vectors representing the stable update subspace.
2. **Given** the accumulated update matrices from the OPD run, **When** the system performs Singular Value Decomposition (SVD), **Then** the system must select $k$ such that the cumulative explained variance is ≥ 80%. If no $k$ achieves [deferred] variance, the system MUST default to $k=10$.

---

### User Story 2 - Execute Low-Rank RL Hybrid with Geometric Projection (Priority: P2)

The researcher must be able to train a PPO-based RL agent where the computed gradients are explicitly projected onto the stable subspace derived from User Story 1 before the parameter update is applied. This tests if the geometry alone can induce foresight.

**Why this priority**: This is the core experimental intervention. It directly tests the hypothesis that geometric stability, independent of the distillation objective, drives the foresight phenomenon.

**Independent Test**: Can be fully tested by running the PPO training loop with the projection module active, ensuring that every update step is mathematically constrained to the subspace defined in Story 1, and verifying that the update direction matches the projection.

**Acceptance Scenarios**:

1. **Given** the top-$k$ singular vectors from the OPD baseline and a standard PPO training step, **When** the system computes the raw RL gradient, **Then** the system must project this gradient onto the subspace and apply the update, ensuring the update vector lies entirely within the span of the top-$k$ vectors.
2. **Given** a training run of the Low-Rank RL variant, **When** the system logs the update direction at each step, **Then** the cosine similarity between the applied update and the subspace basis must be ≥ 0.99, confirming the projection constraint is active.

---

### User Story 3 - Compare Convergence and Subspace Alignment Across Variants (Priority: P3)

The researcher must be able to compare the sample efficiency (steps to [deferred] accuracy) and final subspace alignment of the Low-Rank RL variant against a standard RL baseline and the OPD baseline to determine if "foresight" was induced.

**Why this priority**: This provides the empirical answer to the research question. It synthesizes the data from the previous stories to validate or refute the hypothesis.

**Independent Test**: Can be fully tested by aggregating the accuracy-vs-steps curves from the three variants (Standard RL, Low-Rank RL, OPD) and running a statistical test (paired t-test or Wilcoxon) on the steps-to-threshold metric.

**Acceptance Scenarios**:

1. **Given** the convergence logs from Standard RL, Low-Rank RL, and OPD runs, **When** the system calculates the number of steps required to reach [deferred] accuracy on the GSM8K subset, **Then** it must output a comparison table and a convergence plot visualizing the relative efficiency.
2. **Given** the final accumulated update directions from all three variants, **When** the system computes the cosine similarity between each variant and the "optimal solution" direction (proxied by the final accumulated update direction of the standard PPO baseline), **Then** it must report the alignment scores to determine which variant best mimics the OPD trajectory.

### Edge Cases

- **What happens when** the SVD of the OPD trajectory yields a flat spectrum (no clear low-rank structure)? The system must default to a fixed $k$ (e.g., a representative number of top components) or a variance threshold (e.g., 90% explained variance) to prevent the projection matrix from being ill-defined.
- **How does the system handle** memory exhaustion during SVD on a 300M model? The system must perform SVD on a subset of layers (e.g., only attention projections) or use randomized SVD to ensure the operation fits within the available memory constraint.
- **What happens when** the Low-Rank RL variant fails to converge due to over-constraining the update space? The system must log the stagnation and allow for a sensitivity analysis on the rank $k$ (e.g., testing a range of low to high values) to find a feasible operating point.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute On-Policy Distillation (OPD) on a GSM8K subset (≥1,000 problems) and record parameter update matrices ($\Delta W$) for the first [deferred] of the training trajectory (capped at [deferred] steps). (See US-1)
- **FR-002**: System MUST perform Singular Value Decomposition (SVD) on the accumulated OPD update matrices to extract the top-$k$ singular vectors defining the stable subspace. (See US-1)
- **FR-003**: System MUST implement a PPO-based RL training loop that projects computed gradients onto the pre-computed top-$k$ singular vectors before applying the parameter update. (See US-2)
- **FR-004**: System MUST track the number of training steps required for each variant (Standard RL, Low-Rank RL, OPD) to reach a fixed accuracy threshold on the GSM8K subset. (See US-3)
- **FR-005**: System MUST compute the cosine similarity between the final accumulated update direction of each variant and the direction of the standard PPO baseline (used as the proxy for the optimal solution). (See US-3)
- **FR-006**: System MUST perform a statistical significance test (paired t-test or Wilcoxon signed-rank) on the steps-to-convergence metric across three independent runs for each variant. (See US-3)
- **FR-007**: System MUST ensure all training and analysis operations run on CPU-only hardware with a maximum memory footprint of 7 GB, a total execution time of ≤ 6 hours, and use a 300M parameter model (e.g., TinyLlama-300M) with mixed precision (FP16) and layer-wise SVD (attention projections only). (See US-4)
- **FR-008**: System MUST measure the cosine similarity between the Low-Rank RL trajectory and the OPD trajectory specifically during the first [deferred] of the training steps to validate early geometric alignment (foresight). (See US-3)

### Key Entities

- **Update Trajectory**: A sequence of parameter difference matrices ($\Delta W_t$) recorded during a training run, representing the path of optimization.
- **Stable Subspace**: A low-dimensional vector space defined by the top-$k$ singular vectors of the aggregated OPD update trajectory.
- **Convergence Metric**: The number of training steps required to achieve a specific accuracy threshold (80%) on the validation set.
- **Alignment Score**: The cosine similarity between the final update direction of a variant and the reference standard PPO baseline.
- **Early Trajectory Alignment**: The average cosine similarity between the Low-Rank RL update direction and the OPD update direction calculated over the first [deferred] of the training steps.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The steps-to-80%-accuracy for the Low-Rank RL variant is measured against the Standard RL baseline to determine if geometric constraints reduce sample complexity. (See US-3)
- **SC-002**: The final subspace alignment (cosine similarity) of the Low-Rank RL variant is measured against the standard PPO baseline to determine if the hybrid converges in a similar geometric direction. (See US-3)
- **SC-003**: The statistical significance of the difference in convergence steps between Low-Rank RL and Standard RL is measured against a p-value threshold of < 0.05 using a Wilcoxon signed-rank test. (See US-3)
- **SC-004**: The memory usage during SVD and training for all experimental variants (OPD, Standard RL, Low-Rank RL) is measured against the available RAM limit to ensure the experiment is feasible on free-tier CPU runners. (See US-1, US-2)
- **SC-005**: The total wall-clock time for the full experimental pipeline (OPD + RL Baseline + Hybrid + Analysis) is measured against a predefined time constraint. (See US-1, US-2, US-3, US-4)
- **SC-006**: The Early Trajectory Alignment (first [deferred] of steps) of the Low-Rank RL variant is measured against the OPD baseline to validate that the geometric constraint induces foresight early in training. (See US-3)

## Assumptions

- **Assumption about data**: The GSM8K dataset (first [deferred] problems) contains sufficient reasoning diversity to serve as a proxy for the "foresight" phenomenon; if the dataset lacks complexity, the results may not generalize to harder reasoning tasks.
- **Assumption about model**: A M parameter model (e.g., TinyLlama-300M or similar) is sufficiently small to run in mixed precision (FP16) on CPU within the 7 GB RAM and 6-hour time limit, provided that the dataset is not excessively large and training steps are capped.
- **Assumption about geometry**: The top-$k$ singular vectors (where $k$ is a small integer, e.g., 10-50) capture the majority of the "stable" geometric signal from the OPD trajectory, and projecting onto this subspace does not eliminate essential learning dynamics.
- **Assumption about inference framing**: Since the study uses observational data (training trajectories) without random assignment of the "geometry" variable (it is derived from OPD), findings will be framed as associational (e.g., "Low-Rank RL is associated with faster convergence") rather than strictly causal, unless the experimental design isolates the geometry as the sole variable.
- **Assumption about collinearity**: The predictors (OPD subspace vs. RL objective) are not definitionally identical; the projection is an external constraint applied to the RL process, allowing for a descriptive analysis of their joint relationship.
- **Assumption about threshold**: The 80% accuracy threshold is a community-standard proxy for "reasoning competence" on GSM8K subsets; sensitivity analysis on this threshold (e.g., 75%, 85%) will be deferred to the implementation phase if time permits, but the primary metric is fixed at [deferred] for consistency.
- **Assumption about hardware feasibility**: A 300M parameter model running in FP16 with layer-wise SVD (attention projections only) will fit within the 7 GB RAM constraint and complete within 6 hours on a standard CPU runner.
- **Assumption about reference proxy**: The final accumulated update direction of the standard PPO baseline (unconstrained) is a valid proxy for the "optimal solution" direction for comparative alignment analysis within the same compute budget, as a high-accuracy reference model cannot fit in the defined memory.
- **Assumption about sample size**: The GSM8K subset of [deferred] problems is sufficient to detect a statistically significant difference in convergence steps, assuming a medium effect size (Cohen's d ≥ 0.5) and power ≥ 0.8. The system MUST run at least 3 independent seeds per variant and perform a power analysis post-hoc; if the observed effect size is < 0.5, the sample size MUST be increased to [deferred] problems or the experiment MUST be flagged as inconclusive.