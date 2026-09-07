# llmXive Quickstart Guide

This guide provides instructions for running the llmXive automated science pipeline
to generate workflows, execute them with compressed context, and analyze the
trade-off between context reduction and policy violations.

## Prerequisites

- Python 3.11 or higher
- Required dependencies installed (see `requirements.txt`)

```bash
pip install -r requirements.txt
```

## Project Structure

```
.
├── code/ # Source code
│ ├── main.py # Orchestrator
│ ├── generators/ # Workflow generators
│ ├── engines/ # Execution engines
│ ├── analysis/ # Trade-off analysis
│ ├── utils/ # Utility functions
│ └──...
├── data/
│ ├── raw/ # Generated workflow definitions
│ ├── processed/ # Execution logs
│ └── results/ # Analysis outputs
├── contracts/ # JSON Schemas
├── state/ # Project state registry
└── tests/ # Test suite
```

## Running the Full Pipeline

The pipeline consists of three main stages:
1. **Generate**: Create synthetic workflow baselines
2. **Compress**: Execute workflows with compressed context
3. **Analyze**: Model the trade-off curve and identify safe operating thresholds

### Command to Run the Complete Pipeline

To generate 500 workflows, execute them with compressed context across multiple
depth levels, and perform the full trade-off analysis:

```bash
python code/main.py --generate 500 --analyze
```

This single command will:
- Generate 500 deterministic synthetic workflows with varying depths (1-20) [UNRESOLVED-CLAIM: c_476da6c0 — status=not_enough_info]
- Execute each workflow with the Full Context engine (ground truth)
- Execute each workflow with Compressed Context engines at multiple depth levels
- Perform logistic regression analysis on the results
- Apply Bonferroni correction for multiple comparisons
- Calculate the safe operating threshold with bootstrapped confidence intervals
- Generate all output artifacts

### Expected Output Files

After successful execution, the following files will be created:

**Raw Data** (`data/raw/`):
- `workflow_{id}.json`: Generated workflow definitions

**Processed Data** (`data/processed/`):
- `log_{workflow_id}_{depth}.json`: Execution logs for each workflow at each compression depth
- `corrected_pvalues.json`: Bonferroni-corrected p-values for regression covariates

**Results** (`data/results/`):
- `threshold_ci.json`: Safe operating threshold with 95% confidence interval
- `tradeoff_curve.csv`: Raw regression data for the paper (reduction_pct, error_rate, depth, ci_lower, ci_upper)
- `benchmark.log`: Wall-clock timing information (if benchmark task is run)

**State Registry** (`state/projects/`):
- `PROJ-866-llmxive-follow-up-extending-foundation-p.yaml`: Updated with artifact hashes

## Step-by-Step Execution (Optional)

If you prefer to run each stage independently:

### 1. Generate Workflows Only

```bash
python code/main.py --generate 500
```

### 2. Execute with Compressed Context Only

(Requires workflows to already exist in `data/raw/`)

```bash
python code/main.py --compress
```

### 3. Analyze Trade-offs Only

(Requires processed execution logs in `data/processed/`)

```bash
python code/main.py --analyze
```

## Verifying Results

After the pipeline completes, you can verify the outputs:

```bash
# Check that all expected files exist
ls -la data/raw/
ls -la data/processed/
ls -la data/results/

# View the threshold analysis results
cat data/results/threshold_ci.json

# View the regression curve data
head -n 20 data/results/tradeoff_curve.csv
```

## Running Tests

```bash
pytest tests/ -v
```

## Configuration

- **Compression Depths**: The pipeline automatically tests depths 1-5 by default [UNRESOLVED-CLAIM: c_b7f9a7fd — status=not_enough_info].
- **Bootstrap Resamples**: {{claim:c_b6f08e48}} (Wikipedia: Bootstrapping (statistics), https://en.wikipedia.org/wiki/Bootstrapping_(statistics)).
- **Safety Threshold**: The safe operating zone is defined as ≤1% policy violation error rate [UNRESOLVED-CLAIM: c_d0a67692 — status=not_enough_info].

## Troubleshooting

- **Missing dependencies**: Run `pip install -r requirements.txt`
- **Schema validation errors**: Ensure all generated JSON files conform to schemas in `contracts/`
- **Memory issues**: For very large workflow sets, consider reducing the number of workflows or running in stages