# Quickstart: MobileForge Logic Distillation

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the `projects/PROJ-930-llmxive-follow-up-extending-mobileforge` repository.

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-930-llmxive-follow-up-extending-mobileforge
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `torch` is installed in CPU mode (no CUDA).
    ```bash
    python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
    # Expected: <version> False
    ```

## Workflow

### Step 1: Data Preparation
Download the MobileForge logs and extract the training triples.
```bash
python code/data/download_mobileforge.py
python code/data/extract_triples.py
```
*Output*: `data/processed/extraction_dataset.parquet`

### Step 2: Model Training
Train the distilled model on CPU.
```bash
python code/models/train_distilled.py \
  --data data/processed/extraction_dataset.parquet \
  --output models/distilled_model/ \
  --device cpu
```
*Output*: `models/distilled_model/` (config, weights, tokenizer)

### Step 3: Evaluation
Run the evaluation against the TinyLlama baseline and perform statistical tests.
```bash
python code/evaluation/run_tasks.py \
  --model models/distilled_model/ \
  --baseline tinyllama \
  --tasks data/processed/androidworld_tasks.parquet \
  --output data/processed/evaluation_results.csv
  --ablation retry
```
*Output*: `data/processed/evaluation_results.csv` (includes distilled, baseline, and ablation results)

### Step 4: Statistical Analysis
Calculate metrics, perform McNemar's test, and run sensitivity analysis.
```bash
python code/evaluation/stats.py \
  --results data/processed/evaluation_results.csv \
  --thresholds 0.01 0.05 0.1
```
*Output*: `data/processed/statistical_report.json` (includes p-values, effect size, variance).

## Verification

*   **Check Convergence**: Ensure `final_loss` in the training log is ≤ 0.5.
*   **Check Effect Size**: Verify `statistical_report.json` reports observed effect size and confidence intervals.
*   **Check Robustness**: Verify `variance` across thresholds is ≤ 5%.

## Troubleshooting

*   **OOM Error**: Reduce batch size in `train_distilled.py`.
*   **Emulator Crash**: Check `logcat` output; ensure ADB is connected.
*   **No GPU Error**: The script should run on CPU. If it fails with CUDA errors, ensure `device="cpu"` is set.