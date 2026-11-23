# Quickstart Guide: Statistical Analysis of Publicly Available Recipe Data

This guide provides instructions for setting up the environment, downloading the data, and executing the statistical analysis pipeline for ingredient substitution prediction.

## Environment Setup

1. **Clone the repository** and navigate to the project root:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-175-statistical-analysis-of-publicly-availab
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: Ensure you have Python 3.11 or higher installed.*

4. **Verify installation**:
 ```bash
 python -c "import pandas, numpy, sklearn, pymc, statsmodels; print('All dependencies installed successfully.')"
 ```

## Data Pipeline

The data pipeline handles the acquisition, verification, and preprocessing of Recipe1M, FlavorDB, and Counterfactual datasets.

### Streaming Instructions

Due to the size of the Recipe1M dataset, the pipeline uses streaming to stay within memory constraints (target: < 6 GB RAM).

1. **Run the verification step** to ensure data sources are accessible:
 ```bash
 python code/data/verify.py
 ```
 This will generate `data/verification_report.json`. If the status is "FAILED", check `data/download_errors.log` for details.

2. **Execute the download script** (streaming enabled):
 ```bash
 python code/data/download.py
 ```
 This script streams the Recipe1M dataset and downloads FlavorDB and Counterfactual data. Output files will be saved to `data/raw/`.

3. **Preprocess the data**:
 ```bash
 python code/data/preprocess.py
 ```
 This step normalizes ingredients, constructs the co-occurrence matrix, calculates flavor similarity, and derives functional roles. Output will be saved to `data/processed/`.

4. **Split the data**:
 ```bash
 python code/data/split.py
 ```
 This creates train/test splits based on the sample sizes determined by the power analysis (T008a, T008b). Output will be saved to `data/final/`.

## Model Execution

The model execution phase fits logistic regression and hierarchical Bayesian models.

### Runtime Estimation Methodology

Runtime estimates are calculated using the following formula:
```
Estimated Runtime = (Time per 10,000 rows) * (N / 10,000)
```
Where `N` is the sample size determined by the power analysis (N_logistic or N_bayesian).

**Placeholders for Runtime Estimates**:
- **Logistic Regression**: `[INSERT_ESTIMATED_TIME_HOURS]` hours (based on N_logistic)
- **Bayesian Model**: `[INSERT_ESTIMATED_TIME_HOURS]` hours (based on N_bayesian)
- **Total Pipeline**: `[INSERT_TOTAL_ESTIMATED_TIME_HOURS]` hours

*Note: Actual runtime may vary based on hardware specifications and data characteristics.*

### Execution Steps

1. **Power Analysis** (if not already run):
 ```bash
 python code/models/diagnostics.py
 ```
 This generates `data/power_analysis_logistic.json` and `data/power_analysis_bayesian.json`.

2. **Fit Logistic Regression Model**:
 ```bash
 python code/models/fit_logistic.py
 ```
 This fits the null and full models and saves results to `data/models/`.

3. **Fit Bayesian Model**:
 ```bash
 python code/models/fit_bayesian.py
 ```
 This fits the hierarchical Bayesian model with CPU-only NUTS sampling. Results are saved to `data/models/`.

4. **Run Diagnostics**:
 ```bash
 python code/models/diagnostics.py
 ```
 This calculates VIF, performs Likelihood-Ratio Tests, and runs post-hoc power validation. Outputs are saved to `data/diagnostics/`.

## Evaluation and Reporting

1. **Calculate Metrics**:
 ```bash
 python code/evaluation/metrics.py
 ```
 This calculates AUC, Precision, Recall, and generates calibration plots. Outputs are saved to `data/evaluation/`.

2. **Generate Final Report**:
 ```bash
 python code/evaluation/report.py
 ```
 This performs statistical comparisons (DeLong's test), maps results to success criteria, and generates the final summary report. The report is saved to `data/reports/final_report.md`.

## Troubleshooting

- **Memory Errors**: If you encounter memory errors, ensure streaming is enabled in `code/data/download.py` and `code/data/preprocess.py`. Check `data/memory_profile.json` for peak RAM usage.
- **Data Source Errors**: If data sources are unreachable, check `data/download_errors.log` and verify your internet connection.
- **Convergence Issues**: If the Bayesian model fails to converge, check the R-hat and ESS values in `data/diagnostics/bayesian_convergence.json`. You may need to increase the number of samples or adjust the model priors.

## Contact

For issues or questions, please refer to the project documentation or contact the maintainers.