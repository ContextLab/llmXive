# Quickstart Guide: Bounded Confidence Opinion Dynamics

This guide provides a step-by-step walkthrough for running the simulation and analysis pipeline for the "Impact of Bounded Confidence on Opinion Polarization Speed" project.

## Prerequisites

- Python 3.11+
- pip (Python package installer)
- Git (for cloning the repository)

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd projects/PROJ-672-the-impact-of-bounded-confidence-on-opin
 ```

2. **Install dependencies**:
 Create a virtual environment and install the required packages:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

The pipeline consists of three main stages: Network Generation, Simulation, and Analysis.

### Step 1: Generate Network Ensembles

This step creates the structural backbone for the simulations.

```bash
python code/generate_networks.py
```

**Output**: Network files and metrics are saved to `data/raw/networks/`.
- `network_{topology}_{seed}.graphml`: The network structure.
- `metrics_{topology}_{seed}.json`: Structural metrics (assortativity, path length, etc.).

### Step 2: Run Simulations

Execute the Hegselmann-Krause dynamics on the generated networks.

```bash
python code/simulate_hk.py
```

**Output**: Raw simulation data is saved to `data/raw/simulations/`.
- `run_{topology}_{epsilon}_{seed}.h5`: HDF5 files containing opinion traces and metadata.

*Note: This step may take several hours depending on the number of configurations. Use the `--parallel` flag if available to utilize multiple CPU cores.*

### Step 3: Analyze Scaling Laws

Extract critical thresholds and fit power-law models.

```bash
python code/analyze_scaling.py
```

**Output**: Processed results are saved to `data/processed/`.
- `epsilon_c_values.json`: Estimated critical thresholds.
- `scaling_results.json`: Fitted power-law exponents ($\gamma$).
- `regression_data.json`: Merged dataset for statistical analysis.
- `figures/`: Generated plots (log-log convergence, regression scatter).

## Running Tests

To ensure the integrity of the codebase and results:

```bash
pytest tests/
```

This runs unit tests for network generation, simulation logic, and contract validation against the JSON schemas.

## Sensitivity Analysis

To verify robustness of results to convergence thresholds:

```bash
python code/sensitivity_analysis.py
```

**Output**: `data/processed/sensitivity_report.csv`.

## Troubleshooting

- **Memory Errors**: The simulation for $N=500$ with full time-traces can consume significant RAM. If you encounter `MemoryError`, reduce the number of seeds or use the `--streaming` flag (if supported) to write traces incrementally.
- **Non-Convergence**: Some simulation runs may not converge within the iteration limit. These are flagged as "non-convergent" in the output CSV. Ensure your `max_iterations` parameter in `simulate_hk.py` is sufficiently high for the critical regime.
- **Missing Dependencies**: If `networkx` or `h5py` are missing, ensure you activated the virtual environment and ran `pip install -r code/requirements.txt`.

## Data Interpretation

- **Convergence Time ($T$)**: The number of iterations until the maximum opinion change falls below $10^{-4}$.
- **Critical Threshold ($\epsilon_c$)**: The value of $\epsilon$ where the system transitions from slow/no convergence to fast convergence.
- **Scaling Exponent ($\gamma$)**: A measure of how sharply the convergence time increases as $\epsilon$ approaches $\epsilon_c$. Higher $\gamma$ indicates a more abrupt phase transition.

For detailed methodology and theoretical background, refer to `docs/methodology.md`.
