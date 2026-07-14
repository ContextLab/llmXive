# Quickstart: llmXive follow-up: extending "LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing"

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a GitHub Actions free-tier runner (or local machine with 7GB+ RAM, 2+ CPU cores).
-   HuggingFace CLI token (if required for dataset access).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow
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

4.  **Verify dataset access**:
    Ensure you can access the verified DAVIS and YouTube-VOS URLs (check network connectivity).

## Running the Pipeline

The pipeline is executed via the `main.py` script in the `code/` directory.

### Step 1: Data Preparation (Optional - if not pre-downloaded)
```bash
python code/main.py --stage data_prep --dataset davis --stratify
```
*This downloads and stratifies the dataset into `data/raw/`.*

### Step 2: Optical Flow Computation
```bash
python code/main.py --stage flow_compute --method farneback
```
*This computes flow fields for all clips and stores them in `data/flow/`.*

### Step 3: Baseline Inference
```bash
python code/main.py --stage inference --model baseline
```
*This runs the baseline LiveEdit model and saves metrics to `data/metrics/baseline.jsonl`.*

### Step 4: Flow-Coherence Inference
```bash
python code/main.py --stage inference --model flow_coherence
```
*This runs the modified model and saves metrics to `data/metrics/flow_coherence.jsonl`.*

### Step 5: Statistical Analysis
```bash
python code/main.py --stage analysis --method ks_test --sweep 0.01,0.05,0.1
```
*This performs the K-S test, regression, and sensitivity analysis, saving results to `results/summary.json`.*

## Expected Output

-   `data/metrics/baseline.jsonl`: Baseline performance metrics.
-   `data/metrics/flow_coherence.jsonl`: Flow-Coherence performance metrics.
-   `results/summary.json`: Statistical analysis results (p-values, thresholds).
-   `results/summary.md`: Human-readable research summary.

## Troubleshooting

-   **OOM Error**: If you encounter "Out of Memory", reduce the batch size in `code/config.yaml` or downsample the video resolution.
-   **Invalid Flow**: If many frames are flagged `invalid_flow`, the optical flow algorithm may be struggling with the motion. Check `data/flow/` logs.
-   **Timeout**: If the job exceeds 6 hours, the pipeline will checkpoint. Resume with `--resume`.
