# Quickstart: Influence of Network Topology on Thermal Conductivity in Nanomaterials

## Prerequisites

-   Python 3.11+
-   `pip` (package manager)
-   Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-332-exploring-the-influence-of-network-topol
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Simulation

### Basic Run (Single Graph)
Generate a single network with target degree 4.0 and compute conductivity:
```bash
python code/main.py --target-degree 4.0 --seed 42 --material Si
```

### Full Pipeline (Default Grid)
Run the full study (10 levels, 100 runs each) with sensitivity analysis:
```bash
python code/main.py --run-full-grid --material Si
```
*Note: This will take a moderate amount of time on a standard CPU.*

### Sensitivity Sweep Only
Run sensitivity analysis on a specific result set:
```bash
python code/main.py --sensitivity-only --input data/processed/simulation_results.csv
```

### Custom Material
Use a non-standard material (e.g., "Custom" with k=200):
```bash
python code/main.py --material-override "Custom=200.0" --target-degree 4.0
```

## Output Locations

-   **Raw Logs**: `data/logs/`
-   **Processed Results**: `data/processed/simulation_results.csv`
-   **Analysis Reports**: `data/processed/regression_summary.json`
-   **Plots**: `data/figures/` (if enabled)

## Verification

To verify the installation and basic functionality:
```bash
pytest tests/unit/test_generate.py -v
pytest tests/unit/test_physics.py -v
```

## Troubleshooting

-   **Solver Convergence Failure**: If `convergence_rate` < 1.0, check if the graph is disconnected. The system logs a warning and sets $k_{eff} = 0$.
-   **Memory Error**: Unlikely with N=1000. If it occurs, reduce `N` in `config.py`.
-   **Material Not Found**: Use `--material-override` for non-standard materials.
