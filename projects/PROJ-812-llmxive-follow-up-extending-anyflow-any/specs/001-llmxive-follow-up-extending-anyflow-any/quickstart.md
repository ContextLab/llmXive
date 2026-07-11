# Quickstart: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## 1. Prerequisites

- Python 3.11+
- A minimal CPU core configuration, 7 GB RAM (GitHub Actions free-tier compatible)
- `git`
- `huggingface-cli` (for dataset download)
- `decord` (for efficient video seeking)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-812-llmxive-follow-up-extending-anyflow-any

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Preparation

Download the Kinetics-400 validation set (or a subset) using the HuggingFace `datasets` library.

```bash
python code/scripts/download_data.py --dataset kinetics400 --split validation --num-clips --output data/raw/kinetics_subset
```
*Note: We request 200 clips to ensure we can fill valid slots after timeouts/corruptions.*

*Note: Ensure the downloaded data is checksummed.*

## 4. Running the Pipeline

Execute the full pipeline (feature extraction, divergence calculation, analysis).

```bash
python code/main.py --config code/config.yaml
```

**Arguments**:
- `--config`: Path to configuration file (default: `code/config.yaml`).
- `--timeout-sec`: Maximum time per clip for Euler rollout (default: 900).
- `--target-clips`: Target number of valid clips (default: 60).
- `--max-attempts`: Max attempts per slot (default: 3).

## 5. Outputs

- `data/processed/features.csv`: Extracted statistical features.
- `data/processed/divergence_metrics.csv`: Computed divergence values.
- `data/processed/threshold_results.json`: Optimal threshold and sensitivity analysis.
- `logs/pipeline.log`: Detailed execution logs, including CPU/Memory usage, skipped clips, and timeout counts.

## 6. Verification

To verify the results:

1.  **Check Divergence**: Ensure no NaN values in `divergence_metrics.csv` for `is_primary_analysis=True`.
2.  **Check Threshold**: Confirm `threshold_results.json` contains a valid `optimal_threshold`.
3.  **Reproducibility**: Run the pipeline again with the same seed and verify that checksums of output files match.

```bash
python code/scripts/verify_reproducibility.py --input data/processed/
```