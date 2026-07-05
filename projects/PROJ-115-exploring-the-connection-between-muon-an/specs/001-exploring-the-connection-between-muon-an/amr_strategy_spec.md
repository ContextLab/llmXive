# Adaptive Mesh Refinement (AMR) Strategy Specification

## Overview
This document defines the Adaptive Mesh Refinement (AMR) strategy used to
generate the parameter grid for the muon g-2 dark matter scan. The goal is
to ensure that narrow viable bands and resonance regions are captured with
high precision without wasting computational resources on flat regions.

## Strategy
The AMR strategy follows these steps:
1. **Initial Coarse Grid**: Generate a log-spaced grid over the parameter space
 (m_chi, m_V, g) with a resolution defined by `initial_resolution`.
2. **Physics Evaluation**: Compute the relic density (omega_h2) and Sommerfeld
 enhancement (S_factor) at each grid point.
3. **Error Estimation**: Calculate the local error estimate between adjacent
 points based on the gradient of the physics observables.
4. **Refinement**: Insert new grid points in regions where the error estimate
 exceeds the `refinement_threshold`.
5. **Iteration**: Repeat steps 2-4 until convergence or the maximum depth is reached.

## Parameters
- `max_depth`: Maximum number of refinement iterations (default: 5).
- `tolerance_rel`: Relative error tolerance (default: 0.05).
- `tolerance_abs`: Absolute error tolerance (default: 1e-4).
- `min_grid_spacing`: Minimum spacing between points in log space (default: 0.01).
- `refinement_threshold`: Gradient threshold for refinement (default: 0.1).
- `initial_resolution`: Number of points per dimension in the initial grid (default: 20).
- `max_points`: Safety cap on the total number of grid points (default: 50000).

## Implementation Details
- The grid is represented as a list of `GridPoint` objects.
- The `AdaptiveGridGenerator` class handles the generation and refinement logic.
- The `extract_sommerfeld_factor` function from `physics.yukawa_solver` is used
 to compute the Sommerfeld enhancement.
- The relic density is estimated using a proxy formula: `omega_h2 ~ 1 / (S_factor * g^2)`.
 This is sufficient for driving the AMR strategy. The full RK4 integration is
 performed later for the final viable points.

## Output
- A CSV file (`data/amr_grid_sample.csv`) containing the final grid points.
- A log of the refinement history (number of points at each depth).

## Validation
- The strategy is validated by checking that the final grid density is sufficient
 to capture the viable regions defined in the physics model.
- The error estimates should converge below the `tolerance_rel` in most regions.

## References
- Plan 0.3: Define Adaptive Mesh Refinement (AMR) strategy for grid convergence.