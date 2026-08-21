# Quickstart: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Prerequisites

*   Python 3.11+
*   Git
*   Sufficient free disk space (for video clips and model weights)
*   Internet access (for Hugging Face downloads)
*   **System Dependencies**: `ffmpeg`, `libsm6`, `libxext6` (for OpenCV video decoding)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-812-llmxive-follow-up-extending-anyflow-any
    ```

2.  **Install System Dependencies** (for video decoding):
    ```bash
    # On GitHub Actions (ubuntu-latest)
    sudo apt-get update && sudo apt-get install -y ffmpeg libsm6 libxext6
    ```

3.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to a CPU-only version, `onnxruntime`, and `opencv-python-headless`.*

5.  **Verify setup**:
    ```bash
    python -c "import torch; print('CPU:', torch.backends.mps.is_available() or torch.cuda.is_available() == False)"
    ```

## Running the Pipeline

The pipeline consists of five sequential steps. Run them in order.

### Step 0: Pre-flight Verification
Validates dataset URLs and model weights before download.
```bash
python code/download.py --verify-only
```

### Step 1: Data Download
Download video clips from UCF and DAVIS 2017.
```bash
python code/download.py --output data/raw/videos --count 500
```
*Output*: `data/raw/videos/` (folder of .mp4 files)

### Step 2: Calibration & Annotation
Opens a CLI interface for human annotators to score clips.
1.  **Calibration**: First, score 20 synthetic clips to verify accuracy (≥ 90%).
2.  **Pilot**: Score 50 clips with two annotators to calculate Kappa (≥ 0.81).
3.  **Main**: Score remaining clips.
```bash
python code/annotate.py --input data/raw/videos --output data/raw/ground_truth.csv
```
*Note*: This step requires human interaction. Follow the 5-point Likert rubric. The script will automatically record `annotator_id` (via CLI prompt) and `timestamp` (via `datetime.now()`).
*Output*: `data/raw/ground_truth.csv`

### Step 3: Validation & Variance Check
Checks data quality, calculates variance, and performs the stability check (Constitution VI).
```bash
python code/validate.py --ground-truth data/raw/ground_truth.csv --output data/processed/
```
*Output*: `data/processed/variance_report.csv` (includes Kappa and stability check results)

### Step 4: Inference & Metric Calculation
Computes flow-map divergence for all clips (CPU-only).
```bash
python code/inference.py --input data/raw/videos --ground-truth data/raw/ground_truth.csv --output data/processed/divergence_metrics.csv
```
*Note*: This step includes a pilot check (30 clips) to determine if N=500 is feasible. If not, it automatically switches to N=200.
*Output*: `data/processed/divergence_metrics.csv`

### Step 5: Analysis & Reporting
Performs correlation, regression, sensitivity analysis, and generates the final report.
```bash
python code/analysis.py --divergence data/processed/divergence_metrics.csv --ground-truth data/raw/ground_truth.csv --variance data/processed/variance_report.csv --output data/processed/
python code/report.py --output data/processed/final_report.md
```
*Output*: `data/processed/correlation_results.csv`, `data/processed/sensitivity_report.csv`, `data/processed/final_report.md` (includes variance_report.csv)

## Verification

To verify the pipeline ran correctly:
1.  Check `data/processed/variance_report.csv` for Kappa (≥ 0.81) and stability check.
2.  Check `data/processed/correlation_results.csv` for Pearson $r$ and p-value.
3.  Check `data/processed/final_report.md` to ensure `variance_report.csv` is embedded.
4.  Run the unit tests:
    ```bash
    pytest tests/unit/
    ```

## Troubleshooting

*   **Out of Memory**: Reduce `--batch-size` in `inference.py` (default: a smaller value).
*   **Runtime Timeout**: If the pilot check fails, the script will automatically switch to N=200. If N=200 also fails, the script will exit with an error.
*   **CUDA Error**: Ensure `torch` is installed from the CPU-only wheel. The script should not use CUDA.
*   **Video Decode Error**: Ensure `ffmpeg` is installed on the system.
