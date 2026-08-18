# Quickstart: llmXive follow-up: extending "Translation as a Bridging Action"

## Prerequisites

- Python 3.10+
- A minimal CPU core configuration, 7GB RAM (GitHub Actions Free Tier compatible)
- Disk space: sufficient capacity (for simulation and data)

## 1. Setup Environment

Clone the repository and install dependencies.

```bash
cd projects/PROJ-855-llmxive-follow-up-extending-translation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Generate Synthetic Dataset

Run the data generation script. This will create the raw dataset and validate the schema.

```bash
python code/generate_data.py --config code/config.yaml
```

*   **Output**: `data/raw/synthetic_episodes.parquet`, `data/checksums.json`
*   **Validation**: The script asserts ≥5,000 rows, no forbidden columns, and valid schema.

## 3. Prepare Data Splits

Split the raw data into geometry-disjoint train/test sets.

```bash
python code/utils.py --split --input data/raw/synthetic_episodes.parquet
```

*   **Output**: `data/processed/train.parquet`, `data/processed/test.parquet`

## 4. Train Models

Train the main model, baseline, and control.

```bash
# Main Translation-Only Model
python code/train_model.py --input data/processed/train.parquet --output data/processed/trained_model.pt

# Geometry-Only Baseline (MLP)
python code/train_baseline.py --input data/processed/train.parquet --output data/processed/baseline_model.pt

# Shuffled Translation Control
python code/train_control.py --input data/processed/train.parquet --output data/processed/control_model.pt
```

*   **Validation**: Each script logs the parameter count and ensures it is <10M.

## 5. Evaluate & Report

Run the evaluation script to compute metrics and perform statistical tests.

```bash
python code/evaluate.py \
  --model data/processed/trained_model.pt \
  --baseline data/processed/baseline_model.pt \
  --control data/processed/control_model.pt \
  --test data/processed/test.parquet \
  --output data/processed/metrics_report.json
```

*   **Output**: `data/processed/metrics_report.json` containing accuracy, p-values, and confusion matrix.

## 6. Sensitivity Analysis (Optional)

Run the sensitivity sweep to check robustness.

```bash
python code/sensitivity.py --config code/config.yaml --output data/sweep/
```

## 7. Reproducibility Check

To verify the entire pipeline from scratch:

```bash
rm -rf data/processed/ data/raw/synthetic_episodes.parquet
python code/generate_data.py --config code/config.yaml
python code/utils.py --split --input data/raw/synthetic_episodes.parquet
python code/train_model.py --input data/processed/train.parquet --output data/processed/trained_model.pt
python code/evaluate.py --model data/processed/trained_model.pt --test data/processed/test.parquet --output data/processed/metrics_report.json
```

Verify that the results in `metrics_report.json` match the previous run (within statistical variance).
