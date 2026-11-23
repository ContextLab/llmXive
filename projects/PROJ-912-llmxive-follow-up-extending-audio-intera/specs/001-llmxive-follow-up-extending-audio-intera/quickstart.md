# Quickstart: Audio Interaction Model Extension

## Prerequisites
- Python 3.11+
- Git
- Access to a GitHub Actions runner (free-tier) or local CPU environment with ≥7GB RAM.

## 1. Setup Environment

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-912-llmxive-follow-up-extending-audio-intera

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Data Preparation

The dataset is streamed automatically. No manual download is required.
**Note**: The script splits data first, then calibrates, then filters to ensure no leakage.

```bash
# Run the data filtering script to create the "SubtleCue" testbed
# --split-first ensures a dominant-majority split before filtering
# --calibrate-split ensures a substantial majority of data is used for calibration.
python code/data/subtle_cue_builder.py \
  --datasets esc50,urban_sound_8k \
  --method composite \
  --threshold-freq 8000 \
  --threshold-amp -40 \
  --split-first
```

*Output*: Filtered dataset metadata saved to `data/processed/subtle_cue_manifest.json` (includes calibration and test splits).

## 3. Model Compression & Training

Generate student variants via quantization and pruning.

```bash
# Run the compression script
# Calibration uses the 90% split generated in Step 2
python code/models/compress.py \
  --teacher facebook/wav2vec2-base-960h \
  --configs int,int4 \
  --pruning-ratios,0.2 \
  --distill \
  --calibration-data data/processed/subtle_cue_manifest.json
```

*Output*: Checkpoints saved in `models/checkpoints/`.

## 4. Inference & Evaluation

Run the evaluation pipeline on the "SubtleCue" testbed ([deferred] test split).

```bash
# Run inference and calculate metrics
python code/inference/runner.py \
  --model-dir models/checkpoints/ \
  --testbed data/processed/subtle_cue_manifest.json \
  --thresholds,0.05,0.1
```

*Output*: Metrics saved to `results/metrics.csv`.

## 5. Analysis & Reporting

Generate the robustness curve and sensitivity report.

```bash
# Run robustness analysis
python code/analysis/robustness_curve.py --input results/metrics.csv --output results/robustness_curve.png

# Run sensitivity analysis
python code/analysis/sensitivity.py --input results/metrics.csv --output results/sensitivity_report.json

# Run ablation analysis (normalized by parameter reduction)
python code/analysis/ablation.py --input results/metrics.csv --output results/ablation_report.json
```

*Output*: Plots and reports in `results/`.

## 6. Running on GitHub Actions

To run the full pipeline on CI:

1. Push changes to the `001-audio-compression-robustness` branch.
2. Trigger the workflow (or wait for the scheduled run).
3. View logs in the GitHub Actions tab.

*Note*: The CI runner automatically handles data streaming and memory constraints. If OOM occurs, the job will log the failure and continue with remaining models.

## 7. Troubleshooting

- **OOM Error**: Reduce the `--testbed` size or use a smaller model variant.
- **CUDA Error**: Ensure `CUDA_VISIBLE_DEVICES=""` is set; the pipeline is CPU-only.
- **Missing Data**: Verify internet connection for Hugging Face streaming.
- **Leakage Warning**: Ensure `--split-first` is used in Step 2 to prevent calibration/test overlap.
