# Feature Specification: Exploring the Convergence of Iterated Function Systems with Non-Contractive Maps

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-27  
**Status**: Draft  
**Input**: User description: "Exploring the Convergence of Iterated Function Systems with Non-Contractive Maps"

## User Scenarios & Testing

### User Story 1 - Synthetic IFS Generation and Lipschitz Validation (Priority: P1)

As a researcher, I need to generate a diverse set of synthetic Iterated Function Systems (IFS) with controlled Lipschitz constants (ranging from 0.5 to 2.0) on the unit square [0,1]², and rigorously validate their numerical Lipschitz properties, so that I can establish a reliable dataset for testing the existence of invariant measures in non-contractive regimes.

**Why this priority**: This is the foundational step; without a verified dataset of maps with known properties, any subsequent analysis of invariant measures or topological structure is invalid. It directly addresses the "gap" of systematically characterizing Lipschitz thresholds.

**Independent Test**: Can be fully tested by generating a batch of 50 IFS instances, computing their numerical Lipschitz constants on a 1000-point grid, and verifying that the computed values fall within ±0.05 of the intended target values, independent of any convergence analysis.

**Acceptance Scenarios**:

1. **Given** a target Lipschitz constant of 1.2 and 3 affine maps, **When** the system generates the synthetic IFS instance, **Then** the computed numerical Lipschitz constant on the 1000-point grid is between 1.15 and 1.25.
2. **Given** a target Lipschitz constant of 0.8 (contractive), **When** the system generates the IFS, **Then** the computed Lipschitz constant is ≤ 0.85, ensuring the contractive baseline is correctly represented.
3. **Given** a set of 500 generated instances, **When** the validation script runs, **Then** at least 95% of instances have a computed Lipschitz constant within ±0.05 of their intended target, and any outliers are flagged for re-generation.

---

### User Story 2 - Invariant Measure Approximation via Monte Carlo (Priority: P2)

As a researcher, I need to approximate the empirical invariant measure for each generated IFS using the Chaos Game algorithm (sufficient iterations) and determine whether a non-trivial invariant measure exists, so that I can map the relationship between Lipschitz constants and measure existence.

**Why this priority**: This implements the core experimental methodology to test the research question. It moves from data generation to the actual investigation of the "non-contractive" regime's behavior.

**Independent Test**: Can be fully tested by running the Chaos Game on a known contractive IFS (e.g., Sierpinski triangle) and verifying the resulting point cloud density matches the theoretical fractal measure, independent of the non-contractive analysis.

**Acceptance Scenarios**:

1. **Given** a contractive IFS (Lipschitz < 1.0) with a known attractor, **When** the Chaos Game runs for 10⁶ iterations, **Then** the box-counting dimension of the resulting point cloud is within 0.1 of the theoretical dimension.
2. **Given** a non-contractive IFS (Lipschitz ≥ 1.0), **When** the Chaos Game runs, **Then** the system classifies the result as either "Converged" (points remain bounded within [0,1]² and satisfy the Wasserstein-2 convergence criterion) or "Divergent" (points escape the bounding box of [−1, 2]²).
3. **Given** an IFS instance, **When** the Monte Carlo simulation completes, **Then** the empirical measure is stored as a histogram with bin counts determined by Sturges' rule, and the system reports the Wasserstein-2 distance between the last 10 iteration windows.

---

### User Story 3 - Topological Analysis and Threshold Sensitivity (Priority: P3)

As a researcher, I need to compute topological descriptors (Minkowski-Bouligand dimension) of the limit sets and perform a sensitivity analysis on the Lipschitz threshold to determine the robustness of the observed transition from contractive to non-contractive behavior.

**Why this priority**: This addresses the "relationship to topological structure" part of the research question and satisfies the methodological requirement for threshold justification and sensitivity analysis.

**Independent Test**: Can be fully tested by analyzing a single IFS instance where the Lipschitz constant is varied slightly (e.g., 1.0, 1.05, 1.1) and verifying that the computed dimensions and convergence status change consistently with the theoretical expectations of the threshold.

**Acceptance Scenarios**:

1. **Given** a set of IFS instances where the Lipschitz constant crosses the theoretical boundary (e.g., 0.9, 1.0, 1.1), **When** the topological analysis runs, **Then** the system characterizes the nature of the transition (monotonic, discontinuous, or complex) and reports a detectable change (dimension shift > 0.05 or regression slope change with p < 0.05) at the boundary.
2. **Given** a detected transition point (e.g., Lipschitz = 1.2), **When** the sensitivity analysis sweeps the threshold over {1.15, 1.20, 1.25}, **Then** the system reports the variation in the "convergence stability" rate across these values.
3. **Given** a set of 500 instances, **When** the logistic regression model is fitted to predict convergence stability, **Then** the model achieves an AUC significantly better than random chance (p < 0.05 via permutation test) based on Lipschitz parameters and map overlap geometry.

### Edge Cases

- What happens when the Lipschitz constant is exactly 1.0 (marginally stable)? The system must handle this by running a longer iteration count (e.g., multiple millions) to distinguish between slow convergence and divergence.
- How does the system handle IFS instances where the maps are non-affine (e.g., polynomial)? The numerical gradient estimation on the 1000-point grid must be robust to non-linearities, or such instances are excluded and logged.
- What if the Monte Carlo simulation points diverge to infinity? The system must detect points leaving a bounding box of [−1, 2]² and classify the instance as "Divergent" immediately to save compute resources.
- What if the point cloud fills the space uniformly? The system must distinguish this "Uniform Filling" (potential Lebesgue measure) from "Divergence" (escaping bounds) by checking if the point density remains bounded within [0,1]² and satisfies the Wasserstein convergence check.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a set of synthetic IFS instances on [0,1]² with 2-4 maps each, varying Lipschitz constants from 0.5 to 2.0 in 0.1 increments, with instances distributed uniformly at random across the target values, serving the User Story 1 (See US-1).
- **FR-002**: System MUST compute the numerical Lipschitz constant for each map via gradient estimation on a discretized grid, serving the User Story 1 (See US-1).
- **FR-003**: System MUST execute the Chaos Game algorithm for a sufficient number of iterations per IFS instance to ensure convergence of the attractor. to approximate the empirical invariant measure, serving the User Story 2 (See US-2).
- **FR-004**: System MUST classify each IFS as having "Converged" or "Divergent" based on the Wasserstein-2 distance between the last 10 iteration windows (convergence threshold: W2 < 0.01) and whether points remain within [−1, 2]², serving the User Story 2 (See US-2).
- **FR-005**: System MUST compute the Minkowski-Bouligand dimension (approximated via box-counting method) of the limit set support at multiple scale levels, serving the User Story 3 (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis sweeping the Lipschitz threshold over {1.0, 1.1, 1.2} and report the standard deviation of the "convergence stability" rate across these values, serving the User Story 3 (See US-3).
- **FR-007**: System MUST fit a logistic regression model to predict "convergence stability" from Lipschitz parameters and map overlap geometry (defined as the ratio of the area of intersection of the images of the maps to the area of the unit square), serving the User Story 3 (See US-3).
- **FR-008**: System MUST validate results against multiple benchmark IFS (Sierpinski Triangle, Barnsley Fern, and a specific expanding map from da Cunha et al.) to confirm methodological correctness, serving the User Story 1 (See US-1).

### Key Entities

- **IFS Instance**: A collection of 2-4 continuous maps on [0,1]², characterized by their Lipschitz constants, map type (affine/non-affine), and overlap geometry.
- **Empirical Measure**: A discrete approximation of the invariant measure represented as a 2D histogram (using Sturges' rule for binning) or point cloud resulting from the Chaos Game.
- **Topological Descriptor**: Numerical values (e.g., Minkowski-Bouligand dimension) quantifying the fractal structure of the limit set.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The accuracy of the computed Lipschitz constant is measured against the theoretical Lipschitz constant defined in the synthetic generation parameters, with a success threshold of Mean Absolute Error (MAE) ≤ 0.05 (See US-1).
- **SC-002**: The accuracy of the box-counting dimension estimate is measured against the known theoretical dimension of the 3 benchmark IFS instances from the literature (See US-3).
- **SC-003**: The predictive power of the logistic regression model (AUC) is measured against the binary classification of "convergence stability" derived from the Wasserstein-2 distance check (See US-3).
- **SC-004**: The stability of the "convergence stability" classification is measured across the sensitivity analysis sweep of Lipschitz thresholds {1.0, 1.1, 1.2}, with a success threshold of standard deviation ≤ 0.05 (See US-3).
- **SC-005**: The computational runtime for the full instance analysis is measured against the GitHub Actions free-tier time limit. to ensure feasibility (See Assumptions).

## Assumptions

- The dataset generation and numerical gradient estimation on a dense grid for a representative set of IFS instances will fit within the RAM limit of the GitHub Actions free-tier runner, assuming efficient memory management (e.g., processing instances sequentially or in small batches).
- The Chaos Game algorithm with a sufficiently large number of iterations per instance will complete within the designated runtime limit., assuming the use of optimized vectorized operations (e.g., NumPy) and no GPU acceleration is required.
- The "non-contractive" regime is defined strictly by the numerical Lipschitz constant ≥ 1.0; any theoretical subtleties regarding "weak contraction" or specific map properties are handled by the numerical approximation.
- Several benchmark IFS instances (Sierpinski Triangle, Barnsley Fern, and a specific expanding map from da Cunha et al.) are available in a format that can be parsed and reconstructed within the Python environment for validation.
- The Wasserstein-2 distance metric (with threshold 0.01) is an appropriate and sensitive enough metric to distinguish "converged invariant measures" from "divergent/transient behavior" in the context of non-contractive IFS, as no alternative validated metric is specified in the idea.
- The sensitivity analysis sweep over {1.0, 1.1, 1.2} is sufficient to capture the transition behavior; finer granularity is deferred if computational constraints arise.