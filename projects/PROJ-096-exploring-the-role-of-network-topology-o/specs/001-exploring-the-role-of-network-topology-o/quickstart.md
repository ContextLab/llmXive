# Quickstart: Exploring the Role of Network Topology on Synchronization in Coupled Oscillators

## Prerequisites

- Python 3.11+
- `pip`
- Internet connection (optional, for installing dependencies)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is executed in three sequential steps.

### Step 1: Generate Topologies
Generates multiple network instances with varying rewiring probabilities from a synthetic regular ring lattice.
```bash
python code/generate_topology.py
```
*Output*: `data/processed/graph_p_*.gpickle` and `data/processed/graph_metadata.json`.

### Step 2: Simulate and Analyze
Runs the Kuramoto simulation on all valid graphs and performs statistical analysis.
```bash
python code/simulate_kuramoto.py
python code/analyze_results.py
```
*Output*: `data/processed/results.csv`, `data/processed/analysis_summary.json`, and plots in `data/processed/plots/`.

## Verification

To verify the installation and basic functionality:
```bash
pytest tests/ -v
```
This runs unit tests for graph generation and simulation logic.

## Troubleshooting

- **Numerical Errors**: If the simulation fails to converge, check the `rtol` and `atol` settings in `code/simulate_kuramoto.py`.
- **Memory Issues**: The pipeline is designed for < 2GB RAM. If OOM occurs, reduce the number of time steps in the config.
- **Spec Discrepancy**: If the pipeline fails due to missing data, note that this project uses a **synthetic** base graph and does not require external dataset downloads (unlike the original spec's instruction to use ca-AstroPh).