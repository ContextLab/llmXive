# llmXive Quickstart Guide

## Prerequisites

Ensure you have Python 3.11+ and the required dependencies installed:

```bash
pip install -r requirements.txt
```

## Running the Full Pipeline

The full pipeline can be executed via the main orchestrator script. This will:
1. Generate synthetic workflows
2. Run full context execution
3. Run compressed context execution
4. Perform trade-off analysis

### Step 1: Generate Workflows

Generate a set of synthetic workflows with deterministic seeding:

```bash
python code/generators/synthetic_workflow.py --count 500 --seed 42 --output data/raw/workflows.json
```

### Step 2: Run Full Context Execution

Execute workflows with full context to establish ground truth:

```bash
python code/engines/full_context.py --workflow data/raw/workflows.json --output data/processed/full_context_logs.json
```

### Step 3: Run Compressed Context Execution

Execute workflows with compressed context at various depths:

```bash
python code/engines/compressed_context.py --workflow data/raw/workflows.json --depths 2 4 6 8 10 --output data/processed/compressed_context_logs.json
```

### Step 4: Run Analysis

Perform statistical analysis on the trade-off between context reduction and policy violations:

```bash
python code/analysis/tradeoff_model.py --full data/processed/full_context_logs.json --compressed data/processed/compressed_context_logs.json
```

### Step 5: Apply Multiple Comparison Correction

Apply Bonferroni correction to statistical significance tests:

```bash
python code/analysis/bonferroni_correction.py --input data/processed/regression_stats.json --output data/processed/corrected_pvalues.json
```

### Step 6: Detect Threshold

Identify the safe operating zone threshold:

```bash
python code/analysis/threshold_detection.py --input data/processed/corrected_pvalues.json --output data/results/threshold_ci.json
```

### Step 7: Finalize State Registry

Update the state registry with the final reproducibility hash:

```bash
python code/utils/finalize_state_registry.py
```

## Expected Outputs

After running the full pipeline, you should find the following artifacts:

- `data/raw/workflows.json`: Generated synthetic workflows
- `data/processed/full_context_logs.json`: Full context execution logs
- `data/processed/compressed_context_logs.json`: Compressed context execution logs
- `data/processed/corrected_pvalues.json`: Bonferroni-corrected p-values
- `data/results/threshold_ci.json`: Threshold detection results with confidence intervals
- `data/results/tradeoff_curve.csv`: Regression curve data
- `state/projects/PROJ-866-llmxive-follow-up-extending-foundation-p.yaml`: Updated state registry with reproducibility hash

## Verification

To verify reproducibility, run the pipeline twice with the same seed and compare the output hashes:

```bash
python code/utils/reproducibility_checker.py
```

This will generate a report at `data/results/reproducibility_report.json`.
