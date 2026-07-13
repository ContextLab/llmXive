# Quickstart: llmXive follow-up: extending "ABot-Earth 0.5: Generative 3D Earth Model"

## Prerequisites
*   **OS**: Linux (Ubuntu 22.04+ recommended for GitHub Actions compatibility).
*   **Python**: 3.11 or higher.
*   **Disk Space**: A substantial amount of storage (for raw data, processed patches, and model weights).
*   **RAM**: Minimum 8 GB (system), but the pipeline targets < 6.5 GB peak usage.

## Installation

1.  **Clone and Setup Environment**
    ```bash
    cd projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Verify CPU-Only Configuration**
    Ensure no CUDA is available or forced:
    ```bash
    python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'Device: {torch.get_default_device()}')"
    # Expected Output: CUDA Available: False
    ```

3.  **Download Dependencies (Models)**
    The ONNX model weights will be downloaded automatically on first run if not present in `data/models/`.
    *Note: Ensure you have a stable internet connection for the initial download.*

## Running the Pipeline

### Step 1: Data Curation (Phase 1)
Download and align a representative sample of available data.
```bash
python code/data/download_sentinel.py --count 50 --output data/raw/sentinel_aligned
# Note: Use --count 50 for a quick test run. Use 500 for full experiment.
```
*This step will also fetch OpenTopography LiDAR and compute alignment errors.*

### Step 2: Synthetic Degradation (Phase 2)
Apply degradation masks to the curated data.
```bash
python code/data/synthesize_degradation.py --input data/raw/sentinel_aligned --output data/processed/degraded_scenes --seeds 12345
```

### Step 3: Full Experiment Execution (Phase 3 & 4)
Run the complete pipeline: Baseline 3DGS → Inpainting → Metrics → Threshold Analysis.
```bash
python code/pipeline/run_full_experiment.py \
  --input data/processed/degraded_scenes \
  --lidar data/raw/sentinel_aligned/lidar \
  --output data/results \
  --max-samples 20 \
  --log-performance
```
*   `--max-samples`: Limit to a small sample size for a quick feasibility check (approx. -2 hours).
*   `--log-performance`: Enables detailed RAM/Time logging to `performance_log.csv`.

### Step 4: Analysis & Visualization
Generate the threshold plots and statistical reports.
```bash
python code/analysis/statistical_tests.py --input data/results/metrics.csv --output data/results/report.pdf
python code/analysis/plot_thresholds.py --input data/results/metrics.csv --output data/results/threshold_curve.png
```

## Expected Outputs
*   `data/results/metrics.csv`: Full fidelity metrics for all samples.
*   `data/results/performance_log.csv`: Runtime and RAM usage per sample.
*   `data/results/threshold_curve.png`: Plot showing the critical NNF threshold.
*   `data/results/report.pdf`: Statistical significance report (t-test results).

## Troubleshooting
*   **ERR_OOM_CPU**: If you encounter this error, reduce `--max-samples` or the patch size in `config.py`.
*   **CUDA Error**: Ensure `torch` is installed from the CPU-only wheel and `CUDA_VISIBLE_DEVICES` is unset.
*   **Alignment Error > 2m**: The sample will be automatically excluded and logged. Check `data/raw/exclusion_log.csv`.
