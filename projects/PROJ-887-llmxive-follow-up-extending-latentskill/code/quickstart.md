# llmXive Quickstart Guide

This guide executes the full pipeline in "dry-run" mode (N=1 per task) to verify the entire flow from ingestion to final report generation without timing out.

## Prerequisites

- Python 3.11+
- All dependencies installed via `pip install -r requirements.txt`

## Execution Steps

### 1. Verify Data Sources
```bash
python code/src/validate/citation_check.py
```

### 2. Download Weights (Dry-Run: Skip if already present)
```bash
python code/src/ingestion/download_weights.py --output code/data/raw
```

### 3. Flatten LoRA Weights
```bash
python code/src/ingestion/flatten_lora.py --input code/data/raw --output code/data/processed
```

### 4. Build Skill Vector Index
```bash
python code/src/retrieval/vector_db.py --input code/data/processed/weights.npz --output code/data/processed/skill_index.npz --k 5
```

### 5. Run Dry-Run Evaluation (N=1)
```bash
python code/src/evaluation/runner.py --adapter code/artifacts/synthesized_adapters/test_adapter.pt --task code/data/processed/eval_tasks.yaml --output code/data/results/eval_log.csv --model code/model.gguf
```

### 6. Generate Statistics Report
```bash
python code/src/evaluation/report_generator.py --input code/data/results/eval_log.csv --output code/data/results/stats_report.json
```

### 7. Generate Final Report
```bash
python code/src/evaluation/final_report.py --input code/data/results/stats_report.json --output code/reports/final_report.md
```

### 8. Generate Plots
```bash
python code/src/utils/plotting.py --input code/data/results/stats_report.json --output code/reports/plots
```

## Expected Outputs

- `code/data/processed/skill_index.npz`
- `code/data/raw/alfworld_weights.npz`
- `code/data/raw/searchqa_weights.npz`
- `code/data/results/stats_report.json`
- `code/reports/final_report.md`
