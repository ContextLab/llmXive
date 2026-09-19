# The Impact of Self‑Reported Political News Exposure on Implicit Political Bias

**Project ID**: PROJ-469
**Status**: Production Ready

## Overview

This project analyzes the relationship between self-reported political news exposure frequency and implicit political bias (measured via the Implicit Association Test, IAT) using data from Project Implicit. The pipeline performs data acquisition, preprocessing (MICE imputation), primary regression analysis with interaction terms, robustness checks (bootstrap, alpha sweep, covariate adjustment), and generates a comprehensive PDF report.

## Prerequisites

- Python 3.11 or higher
- CPU-only environment (no GPU required)
- Access to the Project Implicit "Political IAT" dataset

## Installation

1. **Clone the repository** and navigate to the project root.

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Configure environment**:
 - Copy `config.yaml.example` to `config.yaml` and update paths if necessary.
 - Ensure the `data/raw/` directory exists. If you have the raw data, place it there.

## Data Requirements

This project requires the **Project Implicit "Political IAT" dataset**.

- **Source**: Project Implicit (https://projectimplicit.net/)
- **Format**: CSV
- **Required Columns**: `IAT_D_score`, `political_ideology`, `news_exposure_freq`, `age`, `gender`, `education` (for covariates).
- **Location**: The file must be placed in `data/raw/`. The default filename expected by the pipeline is `project_implicit_political.csv` (configurable in `config.yaml`).

### Data Acquisition

If you do not have the data locally, you can attempt to fetch it using the provided script:
```bash
python code/data_fetcher.py
```
*Note: If the specific dataset URL is unavailable or requires manual download, the script will halt with a `ValueError`. In that case, download the data manually from the source and place it in `data/raw/`.*

## Execution

Run the full analysis pipeline:

```bash
python code/main.py
```

This command executes the following steps in order:
1. **Data Loading**: Validates and loads the raw CSV.
2. **Preprocessing**: Performs MICE imputation (5 iterations) and derives variables (z-scores).
3. **Primary Analysis**: Fits the linear regression model `IAT_D ~ news_exposure_z * political_ideology`.
4. **Robustness Checks**: Runs bootstrap (1000 resamples), alpha sensitivity sweep, and covariate adjustment models.
5. **Reporting**: Generates the final PDF report and CSV summaries.

### Individual Modules

You can also run specific components independently:

- **Power Analysis**:
 ```bash
 python code/power.py
 ```
- **Robustness Checks**:
 ```bash
 python code/main_robustness_runner.py
 ```
- **Binary Model Variant**:
 ```bash
 python code/main_binary_runner.py
 ```

## Output Artifacts

All results are saved to the `results/` directory:

- `results/power_design.csv`: A priori power analysis results.
- `results/power_analysis.csv`: Retrospective power analysis results.
- `results/model_summary.csv`: Primary model coefficients and p-values.
- `results/diagnostics.csv`: Imputation diagnostics.
- `results/robustness_metrics.csv`: Aggregated robustness check metrics (bootstrap CI, alpha sweep, etc.).
- `results/binary_model.csv`: Results from the binary ideology model.
- `results/report.pdf`: The final consolidated PDF report.
- `results/*.png`: Generated plots (interaction, bootstrap distribution).

## Project Structure

```text
.
├── code/
│ ├── config.py # Configuration constants
│ ├── config_manager.py # Environment and config loading
│ ├── data_fetcher.py # Data acquisition script
│ ├── data_loader.py # Data loading and validation
│ ├── preprocessing.py # MICE imputation and feature engineering
│ ├── models.py # Primary and covariate regression models
│ ├── power.py # Power analysis utilities
│ ├── robustness.py # Bootstrap and alpha sweep logic
│ ├── reporting.py # Report generation and plotting
│ ├── main.py # Main pipeline entry point
│ └──... (other modules)
├── data/
│ ├── raw/ # Place raw CSV here
│ └── processed/ # Intermediate imputed data
├── results/ # Final outputs
├── tests/ # Unit and integration tests
├── docs/
│ └── README.md # This file
├── requirements.txt
└── config.yaml
```

## Testing

Run the test suite to verify implementation:

```bash
pytest tests/ -v
```

## Troubleshooting

- **Missing Data Error**: Ensure the CSV file is in `data/raw/` and contains the required columns defined in `contracts/dataset.schema.yaml`.
- **Memory Issues**: The pipeline is optimized for CPU. If running on limited RAM, ensure no other heavy processes are running. The bootstrap step (1000 iterations) may take several minutes.
- **Logging**: Check `logs/app.log` for detailed execution logs and error traces.

## License

This project is for research purposes. Data usage must comply with Project Implicit's terms of service.