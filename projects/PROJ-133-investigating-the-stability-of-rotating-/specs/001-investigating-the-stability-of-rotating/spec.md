# Specification: Investigating the Stability of Rotating Bose-Einstein Condensates with Dipolar Interactions

## 1. Introduction

This document defines the requirements for simulating the stability of rotating
Bose-Einstein Condensates (BECs) with dipolar interactions. The primary goal is
to generate a phase diagram mapping the stability regimes as a function of
rotation frequency ($\Omega$) and dipolar interaction strength ($\epsilon_{dd}$).

## 2. Functional Requirements

### FR-001: GPE Solver Implementation
Implement a split-step Fourier solver for the time-dependent Gross-Pitaevskii Equation (GPE)
including the dipolar interaction term.
- **Grid Resolution**: Use a **256x256 grid** for verification runs and a **64x64 grid** for the full batch scan (conditional on `RUN_FULL_GRID=true`).
- **Domain**: Square domain with periodic boundary conditions.
- **Time Stepping**: Adaptive or fixed time step based on stability criteria.

### FR-002: Initial Conditions
Generate Thomas-Fermi approximations for the initial state of the condensate
based on particle number $N$ and interaction strengths.

### FR-003: Vortex Detection
Implement a phase-winding algorithm to detect quantized vortices in the wavefunction.
- Must correctly identify vortex-antivortex pairs.
- Output: List of (x, y) coordinates and circulation signs.

### FR-004: Stability Metrics
Calculate quantitative metrics to classify the stability of the condensate.
- **Primary Metric**: **Vortex Density** (number of vortices per unit area).
- **Secondary Metrics**: Radial Variance, Structure Factor Sharpness.
- **Classification**:
 - **Stable**: Vortex density remains low and constant.
 - **Metastable**: Vortex density increases slowly or fluctuates within a bound.
 - **Unstable**: Rapid increase in vortex density or collapse of the condensate.

### FR-005: Statistical Analysis
Perform statistical analysis on the aggregated simulation results.
- **Method**: **Two-Way ANOVA** (factors: $\Omega$ and $\epsilon_{dd}$) to determine significant effects.
- **Post-hoc**: Dunnett's test for pairwise comparisons against a control group.
- **Significance**: $\alpha = 0.05$.

## 3. System Constraints

### SC-001: Performance
- The full grid scan (approx. 300 runs) must complete within 6 hours on a standard 2-core CI runner.
- Memory usage must not exceed 14 GB.
- If a simulation crashes due to numerical instability, it must be logged and marked as unstable (retention=0), but the pipeline must continue.

### SC-002: Metric Thresholds
- **Metastability Boundary**: Defined as a drop in condensate density > 30% or a specific threshold in **vortex density**.
- **Stability Threshold**: A binary classification based on the calculated **vortex density** exceeding a critical value derived from the simulation parameters.

### SC-003: Statistical Rigor
- All statistical tests must be reproducible using the seeded random state.
- P-values must be reported with at least 4 decimal places.

## 4. Data Model

### SimulationRun
- `run_id`: Unique identifier
- `parameters`: Dict containing $\Omega$, $\epsilon_{dd}$, $N$, grid_size
- `status`: 'success', 'failed', 'unstable'
- `metrics`: Dict of calculated stability metrics
- `artifacts`: Paths to output files (density, phase snapshots)

### StabilityMetric
- `vortex_density`: float (vortices/area)
- `radial_variance`: float
- `structure_factor_sharpness`: float
- `classification`: 'stable', 'metastable', 'unstable'

## 5. Assumptions

- The dipolar interaction range is sufficiently captured by the chosen grid resolution.
- The Thomas-Fermi approximation provides a valid starting point for the dynamics.
- Numerical instabilities are rare enough that the batch runner can handle them without manual intervention.

## 6. Revision History

| Date | Version | Description |
|------|---------|-------------|
| 2023-10-27 | 1.0 | Initial draft |
| 2023-10-28 | 1.1 | Updated FR-004 to use **Vortex Density** instead of retention fraction (T021b). Updated SC-001/SC-002 accordingly. |