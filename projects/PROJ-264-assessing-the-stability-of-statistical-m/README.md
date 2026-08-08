# Assessing the Stability of Statistical Model Performance Across Data Subsets

This project implements a rigorous automated pipeline to evaluate the stability of statistical model performance (Logistic Regression, Random Forest, Linear SVM) across multiple datasets. It utilizes repeated stratified k-fold cross-validation, quantifies variance, computes correlations with dataset properties, and performs statistical significance testing using permutation tests with Benjamini-Hochberg correction.

## Prerequisites

- Python 3.9+
- `pip` for package management

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-264-assessing-the-stability-of-statistical-m
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. (Optional) Set up linting and formatting:
 ```bash
 ruff check.
 black.
 ```

## Usage

### 1. Data Preparation

Download and validate the 15 binary classification datasets defined in `code/config.py`.

```bash
python code/data_loader.py
```

This script:
- Fetches datasets from OpenML (or UCI if necessary).
- Validates sample sizes (skips datasets with < 100 or > 100,000 samples).
- Computes SHA-256 checksums and caches data in `data/raw/`.
- Generates a spectrum report in `data/spectrum_report.json`.

### 2. Evaluation (Repeated Cross-Validation)

Run the evaluation loop for Logistic Regression, Random Forest, and Linear SVM.

```bash
python code/evaluator.py
```

This script:
- Loads validated datasets.
- Skips datasets with < 200 samples (to ensure 10-fold stability).
- Executes 10 repeats of 10-fold stratified cross-validation.
- Calculates Accuracy and F1 scores.
- Writes raw results to `results/raw_evaluations.csv`.

### 3. Analysis

Compute stability metrics, correlations, and statistical significance.

```bash
python code/analyser.py
```

This script:
- Aggregates raw metrics to compute Mean, Std, and Coefficient of Variation (CV).
- Computes Log-Variance metrics.
- Calculates Pearson and Spearman correlations between stability metrics and dataset properties (log(N_samples), log(N_features)).
- Performs permutation tests to compare variance distributions across models.
- Applies Benjamini-Hochberg correction for multiple comparisons.
- Writes results to:
 - `results/stability_metrics.csv`
 - `results/correlation_results.csv`
 - `results/permutation_results.csv`
 - `results/regression_residuals.csv`

### 4. Report Generation

Generate the final summary report.

```bash
python code/scripts/generate_final_report.py
```

This script aggregates all analysis results and renders the final report to `results/final_report.md`.

## Project Structure

```
.
├── code/
│ ├── __init__.py
│ ├── main.py # Entry point for orchestration
│ ├── config.py # Configuration and dataset IDs
│ ├── utils.py # Logging, seeding, error handling
│ ├── data_loader.py # Dataset fetching and validation
│ ├── preprocessor.py # Leakage-safe preprocessing
│ ├── evaluator.py # Repeated CV execution
│ ├── analyser.py # Statistical analysis and testing
│ ├── report_generator.py # Report aggregation logic
│ ├── results_writer.py # File I/O for results
│ └── scripts/
│ ├── pii_scan.py # PII scanning utility
│ └── generate_final_report.py # Report generation entry point
├── data/
│ ├── raw/ # Cached datasets
│ ├── processed/ # Preprocessed data (if applicable)
│ └── spectrum_report.json # Dataset spectrum verification
├── results/
│ ├── raw_evaluations.csv
│ ├── stability_metrics.csv
│ ├── correlation_results.csv
│ ├── permutation_results.csv
│ ├── regression_residuals.csv
│ └── final_report.md
├── tests/
│ ├── __init__.py
│ ├── unit/ # Unit tests
│ ├── integration/ # Integration tests
│ └── contract/ # Schema contract tests
├── docs/
│ └── report_template.md # Markdown template for reports
├── requirements.txt
├── README.md
├── pyproject.toml # Black configuration
└──.ruff.toml # Ruff configuration
```

## Configuration

Edit `code/config.py` to modify:
- List of OpenML/UCI dataset IDs.
- Number of CV repeats and splits.
- Paths for data and results directories.

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Specific test groups:
- **Unit Tests**: `pytest tests/unit/ -v`
- **Integration Tests**: `pytest tests/integration/ -v`
- **Contract Tests**: `pytest tests/contract/ -v`

## License

This project is part of the llmXive automated science pipeline.