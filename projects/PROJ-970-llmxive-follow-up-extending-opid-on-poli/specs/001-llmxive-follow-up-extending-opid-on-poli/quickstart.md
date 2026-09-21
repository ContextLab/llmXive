# Quickstart: OPID Critical-First Routing Complexity Analysis

## Prerequisites
- Python 3.11+
- Git

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/code
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `networkx`, `numpy`, `pandas`, `scipy`, and `pytest` are installed.
    ```bash
    python -c "import networkx; import numpy; import scipy; print('OK')"
    ```

3.  **Verify Config**:
    Ensure `ruff.toml` and `pyproject.toml` (Black config) are present.
    ```bash
    ruff check .
    black --check .
    ```

## Running the Experiments

### 1. Generate Environments
Generate the synthetic graph suite for all tiers.
```bash
python -m src.environment.generator --tiers 1,2,3 --seed 42
```
*Output*: Graphs saved to `data/raw/synthetic_graphs/`.

### 2. Run Simulation Sweep
Execute the full threshold sweep (0.0 to 1.0) across all tiers.
```bash
python -m src.simulation.runner --thresholds 0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0 --episodes 1000 --seed 42
```
*Note*: This runs sequentially to stay within 7GB RAM.

### 3. Aggregate and Analyze
Compute metrics and run statistical tests.
```bash
python -m src.analysis.aggregation --input data/processed/results.csv --output data/processed/aggregated_metrics.csv
python -m src.analysis.stats --input data/processed/aggregated_metrics.csv
```

### 4. Verify Results
Run the test suite to ensure contract compliance.
```bash
pytest tests/contract/ -v
```

## Troubleshooting

- **Memory Error**: Ensure the `runner` is running in sequential mode (default). Do not parallelize.
- **Graph Validation Failed**: If a graph cannot be generated with a valid path, the system will retry. If it fails after 10 retries, check the `seed` and `tier` parameters.
- **Missing Logs**: Check `logs/simulation.log` for "deterministic policy observed" warnings.