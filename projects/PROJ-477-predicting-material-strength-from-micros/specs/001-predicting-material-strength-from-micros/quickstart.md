# Quickstart: Predicting Material Strength from Microstructure Images

## Prerequisites

*   Python 3.11+
*   Git
*   Access to GitHub Actions (for CI) or a local environment with 7GB+ RAM and 2+ CPU cores.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-477-predicting-material-strength-from-micros
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
    *Note: Ensure `torch` is installed with the CPU-only flag (e.g., `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`).*

## Data Setup

The project will automatically download the verified dataset from HuggingFace upon first run.

1.  **Run the Data Download & Preprocessing Script**:
    ```bash
    python code/main.py --stage download
    ```
    *This will:*
    *   Download `data_synth_ebsd.zip` from the verified URL.
    *   Verify the checksum.
    *   Preprocess images (resize to 224x224, normalize).
    *   Split into train/val/test sets.
    *   Generate `manifest.json`.
    *   *Output*: `data/processed/` directory.

## Training

1.  **Run the Training Pipeline**:
    ```bash
    python code/main.py --stage train
    ```
    *This will:*
    *   Initialize MobileNetV2 with frozen weights.
    *   Train for max 50 epochs with early stopping.
    *   Save the best checkpoint to `results/artifacts/`.
    *   *Output*: Model checkpoint and training logs.

## Evaluation & Interpretability

1.  **Run the Evaluation Pipeline**:
    ```bash
    python code/main.py --stage eval
    ```
    *This will:*
    *   Load the best checkpoint.
    *   Compute MSE and R² against the naive baseline.
    *   Perform the t-test.
    *   Generate Grad-CAM heatmaps.
    *   Run sensitivity analysis.
    *   *Output*: `results/metrics.json`, `results/figures/`, `results/sensitivity_report.json`.

## Verification

To ensure reproducibility, run the full pipeline from scratch:

```bash
python code/main.py --stage full
```

This executes `download` -> `train` -> `eval` in sequence.

## Troubleshooting

*   **OOM Error**: Reduce `BATCH_SIZE` in `code/utils/config.py`.
*   **CUDA Error**: Ensure you installed the CPU version of PyTorch.
*   **Missing Data**: Check `data/raw/` for the downloaded zip. If missing, re-run the download stage.
