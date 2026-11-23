# Quickstart: Network Topology Energy Transfer in Spin Systems

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Git

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-326-investigating-the-impact-of-network-stru
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### 1. Generate Synthetic Data
Generates a batch of networks and saves metadata.
```bash
python code/main.py --phase generate --config code/config.yaml
```
*Output*: `data/raw/global_batch_manifest.json`, `data/raw/metadata.json`.

### 2. Run Simulations
Executes Ising dynamics on generated graphs.
```bash
python code/main.py --phase simulate --config code/config.yaml
```
*Output*: `data/analysis/simulation_results.json`.

### 3. Sensitivity Sweep (Optional but Recommended)
Runs the threshold sensitivity analysis.
```bash
python code/main.py --phase sensitivity --config code/config.yaml
```
*Output*: `data/analysis/sensitivity_sweep.json`.

### 4. Analysis & Reporting
Performs regression, ANOVA, and generates final report.
```bash
python code/main.py --phase analyze --config code/config.yaml
```
*Output*: `data/analysis/aggregated_results.json`, `data/analysis/final_results.json`, `data/figures/*.png`.

### 5. Validation
Validates all outputs against schemas.
```bash
pytest tests/contract/
```

## Configuration

Edit `code/config.yaml` to adjust:
- `network_size`: Nodes per graph (default: 500).
- `batch_size`: Number of graphs (default: 100).
- `simulation_steps`: Time steps (default: 100).
- `topology_weights`: Proportion of ER, SF, WS graphs.
- `random_seed`: Global seed for reproducibility.

## Troubleshooting

- **Memory Error**: Reduce `network_size` or `batch_size`.
- **Simulation Divergence**: Check `data/analysis/simulation_results.json` for `[SIMULATION_DIVERGENCE]` flags. Adjust time step or update rule in `config.yaml`.
- **Disconnected Graphs**: Increase `retry_attempts` in `config.yaml` or reduce edge probability for ER graphs.
