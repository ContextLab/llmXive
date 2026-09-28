# Quick Start Guide: Simulated Social Validation Analysis

This guide provides the steps to set up and run the analysis pipeline for the "Impact of Simulated Social Validation on Self-Perception in Adolescents" project.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Git (optional, for cloning the repository)

## 1. Environment Setup

### Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies

Navigate to the project root and install the required packages:

```bash
pip install -r requirements.txt
```

## 2. Project Structure Initialization

If you are starting from a clean repository, initialize the directory structure:

```bash
python code/setup_structure.py
```

This creates the necessary folders: `code/`, `data/`, `tests/`, and their subdirectories.

## 3. Running the Pipeline

The main entry point is `code/main.py`. It orchestrates the entire workflow:
1. **Data Loading**: Attempts to load real data. If it fails, it generates synthetic data using SEM.
2. **Validation**: Ensures data quality (sample size, structure, ordering).
3. **Processing**: Calculates the 'Perceived Social Validation' (PSV) metric.
4. **Analysis**: Runs regression, VIF checks, sensitivity analysis, and non-linearity tests.
5. **Visualization**: Generates diagnostic plots.
6. **Reporting**: Aggregates results and checks for causal language violations.

### Execute the Pipeline

```bash
python code/main.py
```

**Expected Output:**
- Console logs detailing each step.
- Files generated in `data/processed/`:
 - `model_results.json`: Regression coefficients, p-values, VIF scores.
 - `pipeline_run_log.json`: Execution status and timestamps.
 - `scatter_plot.png`: Scatter plot with regression line.
 - `residuals.png`: Residual diagnostic plot.

## 4. Verification & Testing

### Run Unit Tests

Verify individual components:

```bash
pytest tests/unit/ -v
```

### Run Integration Tests

Verify end-to-end flows:

```bash
pytest tests/integration/ -v
```

### Code Quality Checks

Ensure code formatting and linting standards are met:

```bash
# Check formatting
black --check code/ tests/

# Check linting
ruff check code/ tests/
```

## 5. Understanding the Results

### Model Results (`data/processed/model_results.json`)

Contains the core statistical findings:
- `coefficients`: Regression weights for predictors.
- `p_values`: Significance levels.
- `vif_value`: Variance Inflation Factor for multicollinearity.
- `status`: "PASS" or "FAIL" based on VIF threshold.

### Pipeline Log (`data/processed/pipeline_run_log.json`)

Tracks the execution flow:
- `status`: "success", "failed", or "halted".
- `steps`: Detailed log of each stage (load, validate, model, etc.).
- `errors`: Any exceptions raised during execution.

### Visualizations

- **Scatter Plot**: Visualizes the relationship between PSV and Self-Perception.
- **Residual Plot**: Checks for homoscedasticity and normality of errors.

## Troubleshooting

### Data Load Error
If the pipeline fails with `DataLoadError: Failed to fetch real dataset`, it is expected behavior if no real data source is configured or available. The pipeline is designed to automatically fall back to synthetic data generation in this case.

### Stability Threshold Violation
If the pipeline halts with `StabilityThresholdViolationError`, the coefficient variation across sensitivity strategies exceeded the defined limit. Review `data/processed/sensitivity_results.json` (if generated) to inspect the variation.

### Causal Language Violation
If `CausalLanguageViolationError` is raised, the generated report contained prohibited causal terms (e.g., "causes"). This is a safeguard to ensure scientific rigor.

## Next Steps

- **Customization**: Modify `code/utils/constants.py` to adjust thresholds (VIF, stability, significance).
- **Real Data**: Configure `code/data/loader.py` with a verified real data source URL or dataset ID.
- **Extension**: Add new analysis modules in `code/analysis/` and integrate them into `code/main.py`.