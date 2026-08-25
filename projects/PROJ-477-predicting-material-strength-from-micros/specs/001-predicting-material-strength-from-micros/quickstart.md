# Quickstart: Predicting Material Strength from Microstructure Images

## Prerequisites

- Python 3.11+
- `pip`
- Sufficient RAM (for dataset loading and augmentation)
- GB+ Disk space

## Installation

1.  **Clone and Setup**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-477-predicting-material-strength-from-micros
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r code/requirements.txt
    ```

## Data Preparation

The data download and validation are automated.

1.  **Run Validation and Preprocessing**
    This script downloads the dataset, validates it, and prepares the splits.
    ```bash
    python code/main.py --stage preprocess
    ```
    *   **Output**: `data/processed/`, `results/validation_report.json`.
    *   **Note**: If validation fails (invalid ratio > 1%), the script exits with code 1.

## Training

Train the MobileNetV2 model with data augmentation.

1.  **Run Training**
    ```bash
    python code/main.py --stage train
    ```
    *   **Output**: `results/models/best_model.pth`, `results/metrics.log`.
    *   **Duration**: ~2-3 hours on CPU.

## Evaluation & Interpretability

Generate metrics, heatmaps, and sensitivity analysis.

1.  **Run Evaluation**
    ```bash
    python code/main.py --stage evaluate
    ```
    *   **Output**: `results/metrics.json`, `results/plots/gradcam/*.png`, `results/sensitivity_analysis.csv`.

## Reproducibility

To reproduce the exact results:
1.  Ensure `code/config.py` has the same `RANDOM_SEED` (default: 42).
2.  Use the same dataset source URL (verified in `research.md`).
3.  Run the full pipeline:
    ```bash
    python code/main.py --stage full
    ```

## Troubleshooting

- **OOM Error**: Reduce `BATCH_SIZE` in `code/config.py`.
- **Dataset Missing**: Check network connectivity and the HuggingFace URL.
- **Validation Fail**: Inspect `results/validation_report.json` for specific error types.
