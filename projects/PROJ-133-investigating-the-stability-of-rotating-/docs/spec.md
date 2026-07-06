# Specification: Investigating the Stability of Rotating Bose-Einstein Condensates with Dipolar Interactions

## 1. Introduction

This document outlines the requirements for simulating the stability of rotating Bose-Einstein Condensates (BECs) with dipolar interactions. The project aims to generate a phase diagram identifying stable, metastable, and unstable regimes based on rotation frequency ($\Omega$), dipolar interaction strength ($\epsilon_{dd}$), and atom number ($N$).

## 2. Functional Requirements (FR)

### FR-001: GPE Solver Implementation
The system must implement a split-step Fourier method solver for the time-dependent Gross-Pitaevskii Equation (GPE) including dipolar interaction terms.

**Grid Resolution Constraints**:
- **Verification Mode**: The solver must support a **256x256** grid resolution for detailed verification of specific parameter sets.
- **Batch Scan Mode**: For the full parameter grid scan, the solver must default to a **64x64** grid resolution to ensure computational feasibility within CI limits, unless explicitly overridden.
- **Configuration**: The grid size is controlled by the environment variable `RUN_FULL_GRID`.
 - If `RUN_FULL_GRID=true` (default), the solver uses **64x64**.
 - If `RUN_FULL_GRID=false`, the solver uses **256x256** (for verification).

**Performance Assumptions**:
- The 64x64 grid resolution is assumed to allow the full batch scan (approx. 300 runs) to complete within 6 hours on a standard 2-core CI runner.
- The 256x256 grid resolution is assumed to be feasible for short-duration verification runs but too expensive for full batch processing.

### FR-002: Initial Conditions
The system must generate Thomas-Fermi initial conditions for the BEC wavefunction.

### FR-003: Vortex Detection
The system must detect vortices using phase-winding algorithms, handling vortex-antivortex pairs.

### FR-004: Stability Metrics
The system must calculate stability metrics including:
- **Vortex Density**: Number of vortices per unit area (replaces "retention fraction").
- Radial Variance.
- Structure Factor Sharpness.

### FR-005: Statistical Analysis
The system must perform **Two-Way ANOVA** (factors: $\Omega$ and $\epsilon_{dd}$) and **Dunnett's post-hoc test** to determine statistical significance of stability regimes.

### FR-006: Sensitivity Analysis
The system must perform sensitivity analysis on the instability threshold over the discrete values $\{0.25, 0.30, 0.35\}$.

## 3. System Constraints (SC)

### SC-001: Metric Definition
Stability classification must be based on **Vortex Density** rather than retention fraction.

### SC-002: Threshold Handling
Metastable boundaries must be handled as binary thresholds while recording exact percentage drops.

### SC-003: Statistical Method
Statistical significance must be determined using Two-Way ANOVA and Dunnett's test, not One-Way ANOVA or t-tests.

## 4. Data Model

The system uses the following core entities:
- `SimulationRun`: Metadata and parameters for a single GPE simulation.
- `StabilityMetric`: Calculated metrics including `vortex_density`, `radial_variance`, and `structure_factor`.

## 5. Assumptions

1. **Grid Feasibility**: A 64x64 grid is computationally sufficient to capture the gross features of vortex formation and stability boundaries for the full parameter sweep.
2. **Runtime**: The full batch scan on 64x64 will complete within the 6-hour CI window.
3. **Memory**: The 64x64 grid fits within standard CI memory limits (typically 2-4GB).
4. **Reproducibility**: All simulations must be reproducible via the `seed_manager` utility.

## 6. Configuration

- **Grid Size**: Controlled via `RUN_FULL_GRID` environment variable.
- **Physical Parameters**: Loaded from `code/config/grid_config.py`.
- **Logging**: Configured via `code/utils/logger.py`.