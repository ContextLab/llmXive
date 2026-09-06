# Quickstart Guide: Predicting Adsorption Isotherm Parameters

## Prerequisites

Ensure you have Python 3.8+ and pip installed. Install dependencies:

```bash
pip install -r requirements.txt
```

## Data Preparation

1. **Download Data**: The pipeline fetches real data from the NASA/NIST dataset.
2. **Merge & Preprocess**: Automatically handled by the main orchestrator.

## Running the Pipeline

The `code/main.py` script orchestrates the full pipeline. It initializes the runtime logger, executes the requested task, and persists the `data/benchmarks/runtime_log.json` file upon completion or failure.

### Full Curation (US1)

```bash
python code/main.py --task curate_data
```

This runs:
1. Download (T060)
2. Merge (T061)
3. Preprocess (T015a-1, T015b)
4. Fitting (T014c)
5. Audit (T045)

### Training & Evaluation (US2)

```bash
python code/main.py --task train_model
```

This runs:
1. Preprocess
2. Fitting
3. Audit
4. Training (T020, T021)
5. Null Model (T065)
6. Null Comparison (T024)
7. Evaluation (T023)

### SHAP Analysis (US3)

```bash
python code/main.py --task shap_analysis
```

This runs:
1. Training
2. Evaluation
3. SHAP Analysis (T030)
4. Report Generation (T071)

### Benchmark Mode

```bash
python code/main.py --task benchmark
```

Runs the full benchmark pipeline with profiling.

## Output Artifacts

Upon successful completion, the following files will be generated:

- `data/benchmarks/runtime_log.json`: Runtime metrics and stage logs (T055).
- `data/raw/merged_dataset.parquet`: Merged raw data.
- `data/processed/imputed_dataset.parquet`: Cleaned and imputed data.
- `data/results/shap_summary.json`: SHAP feature importance.
- `data/results/consensus_narrative_report.md`: Divergence analysis report.
- `data/validation/exclusion_log.json`: Logs of excluded entries.

## Verification

To verify the runtime log was written:

```bash
cat data/benchmarks/runtime_log.json
```

Ensure `status` is "completed" and `duration_seconds` is populated.
