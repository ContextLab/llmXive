# Quick Start Guide: llmXive AgenticSTS Follow-up

This guide walks you through the execution of the full llmXive pipeline, from data validation to statistical reporting.

## Prerequisites

- Python 3.11 or higher
- `pip` package manager
- Access to the project root directory

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Validate Data Source

Before running the pipeline, ensure that `data/raw/` contains valid trajectory files. The parser will automatically validate checksums and file integrity. If files are missing or corrupted, the pipeline will fail with a clear error message.

```bash
python code/parser.py --validate-only
```

## Step 3: Run the Full Pipeline

Execute the main pipeline script to run all stages in sequence:

```bash
python code/main.py
```

This command performs:
1. Data parsing and metric extraction
2. Entropy calculation
3. Stratified data splitting
4. Ablation study (training and hold-out sets)
5. Proxy validation and sample size checks
6. Classifier training
7. Dynamic and baseline simulations
8. Statistical aggregation and testing
9. Report generation

## Step 4: Dry-Run Mode (Optional)

To verify the pipeline on a small subset before full execution, use dry-run mode:

```bash
python code/main.py --dry-run
```

This processes only the first 5 trajectories, checking for edge cases (NaN entropy, budget truncation) without generating full-scale outputs.

## Step 5: Review Outputs

Upon successful completion, check the following artifacts in `data/processed/`:

- `baseline_comparison.csv`: Win rates and token usage by condition.
- `statistical_results.json`: Significance test results (p-values, effect sizes).
- `token_reduction_verification.json`: Verification of ≥30% token reduction.
- `divergence_report.json`: Trajectory divergence status.

The trained model is saved to `models/layer_utility_classifier.pkl`.

## Troubleshooting

### Data Validation Errors
If the parser reports missing or corrupted data files, ensure that `data/raw/` contains the expected trajectory logs and that checksums are valid.

### Proxy Validation Failure
If the proxy correlation (static log vs. ablation utility) is < 0.7, the pipeline will raise an exception. Review the ablation study configuration and data quality.

### Sample Size Warning
If the sample count is < 300, the pipeline will log a warning and generate fallback k=2 labels. This is expected behavior per specification.

### Token Budget Enforcement
If entropy calculations return NaN/Inf, the simulator defaults to retrieving all layers. Check `data/processed/simulation_logs.json` for audit trails of minimum context floor enforcement.

## Performance Optimization

For CPU-only environments, the pipeline is optimized to complete within 6 hours. Use the `--dry-run` flag for rapid testing. For large datasets, consider chunked processing (see `code/perf_optimizer.py`).

## Next Steps

- Review the statistical results in `data/processed/statistical_results.json`.
- Analyze the baseline comparison in `data/processed/baseline_comparison.csv`.
- Iterate on hyperparameters in `code/config.py` if needed.
- Run unit tests to verify edge cases:
 ```bash
 pytest tests/
 ```