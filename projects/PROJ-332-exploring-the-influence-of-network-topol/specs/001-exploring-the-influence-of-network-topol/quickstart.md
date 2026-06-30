# Quickstart: Influence of Network Topology on Thermal Conductivity

## Prerequisites

- Python 3.11+
- pip (package installer)
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-332-exploring-the-influence-of-network-topol
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### 1. Generate Networks and Solve (Single Run)
Run a single simulation with default parameters (N=1000, p=0.04, material=Si):
```bash
python code/main.py --run-single --seed 42
```
*Output*: `data/processed/simulation_results.csv` (updated with one row).

### 2. Run Full Grid (Default)
Execute the full grid (100 simulations $\times$ 10 connectivity levels):
```bash
python code/main.py --run-grid
```
*Output*:
- `data/processed/simulation_results.csv` (1000 rows).
- `data/processed/regression_summary.json` (scaling exponents, p-values).
- `data/processed/sensitivity_report.csv` (deviation analysis).
- `logs/simulation.log` (detailed logs).
- **State Update**: `state/projects/PROJ-332-exploring-the-influence-of-network-topol.yaml` is updated with the artifact hash.

### 3. Sensitivity Analysis Only
Run sensitivity sweep on existing results:
```bash
python code/main.py --sensitivity-only
```

## Verifying Results

1. **Check Solver Convergence**:
   ```bash
   grep "Failed" data/processed/simulation_results.csv
   # Should return empty or very few lines (< 1% of total)
   ```

2. **Verify Percolation Threshold**:
   ```bash
   python code/regression_analysis.py --check-percolation
   # Output: "Percolation threshold detected at avg_degree = X.XX"
   ```

3. **Validate Scaling Law**:
   ```bash
   python code/regression_analysis.py --plot-scaling
   # Generates a plot in the current directory: scaling_law.png
   ```

## Troubleshooting

- **Solver Failed**: Check `logs/simulation.log` for "Disconnected" or "Residual > 1e-6". Ensure `diameter` and `length` are within physical bounds.
- **Memory Error**: The default grid (a standard set of runs) fits in standard RAM capacities.. If running larger grids, reduce `N` or `simulations_per_level`.
- **Material Error**: If "Material X not found" appears, ensure X is one of {Si, CNT, Ag, Au} or provide a custom value in `code/material_db.py`.
- **State Update Failed**: If the state YAML is not updated, check `logs/simulation.log` for errors in `update_state.py`.

## Expected Output Example

```csv
run_id,seed,N,p,avg_degree,is_connected,effective_k,solver_status,material
1,42,1000,0.04,4.02,True,12.5,Converged,Si
2,43,1000,0.04,3.98,True,11.8,Converged,Si
...
```
