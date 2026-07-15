# Quickstart: llmXive follow-up: extending "Macaron-A2UI: A Model for Generative UI in Personal Agents"

## Prerequisites

- Python 3.11+
- Git
- Access to the A2UI-Bench dataset (local copy required).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-914-llmxive-follow-up-extending-macaron-a2ui
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Prepare Data**:
    - Place the A2UI-Bench dataset in `data/raw/a2ui_bench.csv`.
    - Ensure the CSV has columns: `query`, `intent`, `metadata` (or similar).
    - Run the annotation script (manual step required):
      ```bash
      python code/data/ingest.py --annotate --sample-size 500
      ```
      *This will generate `data/processed/annotated_turns.csv`.*

## Running the Simulation

Execute the main simulation pipeline:

```bash
python code/main.py --config code/config.yaml
```

**Configuration Options** (`code/config.yaml`):
- `latency_steps`: [0, 100, 200, 500, 1000]
- `ui_densities`: [1, 3, 5, 10]
- `patience_mean`: 2000 (ms)
- `random_seed`: 42

## Analyzing Results

1.  **Generate Pareto Plot**:
    ```bash
    python code/analysis/viz.py --input data/simulation/results.csv --output plots/pareto_frontier.png
    ```

2.  **Run Statistical Tests**:
    ```bash
    python code/analysis/stats.py --input data/simulation/results.csv --output data/analysis/stats_report.json
    ```

## Validation

Run the test suite to ensure contract compliance:

```bash
pytest tests/
```

## Troubleshooting

- **Dataset Not Found**: Ensure `data/raw/a2ui_bench.csv` exists and matches the expected schema.
- **Router Training Failed**: Check `data/processed/annotated_turns.csv` for missing labels.
- **Out of Memory**: The simulation is designed for sufficient RAM to support the workload. If errors occur, reduce `sample-size` in `ingest.py`.
