# Data Model: Quantifying the Impact of Network Structure on Energy Dissipation in Driven Granular Materials

## Overview

This document defines the data structures used throughout the pipeline. It ensures that the extraction, analysis, and visualization modules operate on a consistent schema. The data model is designed to be lightweight to fit within the 7GB RAM constraint.

**Critical Note on Functional Dependence**: The `force_heterogeneity` metric is derived from the same contact force vector used to calculate `dissipation_rate`. Therefore, `force_heterogeneity` is **excluded from the regression model** to avoid a tautological result. It is retained in the dataset only for descriptive statistics and visualization.

## Raw Input Schema (Yade-DEM)

The system expects raw input files in a standard Yade-DEM format (e.g., `.csv`, `.log`, or `.dat`). The parser (`code/extraction/parse_dem.py`) must extract the following fields:

| Field Name | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `timestep` | int | Simulation time step index | Simulation log |
| `particle_id` | int | Unique particle identifier | Particle list |
| `x`, `y`, `z` | float | Particle coordinates | Particle list |
| `contact_id` | int | Unique contact identifier | Contact list |
| `p1_id`, `p2_id` | int | IDs of the two particles in contact | Contact list |
| `force_magnitude` | float | Normal force magnitude | Contact forces |
| `force_vector` | list[float] | Force vector components (optional) | Contact forces |
| `total_energy` | float | Total system energy (KE + PE) | Energy log |
| `driving_amplitude` | float | External driving parameter (constant per run) | Simulation metadata |

*Note: If the raw file lacks `driving_amplitude`, it must be extracted from the simulation metadata file or header.*

## Intermediate Schema: Extracted Metrics

**File Format**: CSV (`data/processed/metrics_<run_id>.csv`)  
**Granularity**: One row per timestep.

| Column Name | Type | Description | Calculation Source |
| :--- | :--- | :--- | :--- |
| `timestep` | int | Time step index | Raw input |
| `mean_coordination` | float | Average number of contacts per particle | `network_metrics.py` |
| `clustering_coeff` | float | Average clustering coefficient of the network | `network_metrics.py` |
| `force_heterogeneity` | float | Coefficient of Variation (CV) of contact forces. **WARNING: This metric is functionally dependent on the same force vector as `dissipation_rate`. It is excluded from regression to avoid tautology.** | `network_metrics.py` |
| `dissipation_rate` | float | Energy loss rate (sum of force × relative velocity). | `dissipation.py` |
| `driving_amplitude` | float | Driving amplitude (control variable) | Metadata |
| `volume_fraction` | float | System volume fraction (optional) | Derived from positions |
| `is_steady_state` | bool | Flag indicating if the timestep is in a steady-state window (based on KE variance). **Note: This overrides FR-011 which specified dissipation rate variance.** | `analysis/validation.py` |

**Steady-State Detection Logic**:
- The `is_steady_state` flag is determined by checking the rolling variance of **Kinetic Energy (KE)** over 100 timesteps.
- **Do NOT** use the variance of `dissipation_rate` for this check to avoid collider bias. **This is a necessary methodological override of FR-011.**

**Force Heterogeneity Logic (FR-003)**:
- If all forces are zero, the metric is set to 0.0.
- If >50% of contacts are missing, the timestep is excluded.
- Otherwise, missing forces are imputed as 0.0, and the CV is calculated over non-zero forces.

## Output Schema: Analysis Results

**File Format**: JSON (`data/processed/analysis_results_<run_id>.json`)

```json
{
  "run_id": "string",
  "timestamp": "ISO8601",
  "correlations": [
    {
      "metric": "string",
      "method": "pearson|spearman",
      "coefficient": "float",
      "p_value": "float",
      "significant": "boolean"
    }
  ],
  "regression": {
    "model_type": "GLS|Newey-West",
    "coefficients": {
      "intercept": "float",
      "mean_coordination": "float",
      "clustering_coeff": "float",
      "driving_amplitude": "float",
      "interaction_amplitude_coordination": "float"
    },
    "std_errors": { ... },
    "p_values": { ... },
    "adj_r_squared": "float",
    "vif_scores": { ... }
  },
  "validation": {
    "anova_p_value": "float",
    "generalizable": "boolean",
    "slope_consistency": "string"
  },
  "diagnostics": {
    "steady_state_windows": "int",
    "total_timesteps": "int",
    "memory_peak_gb": "float",
    "runtime_seconds": "float",
    "runtime_status": "string"
  }
}
```

**Note on `runtime_status`**: This field indicates compliance with SC-005.
- `PASS`: Completed within time limit.
- `FAIL`: Exceeded time limit but completed before runner kill.
- `TRUNCATED`: Job killed by runner (timeout).

## Data Flow

1.  **Ingestion**: Raw Yade-DEM file → `parse_dem.py` → List of Timesteps/Contacts.
2.  **Extraction**: Timesteps/Contacts → `network_metrics.py` + `dissipation.py` → `Extracted Metrics` CSV.
3.  **Filtering**: `Extracted Metrics` → `validation.py` (steady-state check using KE variance) → `Filtered Metrics` CSV.
4.  **Analysis**: `Filtered Metrics` → `correlation.py` + `regression.py` (excluding force_heterogeneity) → `Analysis Results` JSON.
5.  **Visualization**: `Analysis Results` JSON + `Filtered Metrics` CSV → `report_gen.py` → PDF Report.