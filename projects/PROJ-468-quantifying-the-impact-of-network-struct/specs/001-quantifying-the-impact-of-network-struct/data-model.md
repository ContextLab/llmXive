# Data Model: Quantifying the Impact of Network Structure on Energy Dissipation in Driven Granular Materials

## 1. Entity Definitions

### Contact Network
A time-indexed graph $G_t = (V, E_t)$ where:
- **Nodes ($V$)**: Particles in the simulation.
- **Edges ($E_t$)**: Pairs of particles with geometric overlap $> 0$.
- **Attributes**:
  - `edge_weight`: Magnitude of the contact force.
  - `node_degree`: Number of contacts per particle (Coordination Number).

### Dissipation Record
A time-indexed row in the processed dataset containing:
- `timestep`: Integer index.
- `metrics`: Derived network topology values.
- `dissipation`: Calculated energy loss rate (Absolute and Normalized).
- `flags`: Status indicators (e.g., 'UNRELIABLE', 'ESTIMATED', 'STATIC').

## 2. Variable Definitions

| Variable Name | Type | Description | Source Calculation |
| :--- | :--- | :--- | :--- |
| `coordination_number` | float | Mean degree of the contact network at timestep $t$. | Mean of `node_degree` over all nodes. |
| `clustering_coeff` | float | Average clustering coefficient of the network. | Mean of local clustering coefficients. |
| `force_heterogeneity` | float | Coefficient of Variation (CV) of contact forces. | $\sigma_{force} / \mu_{force}$. |
| `dissipation_rate_abs` | float | **Primary Outcome**: Absolute energy dissipation. | $Work\_Input - (\Delta KE + \Delta PE)$. |
| `dissipation_rate_norm` | float | **Secondary Outcome**: Normalized energy dissipation. | $D_{abs} / Work\_Input$ (if $Work\_Input > 0$). |
| `driving_amplitude` | float | Amplitude of the driving boundary. | Extracted from simulation metadata. **Used as control variable.** |
| `degree_distribution_entropy` | float | **FR-009 Topology-Only**: Entropy of the degree distribution. | Shannon entropy of node degrees. |
| `force_chain_percolation` | float | **FR-009 Force-Only**: Connectivity of high-force subgraph. | Size of largest component in subgraph of edges > 90th percentile force. |
| `is_stationary` | bool | Result of ADF test on the dissipation series. | ADF p-value < 0.05. |
| `flags` | list | Data quality flags. | `UNRELIABLE`, `ESTIMATED`, `STATIC`, `MISSING_FORCES`. |

## 3. Data Flow

1.  **Input**: Raw Yade-DEM output (particle positions, forces, energy).
2.  **Extraction**: `extract.py` → `processed_metrics.csv` (one row per timestep). **Includes metadata header.**
3.  **Analysis**: `analyze.py` → `regression_results.json` (coefficients, p-values, ANOVA results, GAM/Quantile check results).
4.  **Visualization**: `viz.py` → `report.pdf`.

## 4. Metadata Header (Contract Enforced)
The processed dataset MUST include a header section with:
- `source_file`: Name of the input DEM file.
- `particle_count`: Total number of particles.
- `driving_amplitude`: Amplitude of the driving boundary.
- `friction_coeff`: Friction coefficient used in simulation.
- `extraction_timestamp`: ISO timestamp of extraction.
- `validation_status`: "CODE_VALIDATED" or "SCIENTIFIC_VALIDATED".