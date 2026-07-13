# Quickstart: llmXive follow-up: extending "Moebius: 0.2B Lightweight Image Inpainting Framework with 10B-Level Pe"

## Prerequisites

- **Python**: 3.10+
- **Hardware**: Multiple CPU cores, 7 GB RAM (minimum for CI).
- **OS**: Linux (Ubuntu 20.04+ recommended).
- **Disk**: Sufficient free storage space.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins PyTorch to CPU-only version to ensure compatibility with CI.*

## Data Setup

1.  **Download Dataset**:
    Run the data download script (this fetches the verified Places2 subset):
    ```bash
    python code/data/download.py
    ```
    *This script verifies the checksum against the HuggingFace source.*

2.  **Generate Synthetic Masks**:
    ```bash
    python code/data/mask_generator.py --seed <random_seed>
    ```
    *Output: `data/processed/mask_metrics.json`*

3.  **Simulate Human Annotations**:
    ```bash
    python code/data/annotator.py --participants --seed 42
    ```
    *Output: `data/annotations/human_scores.csv`*

## Training

1.  **Train Gating Head**:
    ```bash
    python code/training/train_gating.py --epochs [REDACTED]
    ```
    *This trains the lightweight gating head to predict complexity from synthetic metrics.*

2.  **End-to-End Fine-Tuning**:
    ```bash
    python code/training/train_end_to_end.py --epochs [a sufficient number of]
    ```
    *Fine-tunes the dynamic Moebius model.*

## Evaluation

1.  **Run Evaluation**:
    ```bash
    python code/eval/evaluate.py
    ```
    *This runs inference on the test set, measures latency, computes FID/LPIPS, and generates the report.*

2.  **View Results**:
    Check `data/results/evaluation_report.json` for metrics.
    Check `data/results/proxy_validation.json` for correlation analysis.

## Verification

To verify the implementation meets the spec:
- **Check Correlation**: Ensure `correlation_proxy_human` in `proxy_validation.json` demonstrates a strong positive correlation.
- **Check Latency**: Ensure `reduction_percent` in `evaluation_report.json` is significantly high for low-complexity bins.
- **Check Quality**: Ensure `fid.difference` is minimized to demonstrate statistically significant improvement.

## Troubleshooting

- **Out of Memory**: If you encounter `RuntimeError: CUDA out of memory` (unlikely on CPU) or `MemoryError`, reduce `batch_size` in `config.py` or use a smaller image resolution.
- **Slow Training**: Ensure you are not accidentally using a GPU. Set `CUDA_VISIBLE_DEVICES=""` before running.
- **Dataset Missing**: If the download fails, manually download the zip from the verified URL and place it in `data/raw/`.
