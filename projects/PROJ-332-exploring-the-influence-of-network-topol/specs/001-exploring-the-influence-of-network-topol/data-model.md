# Data Model: Influence of Network Topology on Thermal Conductivity

## Key Entities

### 1. NetworkGraph
Represents a single synthetic nanowire assembly.
- **Attributes**:
  - `seed` (int): Random seed for reproducibility.
  - `N` (int): Number of nodes.
  - `p` (float): Connection probability.
  - `target_degree` (float): Desired average degree.
  - `measured_degree` (float): Actual average degree.
  - `is_connected` (bool): True if source-sink path exists.
  - `metrics`: Dict containing `avg_path_length`, `clustering_coeff`.

### 2. ThermalResistorModel
Encapsulates the mapping from graph edges to thermal resistances.
- **Attributes**:
  - `material` (str): Material name (e.g., "Si").
  - `diameter` (float): Wire diameter in meters (default 50nm).
  - `length` (float): Wire length in meters (default 1µm).
  - `k_bulk` (float): Bulk thermal conductivity (W/m·K).
  - `size_correction_factor` (float): Fuchs-Sondheimer factor.
  - `edge_resistances` (dict): Map of edge tuples to resistance values.

### 3. SimulationResult
Stores the output of a single simulation run.
- **Attributes**:
  - `effective_conductivity` (float): Calculated $k_{eff}$ (W/m·K).
  - `convergence_status` (str): "success" or "failed".
  - `residual` (float): Final solver residual.
  - `sensitivity_range` (dict): Range of $k_{eff}$ for scaling factors {0.9, 1.0, 1.1}.
  - `percolation_threshold` (float): The operational threshold calculated for the grid.

### 4. RegressionAnalysis
Stores the results of the statistical fit.
- **Attributes**:
  - `scaling_exponent` (float): $t$ from critical scaling law.
  - `confidence_interval` (tuple): 95% CI for $t$.
  - `p_value` (float): Significance of the slope.
  - `percolation_threshold` (float): Critical average degree.

## Data Flow

1.  **Input**: `config.py` (material defaults, hyperparameters).
2.  **Generation**: `models/network.py` creates `NetworkGraph` instances.
3.  **Assignment**: `services/resistor.py` assigns `ThermalResistorModel` to edges.
4.  **Solve**: `services/solver.py` computes `SimulationResult`.
5.  **Aggregate**: `main.py` collects all results into a list.
6.  **Output**: `utils/logging.py` writes to `data/processed/simulation_results.csv` (Runtime generation).
7.  **Analyze**: `analysis/regression.py` reads CSV to produce `RegressionAnalysis`.

## Storage Format

- **Primary Output**: `data/processed/simulation_results.csv`
  - **Format**: CSV (Comma Separated Values).
  - **Encoding**: UTF-8.
  - **Delimiter**: `,`
  - **Header**: `seed,N,p,target_degree,measured_degree,material,diameter,length,k_eff,residual,convergence_status,scaling_factor,percolation_threshold,is_connected`
  - **Generation**: Created dynamically by `main.py` upon first write. No pre-existing file.