# Feature Specification: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

**Feature Branch**: `001-asymptotic-behavior-of-random-matrix-eig`  
**Created**: 2026-07-05  
**Status**: Draft  
**Input**: User description: "How does the rank and sparsity pattern of a deterministic perturbation affect the emergence of outlier eigenvalues in the limiting spectral distribution of Wigner matrices as matrix dimension approaches infinity?"

## User Scenarios & Testing

### User Story 1 - Core Spectral Analysis of Perturbed Wigner Matrices (Priority: P1)

A researcher needs to generate Wigner matrices of varying dimensions (up to N=2000), apply deterministic perturbations of fixed rank but varying sparsity patterns (diagonal, block-sparse, random sparse), and compute the resulting eigenvalue spectra to identify outliers relative to the theoretical semicircle law edge.

**Why this priority**: This is the foundational capability required to answer the primary research question. Without the ability to generate the matrices and compute their spectra, no analysis of outlier emergence can occur.

**Independent Test**: Can be fully tested by running a simulation script that generates a single instance of a perturbed matrix, computes its eigenvalues, and verifies that the largest eigenvalue exceeds the theoretical bulk edge (2.0) when the perturbation norm is sufficiently large, while remaining within the bulk when the norm is small.

**Acceptance Scenarios**:

1. **Given** a Wigner matrix of dimension N=1000 and a rank-1 diagonal perturbation with spectral norm θ=2.5, **When** the eigenvalues are computed, **Then** at least one eigenvalue must be detected outside the interval [-2.0, 2.0] (specifically > 2.0).
2. **Given** a Wigner matrix of dimension N=1000 and a rank-1 diagonal perturbation with spectral norm θ=1.5, **When** the eigenvalues are computed, **Then** all eigenvalues must fall within a symmetric interval centered at zero (within a specified tolerance) (DOI/arXiv/author-year).

---

### User Story 2 - Phase Transition Threshold Detection (Priority: P2)

A researcher needs to systematically vary the spectral norm of the perturbation across a range of values (e.g., θ ∈ [1.0, 3.0]) and matrix dimensions (N ∈ [100, 2000]) to empirically determine the critical threshold where outlier eigenvalues begin to emerge for different sparsity patterns.

**Why this priority**: This extends the core analysis to address the "asymptotic behavior" and "phase transition" aspects of the research question, providing the data necessary to characterize the threshold shift caused by sparsity.

**Independent Test**: Can be fully tested by executing a parameter sweep script that generates a grid of perturbation norms and dimensions, records the presence/absence of outliers for each configuration, and outputs a dataset that clearly shows a transition from "no outlier" to "outlier present" as the norm increases.

**Acceptance Scenarios**:

1. **Given** a set of 100 simulations for each perturbation norm in the range [1.5, 2.5] with step 0.1, **When** the results are aggregated over 100 independent runs, **Then** the probability of outlier emergence must show a monotonic increase from near zero to near 1.0 as the norm increases.
2. **Given** two different sparsity patterns (e.g., diagonal vs. random sparse) with the same rank and norm, **When** the transition thresholds are compared, **Then** the system must output a distinct critical norm value for each pattern if a difference exists, or confirm statistical equivalence if no difference is found.

---

### User Story 3 - Sensitivity Analysis of Sparsity Thresholds (Priority: P3)

A researcher needs to perform a sensitivity analysis on the sparsity parameter of the perturbation matrix to determine how robust the outlier emergence threshold is to small changes in the sparsity pattern, ensuring the findings are not artifacts of a specific discrete configuration.

**Why this priority**: This addresses the methodological requirement for threshold justification and sensitivity analysis, ensuring the results are scientifically defensible and not dependent on arbitrary choices of sparsity parameters.

**Independent Test**: Can be fully tested by running a script that varies the sparsity level (defined as the support density p) of the perturbation matrix over a small concrete set (e.g., {0.1, 0.2, 0.3}) and reports the variation in the detected outlier threshold.

**Acceptance Scenarios**:

1. **Given** a perturbation matrix with a fixed rank and a nominal sparsity level S, where S is swept across the set {0.1, 0.2, 0.3}, **When** the sparsity is swept, **Then** the system must report the change in the critical norm required for outlier emergence for each step.
2. **Given** the sensitivity analysis results, **When** the data is reviewed, **Then** the report must explicitly state whether the outlier threshold shifts significantly (e.g., > 5% change relative to the nominal sparsity threshold) or remains stable across the swept sparsity values.

### Edge Cases

- What happens when the perturbation rank $k$ is 0 (i.e., no perturbation)? The system must correctly identify that no outliers exist and the spectrum follows the standard semicircle law.
- How does the system handle matrix dimensions $N$ where the memory constraint (7 GB RAM) is exceeded during eigenvalue computation? The system must gracefully fail with a clear error message suggesting a reduction in $N$ or a switch to iterative solvers.
- What happens when the perturbation norm $\theta$ is exactly at the theoretical BBP threshold (e.g., $\theta = 1$)? The system must handle the numerical instability near the edge and report the result with appropriate confidence intervals or note the ambiguity. Note: While 1.0 is the theoretical threshold for dense perturbations, this study investigates if sparse perturbations shift this threshold, making $\theta=1$ a critical boundary case to test.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate Wigner matrices of dimension $N$ where entries are drawn from a standard normal distribution, scaled by $1/\sqrt{N}$, for $N \in [100, 2000]$. (See US-1)
- **FR-002**: System MUST construct deterministic perturbation matrices $P_N$ with fixed rank $k \in \{1, 2, 5\}$ and configurable sparsity patterns (diagonal, block-sparse, random sparse support). For fixed rank, 'sparsity' refers to the support structure or support density. (See US-1)
- **FR-003**: System MUST compute the extreme eigenvalues (top 10) of the perturbed matrix $A_N = W_N + P_N$ using CPU-tractable iterative solvers that fit within available memory constraints of the execution environment. (See US-1)
- **FR-004**: System MUST detect and record "outlier" eigenvalues as those exceeding the theoretical bulk support edge (2.0) by a margin of at least 0.05 OR exceeding the predicted BBP outlier location $\lambda = \theta + 1/\theta$ for $\theta > 1$. (See US-2)
- **FR-005**: System MUST perform a parameter sweep over perturbation norms $\theta \in [1.0, 3.0]$ with a step size of 0.1 to identify the critical threshold for outlier emergence. (See US-2)
- **FR-006**: System MUST execute a sensitivity analysis on the sparsity parameter by sweeping the support density over a defined set of ratios and reporting the variation in the critical threshold. (See US-3)
- **FR-007**: System MUST frame all reported findings as associational correlations between perturbation structure and outlier emergence, avoiding causal claims unless randomization is explicitly simulated. (See US-1, US-2, US-3)
- **FR-008**: System MUST fix the base Wigner matrix to be dense (p=1) to isolate the effect of perturbation sparsity, acknowledging this as a scope boundary. (See US-1)
- **FR-009**: System MUST investigate the potential shift in the BBP threshold due to perturbation sparsity, acknowledging the theoretical consensus that for finite-rank perturbations of Wigner matrices, the threshold is typically $\theta=1$, and the experiment is designed to verify this or detect deviations. (See US-2)
- **FR-010**: System MUST use a convergence tolerance of $1e-10$ and compute the top 10 eigenvalues when using iterative solvers to ensure reliable detection of outliers near the bulk edge. (See FR-003)

### Key Entities

- **WignerMatrix**: A symmetric random matrix with independent Gaussian entries scaled by $1/\sqrt{N}$.
- **PerturbationMatrix**: A deterministic low-rank matrix with specific sparsity patterns and spectral norm $\theta$.
- **SpectralOutlier**: An eigenvalue of the perturbed matrix that lies outside the interval [-2.0, 2.0] or exceeds the predicted BBP location.
- **PhaseTransitionThreshold**: The critical value of $\theta$ at which the probability of outlier emergence transitions from near 0 to near 1.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The critical perturbation norm $\theta_c$ for outlier emergence is measured against the theoretical BBP threshold of 1.0 for dense perturbations, to determine the shift caused by sparsity. (See FR-005)
- **SC-002**: The variation in the critical threshold $\theta_c$ is measured across the sparsity sweep set to assess the sensitivity of the phase transition to sparsity pattern. (See FR-006)
- **SC-003**: The empirical probability of outlier emergence is measured against the theoretical prediction for the given perturbation norm and rank to validate the simulation model. (See FR-004)
- **SC-004**: The computational runtime for the full parameter sweep (N=2000, 100 iterations per norm) is measured against the 6-hour CI job limit to ensure feasibility. (See FR-003)

## Assumptions

- The dataset (generated random matrices) contains all necessary variables (eigenvalues, perturbation norms, sparsity patterns) to answer the research question, as the variables are constructed synthetically rather than extracted from an external source.
- The analysis is purely observational (simulated data), so all findings are framed as associational relationships between perturbation structure and spectral properties, not causal effects.
- The sample size (number of Monte Carlo iterations per configuration) is set to 100 to balance statistical power with the 6-hour compute constraint; this number is a defensible community-standard default for simulation studies of this scale.
- The threshold for defining an "outlier" (eigenvalue > 2.0 + 0.05 or > $\theta + 1/\theta$) is justified by the theoretical edge of the semicircle law and the numerical precision limits of the solver; a sensitivity analysis is performed by varying this margin by ±0.02 to ensure robustness.
- The perturbation sparsity patterns (diagonal, block-sparse, random) are representative of the class of sparse perturbations relevant to the research question, and the results are not expected to generalize to all possible sparse structures without further study.
- The iterative solver (ARPACK) is sufficient to compute the largest eigenvalues within the 7 GB RAM constraint for matrices up to N=2000; if memory limits are exceeded, the system will reduce N or switch to a more memory-efficient method.
- The perturbation rank $k$ is fixed and small ($k \le 5$) to ensure the perturbation remains "finite-rank" in the asymptotic limit, consistent with the research question's focus on low-rank signals.
- The base Wigner matrix is fixed to be dense (p=1) to isolate the effect of perturbation sparsity, as the primary focus is on the sparsity of the perturbation $P_N$. Future work may explore sparse base matrices.
- The computational environment (GitHub Actions free tier) provides a multi-core CPU and sufficient RAM, which is adequate for the proposed simulation size and method.
- The theoretical BBP threshold for dense perturbations serves as the baseline reference for comparing the effects of sparsity.
- The specific sparsity ratios {0.1, 0.2, 0.3} used in the sensitivity analysis are a default sweep set chosen to demonstrate the methodology; other sets may be used in future experiments.
- The 'sparsity parameter' for fixed-rank matrices refers to the support density (probability of a non-zero entry in the support mask) rather than the ratio of non-zeros to $N^2$, which would change the rank.