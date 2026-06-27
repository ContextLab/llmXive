# Feature Specification: Quantifying the Effect of Disorder on Electronic Transport in 1D Chains

**Feature Branch**: `[001-quantifying-disorder-effect]`  
**Created**: 2026-06-07  
**Status**: Draft  
**Input**: User description: "Quantifying the Effect of Disorder on Electronic Transport in 1D Chains"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compute Localization Length via Participation Ratio (Priority: P1)

As a computational physicist, I need to generate disordered 1D tight-binding Hamiltonians and compute the localization length of eigenstates near the band center using the participation ratio method, so that I can quantify how disorder strength affects electronic localization.

**Why this priority**: This is the core analysis method specified in the idea. Without it, no localization length measurements exist. It forms the minimum viable research product.

**Independent Test**: Can be fully tested by generating a single disorder realization (L=400, W=1.0), computing eigenstates, extracting participation ratios for states within |E| < 0.1 of band center, and verifying PR values decrease with increasing W.

**Acceptance Scenarios**:

1. **Given** a Hamiltonian with L=400 sites and disorder width W=1.0, **When** eigenstates near E=0 are computed, **Then** participation ratios must be calculated for all eigenstates within |E| < 0.1 of band center
2. **Given** 100 disorder realizations at W=1.0, **When** localization lengths are extracted via PR scaling, **Then** the mean localization length must have a standard error ≤ 10% of the mean value
3. **Given** increasing disorder widths (W=0.5, 1.0, 2.0), **When** localization lengths are compared, **Then** ξ must decrease monotonically with increasing W

---

### User Story 2 - Verify with Transfer Matrix Method (Priority: P2)

As a computational physicist, I need to implement the transfer matrix method as an independent validation approach, so that I can confirm the participation ratio results are not method-dependent artifacts.

**Why this priority**: This provides methodological robustness. The idea explicitly requires "independent validation" via transfer matrix. Without it, results are single-method and less defensible.

**Independent Test**: Can be fully tested by running the transfer matrix method on the same Hamiltonian realizations used for PR analysis, computing Lyapunov exponents, and verifying ξ_TM ≈ ξ_PR within 15% for at least 80% of realizations.

**Acceptance Scenarios**:

1. **Given** 100 disorder realizations at W=1.0, **When** transfer matrix products are computed [deferred] iterations, **Then** Lyapunov exponents must yield localization lengths consistent with PR values within 15% relative error
2. **Given** increasing system sizes (L=100, 200, 400, 800), **When** transfer matrix convergence is monitored, **Then** the relative change in γ between consecutive size doublings must be ≤ 5% at L=800
3. **Given** a specific eigenstate at E=0, **When** both PR and transfer matrix methods are applied, **Then** the two localization length estimates must agree within 15% for at least 80 out of 100 realizations

---

### User Story 3 - Visualize Eigenstate Localization Patterns (Priority: P3)

As a computational physicist, I need to visualize individual eigenstate probability densities across chain sites, so that I can point to specific sites where the electron is localized and verify the exponential decay pattern (addressing reviewer Feynman's request for worked examples).

**Why this priority**: This addresses the Feynman reviewer comment about visualizing "what the electron is doing." It provides interpretability beyond numerical metrics but is not required for the core localization length analysis.

**Independent Test**: Can be fully tested by generating a single eigenstate visualization (L=200, W=2.0, E≈0), confirming the probability density shows clear exponential decay from a localization center, and verifying the decay length matches the computed ξ.

**Acceptance Scenarios**:

1. **Given** an eigenstate at E=0 with W=2.0 and L=200, **When** the probability density |ψ_i|² is plotted across all sites, **Then** the plot must show clear exponential decay from at least one localization center
2. **Given** the same eigenstate, **When** a logarithmic scale plot of |ψ_i|² vs distance from localization center is generated, **Then** the slope must yield a decay length within 20% of the computed localization length ξ
3. **Given** a comparison between W=0.5 and W=2.0 eigenstates, **When** their probability densities are plotted, **Then** the W=2.0 state must show visibly narrower spatial extent (full width at half maximum ≤ 60% of W=0.5 state)

---

### Edge Cases

- What happens when disorder width W=0 (no disorder)? The system should produce delocalized eigenstates with PR scaling extensively with system size., and the code must handle this boundary case without numerical instability in the log(ξ) vs log(W) fit.
- How does the system handle numerical precision limits for large L=1600 matrices? The diagonalization must complete within memory constraints; if scipy.linalg.eigh fails due to RAM, the system must fall back to iterative eigensolvers for states near band center only.
- What happens when a transfer matrix product underflows to zero? The system must implement logarithmic accumulation (sum of log singular values) rather than direct matrix multiplication to maintain numerical stability [deferred] iterations.
- How does the system handle edge sites in the chain? The tight-binding Hamiltonian must use open boundary conditions (no periodic wrapping) consistent with the 1D Anderson model formulation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate 1D tight-binding Hamiltonian matrices of size L×L with nearest-neighbor hopping t=1 and on-site energies ε_i drawn from uniform distribution U(-W/2, W/2) for each disorder width W (See US-1)
- **FR-002**: System MUST compute participation ratio PR = (∑|ψ_i|²)² / ∑|ψ_i|⁴ for eigenstates within |E| < 0.1 of band center (See US-1)
- **FR-003**: System MUST extract localization length ξ from PR scaling with system size using the relationship ξ ∝ PR (See US-1)
- **FR-004**: System MUST implement transfer matrix method computing Lyapunov exponent γ = 1/ξ from product of random transfer matrices [deferred] iterations (See US-2)
- **FR-005**: System MUST perform linear regression of log(ξ) vs log(W) and report slope, R², and 95% confidence intervals (See US-1)
- **FR-006**: System MUST generate probability density visualizations |ψ_i|² vs site index for eigenstates near E=0 (See US-3)
- **FR-007**: System MUST run all computations on CPU-only infrastructure with ≤7 GB RAM and complete within 6 hours total (See US-1)
- **FR-008**: System MUST use scipy.linalg.eigh for exact diagonalization; if memory exceeds 6 GB for L=1600, fall back to scipy.sparse.linalg.eigsh targeting only states near E=0 (See US-1)
- **FR-009**: System MUST implement logarithmic accumulation for transfer matrix products to prevent numerical underflow [deferred] iterations (See US-2)
- **FR-010**: System MUST apply Bonferroni correction for multiple hypothesis testing across 10 disorder widths (See US-1)

### Key Entities

- **Hamiltonian**: 1D tight-binding matrix with nearest-neighbor hopping t=1 and random on-site potential ε_i ~ U(-W/2, W/2); key attributes: size L, disorder width W, eigenvalues, eigenvectors
- **Eigenstate**: Single eigenvector ψ with associated eigenvalue E; key attributes: probability density |ψ_i|², participation ratio PR, energy E
- **Localization Length**: Derived quantity ξ computed from PR or transfer matrix; key attributes: value, uncertainty, method of computation (PR or TM)
- **Disorder Realization**: Single instance of random on-site potentials; key attributes: W value, L value, realization index (1-100)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Localization length scaling exponent (slope of log(ξ) vs log(W)) is measured against theoretical prediction for weak disorder; success if fitted slope is within 95% confidence interval of -1 (See US-1)
- **SC-002**: Method agreement is measured against PR baseline; success if transfer matrix localization lengths agree with PR values within 15% relative error for ≥80% of realizations (See US-2)
- **SC-003**: Statistical power is measured against t-test requirements; success if 100 disorder realizations per W value achieve ≥80% power to detect slope deviation from -1 at α=0.05 (See US-1)
- **SC-004**: Visualization decay length is measured against computed localization length; success if eigenstate probability density plots show decay lengths within 20% of ξ (See US-3)
- **SC-005**: Multiplicity correction is measured against family-wise error rate; success if Bonferroni-corrected p-values maintain FWER ≤ 0.05 across 10 disorder widths (See US-1)
- **SC-006**: Compute feasibility is measured against hardware constraints; success if all 1000 realizations (10 W values × 100 realizations) complete within 6 hours on 2 CPU cores with ≤7 GB peak RAM (See US-1)

## Assumptions

- The 1D Anderson model with uncorrelated on-site disorder will exhibit all states localized for any W > 0, consistent with theoretical predictions; this is not tested but used to frame the scaling analysis.
- The uniform distribution U(-W/2, W/2) for on-site potentials is the standard convention for weak disorder scaling studies; alternative distributions (Gaussian, binary) are out of scope.
- States within |E| < 0.1 of the band center (E=0) are representative of localization behavior across the spectrum; states near band edges may show different scaling and are excluded.
- The relationship ξ ∝ PR holds for 1D systems; this proportionality constant is absorbed into the localization length definition and does not require independent calibration.
- Sample size of 100 realizations per disorder width provides sufficient statistical power; if post-hoc power analysis shows <80% power, the limitation will be documented but not block completion.
- Theoretical prediction of inverse scaling between ξ and W (negative slope in log-log space) applies to weak disorder regime (W < 1); stronger disorder may show deviations that are recorded as findings rather than failures.
- All computations will use double-precision floating point (64-bit); single precision is not used as it may introduce numerical instability in transfer matrix products.
- Open boundary conditions (no periodic wrapping) are used for the tight-binding chain; periodic boundary conditions would alter finite-size scaling and are excluded.
- The transfer matrix method will use [deferred] iterations as the default; this is based on convergence studies in the literature and is sufficient for L ≤ 1600.
- Bonferroni correction is applied across the 10 disorder widths as the family of hypothesis tests; this is conservative but ensures FWER control without requiring more complex methods.
