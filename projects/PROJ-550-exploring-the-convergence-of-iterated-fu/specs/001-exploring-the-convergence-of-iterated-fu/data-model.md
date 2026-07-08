# Data Model: Exploring the Convergence of Iterated Function Systems with Non-Contractive Maps

## Overview

This document defines the schema for the synthetic IFS dataset, the empirical measure approximations, and the analysis results. All data is stored in `data/` as Parquet or CSV files, with checksums recorded in `data/checksums.json`. The model now distinguishes between "Converged", "Bounded-Chaotic", "Uniform", and "Divergent" behaviors to avoid circular definitions and category errors.

## Entities

### 1. IFS Instance
A single synthetic Iterated Function System.
-   **ID**: Unique string identifier (e.g., `ifs_0001`).
-   **Target_Lipschitz**: Float (0.5 to 2.0). *Theoretical parameter used for modeling.*
-   **Computed_Lipschitz**: Float (numerical estimate). *Used for validation only.*
-   **Num_Maps**: Integer (2-4).
-   **Map_Parameters**: JSON array of affine transformation matrices and translation vectors.
-   **Overlap_Geometry**: Float (ratio of intersection area to unit square).

### 2. Empirical Measure (Chaos Game Result)
The output of the Monte Carlo simulation.
-   **IFS_ID**: Foreign key to IFS Instance.
-   **Behavior_Class**: Enum ("Converged", "Bounded-Chaotic", "Uniform", "Divergent").
-   **Wasserstein_2**: Float (distance between last 10 windows).
-   **Point_Count**: Integer (number of points retained).
-   **Histogram_Bins**: JSON (2D histogram counts using Sturges' rule).
-   **Escape_Time**: Integer (iteration count when escape occurred, if divergent).
-   **Lyapunov_Exponent**: Float (approximated).

### 3. Topological Descriptor
Computed fractal dimensions.
-   **IFS_ID**: Foreign key.
-   **Box_Counting_Dim**: Float (for Converged sets).
-   **Transient_Dim**: Float (for Bounded-Chaotic/Divergent sets, dimension of transient cloud).
-   **Scale_Count**: Integer (number of scales used, default 50).
-   **R_Squared**: Float (fit quality of the log-log regression).

### 4. Analysis Result
Aggregated metrics for modeling.
-   **IFS_ID**: Foreign key.
-   **Invariant_Measure_Exists**: Boolean (True if "Converged").
-   **Lipschitz_Group**: Categorical (binned for sensitivity analysis).
-   **Model_Predicted_Prob**: Float (from logistic regression).

## File Structure

```text
data/
├── raw/
│   ├── ifs_instances.parquet      # synthetic IFS definitions
│   └── benchmarks.csv             # 3 benchmark IFS definitions
├── derived/
│   ├── chaos_results.parquet      # Simulation outcomes (Behavior_Class, W2, Lyapunov)
│   ├── topology_results.parquet   # Box-counting and Transient dimensions
│   └── analysis_summary.csv       # Aggregated metrics for modeling
└── checksums.json                 # Integrity manifest (updated after each step)
```

## Data Flow

1.  **Generation**: `generators.py` creates `raw/ifs_instances.parquet`.
2.  **Benchmark Validation**: `benchmarks.py` validates methodology. Results stored in `derived/benchmark_results.parquet`.
3.  **Simulation**: `chaos_game.py` reads instances, runs Chaos Game (with multi-stage checks), writes `derived/chaos_results.parquet`.
4.  **Analysis**: `topology.py` and `analysis.py` read results, compute metrics (including Transient Dimension), write `derived/topology_results.parquet` and `analysis_summary.csv`.
5.  **Checksum**: A final step generates `data/checksums.json` covering all derived artifacts.

## Constraints

-   **Memory**: All Parquet files must be read in chunks if total size > 4GB.
-   **Precision**: Floats stored as `float64` to ensure numerical stability in gradient estimation.
-   **Immutability**: Raw files are never overwritten; new versions are saved with timestamps if regeneration is required.