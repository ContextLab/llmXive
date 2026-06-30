# Quantifying the Impact of Data Cleaning on Statistical Inference

## Project Overview

This project implements an automated research pipeline to quantify how common data cleaning strategies (outlier removal, imputation, categorical recoding) impact statistical inference results. The pipeline downloads public datasets, establishes baseline statistical metrics, applies cleaning strategies systematically, and compares the resulting p-values, confidence intervals, and effect sizes.

## Research Goal

To determine whether and how data cleaning procedures alter the conclusions of statistical tests, potentially introducing bias or false positives/negatives in scientific analysis.

## Pipeline Architecture

The pipeline consists of four main phases:

1. **Dataset Acquisition**: Downloads public datasets from UCI Machine Learning Repository
2. **Baseline Analysis**: Computes initial statistical metrics (p-values, 95% CI, effect sizes) on raw data
3. **Cleaning Strategy Application**: Applies three cleaning strategies:
 - IQR-based outlier removal (k=1.5)
 - Mean/Median/KNN imputation for missing values
 - Categorical recoding for factor encoding
4. **Metrics Comparison & Sensitivity Analysis**: Computes differences between baseline and cleaned results, performs sensitivity analysis across dataset sizes and missingness rates, and generates visualizations.

## Directory Structure

```
PROJ-256-quantifying-the-impact-of-data-cleaning-/
├── code/
│ ├── analysis.py # Statistical analysis functions (t-tests, linear regression)
│ ├── cleaning.py # Data cleaning strategies (outlier removal, imputation)
│ ├── config.py # Environment configuration management
│ ├── data_loader.py # Dataset download and validation logic
│ ├── models.py # Pydantic data models (Dataset, CleaningStrategy, AnalysisResult)
│ ├── reporting.py # Metrics comparison and report generation
│ ├── utils.py # Utility functions (random seeding, checksums, logging)
│ ├── t013_record_baseline_metrics.py
│ ├── t022_save_cleaned_datasets.py
│ ├── t023_reanalyze_cleaned_variants.py
│ ├── t030_dataset_size_sensitivity.py
│ ├── t031_bootstrap_variance.py
│ ├── t032_permutation_null_fpr.py
│ ├── t033_outlier_threshold_sweep.py
│ ├── t034_generate_forest_plot.py
│ ├── t035_generate_ci_heatmap.py
│ ├── t036_pvalue_shift_reporting.py
│ ├── t037_ci_width_reporting.py
│ ├── t038_effect_size_reporting.py
│ ├── t039_log_excluded_datasets.py
│ ├── t040_create_comparison_report.py
│ └── t041_generate_final_report.py
├── data/
│ ├── raw/ # Downloaded raw datasets
│ └── processed/ # Cleaned datasets and analysis results
├── tests/
│ ├── unit/ # Unit tests for individual functions
│ └── integration/ # Integration tests for pipeline components
├── docs/
│ └── README.md # This file
├── requirements.txt # Python dependencies
└── tasks.md # Task tracking and implementation status
```

## Quick Start

### Prerequisites

- Python 3.11+
- pip package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-256-quantifying-the-impact-of-data-cleaning-

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root with the following variables:

```env
DATASET_URLS="..."
OUTPUT_PATH="./data/processed"
RANDOM_SEED=42
BOOTSTRAP_ITERATIONS=1000
LOG_LEVEL=INFO
```

### Running the Pipeline

Execute the pipeline steps in order:

```bash
# 1. Download datasets and run baseline analysis
python code/t013_record_baseline_metrics.py

# 2. Apply cleaning strategies and save cleaned datasets
python code/t022_save_cleaned_datasets.py

# 3. Re-analyze cleaned variants
python code/t023_reanalyze_cleaned_variants.py

# 4. Run sensitivity analyses and generate reports
python code/t030_dataset_size_sensitivity.py
python code/t031_bootstrap_variance.py
python code/t032_permutation_null_fpr.py
python code/t033_outlier_threshold_sweep.py

# 5. Generate visualizations
python code/t034_generate_forest_plot.py
python code/t035_generate_ci_heatmap.py

# 6. Generate per-metric reports
python code/t036_pvalue_shift_reporting.py
python code/t037_ci_width_reporting.py
python code/t038_effect_size_reporting.py
python code/t039_log_excluded_datasets.py

# 7. Create final comparison report
python code/t040_create_comparison_report.py
python code/t041_generate_final_report.py
```

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests
pytest -v
```

## Output Artifacts

The pipeline produces the following artifacts in `data/processed/`:

- `baseline_metrics.json`: Baseline statistical metrics for raw datasets
- `cleaned_metrics.json`: Statistical metrics after applying cleaning strategies
- `null_fpr_metrics.json`: False positive rate estimates from permutation tests
- `comparison_report.json`: Aggregated comparison between baseline and cleaned results
- `forest_plot.png`: Visualization of p-value shifts across datasets
- `ci_heatmap.png`: Heatmap of confidence interval width changes

## Key Metrics

- **P-value Shift**: Absolute and relative difference in p-values between baseline and cleaned data
- **CI Width Change**: Change in confidence interval width after cleaning
- **Effect Size Delta**: Change in Cohen's d or R² values
- **Inconsistency Rate**: Proportion of datasets where significance status changes (p < 0.05)
- **False Positive Rate (FPR)**: Proportion of tests with p ≤ 0.05 in null datasets

## Statistical Methods

- **T-tests**: Independent two-sample t-tests using `scipy.stats.ttest_ind`
- **Linear Regression**: OLS regression using `statsmodels`
- **Effect Sizes**: Cohen's d for t-tests, R² for regression
- **Bootstrap**: Resampling with replacement for variance estimation (default: 1000 iterations)
- **Permutation Tests**: Shuffled outcome variables for FPR estimation
- **Multiple Testing Correction**: Bonferroni correction for Family-Wise Error Rate control

## Cleaning Strategies

1. **IQR Outlier Removal**: Removes rows where |z-score| > k (default k=1.5)
2. **Mean Imputation**: Replaces missing values with column mean
3. **Median Imputation**: Replaces missing values with column median
4. **KNN Imputation**: Uses k-nearest neighbors (default k=5) for imputation
5. **Categorical Recoding**: Converts categorical variables to numeric factors

## Limitations and Notes

- **Dataset Availability**: Currently limited to 2 verified datasets (UCI HAR, UCI Shopper) due to public data availability constraints. [UNRESOLVED-CLAIM: c_1dc77be1 — status=not_enough_info]
- **Bootstrap Iterations**: Fallback to 500 iterations if dataset size exceeds 5000 rows for computational tractability. [UNRESOLVED-CLAIM: c_ac305073 — status=not_enough_info]
- **Statistical Limitations**: Median/IQR calculations on small sample sizes (n=2) are flagged as unstable. [UNRESOLVED-CLAIM: c_05208814 — status=not_enough_info]
- **FWER vs FDR**: Bonferroni correction (FWER) implemented as per requirements, though Benjamini-Hochberg (FDR) may be more appropriate for some use cases.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes following the existing code style (black, ruff)
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Acknowledgments

- UCI Machine Learning Repository for public datasets
- SciPy, StatsModels, and Scikit-learn communities for statistical tools
- Research team for project design and specification