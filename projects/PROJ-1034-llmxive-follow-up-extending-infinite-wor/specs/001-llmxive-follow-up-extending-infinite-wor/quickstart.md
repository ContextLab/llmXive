# Quickstart: llmXive follow-up: extending "Infinite Worlds with Versatile Interactions"

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with multiple cores, 7GB+ RAM)

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd specs/001-llmxive-followup
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Simulation

### 1. Run a Single Configuration (Baseline Test)

To test the CA Eco-Director with default parameters:

```bash
python -m src.cli.run_simulation --agent ca_eco_director --steps 2000 --seed 42
```

### 2. Run the Full Parameter Sweep

To execute the full sweep ([deferred] steps per config) and generate the LMM/RF analysis:

```bash
python -m src.cli.run_simulation --mode sweep --steps 2000 --seed 42
```

This will:
- Initialize the **Stochastic Physics Sandbox** (no external dataset download required).
- Run simulations for all parameter combinations with multiple noise seeds each.
- Save raw logs to `data/raw/`.
- Run statistical analysis and save results to `data/processed/`.
- Generate a summary report in `reports/summary.html`.

### 3. Validate Data

To ensure data integrity and schema compliance:

```bash
python -m src.cli.validate_data --path data/raw/
```

## Expected Outputs

- `data/raw/simulation_logs.parquet`: Raw time-series metrics.
- `data/processed/lmm_results.json`: LMM coefficients and p-values.
- `data/processed/rf_importance.json`: Random Forest feature importance.
- `data/processed/sensitivity_report.json`: Inconsistency rates across thresholds.
- `data/processed/rare_events.json`: Rare event counts and histograms.
- `reports/summary.html`: Visual summary of coherence, diversity, and latency.

## Troubleshooting

- **OOM Errors**: If you encounter Out Of Memory errors, reduce the `--steps` parameter or limit the `ParameterGrid` size in `config.py`.
- **Timeout**: The default CI job limit is set to a reasonable duration to ensure efficient resource utilization. If the sweep exceeds this, reduce the number of configurations in the grid.
- **Data Unavailable**: Not applicable. The simulation uses the internal Stochastic Physics Sandbox and does not require external datasets.