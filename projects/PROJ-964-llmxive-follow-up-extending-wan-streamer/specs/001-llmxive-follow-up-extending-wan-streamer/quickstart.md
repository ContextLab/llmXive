# Quickstart: llmXive follow-up: extending "Wan-Streamer v0.1"

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a CPU-only environment (e.g., GitHub Actions, local machine with ≥7 GB RAM).
*   (Optional) Local copy of Wan-Streamer v0.1 logs (if not using VoxCeleb2 fallback).

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-964-llmxive-follow-up-extending-wan-streamer
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
    *Note: `requirements.txt` pins all versions to ensure reproducibility.*

## Data Preparation

The system automatically handles data fetching. If Wan-Streamer logs are missing, it falls back to VoxCeleb2.

1.  **Run the data fetcher**:
    ```bash
    python code/data/fetch_data.py
    ```
    *This script checks for local logs. If missing, it downloads a sample of VoxCeleb2 from the verified Hugging Face URL.*

2.  **Extract and preprocess**:
    ```bash
    python code/data/extract_turn_taking.py
    ```
    *Output: `data/processed/turn_taking_dataset.parquet`.*

## Training the Estimator

1.  **Run the training script**:
    ```bash
    python code/model/estimator_train.py
    ```
    *This trains the lightweight RNN/Transformer on CPU. It monitors RAM usage and will reduce sample size if limits are approached.*
    *Output: `data/artifacts/estimator.pt`.*

## Simulation & Evaluation

1.  **Run the hybrid simulation**:
    ```bash
    python code/model/hybrid_simulate.py
    ```
    *This runs the hybrid inference pipeline, including the randomized counterfactual intervention.*
    *Output: `data/processed/hybrid_results.parquet`.*

2.  **Calculate metrics and run statistical tests**:
    ```bash
    python code/metrics/calculate_fid_stability.py
    python code/metrics/validate_proxy_mos.py
    python code/metrics/statistical_tests.py
    ```
    *Output: `data/artifacts/metrics.json` and logs.*

## Validation

1.  **Update state**:
    ```bash
    python code/utils/state_manager.py --update
    ```
    *This updates `state.yaml` with artifact hashes and validation status.*

2.  **Verify contracts**:
    ```bash
    pytest tests/contract/
    ```
    *Ensures all data files match the schemas in `contracts/`.*

## Troubleshooting

*   **RAM Exceeded**: The system automatically reduces the sample size. Check logs for "Power Limitation" warnings.
*   **No Human Data**: If proxy MOS validation fails due to missing human ratings, the system logs "Assumption Validated (No Human Data Available)" and continues.
*   **Dataset Missing**: Ensure you have internet access for the VoxCeleb2 fallback.
