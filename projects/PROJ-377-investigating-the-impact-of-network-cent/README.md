# llmXive: Investigating the Impact of Network Centrality on the Consolidation of Motor Memories

**Project ID:** PROJ-377-investigating-the-impact-of-network-cent

## Overview

This project investigates the relationship between functional network centrality in the brain and the consolidation of motor memories. We utilize fMRI data to compute centrality metrics (degree, betweenness, eigenvector) across the AAL3 atlas (~90 regions) and correlate these with behavioral motor improvement scores.

The pipeline is designed to be reproducible, memory-efficient, and robust, incorporating validation steps such as permutation testing and cross-validation.

## Key Features

- **Data Ingestion & Preprocessing**: Automated download from OpenNeuro and preprocessing via fMRIPrep.
- **Behavioral Analysis**: Extraction of motor scores, retention rate calculation, and power checks.
- **Network Centrality**: Calculation of degree, betweenness, and eigenvector centrality for the full AAL3 atlas.
- **Statistical Modeling**: Linear regression and GAM models with motion (FD) and demographic covariates.
- **Validation**: Freedman-Lane permutation tests and k-fold cross-validation to ensure robustness.
- **Reproducibility**: Automated generation of checksums, resource usage logs, and final reports.

## Project Structure

```
.
├── code/
│ ├── analysis/ # Centrality, regression, validation, exclusion logic
│ ├── data/ # Download, preprocessing, behavioral extraction
│ ├── utils/ # Logging, configuration, metrics, reproducibility
│ ├── quickstart_validation.py
│ └── requirements.txt
├── data/
│ ├── raw/ # Downloaded raw data and metadata
│ ├── processed/ # Preprocessed data, behavioral scores, centrality metrics
│ └── artifacts/ # Final reports and figures
├── docs/ # Documentation
├── tests/ # Unit, integration, and contract tests
├── README.md
└── plan.md
```

## Prerequisites

- Python 3.8+
- `openneuro-cli` (for data download)
- fMRIPrep (for preprocessing)
- Required Python packages (see `code/requirements.txt`)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-377-investigating-the-impact-of-network-cent
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

4. Ensure `openneuro-cli` is installed and configured:
 ```bash
 openneuro login
 ```

## Usage

### Data Download and Preprocessing

Run the data download and preprocessing pipeline:

```bash
python code/data/download.py
python code/data/preprocess.py
```

This will:
- Download the dataset from OpenNeuro.
- Validate required columns and retention rates.
- Preprocess fMRI data using fMRIPrep.
- Extract behavioral metrics and save to `data/processed/behavioral/`.

### Centrality Calculation

Compute network centrality metrics:

```bash
python code/analysis/centrality.py
```

This generates centrality metrics for all subjects and regions, saving results to `data/processed/centrality/`.

### Regression Analysis

Fit linear and non-linear models:

```bash
python code/analysis/regression.py
```

Outputs include regression summaries, scatter plots, and non-linearity checks in `data/processed/regression/`.

### Validation

Perform permutation tests and cross-validation:

```bash
python code/analysis/validation.py
```

Results are saved to `data/processed/validation/`.

### Reproducibility Report

Generate the final reproducibility report:

```bash
python code/utils/metrics.py
```

This produces `reproducibility_report.json` containing checksums, resource usage, and validation metrics.

## Configuration

Configuration settings (dataset URLs, thresholds, paths) are managed via `code/utils/config.py`.
You can override settings by creating a `config.json` file in the project root or by modifying the default values in the config module.

## Testing

Run the test suite:

```bash
pytest tests/
```

- **Contract Tests**: `tests/contract/`
- **Integration Tests**: `tests/integration/`
- **Unit Tests**: `tests/unit/`

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Ensure all tests pass.
5. Submit a pull request.

## License

This project is licensed under the MIT License.

## Contact

For questions or issues, please open an issue on the repository.
