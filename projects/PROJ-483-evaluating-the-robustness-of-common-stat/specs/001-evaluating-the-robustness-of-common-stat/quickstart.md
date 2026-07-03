# Quickstart: Evaluating the Robustness of Common Statistical Tests to Non-Independence in Public Datasets

## Prerequisites
-   Python 3.10 or higher
-   Git
-   Access to a GitHub Actions runner (for CI execution) or a local machine with 8GB+ RAM.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd your-repo/projects/PROJ-483-evaluating-the-robustness-of-common-stat
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

## Running the Simulation

### Option A: Full Pipeline (Recommended)
This command downloads data, runs the full simulation (all tests, all dependencies), and generates reports.
```bash
python code/main.py --mode full
```
*Note: This may take up to 6 hours on a 2-core runner.*

### Option B: Single Configuration (Debug)
Run a single test type with a specific dependency strength for quick validation.
```bash
python code/main.py --mode debug \
  --dataset uci_har_test \
  --test t_test \
  --structure temporal \
  --strength 0.3 \
  --replications 1000
```

### Option C: Reproduce a Specific Run
Re-run a simulation using a previously saved configuration and seed.
```bash
python code/main.py --mode reproduce \
  --run-id <UUID_FROM_RESULTS>
```

## Verifying Results

1.  **Check Outputs**:
    -   Aggregated metrics: `results/aggregated.csv`
    -   Visualizations: `results/plots/error_rate_curves.png`
    -   Logs: `logs/execution.log`

2.  **Validate Checksums**:
    Ensure data integrity by running:
    ```bash
    python code/main.py --mode verify-checksums
    ```

3.  **Run Tests**:
    ```bash
    pytest tests/ -v
    ```

## Troubleshooting

-   **OOM Error**: If you encounter `MemoryError`, ensure you are running on a machine with at least 8GB RAM, or reduce the `--replications` flag. The GitHub Actions runner has 7GB RAM; the pipeline is optimized for this, but large datasets may require sampling.
-   **Missing Dataset**: If a dataset fails to download, check the `data/manifests/checksums.json` file. The script will automatically retry verified URLs.
-   **Slow Execution**: Ensure you are using `numpy` vectorized operations. If running locally, ensure no other heavy processes are running.
