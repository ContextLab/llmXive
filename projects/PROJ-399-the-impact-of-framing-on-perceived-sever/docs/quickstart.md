# Quickstart Guide: Simulation-Based Sensitivity Analysis of Framing Effects

This guide provides instructions for running the analysis pipeline for project **PROJ-399**.
The project uses **R 4.3+** for statistical analysis and **Python** for utility scripts and data orchestration.

## Prerequisites

- **R 4.3.0 or higher** installed.
- **Python 3.9+** installed (for utility scripts).
- **renv** package (will be initialized automatically).
- **Git** for version control.

## 1. Project Setup

Ensure the project structure is initialized. If you are starting from scratch, run the setup script:

```bash
python code/setup_project_structure.py
```

This will create the required directories:
- `projects/PROJ-399-the-impact-of-framing-on-perceived-sever/data/raw/`
- `projects/PROJ-399-the-impact-of-framing-on-perceived-sever/data/processed/`
- `projects/PROJ-399-the-impact-of-framing-on-perceived-sever/results/plots/`
- `code/`
- `tests/`
- `.github/workflows/`

### Initialize R Environment

Navigate to the `code/` directory and initialize `renv`:

```bash
cd code
R
```

Inside R:
```r
if (!require("renv")) install.packages("renv")
renv::init()
renv::restore()
```

This will install the pinned dependencies defined in `code/renv.lock` (e.g., `lme4`, `pwr`, `dplyr`, `ggplot2`).

## 2. Configuration

Ensure `code/config.yaml` exists and contains the random seed and file paths:

```yaml
seed: 42
paths:
 raw_data: "../data/raw"
 processed_data: "../data/processed"
 results: "../results"
```

## 3. Running the Analysis Pipeline

The pipeline consists of three main R scripts. Execute them in the following order from the `code/` directory.

### Step 1: Data Preparation (`01_data_prep.R`)

This script fetches the MPSD-v2 stimulus data from the OSF repository, validates the columns, and generates the synthetic dataset (N=300) with sensitivity analysis loops.

**Command:**
```bash
Rscript 01_data_prep.R
```

**Outputs:**
- `../data/processed/synthetic_data.csv`: The generated dataset.
- `../data/processed/sensitivity_datasets/`: Directory containing datasets for various delta values.
- `../results/processed/sensitivity_curve_data.csv`: Aggregated sensitivity results.

*Note: This script requires internet access to fetch the OSF data.*

### Step 2: Power Analysis (`02_power_analysis.R`)

This script performs an *a priori* power analysis to verify that the sample size (N=300) is sufficient to detect a small-to-medium effect size (d=0.3) with ≥80% power.

**Command:**
```bash
Rscript 02_power_analysis.R
```

**Outputs:**
- `../results/intermediate/us3_results.json`: Verification results.
- If power < 0.80, the script will halt with a critical warning.

### Step 3: Statistical Analysis (`03_analysis.R`)

This script fits the mixed-effects linear model for severity ratings (US1) and the logistic regression model for sharing intentions (US2).

**Command:**
```bash
Rscript 03_analysis.R
```

**Outputs:**
- `../results/intermediate/us1_results.json`: Mixed-effects model results (coefficient, p-value, effect size).
- `../results/intermediate/us2_results.json`: Logistic regression results (odds ratios).

## 4. Export and Reporting (`04_export.R`)

This script aggregates all intermediate results and generates visualizations.

**Command:**
```bash
Rscript 04_export.R
```

**Outputs:**
- `../results/plots/`: Various plots including `us1_severity_barplot.png` and `sensitivity_analysis.png`.
- `../results.md`: The final aggregated report in the project root.

## 5. Verification

To ensure the pipeline runs correctly on a fresh environment, run the CI workflow locally or on GitHub Actions:

```bash
.github/workflows/analyze.yml
```

Or execute the test suite:

```bash
Rscript -e "devtools::test()"
```

## Troubleshooting

- **Missing Dependencies**: If `renv::restore()` fails, ensure your R version matches the lockfile requirements (R 4.3+).
- **OSF Fetch Errors**: Ensure your network allows access to `osf.io`. The script will fail loudly if the data cannot be retrieved.
- **Power Analysis Failure**: If `us3_results.json` indicates power < 0.80, review the sample size assumptions in `02_power_analysis.R`.