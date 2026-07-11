# Quickstart: Predicting Molecular Reactivity Using Graph Neural Networks

## Prerequisites

*   Python 3.11+
*   4 GB+ RAM available
*   Git

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-243-predicting-molecular-reactivity-using-gr
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `torch` is installed in CPU mode:
    ```python
    import torch
    assert torch.cuda.is_available() == False, "GPU detected; this plan requires CPU-only."
    ```

## Running the Pipeline

### 1. Data Ingestion
Download and preprocess QM9 (automatically handles retries and memory checks):
```bash
python code/main.py --stage download_preprocess
```
*Output*: `data/processed/graphs.pkl`

### 2. Model Training
Train Spectral GNN, Heterophily GNN, and Random Forest:
```bash
python code/main.py --stage train
```
*Output*: `code/models/weights_spectral.pth`, `weights_hetero.pth`, `rf_model.pkl`

### 3. Evaluation
Compute metrics and run the paired t-test:
```bash
python code/main.py --stage evaluate
```
*Output*: `data/processed/metrics.json`

### 4. Interpretability
Generate feature attribution maps:
```bash
python code/main.py --stage explain
```
*Output*: `data/processed/attribution.json`

## Expected Outputs

*   **Metrics**: A JSON file containing MSE, MAE, R, and p-values for all models.
*   **Artifacts**: Model weights and attribution maps saved in `data/processed/`.
*   **Logs**: Console output detailing memory usage and training progress.

## Troubleshooting

*   **Memory Error**: If the process crashes, the script should have automatically reduced the dataset subset size. Check `logs/memory_monitor.log`.
*   **Download Failure**: The script retries 3 times. If it fails, check your internet connection and the HuggingFace status.
*   **CUDA Error**: Ensure `torch` was installed with the CPU-only flag (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
