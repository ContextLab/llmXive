# Quick Start Guide: Statistical Test Sensitivity Analysis

This guide provides step-by-step instructions to set up the environment, generate data, run the simulation pipeline, visualize results, and interpret the findings for the **llmXive Statistical Sensitivity Analysis** project.

## Environment Setup

### Prerequisites
- Python 3.11 or higher
- pip (Python package installer)
- A POSIX-compliant shell (bash, zsh, etc.) or Windows PowerShell

### 1. Clone and Navigate
Ensure you are in the project root directory.

```bash
cd /path/to/proj-482-assessing-the-sensitivity-of-common-stat
```

### 2. Create Virtual Environment
It is recommended to use a virtual environment to isolate dependencies.

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
Install all required packages listed in `requirements.txt`.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation
Ensure all critical modules are importable.

```bash
python -c "import numpy, pandas, scipy, matplotlib, seaborn; print('Dependencies OK')"
```

## Data Generation

The pipeline generates synthetic datasets with known ground truth (Null and Alternative hypotheses) across various distributions (Normal, Uniform, Log-Normal) and sample sizes.

### Generate Validation Dataset
Before running the full simulation, generate a small validation dataset to ensure the data generator is working correctly.

```bash
python code/run_data_gen.py
```

**Output**:
- `data/raw/sample_validation.csv`: Contains metadata and statistical checks for the generated data.

## Simulation Execution

The core simulation runs Monte Carlo experiments to assess the sensitivity of t-tests, ANOVA, and Chi-squared tests to dataset size and distribution shape.

### Run the Full Pipeline
Execute the complete workflow (Data Gen -> Simulation -> Analysis -> Export) using the main entry point.

```bash
python code/main.py
```

**Orchestration Steps**:
1. **Setup**: Ensures `data/raw`, `data/processed`, and `figures` directories exist.
2. **Data Gen**: Generates synthetic datasets (US1).
3. **Simulation**: Runs adaptive Monte Carlo replicates (US2).
 - Uses Clopper-Pearson intervals for internal convergence.
 - Stores raw p-values in `data/processed/raw_pvalues.csv`.
 - Counts Type I and Type II errors.
4. **Analysis**: Aggregates results and computes Bootstrap CIs (US3).
5. **Export**: Saves final CSVs and plots.

**Output Files**:
- `data/processed/error_counts.csv`: Aggregated error counts per scenario.
- `data/processed/raw_pvalues.csv`: Raw p-values for every replicate.
- `data/processed/stability_trend.csv`: Stability analysis results.
- `data/processed/error_rates.csv`: Final aggregated error rates with CIs.
- `figures/`: Generated plots (PNG/SVG).

### Run Specific Stages
You can also run individual stages if you wish to debug or inspect intermediate results.

**Run Simulation Only**:
```bash
python code/run_simulation.py
```

**Run Analysis Only** (requires simulation results to exist):
```bash
python code/run_analyzer.py
```

## Visualization

The pipeline automatically generates publication-ready plots during the export phase.

### View Generated Plots
After running `python code/main.py`, inspect the `figures/` directory (or `data/processed/plots/` depending on configuration).

Key plots include:
- **Error Rate vs. Sample Size**: Shows how Type I error rates converge to alpha (0.05) as sample size increases.
- **Test Comparison**: Compares the sensitivity of t-test, ANOVA, and Chi-squared tests across distributions.
- **Stability Trend**: Visualizes the deviation of error rates from the nominal threshold.

### Manual Plot Generation
If you need to regenerate plots without re-running the full analysis:

```bash
python code/visualizer.py
```

## Interpretation

### Understanding the Results

1. **Type I Error Rate (False Positive Rate)**:
 - Ideally, this should equal the significance level $\alpha$ (0.05).
 - Deviations indicate the test is either too conservative (rate < 0.05) or too liberal (rate > 0.05) for that specific sample size/distribution.
 - **Convergence**: As sample size ($n$) increases, the observed rate should converge to 0.05 for valid tests.

2. **Power (1 - Type II Error)**:
 - Measures the test's ability to detect a true effect.
 - Higher power is better. Look for how power increases with sample size.

3. **Distribution Sensitivity**:
 - **Normal**: Tests should perform as expected (robust).
 - **Log-Normal**: High skewness may cause deviations in small samples, especially for tests assuming normality (e.g., t-test).
 - **Uniform**: Tests may show different convergence rates compared to normal distributions.

4. **Adaptive Replication**:
 - The simulation runs until the 95% Confidence Interval (CI) width for the error rate is $\le$ 0.01.
 - This ensures high precision in the estimated error rates.

### Key Metrics to Report
- **Beta Coefficients**: From the regression analysis (T027), indicating the impact of sample size and distribution on error rates.
- **CI Widths**: Narrower CIs indicate more precise estimates.
- **Convergence Point**: The sample size at which the error rate stabilizes within the CI bounds.

## Troubleshooting

- **Missing `data/raw/`**: Ensure `code/setup_directories.py` runs successfully or manually create the directory.
- **Import Errors**: Verify that `requirements.txt` was installed in the active virtual environment.
- **Simulation Timeout**: If the adaptive loop takes too long, check `code/config.py` for the maximum replicate cap or reduce the sample size range for testing.
- **Memory Issues**: The pipeline streams data where possible, but large sample sizes may require more RAM.

## Next Steps

- Review the generated `data/processed/error_rates.csv` for detailed numerical results.
- Examine the plots in `figures/` for visual trends.
- Consult `README.md` for a full project overview and contribution guidelines.