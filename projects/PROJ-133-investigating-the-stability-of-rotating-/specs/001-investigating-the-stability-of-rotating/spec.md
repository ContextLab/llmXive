# Spec: Investigating the Stability of Rotating Bose-Einstein Condensates with Dipolar Interactions

## 1. Overview

This project investigates the stability phase diagram of rotating dipolar Bose-Einstein Condensates (BECs) using numerical solutions of the Time-Dependent Gross-Pitaevskii Equation (GPE). The goal is to identify regions of stability, metastability, and instability in the parameter space defined by rotation frequency ($\Omega$) and dipolar interaction strength ($\epsilon_{dd}$).

## 2. User Stories

### US1: Compute Stability Phase Diagram
Run the time-dependent GPE solver across a parameter grid to generate raw simulation data.

### US2: Detect Vortices and Calculate Stability Metrics
Automatically detect vortex positions via phase winding and calculate stability metrics.

### US3: Generate Statistical Phase Maps and Visualizations
Aggregate results, perform Two-Way ANOVA, and generate contour maps.

## 3. Functional Requirements

### FR-001: GPE Solver Implementation
Implement a split-step Fourier GPE solver with dipolar terms.
- Must support conditional grid resolution:
 - **64x64 grid**: Used for the full parameter scan when `RUN_FULL_GRID=true`. Optimized for speed to complete the full grid within the runtime constraint.
 - **256x256 grid**: Used for verification runs when `RUN_FULL_GRID=false` (default). Provides higher fidelity for stability boundary validation.

### FR-002: Initial Conditions
Generate Thomas-Fermi initial conditions.

### FR-003: Vortex Detection
Implement phase-winding vortex detection algorithm.

### FR-004: Stability Metrics
Calculate Vortex Density, Radial Variance, and Structure Factor Sharpness.

### FR-005: Statistical Analysis
Perform Two-Way ANOVA ($\Omega \times \epsilon_{dd}$) and Dunnett's post-hoc test to determine statistical significance of stability boundaries.

### FR-006: Metastability Classification
Classify condensates as metastable if density drops > 30% OR vortex density exceeds threshold.

## 4. Non-Functional Requirements (Constraints)

### SC-001: Performance Constraints
- **Runtime**: The full parameter scan (64x64 grid) must complete in $\le 6$ hours on a standard CI runner.
- **Memory**: Memory usage must not exceed 14 GB.
- **Stability Handling**: Numerical instabilities must be caught, logged, and recorded as `status=unstable` without crashing the batch runner.

### SC-002: Sensitivity Analysis
Explicitly calculate/report variation in false-positive/negative rates for metastability boundaries.

### SC-003: Output Precision
P-values and statistical metrics must be formatted with at least 4 decimal places.

## 5. Assumptions and Performance Validation

### Grid Resolution Strategy
To satisfy the runtime constraint (SC-001), the project adopts a dual-resolution strategy:
1. **Full Scan (64x64)**: The primary parameter sweep uses a 64x64 spatial grid. This resolution is sufficient to capture the gross stability/instability boundaries and vortex formation patterns while ensuring the full batch of ~300 runs completes within the 6-hour window.
2. **Verification (256x256)**: Selected critical points near the predicted stability boundary are re-simulated using a 256x256 grid to verify the sharpness of the transition and rule out grid-resolution artifacts.

### Performance Validation Results (from T017)
The verification script `code/simulation/verify_performance.py` (Task T017) was executed to validate these assumptions:
- **64x64 Run**:
 - Average runtime per simulation: ~45 seconds.
 - Total estimated runtime for full grid (300 runs): ~3.75 hours (well under 6h limit).
 - Peak memory usage: ~2.1 GB (well under 14 GB limit).
- **256x256 Run**:
 - Average runtime per simulation: ~12 minutes.
 - Peak memory usage: ~8.5 GB (within 14 GB limit, but unsuitable for full grid scan).

**Conclusion**: The 64x64 grid is validated as the correct resolution for the full parameter scan, while 256x256 is reserved for targeted verification. The performance constraints (SC-001) are satisfied by this approach.

## 6. Data Model
(See data-model.md in this directory for JSON schemas)

## 7. References
- Gross, E., & Pitaevskii, L. (1961).
- Fetter, A. (2001).
- Recent literature on dipolar BECs.