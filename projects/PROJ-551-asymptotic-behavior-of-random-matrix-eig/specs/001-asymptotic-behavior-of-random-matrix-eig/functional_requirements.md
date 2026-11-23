# Functional Requirements: Asymptotic Behavior of Random Matrix Eigenvalues

## FR-001: Wigner Matrix Generation
The system MUST generate symmetric $N \times N$ matrices with i.i.d. entries (mean 0, variance $1/N$).

**Inputs**:
- `n`: Matrix dimension (integer)
- `seed`: Random seed (integer)

**Outputs**:
- Symmetric matrix $W_N$
- Metadata (seed, timestamp, checksum)

## FR-002: Perturbation Construction
The system MUST create rank-$k$ perturbations with configurable sparsity patterns.

**Inputs**:
- `rank`: Number of non-zero eigenvalues (integer)
- `norm`: Perturbation strength $\theta$ (float)
- `pattern`: DIAGONAL, RANDOM_SPARSE, or BLOCK_SPARSE
- `sparsity_density`: Support density $p \in (0, 1]$

**Outputs**:
- Perturbation matrix $P_N$
- Verification of rank preservation

## FR-003: Eigenvalue Computation
The system MUST compute the top 10 eigenvalues using iterative solvers (ARPACK).

**Inputs**:
- Matrix $A = W_N + P_N$
- `tol`: Convergence tolerance (default $10^{-10}$)

**Outputs**:
- Sorted eigenvalues (descending)
- Validation against semicircle edge (±2.0)

## FR-004: Outlier Detection
The system MUST identify eigenvalues exceeding the theoretical bulk edge.

**Inputs**:
- Eigenvalues $\lambda_1, \dots, \lambda_{10}$
- Theoretical edge (±2.0)

**Outputs**:
- Boolean `outlier_detected`
- List of outlier eigenvalues

## FR-005: Parameter Sweep
The system MUST execute grid searches over $N$ and $\theta$.

**Inputs**:
- `matrix_sizes`: List of $N$ values
- `theta_range`: List of $\theta$ values
- `num_iterations`: Monte Carlo iterations per configuration

**Outputs**:
- Aggregated results (CSV)
- Fitted threshold parameters (JSON)

## FR-006: Sensitivity Analysis
The system MUST analyze stability across sparsity densities.

**Inputs**:
- `sparsity_densities`: List of $p$ values
- `base_theta`: Reference perturbation strength

**Outputs**:
- Variation in $\theta_c$ estimates
- Stability assessment report

## FR-007: Observational Constraint
All findings MUST be framed as associational correlations. No physical observer modeling is permitted.

## FR-008: Reproducibility
The system MUST log all random seeds, parameters, and timestamps.

## FR-009: Rank Preservation
The system MUST verify that sparsity masking does not alter the intended perturbation rank.

## FR-010: Data Hygiene
The system MUST capture checksums for all raw data instances.
