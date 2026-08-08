# Quickstart: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## Prerequisites

- **Python**: 3.11 or higher.
- **System**: Linux environment (recommended for GitHub Actions compatibility).
- **RAM**: ≥ 7GB available.
- **Disk**: ≥ 14GB available.
- **Dependencies**: `pip` and `git`.

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat
    ```

2.  **Create a virtual environment** and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to a CPU-only build to ensure compatibility with the target environment.*

## Data Preparation

The project uses the **LIBERO** dataset. The data preparation script will download a sample subset and convert it to the required format.

1.  **Run the data download and quantization pipeline**:
    ```bash
    python code/main.py --task prepare_data --bit_depth 4 8 16
    ```
    This will:
    - Download a sample of the LIBERO dataset from the verified Hugging Face sources.
    - Compute velocities from continuous data via finite differencing.
    - Quantize states to 4, 8, and 16-bit discrete vectors.
    - Inject noise (std dev = 0.1 * quantization_step).
    - Save results to `data/processed/quantized/`.

2.  **Verify data integrity**:
    ```bash
    python code/main.py --task verify_data
    ```
    This checks for 1-bit collapse and ensures all files are within expected size limits.

## Training & Inference

Execute the training and inference loop on the CPU.

1.  **Run the full experiment** (Training + Inference + Analysis):
    ```bash
    python code/main.py --task run_experiment --n_runs 10 --horizons 100 250 500 1000
    ```
    - This will train the adapted Kairos model for each bit depth.
    - Train a continuous baseline model per-run for fair comparison.
    - Perform inference on long sequences.
    - Calculate error metrics and stability thresholds.
    - Generate the final `stability_report.json`.

2.  **Monitor resource usage**:
    The script logs CPU utilization and peak RAM usage to `results/resource_profile.json`.

## Analysis & Reporting

1.  **View the stability report**:
    ```bash
    cat results/aggregate/stability_report.json
    ```
    This file contains the minimum information density threshold and statistical significance results.

2.  **Visualize results** (optional, requires `matplotlib`):
    ```bash
    python code/analysis/plot_results.py
    ```

## Troubleshooting

- **Out of Memory (OOM)**: Reduce the sample size in `code/config.py` or decrease the batch size.
- **Timeout (6h limit)**: The script will checkpoint and exit gracefully. Resume by running `python code/main.py --task resume`.
- **1-bit Collapse**: If the data is flagged as "Invalid Data" for 1-bit, the analysis will skip that level and report the reason.

## Validation

To ensure the pipeline is working correctly:
- Run `pytest tests/` to execute unit and integration tests.
- Verify that `results/aggregate/stability_report.json` contains a `stability_claim_framing` field and valid p-values.