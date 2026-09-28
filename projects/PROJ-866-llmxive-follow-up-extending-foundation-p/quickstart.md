# llmXive Quickstart Guide

## Prerequisites

- Python 3.11+
- Installed dependencies (see `requirements.txt`)

## Project Structure

- `code/`: Source code
- `data/`: Data directories
 - `data/raw/`: Generated workflows
 - `data/processed/`: Execution logs
 - `data/results/`: Analysis outputs
- `tests/`: Test suite
- `state/`: State registry

## Running the Full Pipeline

The full pipeline can be executed using the main orchestrator:

```bash
python code/main.py --generate --compress --analyze
```

This command will:
1. Generate synthetic workflows (T012)
2. Execute full context validation (T014)
3. Execute compressed context variants (T021)
4. Analyze trade-offs and identify thresholds (T029-T031)

## Individual Component Execution

If you need to run individual components, use the following commands:

### Generate Workflows

```bash
python code/generators/synthetic_workflow.py --count 500 --seed 42 --output data/raw/workflows.json
```

### Full Context Execution

```bash
python code/engines/full_context.py --workflow data/raw/workflows.json --output data/processed/full_context_logs.json
```

### Compressed Context Execution

```bash
python code/engines/compressed_context.py --workflow data/raw/workflows.json --depths 1 2 4 6 8 10 12 14 16 18 20 --output data/processed/compressed_context_logs.json
```

### Analysis

```bash
python code/analysis/tradeoff_model.py --full data/processed/full_context_logs.json --compressed data/processed/compressed_context_logs.json
```

### Verify Invalid Workflow Exclusion (T067)

```bash
python code/utils/verify_invalid_workflow_exclusion.py
```

This script verifies that all workflows marked as `is_valid=false` in `data/raw/` are correctly excluded from the final analysis in `data/results/tradeoff_curve.csv` and `data/results/threshold_ci.json`.

### Bonferroni Correction

```bash
python code/analysis/bonferroni_correction.py --input data/processed/pairwise_comparison_results.json --output data/processed/corrected_pvalues.json
```

### Threshold Detection

```bash
python code/analysis/threshold_detection.py --input data/processed/tradeoff_curve.csv --output data/results/threshold_ci.json
```

## Verification Steps

1. **Reproducibility Check**:
 ```bash
 python code/utils/reproducibility_checker.py --run1 data/run1 --run2 data/run2
 ```

2. **Data Consistency Check**:
 ```bash
 python code/utils/verify_data_consistency.py
 ```

3. **Invalid Workflow Exclusion Check**:
 ```bash
 python code/utils/verify_invalid_workflow_exclusion.py
 ```

## Expected Outputs

After running the full pipeline, the following files should be present:

- `data/raw/workflows.json`: Generated workflows
- `data/processed/full_context_logs.json`: Full context execution logs
- `data/processed/compressed_context_logs.json`: Compressed context execution logs
- `data/processed/binned_data.json`: Binned data for analysis
- `data/processed/pairwise_comparison_results.json`: Pairwise comparison results
- `data/processed/corrected_pvalues.json`: Corrected p-values
- `data/results/tradeoff_curve.csv`: Trade-off curve data
- `data/results/threshold_ci.json`: Threshold confidence interval
- `data/results/glmm_diagnostics.json`: GLMM diagnostics
- `data/results/invalid_workflow_exclusion_report.json`: T067 verification report

## Troubleshooting

If you encounter issues:

1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check that `data/` directories exist and are writable
3. Verify that the seed is consistent for reproducibility
4. Check logs in `data/processed/` for specific error messages

## Notes

- All commands assume execution from the project root directory
- The `--generate` flag triggers workflow generation
- The `--compress` flag triggers compressed context execution
- The `--analyze` flag triggers statistical analysis
- Invalid workflows are automatically filtered during analysis
- Edge cases (single-node graphs, depth=0) are logged separately
