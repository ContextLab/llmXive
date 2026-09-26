# Quickstart: Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems

## Prerequisites

-   Python 3.11+
-   `pip` or `venv`
-   Access to the verified datasets (requires internet connection for SNAP/Network Repository download).

## Installation

1.  **Clone the repository** (or navigate to the project root).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: `requirements.txt` will contain pinned versions of `networkx`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `pytest`, `requests`)*

## Running the Pipeline

### 1. Download Data
The pipeline expects raw data in `data/raw/`. Run the download script:
```bash
python -m src.main --action download
```
This will fetch graphs from the verified SNAP and Network Repository URLs and save them to `data/raw/`.

### 2. Execute Full Pipeline
Run the main orchestration script to process all available networks, run simulations, and perform regression:
```bash
python -m src.main --action run
```
**Expected Output**:
-   `data/processed_metrics.csv`: Topological features.
-   `results/sim_results.json`: Simulation thresholds.
-   `results/regression_summary.json`: Statistical analysis.
-   `results/pipeline_status.json`: Execution status (SUCCESS/TIMEOUT).

### 3. Visualize Results
Generate heatmaps and diagnostic plots:
```bash
python -m src.main --action viz
```
Output will be saved to `results/figures/`.

## Verification

To ensure the implementation matches the spec:

1.  **Unit Tests**:
    ```bash
    pytest tests/ -v
    ```
    This validates topology metrics, RK45 integration, and regression logic.

2.  **Schema Validation**:
    The pipeline automatically validates output JSONs against the schemas defined in `contracts/`.
    ```bash
    python -m src.validators --validate-all
    ```

3.  **Manual Verification (SC-003)**:
    Check `results/verification_report.json` for an initial set of alphabetically sorted networks.

4.  **Ring Graph Validation (SC-006)**:
    Check `results/verification_report.json` for the Ring Graph test result (must be within 5% of theoretical).

## Troubleshooting

-   **Timeout Error**: If the pipeline exceeds a predetermined time threshold, check `results/pipeline_status.json`. The system will log the specific network ID causing the delay.
-   **Insufficient Data**: If `N < 10`, the regression step will be skipped, and a warning will be logged in `results/regression_summary.json`.
-   **Disconnected Graphs**: Networks with multiple components will be flagged in `sim_results.json` with `status: "disconnected"` and excluded from regression.
-   **Data Fetch Failure**: If the SNAP or Network Repository URLs fail, the pipeline will halt with a warning in `results/pipeline_status.json`.