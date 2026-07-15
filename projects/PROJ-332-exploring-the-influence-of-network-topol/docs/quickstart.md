# Quickstart Guide: Network Topology & Thermal Conductivity

This guide explains how to run the default simulation grid to explore the influence of network topology on thermal conductivity in nanomaterials.

## Prerequisites

Ensure you have Python 3.8+ installed. Install the required dependencies:

```bash
pip install -r code/requirements.txt
```

## Running the Default Grid

The default grid runs simulations across multiple levels of average node degree (`avg_degree`) and connection probabilities (`p`) to generate a comprehensive dataset.

Execute the main simulation script from the project root:

```bash
python code/main.py
```

### Configuration

The simulation parameters (node count `N`, connection probability `p`, wire diameter `d`, length `l`, and random `seed`) are loaded from environment variables or default values defined in `code/config.py`.

To override defaults, set environment variables before running:

```bash
export N=100
export P=0.1
export D=50e-9 # 50nm
export L=1e-6 # 1um
export SEED=42
python code/main.py
```

### What Happens

1. **Grid Generation**: The script iterates over a predefined set of target average degrees (e.g., 2.0, 3.0, 4.0, 5.0) and connection probabilities.
2. **Network Creation**: For each parameter set, a nanowire network graph is generated using `generate_nanowire_network`.
3. **Thermal Solving**: Thermal resistance is assigned based on material properties (defaulting to Silicon or CNT) and the Fuchs-Sondheimer size-correction factor is applied. The Kirchhoff heat flow is solved to determine effective conductivity.
4. **Analysis**: Regression analysis and percolation threshold detection are performed on the collected results.
5. **Output**: Results are appended to `data/processed/simulation_results.csv`.

## Output Files

- **`data/processed/simulation_results.csv`**: Contains the raw simulation results including `seed`, `N`, `p`, `avg_degree`, `conductivity`, `percolation_flag`, and `scaling_factor`.
- **`state/projects/PROJ-332-exploring-the-influence-of-network-topol.yaml`**: Updated with the SHA-256 hash of the results file for reproducibility tracking.

## Verification

After completion, verify the output by checking the CSV header and row count:

```bash
head -n 5 data/processed/simulation_results.csv
wc -l data/processed/simulation_results.csv
```

Expected columns: `seed,N,p,avg_degree,conductivity,percolation_flag,scaling_factor`.