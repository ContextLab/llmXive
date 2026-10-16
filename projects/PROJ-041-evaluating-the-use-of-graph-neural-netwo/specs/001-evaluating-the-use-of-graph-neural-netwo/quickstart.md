# Quickstart: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

## Prerequisites

*   Python 3.11+
*   `pip`
*   Access to the CTU-13 dataset (or the verified NetFlow fallback).
*   ~Sufficient free disk space (several gigabytes) for data and dependencies.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <project-dir>
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
    *Note: This installs `torch` (CPU version), `networkx`, `scikit-learn`, `xgboost`, `captum`, and the `datasets` library used for CTU‑13 download.*

## Data Setup

The pipeline expects data in `data/raw/`.

1.  **Download CTU-13** (if available locally) or use the verified fallback:
    ```bash
    # If you have CTU-13, place it in data/raw/ctu13_scenario1.csv
    # Otherwise, download it automatically:
    python code/data/download_ctu13.py
    ```

2.  **Verify Data Integrity**:
    ```bash
    python code/utils/memory_monitor.py --check
    ```

## Running the Pipeline

Execute the full analysis pipeline (Ingestion -> Graph Construction -> Training -> Evaluation):

```bash
python code/main.py --scenarios 1 2 3 --seeds 42 123 456
```

*   `--scenarios`: List of CTU-13 scenario IDs to process (or BoT-IoT scenarios if using fallback).
*   `--seeds`: Random seeds for reproducibility.

### Expected Output
*   `data/processed/`: GraphML files (including `graph_{scenario}_subsampled.graphml`) and feature matrices.
*   `data/results/`: CSV files with metrics and p-values.
*   `logs/`: Memory usage logs and training progress.

## Verification

1.  **Run Unit Tests** (optional – only runs utilities that do not depend on the full dataset):
    ```bash
    pytest code/tests/test_graph_construction.py -v
    ```

2.  **Check Memory Limit**:
    The test `test_memory_limits.py` simulates a large graph and asserts that peak memory < 7GB.

## Troubleshooting

*   **CUDA Error**: If you see "CUDA not available", ensure you installed the CPU version of PyTorch. The code explicitly sets `device='cpu'`.
*   **Memory Error**: If the script crashes with OOM, reduce the `--scenarios` list or check if the graph subsampling logic is active (nodes > 5,000).
*   **Missing Data**: If CTU-13 is missing, the script will raise a clear error because no fallback is allowed for Task T002.
*   **Unseen Nodes in Test**: If the test set contains new IPs, they will be dropped or assigned default features as per the Temporal Holdout strategy.
