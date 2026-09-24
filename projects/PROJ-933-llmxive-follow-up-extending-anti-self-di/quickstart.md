# Quickstart Guide: llmXive Follow-up

This guide outlines the steps to execute the full research pipeline.

## Prerequisites

- Python 3.9+
- `pip install -r requirements.txt`

## Execution Order

The pipeline consists of sequential stages. Run them in order.

### 1. Project Setup & Data Fetch
```bash
python code/setup_project.py
python code/setup_linting.py
python code/data/download.py
```

### 2. Data Preprocessing & Context Simulation
```bash
python code/data/preprocess.py
```
*Outputs: `data/context_splits.json`, `data/excluded_prompts.log`, `data/context_stats.json`*

### 3. Inference-Only Pass (Teacher Distribution)
```bash
python code/models/inference_only.py --mode inference
```
*Outputs: `data/teacher_logits_raw.jsonl`, `data/teacher_distribution.json`*

### 4. Validation of Artifacts (T022)
```bash
python code/data/validate_logits.py
```
*Verifies `data/teacher_logits_raw.jsonl` completeness.*

### 5. Training Loop (AntiSD)
```bash
# The main entry point wraps the timeout enforcer and training loop
python main.py --mode train --timeout 19800
```
*Note: `--timeout` expects an integer in seconds (e.g., 19800 for 5.5h).*
*Outputs: `results/training_trajectory.json`, `results/training_metrics.json`, `results/trajectories.jsonl`*

### 6. Analysis & Reporting
```bash
python code/models/metrics.py
python code/analysis/statistical_test.py
python code/analysis/human_score_ingest.py
python code/analysis/visualize.py
python code/analysis/report_generator.py
```
*Outputs: `results/final_report.md`, `results/plots/*`*

## Full Pipeline Run
To run the entire pipeline (excluding manual human scoring step):
```bash
python code/setup_project.py && \
python code/data/download.py && \
python code/data/preprocess.py && \
python code/models/inference_only.py --mode inference && \
python code/data/validate_logits.py && \
python main.py --mode train --timeout 19800 && \
python code/analysis/report_generator.py
```

## Troubleshooting
- **Timeout Errors**: Ensure `--timeout` is an integer. The default is 5.5 hours (19800s).
- **Missing Data Files**: Ensure previous stages completed successfully before running the next.
- **OOM Errors**: The inference pass uses streaming; if issues persist, reduce batch size in `config/settings.yaml`.