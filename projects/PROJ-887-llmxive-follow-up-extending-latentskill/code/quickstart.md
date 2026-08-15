# Quickstart Guide: llmXive Follow-up

This guide outlines the steps to run the full analysis pipeline for the "Extending LatentSkill" project.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Execution Order

Run the following commands in sequence. Each step produces data required by the next.

### 1. Download Weights (T012b)
Downloads real LoRA weights from HuggingFace.
```bash
python src/ingestion/download_weights.py
```
*Output*: `data/raw/alfworld_weights.npz`, `data/raw/searchqa_weights.npz`

### 2. Flatten LoRA & Build Index (T013, T014d)
Flattens weights into vectors and saves the skill index.
```bash
python src/ingestion/flatten_lora.py
python src/retrieval/vector_db.py
```
*Output*: `data/processed/skill_index.npz`

### 3. Generate Evaluation Tasks (T022g1)
Creates held-out composite task pairs.
```bash
python src/validation/generate_eval_tasks.py
```
*Output*: `data/processed/known_composites_pairs.yaml`

### 4. Linearity Check (T030)
Calculates Pearson correlation between text and weight spaces.
```bash
python src/validation/linearity_check.py
```
*Output*: `data/results/linearity_correlation.json`

### 5. Evaluation Runner (T026, T027)
Runs synthesized adapters on the environment.
```bash
python src/evaluation/runner.py --adapter <adapter_path> --task <task_id> --output data/results/eval_log.csv
# Note: Run this loop for multiple tasks/adapters as required by the full evaluation script.
# For the full sweep, use:
python src/evaluation/run_sensitivity_sweep.py
```

### 6. Statistical Analysis (T057, T058)
Computes p-values and applies Benjamini-Hochberg correction.
```bash
python src/evaluation/stats.py
```

### 7. Report Generation (T032b)
Compiles all results into a final report.
```bash
python src/evaluation/report_generator.py
```
*Output*: `data/results/stats_report.json`

## Verification

After running the full pipeline, verify that `data/results/stats_report.json` exists and contains valid metrics.