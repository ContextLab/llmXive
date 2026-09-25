# Quickstart Guide: llmXive Automated Science Pipeline

This guide provides the commands to run the full llmXive pipeline, including data generation, execution, analysis, and verification.

## Prerequisites

- Python 3.11+
- Required packages installed (see `requirements.txt`)
- Project root directory

## Running the Full Pipeline

### 1. Generate Synthetic Workflows

Generate 500 synthetic workflows with deterministic seeding:

```bash
python code/generators/synthetic_workflow.py --count 500 --seed 42 --output data/raw/workflows.json
```

### 2. Execute Full Context Validation

Run the full context execution engine on all generated workflows:

```bash
python code/engines/full_context.py --workflow data/raw/workflows.json --output data/processed/full_context_logs.json
```

### 3. Execute Compressed Context Variants

Run compressed context execution with multiple depth levels:

```bash
python code/engines/compressed_context.py --workflow data/raw/workflows.json --depth 2 --output data/processed/compressed_depth_2.json
python code/engines/compressed_context.py --workflow data/raw/workflows.json --depth 4 --output data/processed/compressed_depth_4.json
python code/engines/compressed_context.py --workflow data/raw/workflows.json --depth 6 --output data/processed/compressed_depth_6.json
python code/engines/compressed_context.py --workflow data/raw/workflows.json --depth 8 --output data/processed/compressed_depth_8.json
python code/engines/compressed_context.py --workflow data/raw/workflows.json --depth 10 --output data/processed/compressed_depth_10.json
```

### 4. Run Trade-off Analysis

Perform the full trade-off analysis including regression, threshold detection, and corrections:

```bash
python code/analysis/tradeoff_model.py --full data/processed/full_context_logs.json --compressed data/processed/compressed_context_logs.json
```

### 5. Apply Bonferroni Correction

Apply multiple comparison corrections to the regression results:

```bash
python code/analysis/bonferroni_correction.py --input data/processed/regression_stats.json --output data/processed/corrected_pvalues.json
```

### 6. Detect Threshold with Confidence Intervals

Identify the safe operating zone threshold:

```bash
python code/analysis/threshold_detection.py --full data/processed/full_context_logs.json --compressed data/processed/compressed_context_logs.json --output data/results/threshold_ci.json
```

### 7. Generate Regression Data

Create the CSV file for regression analysis:

```bash
python code/analysis/generate_regression_data.py --processed data/processed/ --output data/results/tradeoff_curve.csv
```

### 8. Run Data Hygiene Audit

Verify data integrity and derivation consistency:

```bash
python code/utils/data_hygiene_audit.py
```

## Expected Output Files

After running the full pipeline, the following files should be present:

- `data/raw/workflows.json` - Generated synthetic workflows
- `data/processed/full_context_logs.json` - Full context execution logs
- `data/processed/compressed_depth_*.json` - Compressed context execution logs
- `data/processed/corrected_pvalues.json` - Bonferroni-corrected p-values
- `data/results/tradeoff_curve.csv` - Regression curve data
- `data/results/threshold_ci.json` - Threshold detection results with confidence intervals
- `data/results/data_hygiene_audit.json` - Data hygiene audit report

## Verification

To verify the pipeline ran correctly:

1. Check that all output files exist in their expected locations
2. Run the data hygiene audit to ensure data integrity
3. Verify that the threshold CI file contains valid confidence intervals
4. Confirm that the trade-off curve CSV has the expected columns

## Troubleshooting

If you encounter errors:

- Ensure all required packages are installed (`pip install -r requirements.txt`)
- Verify that input files exist in the expected locations
- Check that the output directories (`data/raw/`, `data/processed/`, `data/results/`) exist
- Review the error messages for specific issues with file paths or data formats

## Parallel Execution

For faster execution, you can run independent tasks in parallel:

- Steps 1 (Generate) can be run independently
- Steps 2-3 (Execution) can be parallelized across different depth levels
- Steps 4-7 (Analysis) should be run sequentially as they depend on previous outputs

## Notes

- All commands use relative paths from the project root
- The `--seed` parameter ensures deterministic results for reproducibility
- The pipeline is designed to handle edge cases (single-node graphs, depth=0) gracefully
- Data hygiene audit is critical for ensuring research integrity