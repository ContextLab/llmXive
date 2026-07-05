# Quickstart: Assessing the Validity of Modified Newtonian Dynamics with Galaxy Rotation Curves

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to GitHub Actions (for CI) or local machine with 2 CPU cores, ~7 GB RAM

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo/projects/PROJ-076-assessing-the-validity-of-modified-newto
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Download Data

```bash
python code/download.py
```

- Downloads SPARC data from the canonical SPARC archive (https://astroweb.cwru.edu/SPARC/)
- Saves to `data/raw/sparc/`
- Records checksums in `data/metadata.yaml`

### Step 2: Preprocess Data

```bash
python code/preprocess.py
```

- Filters galaxies: inclination uncertainty <10°, ≥15 radial points
- Saves filtered data to `data/processed/filtered_galaxies.csv`

### Step 3: Fit Models

```bash
python code/fit.py
```

- Fits MOND (with fitted M/L) and NFW (with cosmological prior) models to each galaxy
- Computes reduced χ², AIC, BIC, and KS test statistics
- Saves results to `results/fit_summary.csv`

### Step 4: Residual Analysis

```bash
python code/residuals.py
```

- Computes standardized residual distributions
- Runs parametric bootstrap (generating synthetic data under the null)
- Computes Kolmogorov-Smirnov (KS) distance and p-values
- Applies Holm-Bonferroni correction
- Saves results to `results/residual_stats.csv`

### Step 5: Sensitivity Analysis

```bash
python code/sensitivity.py
```

- Sweeps χ² thresholds: {1.0, 1.25, 1.5, 1.75}
- Reports pass rates for both models
- Saves results to `results/sensitivity_report.csv`

## Testing

### Run Unit Tests

```bash
pytest tests/unit/
```

### Run Contract Tests

```bash
pytest tests/contract/
```

### Run Integration Tests

```bash
pytest tests/integration/
```

## Expected Outputs

- `data/processed/filtered_galaxies.csv`: Filtered galaxy data
- `results/fit_summary.csv`: Model fit results (parameters, metrics, KS statistics)
- `results/residual_stats.csv`: Residual statistics and bootstrap p-values
- `results/sensitivity_report.csv`: Threshold sweep results
- `data/metadata.yaml`: Checksums and version info

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Download fails | Check internet connection; verify SPARC URL; retry manually |
| Convergence errors | Check parameter bounds; reduce max iterations; log warnings |
| Runtime >6 hours | Reduce bootstrap iterations to 5,000; parallelize galaxy fits |
| Memory error | Process galaxies in batches; reduce data chunk size |

## Next Steps

- Review `research.md` for methodological details
- Examine `plan.md` for implementation roadmap
- Run `pytest` to validate all contracts
- Generate figures and paper from `results/` outputs