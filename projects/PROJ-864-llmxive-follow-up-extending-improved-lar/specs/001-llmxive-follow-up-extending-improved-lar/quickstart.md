# Quickstart: llmXive Overfitting Trajectory Study

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM, GB+ Disk (Free-tier CI runner)

## Setup

1.  **Clone and Install Dependencies**
    ```bash
    cd projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/
    pip install -r requirements.txt
    ```

2.  **Verify Environment**
    ```bash
    python -c "import torch; print(torch.__version__); print('CPU:', torch.backends.cpu.is_available())"
    ```

## Execution Workflow

### Step 1: Construct Micro-Corpus
Run the data preparation script. This will download, tokenize, and truncate the dataset.
```bash
python data/download_micro_corpus.py --tokenizer gpt2 --target-tokens
```
*Output*: `data/processed/micro_corpus_train.jsonl`, `data/processed/micro_corpus_test.jsonl`, `data/artifacts/corpus_validation.json`

### Step 2: Run Training Experiment
Execute the main training loop. This trains both models (2 seeds each) and logs metrics.
```bash
python training/run_experiment.py --epochs --seeds 2 --batch-size --max-time-h
```
*Note*: The `--max-time-h` flag ensures the job stops before the CI limit to allow time for analysis.
*Output*: `data/artifacts/training_logs.csv`

### Step 3: Statistical Analysis
Run the analysis script to compute ANOVA and correlations.
```bash
python analysis/statistical_test.py --log-file data/artifacts/training_logs.csv
```
*Output*: `data/artifacts/statistical_results.json`

### Step 4: HumanEval Benchmark
Evaluate final checkpoints on HumanEval.
```bash
python training/evaluate_human_eval.py --checkpoint data/artifacts/checkpoints/
```
*Output*: `data/artifacts/human_eval_results.json`

## Verification

- **Data Bounds**: Check `data/processed/micro_corpus_train.jsonl` for token count (should be on the order of millions).
- **Validation**: Check `data/artifacts/corpus_validation.json` for status "PASS".
- **Logs**: Ensure `training_logs.csv` has entries for all completed epochs.
- **Stats**: Verify `statistical_results.json` contains `interaction_p_value` and `correlation_r_ar`.

## Troubleshooting

- **OOM Error**: Reduce `--batch-size` in `run_experiment.py`.
- **Timeout**: The job will auto-stop. Check `training_logs.csv` for the last completed epoch.
- **Dataset Missing**: Ensure `huggingface-cli login` is configured if using gated datasets (not required for this study).
