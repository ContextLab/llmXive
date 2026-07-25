# Quick Start Guide

## Prerequisites

- Python 3.11+
- Required packages (install via `pip install -r requirements.txt`):
 - numpy
 - scipy
 - pandas
 - matplotlib
 - seaborn
 - pytest

## Project Structure

```
PROJ-054/
├── code/
│ ├── utils/
│ │ ├── exceptions.py
│ │ ├── regularization.py
│ │ └── simulation.py
│ ├── generate_data.py
│ ├── run_tests.py
│ ├── collect_pvalues.py
│ ├── analyze_pvalues.py
│ ├── bootstrap_ci.py
│ ├── plot_qq.py
│ ├── sensitivity_analysis.py
│ └── integrate_pipeline.py
├── data/
│ ├── synthetic/
│ │ ├── {seed}.json
│ │ └── trajectories/
│ │ └── {seed}.json
│ └── results/
│ └── bootstrap_cis.json
├── tests/
│ ├── unit/
│ └── integration/
├── docs/
│ ├── methodology_data_generation.md
│ ├── methodology_analysis.md
│ └── quickstart.md
└── requirements.txt
```

## Running the Pipeline

### Step 1: Generate Synthetic Data

Generate datasets with controlled correlation and distributional violations:

```bash
python code/generate_data.py --n 100 --p 200 --rho 0.5 --distribution t --seed 42
```

This will:
- Create a dataset with $n=100$ samples, $p=200$ dimensions
- Apply correlation threshold $\rho=0.5$
- Use a t-distribution (heavy-tailed violation)
- Store metadata in `data/synthetic/42.json`

### Step 2: Run Hypothesis Tests

Execute t-tests and F-tests on the generated data:

```bash
python code/run_tests.py --data-path data/synthetic/42.json
```

This will:
- Perform hypothesis tests on each dimension
- Collect p-values ensuring exactly $p$ values per iteration
- Store results for downstream analysis

### Step 3: Collect P-Values

Aggregate p-values across iterations:

```bash
python code/collect_pvalues.py --trajectory-path data/synthetic/trajectories/42.json
```

### Step 4: Analyze P-Value Distributions

Perform comprehensive analysis:

```bash
python code/analyze_pvalues.py --trajectory-path data/synthetic/trajectories/42.json
```

This will:
- Generate permutation-based Gold Standard reference
- Calculate KS statistics comparing standard tests to reference
- Output analysis results

### Step 5: Generate QQ-Plots

Create visual diagnostics:

```bash
python code/plot_qq.py --trajectory-path data/synthetic/trajectories/42.json --output figures/qq_plot_42.png
```

### Step 6: Compute Bootstrap Confidence Intervals

Quantify uncertainty in KS statistics:

```bash
python code/bootstrap_ci.py --trajectory-path data/synthetic/trajectories/42.json --output data/results/bootstrap_cis.json
```

### Step 7: Run Sensitivity Analysis

Sweep across correlation levels:

```bash
python code/sensitivity_analysis.py --rho-values 0 0.1 0.3 0.5 0.7 0.9
```

### Step 8: Run Full Integration Pipeline

Execute the complete workflow:

```bash
python code/integrate_pipeline.py --config-path configs/simulation_config.json
```

This orchestrates:
- Data generation across parameter sweeps
- Hypothesis test execution
- P-value collection
- Analysis and visualization
- Results aggregation

## Running Tests

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### Full Test Suite

```bash
pytest tests/ -v --tb=short
```

## Key Outputs

- `data/synthetic/{seed}.json`: Dataset metadata and integrity hash
- `data/synthetic/trajectories/{seed}.json`: Full p-value trajectories
- `data/results/bootstrap_cis.json`: KS statistics with confidence intervals
- `figures/qq_plot_{seed}.png`: Visual diagnostics of p-value distributions

## Troubleshooting

### Memory Issues

If you encounter memory warnings (RSS > 6GB):
- Reduce the dimensionality $p$ or sample size $n$
- Process data in smaller batches
- Ensure you have sufficient swap space

### Numerical Instability

If you encounter condition number warnings:
- The regularization module will automatically apply shrinkage
- Consider reducing the correlation threshold $\rho$
- Check that $n$ is not too small relative to $p$

### Missing Dependencies

Ensure all required packages are installed:
```bash
pip install -r requirements.txt
```

## Next Steps

1. Review the methodology documentation:
 - [Data Generation Methodology](methodology_data_generation.md)
 - [Analysis Methodology](methodology_analysis.md)
2. Explore the sensitivity analysis results
3. Interpret the KS statistics and QQ-plots
4. Draw conclusions about p-value validity under different conditions

## References

- Task T001-T003: Project setup
- Task T004-T008: Foundational utilities
- Task T013-T017: Data generation
- Task T020-T022: Hypothesis testing
- Task T026-T030: Analysis pipeline
- Task T034: Documentation
