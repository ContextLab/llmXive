# Data Model: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

## Overview

This document defines the data structures used throughout the project. All data is stored in `data/` and versioned via checksums.

## Entities

### 1. NetworkRealization

Represents a single atomic connectivity graph.

- **`id`**: Unique string identifier (e.g., `sw_001`).
- **`type`**: Enum: `small_world`, `scale_free`, `random`.
- **`nodes`**: Integer count of nodes ($N$).
- **`edges`**: List of tuples `(u, v)`.
- **`metrics`**: Dictionary of topological features:
    - `clustering_coefficient`: Float.
    - `average_path_length`: Float.
    - `degree_variance`: Float.
    - `spectral_gap`: Float.
    - `betweenness_centrality`: List of floats (one per node).
- **`cutoff_used`**: Float (distance multiplier).
- **`seed`**: Integer (random seed used).

### 2. TransportResult

Represents the computed thermal conductivity for a realization.

- **`realization_id`**: Reference to `NetworkRealization.id`.
- **`conductivity`**: Float ($\kappa$ in W/m·K).
- **`convergence_status`**: Enum: `converged`, `failed`, `retry_exhausted`.
- **`method`**: Enum: `allen_feldman`, `nemd`.
- **`regime_detected`**: Enum: `diffusive`, `ballistic`, `mixed`.
- **`computation_time`**: Float (seconds).
- **`error_estimate`**: Float (standard error).

### 3. CorrelationAnalysis

Aggregated statistical results.

- **`metric_name`**: String (e.g., `clustering_coefficient`).
- **`topology_type`**: String (e.g., `small_world`).
- **`correlation_coefficient`**: Float ($r$).
- **`p_value`**: Float (uncorrected).
- **`p_value_corrected`**: Float (Bonferroni/FDR).
- **`confidence_interval`**: Dictionary `{lower: Float, upper: Float}`.
- **`r_squared`**: Float.
- **`sample_size`**: Integer ($N$).

### 4. PowerLawFit

Results of the power-law fit between disorder and conductivity (SC-005).

- **`disorder_parameter`**: String (e.g., `1 - clustering`).
- **`power_law_r_squared`**: Float.
- **`power_law_exponent`**: Float.
- **`power_law_p_value`**: Float (test against null hypothesis $R^2=0$).
- **`ci_lower`**: Float.
- **`ci_upper`**: Float.
- **`ci_width`**: Float.
- **`ci_width_target_met`**: Boolean.

### 5. ANOVAResult

Results of the Analysis of Variance.

- **`metric_name`**: String.
- **`f_statistic`**: Float.
- **`p_value`**: Float.
- **`effect_size`**: Float (e.g., $\eta^2$).

## File Formats

- **Graphs**: `.graphml` (NetworkX format).
- **Results**: `.csv` (Transport results), `.json` (Analysis results).
- **Config**: `.yaml` (Simulation parameters).

## Data Flow

1.  `01_generate_networks.py` → `data/processed/graphs/`
2.  `02_compute_transport.py` → `data/processed/transport/`
3.  `03_analyze_correlations.py` → `data/processed/analysis/`