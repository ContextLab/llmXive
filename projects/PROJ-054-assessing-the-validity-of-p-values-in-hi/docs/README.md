# Project Documentation: Assessing the Validity of p-Values

## Project Overview

This project investigates the statistical validity of p-values derived from
standard hypothesis tests (t-tests, F-tests) when applied to high-dimensional
data. Specifically, we examine how correlation structures and distributional
violations affect the uniformity of p-values under the null hypothesis.

## Directory Structure

```
PROJ-054/
├── code/ # Implementation modules
│ ├── generate_data.py # Synthetic data generation
│ ├── run_tests.py # Hypothesis test execution
│ ├── analyze_pvalues.py # KS stats, permutation tests
│ ├── plot_qq.py # QQ-plot generation
│ ├── sensitivity_analysis.py # Parameter sweeps
│ └── utils/ # Shared utilities (exceptions, regularization)
├── data/ # Generated data and results
│ ├── synthetic/ # Raw datasets and metadata
│ ├── results/ # KS stats, bootstrap CIs, sensitivity data
│ └── sweep/ # Parameter sweep configurations
├── docs/ # This documentation
├── tests/ # Unit and integration tests
└── specs/ # Feature specifications and requirements
```

## Quick Start

### Prerequisites

- Python 3.11+
- Dependencies listed in `requirements.txt` (numpy, scipy, pandas, matplotlib, seaborn, pytest)

### Running the Pipeline

1. **Generate Data**:
 ```bash
 python code/generate_data.py --n 100 --p 500 --rho 0.3 --seed 42
 ```

2. **Run Hypothesis Tests**:
 ```bash
 python code/run_tests.py --seed 42
 ```

3. **Analyze Results**:
 ```bash
 python code/analyze_pvalues.py --seed 42
 ```

4. **Generate Visuals**:
 ```bash
 python code/plot_qq.py --seed 42
 ```

5. **Run Full Sensitivity Sweep**:
 ```bash
 python code/sensitivity_analysis.py
 ```

## Key Concepts

- **High-Dimensional Instability**: When $p \approx n$ or $p > n$, covariance
 matrices become singular, leading to unstable test statistics.
- **Anti-Conservative Bias**: The tendency of standard tests to produce
 spuriously small p-values (false positives) under these conditions.
- **Permutation Test**: A non-parametric method used as a "Gold Standard"
 to validate p-value distributions without relying on asymptotic assumptions.

## Documentation Links

- [Methodology Overview](methodology.md)
- [Data Generation Specification](data_generation.md)
- [Analysis Methodology](analysis_methodology.md)

## Contributing

Please refer to the `tasks.md` file for the current implementation roadmap
and progress.
