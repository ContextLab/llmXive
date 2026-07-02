# Quickstart: Assessing the Validity of Frequentist Confidence Intervals with Small Sample Sizes

## Overview

This guide provides step-by-step instructions to set up and run the Monte Carlo simulation for assessing confidence interval coverage in small samples. The simulation evaluates t-intervals and bootstrap percentile intervals across multiple parametric distributions, sample sizes, and confidence levels.

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Git (for cloning the repository)
- Sufficient RAM and disk space (GitHub Actions free-tier compatible)
- Internet access (to download dependencies)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd projects/PROJ-263-assessing-the-validity-of-frequentist-co
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 `requirements.txt` should include:
 ```
 pandas>=2.0.0
 numpy>=1.24.0
 scipy>=1.11.0
 scikit-learn>=1.3.0
 pyyaml>=6.0
 pytest>=7.4.0
 ```

4. **Verify installation**:
 ```bash
 python -c "import pandas, numpy, scipy, sklearn; print('All dependencies installed successfully')"
 ```

## Running the Simulation

### Step 1: Generate Synthetic Distributions

Run the data generation script to create synthetic datasets from parametric distributions:
```bash
python code/generate_data.py
```
This script generates synthetic data from distributions (LogNormal, Beta, t-distribution, Gamma) with known theoretical parameters, checksums them, and stores them in `data/raw/`.

### Step 2: Run Monte Carlo Simulation

Execute the main simulation script:
```bash
python code/main.py
```
This script:
- Loads synthetic distributions
- Performs a sufficient number of Monte Carlo replications per configuration (distribution × sample size × confidence level) to ensure stable estimation of coverage properties.
- Computes t-intervals and bootstrap percentile intervals (with a sufficient number of inner resamples)
- Calculates coverage rates against the theoretical mean
- Applies Bonferroni correction for multiple comparisons
- Generates aggregate and sensitivity reports

**Expected runtime**: ≤ 6 hours on 2-core CPU.

### Step 3: Review Results

Outputs are stored in `outputs/`:
- `coverage_results.json`: Aggregate coverage rates per configuration
- `sensitivity_results.json`: Sensitivity analysis across sample sizes and confidence levels
- `report.md`: Human-readable summary of findings

View results:
```bash
cat outputs/report.md
```

## Configuration Options

Edit `code/config.yaml` to customize:
```yaml
simulation:
 sample_sizes: [10, 20, 30]
 confidence_levels: [0.90, 0.95, 0.99]
 replications: 10000
 bootstrap_resamples: 2000 # Inner resamples for bootstrap interval
 random_seed: 42
 significance_threshold: 0.01 # 1.0% deviation threshold

distributions:
 # List of distributions to include (auto-detected from data/raw/)
 exclude_patterns: [] # Patterns to exclude distributions
```

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

Run contract tests (validate output schemas):
```bash
pytest tests/contract/ -v
```

## Troubleshooting

### Issue: Runtime exceeds 6 hours
**Solution**: Reduce the number of distributions or replications in `config.yaml`, or reduce `bootstrap_resamples` to 1,000.

### Issue: Memory exceeds 7 GB
**Solution**: Process distributions sequentially (already implemented); reduce distribution count if necessary.

### Issue: Coverage rates are 0% or 100%
**Solution**: Verify that the theoretical population mean is correctly computed from the parametric distribution parameters.

## Reproducibility

To reproduce results:
1. Ensure the same `random_seed` is used (default: 42).
2. Re-run `generate_data.py` to fetch the same synthetic distributions.
3. Re-run `main.py` with the same configuration.
4. Compare outputs using checksums (recorded in `state/`).

## Next Steps

- Review `outputs/report.md` for findings.
- Extend analysis with additional distributions or sample sizes.
- Contribute to the paper section in `paper/`.