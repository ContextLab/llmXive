# Quickstart: Socratic Transformers

## 1. Prerequisites

-   Python 3.11+
-   Git
-   (Optional) Kaggle CLI for GPU offload (if CPU fails)

## 2. Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Dependencies**:
    -   `transformers`, `peft`, `bitsandbytes`, `datasets`, `scikit-learn`, `accelerate`.

## 3. Running the Pipeline

### Step 1: Data Generation
Download GSM8K and generate the three conditions (Static, Selection, Ablation).
```bash
python -m src.data.generator --config src/utils/config.yaml
```
*Output*: `data/processed/static_tuples.jsonl`, `dialogue_tuples.jsonl`, `ablation_tuples.jsonl`.

### Step 2: Fine-Tuning
Train the model on each condition. The script auto-detects OOM and offloads to Kaggle if necessary. **Runs multiple independent seeds per condition.**
```bash
python -m src.model.trainer --condition selection --seeds 5
python -m src.model.trainer --condition ablation --seeds 5
python -m src.model.trainer --condition static --seeds 5
```

### Step 3: Evaluation
Evaluate on GSM8K test, MATH-500, and MMLU-STEM.
```bash
python -m src.eval.metrics --conditions selection ablation static
```

### Step 4: Analysis
Run statistical tests (Independent t-tests with Bonferroni correction).
```bash
python -m src.eval.stats --input data/results/metrics.json
```

## 4. Reproducibility

-   **Seeds**: All random seeds are pinned in `src/utils/config.yaml`.
-   **Data**: Raw datasets are fetched via `datasets.load_dataset` on every run.
-   **Checksums**: Verify data integrity with `python -m src.utils.io verify`.

## 5. Troubleshooting

-   **OOM Error**: If the training script fails with `CUDA out of memory` or `exit code 137`, it will automatically attempt to offload to a Kaggle GPU instance. Ensure your Kaggle account is linked if running locally.
-   **Dataset Download**: Ensure internet access. If behind a proxy, set `HF_DATASETS_OFFLINE=0`.
-   **Timeout**: If a run exceeds a predefined time threshold, it will be terminated. Check logs for "TIMEOUT" message.