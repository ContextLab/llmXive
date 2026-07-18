# Quickstart: Embodied Curriculum Learning Analysis

## Prerequisites

- Python 3.11+
- `pip` package manager

## Setup

1. **Clone the repository** and navigate to the project root.
2. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
3. **Verify installation**:
 ```bash
 python code/src/cli.py --help
 ```

## Quick Start Guide

### Step 1: Prepare Data

Place your input data in `data/raw/`. The file should be a CSV or JSON with columns:
- `pre_test_score`
- `post_test_score`
- `instruction_type`

Example `data/raw/sample.csv`:
```csv
pre_test_score,post_test_score,instruction_type
50,65,embodied
48,55,static
52,70,embodied
49,58,static
```

### Step 2: Run Analysis

**Option A: Analyze Real Data**
```bash
python code/src/cli.py --mode=secondary_analysis --input=data/raw/sample.csv
```
Output: `data/processed/results.json`

**Option B: Generate Synthetic Data**
```bash
python code/src/cli.py --mode=synthetic --sample-size=500 --seed=42
```
Output: `data/synthetic/dataset.csv` and `data/synthetic/mapping_log.json`

**Option C: Run Sensitivity Sweep**
```bash
python code/src/cli.py --mode=secondary_analysis --input=data/raw/sample.csv --sweep_thresholds=0.05,0.01
```

### Step 3: Review Results

Check `data/processed/results.json` for:
- T-statistic and p-value
- Cohen's d (effect size)
- Confidence intervals
- Power analysis
- Associational framing notes

## Key Concepts

- **Gain Score**: `post_test_score - pre_test_score`
- **Associational Framing**: All results are correlations, not causal claims.
- **Sensitivity Sweep**: Tests robustness across different significance thresholds.
- **Automatic Fallback**: Missing `instruction_type` triggers synthetic data generation.

## Troubleshooting

- **Missing Columns**: If `pre_test_score` or `post_test_score` are missing, the system logs skipped records and excludes them.
- **Small Sample Size**: If N < 30, sensitivity analysis is skipped with a warning.
- **Collinearity**: If |r| > 0.8 between predictors, a diagnostic is reported.

## Next Steps

- Explore `docs/README.md` for detailed methodological explanations.
- Run `pytest` in the `code/` directory to verify the installation.
- Customize `synthetic_gen.py` parameters for specific validation scenarios.
