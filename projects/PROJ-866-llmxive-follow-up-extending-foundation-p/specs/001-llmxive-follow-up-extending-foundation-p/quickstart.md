# Quickstart: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

## Prerequisites

-   Python 3.11+
-   `pip`
-   Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-866-llmxive-follow-up-extending-foundation-p
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
    *Note: `requirements.txt` includes `networkx`, `tiktoken` (cl100k_base), `scikit-learn`, `pandas`, `pytest`, `pm4py`, `statsmodels`.*

## Running the Simulation

1.  **Generate Workflows**:
    ```bash
    python src/cli/run_simulation.py --generate --seed [RANDOM_SEED] --count 500
    ```
    *Output*: `data/raw/workflows.json` (500 unique workflows).

2.  **Execute Full Context Baseline**:
    ```bash
    python src/cli/run_simulation.py --execute --mode full
    ```
    *Output*: `data/processed/full_context_logs.json`.

3.  **Execute Compressed Context Variants**:
    ```bash
    python src/cli/run_simulation.py --execute --mode compressed --depths 1,2,3,4,5,6,7,8,9,10
    ```
    *Output*: `data/processed/compressed_context_logs.json`.

4.  **Run Analysis**:
    ```bash
    python src/cli/run_simulation.py --analyze --bootstraps [sufficient_resampling_iterations]
    ```
    *Output*: `data/results/tradeoff_curve.csv`, `data/results/threshold_report.json`, `data/results/run_metrics.json`.

## Testing

Run the full test suite to verify correctness:
```bash
pytest tests/ -v
```
*Includes `test_oracle_independence` to verify separation of concerns.*

## Verifying Results

-   Check `data/results/tradeoff_curve.csv` for the regression curve.
-   Check `data/results/threshold_report.json` for the "safe operating zone" threshold (error rate ≤ 1%), **rounded to 2 decimal places**.
-   Check `data/results/run_metrics.json` for total wall-clock time (SC-005).
-   Ensure `state/projects/...yaml` has been updated with the new artifact hashes.
