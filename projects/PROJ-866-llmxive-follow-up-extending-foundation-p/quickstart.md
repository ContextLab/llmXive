# llmXive Quickstart Guide

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Quick Start

### 1. Generate Workflows

Generate 500 synthetic workflows with deterministic seeding:

```bash
python code/generators/synthetic_workflow.py --count 500 --output data/raw --seed 42
```

### 2. Execute Full Context

Run the full context engine on all generated workflows:

```bash
# Note: This is typically done via the main orchestrator (see below)
# To run manually on a single file:
python code/engines/full_context.py --workflow data/raw/wf_0000.json --output data/processed/full_wf_0000.json
```

### 3. Execute Compressed Context

Run compressed context execution:

```bash
# Note: This is typically done via the main orchestrator (see below)
# To run manually on a single file:
python code/engines/compressed_context.py --workflow data/raw/wf_0000.json --depth 2 --output data/processed/compressed_wf_0000_depth2.json
```

### 4. Run Full Pipeline (Recommended)

The main orchestrator handles generation, execution, and analysis in one command:

```bash
python code/main.py --generate 500 --compress --analyze
```

This command:
1. Generates 500 workflows to `data/raw/`
2. Executes full context validation
3. Executes compressed context for depths 1-5
4. Runs analysis (regression, Bonferroni correction, threshold detection)
5. Outputs results to `data/results/`

### 5. Verify Results

Check the output files:

```bash
ls -la data/results/
# Should contain:
# - tradeoff_curve.csv
# - threshold_ci.json
# - corrected_pvalues.json (in data/processed/)
```

## Troubleshooting

### Missing Output Files

If output files are missing, ensure the pipeline ran to completion. Check for errors in the console output.

### Determinism Issues

Ensure you are using the same `--seed` value for reproducible results. The pipeline explicitly seeds `random` and `numpy.random` at startup.

### CLI Argument Errors

If you encounter `argparse` errors, ensure you are using the correct flags as shown above. The scripts require `--output` for generators and `--workflow`/`--output` for engines.
