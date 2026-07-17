# Quick Start Guide: Flight Delay Statistical Analysis

This guide provides instructions for setting up and running the statistical analysis pipeline for flight delay distributions.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Sufficient disk space (~2GB for raw data, ~500MB for processed)
- Sufficient RAM (6.5GB recommended for full dataset processing)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-105-statistical-analysis-of-publicly-availab
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

## Configuration

The pipeline uses `code/config.py` for configuration. Key settings include:
- `TARGET_YEAR`: The year of flight data to analyze (default: 2023).
- `MEMORY_LIMIT_GB`: Maximum allowed RAM usage (default: 6.5).
- `RANDOM_SEED`: Random seed for reproducibility (default: 42).

To change the target year, edit `code/config.py`:
```python
TARGET_YEAR: int = 2023 # Change this value
```

## Running the Pipeline

The pipeline is executed in stages via `code/main.py`.

### Full Pipeline Execution

To run the entire analysis (Data Acquisition -> Modeling -> Diagnostics -> Validation):

```bash
python code/main.py
```

This will:
1. Download raw BTS data for the specified year.
2. Preprocess and clean the data.
3. Fit parametric models (Exponential, Gamma, Log-Normal, Weibull, Pareto).
4. Perform heavy-tail diagnostics (Hill estimator, Bootstrap GoF).
5. Generate all result files and validation reports.

### Running Individual Stages

You can run specific stages by passing arguments:

```bash
# Stage 1: Data Acquisition and Preprocessing
python code/main.py --stage 1

# Stage 2: Model Fitting
python code/main.py --stage 2

# Stage 3: Diagnostics
python code/main.py --stage 3

# Stage 4: Final Validation
python code/main.py --stage 4
```

## Output Files

After successful execution, the following files will be generated:

- `data/processed/cleaned_delays.csv`: The preprocessed dataset.
- `data/results/summary_report.json`: Overview of data quality and retention.
- `data/results/model_comparison.json`: Metrics for all fitted distributions.
- `data/results/x_min_estimate.json`: Estimated threshold for tail analysis.
- `data/results/tail_index_estimate.json`: Hill estimator results.
- `data/results/bootstrap_gof.json`: Bootstrap goodness-of-fit p-values.
- `data/results/log_normal_test.json`: Log-normal discrimination results.
- `data/results/vuong_test_results.json`: Vuong test comparison.
- `data/results/validation_status.json`: Final pass/fail status for all success criteria.
- `figures/`: Directory containing diagnostic plots (log-log survival, QQ-plots).

## Testing

To run the test suite:

```bash
pytest tests/
```

To run with coverage:

```bash
pytest --cov=code --cov-report=html
```

## Troubleshooting

- **Memory Error**: If the pipeline fails with a memory error, reduce the `MEMORY_LIMIT_GB` in `config.py` or process a smaller sample of the data (if supported).
- **Data Download Failure**: Ensure you have an active internet connection and that the BTS URL is accessible. The pipeline includes retry logic for transient network issues.
- **Model Convergence Failure**: If specific models fail to converge, check the logs in `data/logs/pipeline.log` for detailed error messages.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
