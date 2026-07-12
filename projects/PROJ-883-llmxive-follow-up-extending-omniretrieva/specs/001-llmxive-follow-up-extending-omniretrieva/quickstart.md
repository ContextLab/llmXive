# Quickstart: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites

*   Python 3.11+
*   `pip` package manager
*   GitHub Actions Runner (or local machine with sufficient RAM)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `pandas`, `scipy`, `statsmodels`, `networkx`, `duckdb`, `pyyaml`, `whoosh`.*

## Running the Experiment

The experiment is executed via the main orchestration script:

```bash
python code/main.py --output data/processed/
```

### What this does:
1.  **Generates** 500 synthetic queries (balanced across Text, Relational, Graph; depths 1-4). *Note: The generator includes a hard-stop loop (`if count >= 500: break`) to strictly enforce the 500 query limit.*
2.  **Executes** each query against the respective CPU-throttled engine (Whoosh, DuckDB, NetworkX). *Latency is measured via real execution (`time.perf_counter`) with complexity-proportional artificial delays added by the CPU-burner loop.*
3.  **Records** latency, translation errors, and timeouts.
4.  **Runs** the LMM and Jonckheere-Terpstra analysis to test for interaction effects and monotonic trends.
5.  **Generates** the interaction plot and saves results to `data/processed/`.

### Expected Output
*   `data/processed/metrics.jsonl`: Raw execution logs (including `cpu_burner_ms`).
*   `data/processed/analysis_results.json`: Statistical analysis results (LMM p-values, trend test p-values, CIs).
*   `data/processed/plots/interaction_plot.png`: Visualization of latency vs. complexity.

## Validation

To ensure the results are reproducible and valid:

1.  **Run the test suite**:
    ```bash
    pytest tests/ -v
    ```
2.  **Validate schemas**:
    ```bash
    pytest tests/contract/ -v
    ```
    *This ensures all output files match the defined YAML schemas, including the query limit.*

## Troubleshooting

*   **CPU Throttling Failed**: If the script detects that `cgroups` or `resource` limits are not applied, it will exit with a specific error code. Ensure you are running in a container or environment that supports resource limits.
*   **Memory Error**: If you encounter `MemoryError`, reduce the `--num-queries` argument (e.g., `python code/main.py --num-queries 200`). *Note: The schema enforces a maximum limit.*
*   **Timeouts**: Queries exceeding a predefined timeout threshold are recorded as timeouts. This is expected behavior for high-complexity graph queries under strict CPU constraints.
*   **Latency Measurement**: Ensure that `time.perf_counter()` is used in the engine scripts. Simulated latencies are not allowed; all base latency is measured via real execution.
