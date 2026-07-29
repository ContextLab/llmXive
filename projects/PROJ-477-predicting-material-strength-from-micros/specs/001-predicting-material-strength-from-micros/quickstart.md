# Quickstart: Predicting Material Strength from Microstructure Images

## Prerequisites
- Python 3.11+
- pip
- 7GB+ RAM (for local testing)
- Access to the verified HuggingFace dataset URL.

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Download & Preprocessing

1. **Download the dataset**:
   ```bash
   python code/data/download.py
   ```
   *Output*: `data/raw/data_synth_ebsd.zip` and checksum verification.

2. **Preprocess and Split**:
   ```bash
   python code/data/preprocess.py
   ```
   *Output*: `data/processed/` (train/, val/, test/ directories) and `data/processed/manifest.csv`.

3. **Validate Data**:
   ```bash
   python code/data/validate.py
   ```
   *Output*: `results/validation_report.json`. Exits with code 1 if invalid pairs > 1%.

4. **Extract Features**:
   ```bash
   python code/data/extract_features.py
   ```
   *Output*: `data/features/grain_features.csv`.

## Model Training

1. **Train the CNN**:
   ```bash
   python code/models/train.py
   ```
   *Output*: `models/best_checkpoint.pt`, `results/training_log.json`.
   *Note*: Uses early stopping (patience=5). Runs on CPU by default.

2. **Run Ablation (No Augmentation)**:
   ```bash
   python code/models/train_ablation.py
   ```
   *Output*: `models/best_ablation_checkpoint.pt`.

## Evaluation & Interpretation

1. **Run Evaluation**:
   ```bash
   python code/eval/metrics.py
   ```
   *Output*: `results/performance_report.json`, `results/null_hypothesis_report.json`.

2. **Generate Interpretability**:
   ```bash
   python code/eval/interpret.py
   ```
   *Output*: `results/interpretability_report.json`, Grad-CAM heatmaps in `results/heatmaps/`.

3. **Generate Predictions with Confidence Intervals**:
   ```bash
   python code/eval/predictor.py
   ```
   *Output*: `results/predictions.csv` (contains `predicted_strength`, `ci_lower`, `ci_upper`, `baseline_strength`).

4. **Sensitivity Analysis**:
   ```bash
   python code/eval/sensitivity.py
   ```
   *Output*: `results/sensitivity_analysis.csv`.

## Running Tests

```bash
pytest tests/
```

## Troubleshooting

- **Memory Error**: Reduce `batch_size` in `code/utils/config.py`.
- **Data Missing**: Verify the HuggingFace URL is accessible; check `data/raw/` for incomplete downloads.
- **Baseline Outperforms**: This is a valid scientific result; check `results/null_hypothesis_report.json` for the p-value.