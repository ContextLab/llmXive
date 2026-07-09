# Quickstart: Exploring the Role of Network Structure in Superconducting Qubit Coupling

## Prerequisites
- Python 3.11+
- Internet access (for IBM Quantum API)
- (Optional) IBM Quantum API token (for higher rate limits, though public access is used by default).

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    git clone <repo-url>
    cd projects/PROJ-163-exploring-the-role-of-network-structure-/
    ```

2.  **Create a virtual environment** and install dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Verify dependencies**:
    ```bash
    python -c "import networkx, scipy, pandas, qiskit_ibm_runtime, sklearn; print('Dependencies OK')"
    ```

## Running the Pipeline

The full analysis pipeline can be executed via the main script.

```bash
# Run the full pipeline (Fetch -> Graph -> Stats -> Viz -> Hygiene)
python code/main.py
```

### Output
- **Data**: Saved to `data/processed/` (CSVs).
- **Figures**: Saved to `data/processed/plots/` (PNGs).
- **Logs**: Printed to stdout and saved to `logs/pipeline.log`.
- **State Update**: `state/projects/PROJ-163-...yaml` is updated with data checksums.

## Testing

Run the test suite to verify graph calculations and API mocking.

```bash
# Unit tests (mocked API)
pytest tests/test_fetcher.py -v

# Integration tests (live API, rate-limited)
pytest tests/test_integration_fetch.py -v
```

## Data Inspection

To inspect the raw data fetched:
```bash
ls data/raw/
cat data/processed/graph_metrics.csv | head
```

To check the correlation results:
```bash
cat data/processed/correlation_results.csv | grep "True"  # Filter significant results
```

## Troubleshooting

- **Rate Limit Errors**: The fetcher automatically retries with exponential backoff. If persistent, add an IBM Quantum token to `QISKIT_IBM_TOKEN` environment variable.
- **Disconnected Graphs**: Devices with disconnected coupling maps will have `spectral_gap=0` and be excluded from path-length correlations. Check `logs/pipeline.log` for warnings.
- **Missing Metrics**: If a device lacks `entanglement_fidelity`, it is skipped for that specific correlation.
- **Low Power**: If N < 30, the output will explicitly state the Minimum Detectable Effect Size (MDES) and flag the study as exploratory.