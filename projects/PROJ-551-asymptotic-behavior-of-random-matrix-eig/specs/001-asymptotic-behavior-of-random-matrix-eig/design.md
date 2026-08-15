# Design Document: Asymptotic Behavior of Random Matrix Eigenvalues

## Problem Statement
Investigate how sparse deterministic perturbations affect the eigenvalue distribution of large Wigner matrices. Specifically, determine the critical perturbation strength $\theta_c$ where outlier eigenvalues emerge beyond the semicircle bulk.

## Theoretical Background
### Wigner Semicircle Law
For an $N \times N$ symmetric matrix $W_N$ with i.i.d. entries (mean 0, variance $1/N$), the empirical spectral distribution converges to:
$$ \rho(x) = \frac{1}{2\pi} \sqrt{4 - x^2}, \quad x \in [-2, 2] $$

### BBP Phase Transition
When adding a rank-$k$ perturbation $P_N$ with norm $\theta$, outliers emerge when $\theta > 1$. The outlier location is given by:
$$ \lambda_{out} = \theta + \frac{1}{\theta} $$

## Architecture
### Components
1. **Generators**: Create Wigner matrices and perturbations
2. **Solvers**: Compute eigenvalues using iterative methods
3. **Analyzers**: Detect outliers and fit threshold curves
4. **Hygiene**: Capture checksums and ensure data integrity

### Data Flow
```
[Config] → [Generator] → [Raw Matrix] → [Solver] → [Eigenvalues]
 ↓
 [Checksum] → [Storage]
 ↓
 [Analyzer] → [Results]
```

## Implementation Strategy
1. **Phase 1**: Setup project structure and dependencies
2. **Phase 2**: Build foundational utilities (config, hygiene, models)
3. **Phase 3**: Implement core simulation (US1)
4. **Phase 4**: Execute parameter sweep (US2)
5. **Phase 5**: Perform sensitivity analysis (US3)
6. **Phase 6**: Document and validate reproducibility

## Constraints
- **Memory**: < 7 GB RAM for $N=2000$
- **Compute**: CPU-only, use ARPACK for $N > 500$
- **Reproducibility**: Fixed seeds, structured logging, checksums
- **Observational**: No physical observer modeling (FR-007)

## Risk Mitigation
- **Memory overflow**: Use streaming for large matrices
- **Non-convergence**: Validate eigenvalues against semicircle edge
- **Data corruption**: Implement checksums at every stage
- **Irreproducibility**: Log all seeds and parameters
