# Quickstart: DreamX-Lite Evaluation

## Prerequisites

- Python 3.10+
- System dependencies: `COLMAP` (for SfM), `ffmpeg` (for video processing)
- Git
- Access to HuggingFace (if the dataset requires a token)

## 1. Environment Setup

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install COLMAP system dependencies (Ubuntu example)
sudo apt-get update
sudo apt-get install -y colmap
```

## 2. Data Preparation

The pipeline attempts to download the DreamX-World subset automatically. If unavailable, it will fall back to a small ScanNet subset for logic verification.

```bash
# Run the data download script
python code/utils/io.py --download
```
*Note: If the dataset requires a token, set `HF_TOKEN` environment variable.*

## 3. Running the Evaluation

The main pipeline script handles generation, SfM, and metric computation.

```bash
# Run the full evaluation (Baseline vs. DreamX-Lite)
python code/pipeline/generate.py --config config/eval_config.yaml
python code/pipeline/evaluate.py --input data/generated/ --output data/derived/metrics.csv
```

## 4. Statistical Analysis

Once metrics are generated, run the statistical analysis.

```bash
python code/analysis/stats.py --input data/derived/metrics.csv --output data/derived/statistical_results.json
```

## 5. Verification

- **Reproducibility**: Run `pytest tests/` to verify metric independence and pipeline integrity.
- **Check Results**: Inspect `data/derived/statistical_results.json` for McNemar and Wilcoxon p-values.

## Troubleshooting

- **SfM Failure**: If SfM fails on many trajectories, check the `sfm_failure_reason` in the metrics log. Consider downsampling video frames or reducing resolution.
- **OOM Errors**: If the CPU runner runs out of memory, reduce the video resolution in `config/eval_config.yaml` or reduce the number of trajectories.
- **Dataset Missing**: If the DreamX-World subset is not found, the script will log a warning and attempt to use the ScanNet fallback. The final report will note this limitation.
