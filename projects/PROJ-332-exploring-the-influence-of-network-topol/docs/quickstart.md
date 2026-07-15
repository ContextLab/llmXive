# Quickstart Guide

## Overview

This project simulates the influence of network topology on thermal conductivity in nanomaterials.
It generates synthetic nanowire networks, computes effective thermal conductivity using Kirchhoff's laws,
and analyzes scaling relationships between graph metrics and conductivity.

## Prerequisites

- Python 3.9+
- pip
- Required packages listed in `code/requirements.txt`

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

3. (Optional) Set up pre-commit hooks:
 ```bash
 cd code
 pre-commit install
 ```

## Running the Default Simulation Grid

The default simulation runs a grid of parameters to generate multiple nanowire networks
and compute their thermal conductivities.

### Step 1: Configure Parameters (Optional)

Edit `code/config.py` or set environment variables to customize:
- `N`: Number of nodes (default: 100)
- `p`: Connection probability (default: 0.1)
- `d`: Wire diameter in nm (default: 50)
- `l`: Wire length in nm (default: 1000)
- `seed`: Random seed for reproducibility (default: 42)

Example environment variable setup:
```bash
export SIM_N=150
export SIM_P=0.15
export SIM_D=75
export SIM_L=1500
export SIM_SEED=123
```

### Step 2: Run the Simulation

Execute the main simulation script:
```bash
cd code
python main.py
```

This will:
1. Generate a grid of nanowire networks with varying average degrees
2. Compute effective thermal conductivity for each network
3. Perform regression analysis to identify scaling laws
4. Run sensitivity analysis on key parameters
5. Save results to `data/processed/simulation_results.csv`

### Step 3: Verify Output

Check the output file:
```bash
head data/processed/simulation_results.csv
```

Expected columns:
- `seed`: Random seed used
- `N`: Number of nodes
- `p`: Connection probability
- `avg_degree`: Average node degree
- `conductivity`: Effective thermal conductivity (W/(m·K))
- `percolation_flag`: Whether percolation threshold was crossed
- `scaling_factor`: Calculated scaling factor from regression

## Running Tests

Run the full test suite:
```bash
cd code
pytest
```

Run specific test categories:
```bash
# Unit tests
pytest tests/unit/

# Contract tests
pytest tests/contract/

# Integration tests
pytest tests/integration/
```

## Analyzing Results

After running the simulation, you can analyze the results using the provided analysis modules:

```bash
# Run regression analysis
cd code
python regression_analysis.py

# Run sensitivity analysis
python sensitivity_analysis.py
```

## Troubleshooting

### "Material not found in local store or NIST defaults"

Ensure the material name is one of the supported defaults (Si, CNT, Ag, Au) or provide a custom value in `code/config.py`.

### "Graph disconnected; conductivity set to 0.0"

This occurs when the generated network has disconnected components. Increase the connection probability `p` to ensure connectivity.

### "Runtime ceiling (6h) exceeded"

The simulation aborted because it exceeded the 6-hour limit. Reduce the parameter grid size or node count `N`.

## Next Steps

- Review `docs/spec.md` for detailed requirements
- Check `docs/tasks.md` for implementation status
- Explore `code/` for module documentation
- Run `python update_state.py` to update project state after changes
