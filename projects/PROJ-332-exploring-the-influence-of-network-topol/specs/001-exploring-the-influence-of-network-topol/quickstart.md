# Quickstart: Influence of Network Topology on Thermal Conductivity

## Prerequisites

- Python 3.11 or higher
- Git
- A terminal with `pip` access

## Installation

1.  **Clone the repository** (or navigate to the project root).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins specific versions of `networkx`, `scipy`, `numpy`, etc.*

## Running the Simulation

### Default Grid Sweep
To run the full simulation grid (Multiple connectivity levels, 100 simulations each):
```bash
python code/main.py --grid
```
This will:
1.  Generate a large set of random geometric graphs.
2.  Assign thermal resistances (using NIST defaults).
3.  Solve for effective conductivity.
4.  Perform sensitivity analysis.
5.  Output `data/processed/simulation_results.csv`.

### Single Simulation
To run a single simulation with custom parameters:
```bash
python code/main.py --N 500 --p 0.05 --material Si --seed 42
```

### Running Sensitivity Analysis Only
```bash
python code/main.py --sensitivity-only --base-k 10.0
```

### Providing Custom Material Values
For non-standard materials, provide the thermal conductivity value:
```bash
python code/main.py --material "CustomAlloy" --k-value 25.5
```

## Verifying Results

### Check CSV Output
Verify the output file was created and contains data:
```bash
head data/processed/simulation_results.csv
```
Expected columns: `seed`, `N`, `p`, `measured_degree`, `k_eff`, `convergence_status`, `percolation_threshold`, `is_connected`.

### Run Tests
Ensure the solver and generator are working correctly:
```bash
pytest code/tests/ -v
```
This runs unit tests for graph generation, convergence checks, and regression logic.

## Troubleshooting

- **"Material not found"**: Ensure the material name matches one of the NIST defaults (Si, CNT, Ag, Au) or provide a custom value via `--k-value`.
- **"Solver failed to converge"**: Check if the graph is disconnected. The system logs warnings for disconnected graphs and sets $k_{eff}=0$.
- **"Memory Error"**: The default $N=1000$ should fit in 7GB RAM. If using larger $N$, reduce the number of simulations per level.
- **"Timeout"**: The job exceeded the allocated time limit. Reduce the grid size or node count.