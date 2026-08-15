# User Stories: Asymptotic Behavior of Random Matrix Eigenvalues

## US1: Core Spectral Analysis (Priority: P1)
**As a** researcher,
**I want** to generate Wigner matrices with sparse perturbations and compute eigenvalues,
**So that** I can identify outliers beyond the semicircle bulk.

**Acceptance Criteria**:
- [ ] Generate $N=1000$ Wigner matrix with rank-1 diagonal perturbation ($\theta=2.5$)
- [ ] Verify existence of eigenvalue > 2.0
- [ ] Log all parameters and random seeds to `data/logs/simulation_run.log`
- [ ] Save raw matrix to `data/raw/` with checksum

**Test Scenario**:
```python
# Run single simulation
result = run_simulation(n=1000, theta=2.5, seed=42)
assert result.outlier_detected == True
assert any(λ > 2.0 for λ in result.eigenvalues)
```

## US2: Phase Transition Threshold (Priority: P2)
**As a** researcher,
**I want** to sweep perturbation norms and dimensions,
**So that** I can empirically determine the critical threshold $\theta_c$.

**Acceptance Criteria**:
- [ ] Execute grid search: $N \in [500, 2000]$, $\theta \in [1.0, 3.0]$
- [ ] Output monotonic transition from "no outlier" to "outlier"
- [ ] Fit sigmoid curve to estimate $\theta_c$ with confidence intervals
- [ ] Compare $\theta_c$ across sparsity patterns

**Test Scenario**:
```python
# Run parameter sweep
results = run_sweep(matrix_sizes=[500, 1000, 2000], theta_range=[1.0, 3.0])
assert is_monotonic(results.outlier_probability)
assert results.theta_c_estimate > 0.9 and results.theta_c_estimate < 1.2
```

## US3: Sensitivity Analysis (Priority: P3)
**As a** researcher,
**I want** to analyze sensitivity to sparsity parameters,
**So that** I can ensure findings are robust to discrete configuration choices.

**Acceptance Criteria**:
- [ ] Sweep sparsity density $p \in \{0.1, 0.2, 0.3\}$
- [ ] Report if $\theta_c$ shifts > 5%
- [ ] Handle edge case $k=0$ (no perturbation)
- [ ] Generate sensitivity report with stability assessment

**Test Scenario**:
```python
# Run sensitivity analysis
report = run_sensitivity(sparsity_densities=[0.1, 0.2, 0.3])
assert report.stability == "STABLE" or report.max_shift < 0.05
```

## Edge Cases
- **N=100**: Small matrix validation
- **θ=1.0**: Boundary condition (no outlier expected)
- **k=0**: No perturbation (semicircle law only)
- **p=0**: Zero sparsity (full perturbation)
