# Quickstart: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Prerequisites
*   Python 3.11+
*   Access to Hugging Face (for dataset downloads)
*   7GB+ RAM, 2+ CPU cores
*   ~15GB disk space

## Installation

1.  **Clone and Setup Environment**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/code
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**
    ```bash
    python -c "import torch; import onnxruntime; import cv2; print('All dependencies OK')"
    ```

## Data Preparation

1.  **Download Datasets**
    Run the download script to fetch UCF101 and Kinetics-400 subsets.
    ```bash
    python data/download.py --source ucf101,kinetics-400 --output ../data/raw
    ```
    *Note: This will download ~2GB of data. Checksums are verified automatically.*

2.  **Manual Annotation (Required)**
    Run the annotation tool to generate ground truth scores.
    ```bash
    python data/annotate.py --input ../data/raw --output ../data/annotations/continuity_scores.csv
    ```
    *Follow the on-screen prompts to assign scores (1-5) to each clip. Ensure inter-annotator agreement is checked. The system will automatically oversample to ensure N>=500 valid clips.*

## Execution

1.  **Run Full Pipeline**
    Execute the main pipeline script. This performs:
    *   Pre-flight runtime check (FR-009)
    *   Divergence computation (CPU-only)
    *   Correlation and sensitivity analysis (with IPW for natural distribution)
    ```bash
    python main.py --config config.yaml
    ```

2.  **Output Artifacts**
    Results will be saved to `../data/processed/`:
    *   `divergence_metrics.csv`: Per-clip metrics.
    *   `correlation_results.csv`: Statistical tests (includes `source_code_hash`).
    *   `sensitivity_report.csv`: Threshold analysis.
    *   `variance_report.csv`: Variance check.

## Troubleshooting

*   **Runtime Exceeds 5.5 Hours**: The script will automatically reduce Euler steps to N=200 and re-run. If this still fails, the script will halt with a "Feasibility Error".
*   **Low Variance**: If `variance_report.csv` shows variance < 0.05 (and not bimodal), the pipeline halts. Re-check annotation rubric.
*   **ONNX Loading Error**: Ensure `onnxruntime` is installed for CPU (`onnxruntime` not `onnxruntime-gpu`).
*   **Insufficient Samples**: If the final valid sample count < 500, the system will attempt to fetch and annotate replacements automatically.