# Quickstart: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

## Prerequisites

*   Python 3.11+
*   Git
*   Substantial RAM (recommended for full runs)

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-813-llmxive-follow-up-extending-mint-managed
    python -m venv venv
    source venv/bin/activate
    ```

2.  **Verify Project Structure**:
    Ensure the following directories exist. If not, create them:
    ```bash
    mkdir -p code/data code/simulation code/analysis tests code/utils data/raw data/processed data/logs docs
    ```

3.  **Install Dependencies**:
    Create `requirements.txt` with the following content:
    ```text
    simpy>=4.0.0
    numpy>=1.24.0
    scipy>=1.10.0
    networkx>=3.0.0
    pandas>=2.0.0
    pytest>=7.0.0
    hypothesis>=6.0.0
    pyyaml>=6.0.0
    ```
    Then install:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Linting & Formatting**:
    Create `pyproject.toml` with the following content:
    ```toml
    [tool.black]
    line-length = 88
    target-version = ['py311']

    [tool.ruff]
    line-length = 88
    select = ["E", "F", "W", "I"]
    ignore = []
    ```
    Install and run:
    ```bash
    pip install ruff black
    ruff check code/
    black --check code/
    ```

5.  **Verify Environment**:
    ```bash
    pytest tests/unit/test_env.py -v
    ```

## Running the Simulation

### Step 1: Generate Synthetic Data
```bash
python code/data/generator.py --seed <random_value> --adapters 1000 --trace-size 100000
```
*Outputs to `data/processed/topology.pkl` and `data/processed/trace.npy`.*

### Step 2: Run Simulation (Single Policy)
```bash
python code/simulation/runner.py --policy FCFS --seed 42
```
*Outputs to `data/processed/results_fcfs_42.csv`.*

### Step 3: Run Full Experiment (All Policies)
```bash
python code/cli/main.py --replications 10 --policy all
```
*Runs FCFS, Greedy, and Topological Lookahead across multiple seeds.*

### Step 4: Statistical Analysis
```bash
python code/analysis/statistics.py --input data/processed/results_*.csv
```
*Outputs `data/processed/statistical_report.json` with p-values and confidence intervals.*

## Validation

*   **Memory Check**: Monitor `top` or `htop` during `runner.py`. Should not exceed a manageable memory footprint.
*   **Time Check**: Full 10-replication run should complete in < 6 hours.
*   **Schema Check**:
    ```bash
    pytest tests/contract/test_schemas.py
    ```
*   **Directory Check**: Verify `code/`, `data/`, `tests/` directories exist and contain the expected files.