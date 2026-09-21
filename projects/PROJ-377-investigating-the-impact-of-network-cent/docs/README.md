# PROJ-377: Investigating the Impact of Network Centrality on the Consolidation of Motor Memories

## Project Overview

This project investigates the relationship between functional network centrality in the motor cortex and the consolidation of motor memories. We analyze fMRI data to compute centrality metrics (degree, betweenness, eigenvector) from the AAL3 atlas (~90 regions) and correlate these with behavioral motor improvement scores.

## Key Features

- **Data Ingestion**: Automated download and validation of OpenNeuro datasets
- **Preprocessing**: Memory-efficient fMRIPrep wrapper with motion artifact handling
- **Centrality Analysis**: Full-atlas centrality metric computation using NetworkX
- **Statistical Modeling**: Linear regression and GAM models with motion covariates
- **Validation**: Freedman-Lane permutation tests and k-fold cross-validation
- **Reproducibility**: Automated checksums, resource usage tracking, and artifact validation

## Directory Structure

```
.
├── code/
│ ├── analysis/
│ │ ├── centrality.py # Centrality metric computation
│ │ ├── regression.py # Statistical modeling
│ │ └── validation.py # Permutation tests & CV
│ ├── data/
│ │ ├── download.py # Dataset download
│ │ ├── preprocess.py # fMRIPrep wrapper
│ │ ├── behavioral_extraction.py
│ │ ├── connectivity_matrix.py
│ │ ├── power_check.py
│ │ ├── retention_validation.py
│ │ ├── subject.py
│ │ └── validation.py
│ ├── setup_data_dirs.py
│ └── utils/
│ ├── config.py # Configuration management
│ ├── logging.py # Logging & resource tracking
│ └── metrics.py # Reproducibility reporting
├── data/
│ ├── raw/
│ │ ├── metadata.csv
│ │ └── fmriprep/
│ ├── processed/
│ │ ├── behavioral/
│ │ │ ├── subject_scores.csv
│ │ │ ├── fd_mean.csv
│ │ │ └── retention_metrics.json
│ │ ├── centrality/
│ │ │ ├── subject_id_metrics.csv
│ │ │ ├── global_scores.csv
│ │ │ ├── vif_values.csv
│ │ │ └── model_predictors.csv
│ │ ├── regression/
│ │ │ ├── linear_model_summary.csv
│ │ │ ├── nonlinearity_check.csv
│ │ │ └── regional_pvalues.csv
│ │ ├── validation/
│ │ │ ├── null_distribution.csv
│ │ │ ├── permutation_results.json
│ │ │ ├── cv_results.json
│ │ │ ├── baseline_r2.json
│ │ │ └── fdr_corrected_pvalues.csv
│ │ └── logs/
│ │ └── exclusion_log.csv
│ └── artifacts/
├── tests/
│ ├── contract/
│ ├── integration/
│ └── unit/
├── docs/
│ └── README.md
├── data-model.md
├── plan.md
├── quickstart.md
└── requirements.txt
```

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-377-investigating-the-impact-of-network-cent
 ```

2. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

3. **Install fMRIPrep** (if not already installed):
 ```bash
 # Follow instructions at https://fmriprep.org/en/stable/installation.html
 ```

4. **Install OpenNeuro CLI**:
 ```bash
 pip install openneuro
 ```

## Usage

### Quick Start

Run the full pipeline using the provided scripts:

```bash
# Step 1: Download and validate data
python code/data/download.py
python code/data/validation.py

# Step 2: Preprocess fMRI data
python code/data/preprocess.py

# Step 3: Extract behavioral metrics
python code/data/behavioral_extraction.py

# Step 4: Calculate centrality metrics
python code/analysis/centrality.py

# Step 5: Run regression analysis
python code/analysis/regression.py

# Step 6: Perform validation (permutation & CV)
python code/analysis/validation.py

# Step 7: Generate reproducibility report
python code/utils/metrics.py
```

### Configuration

Modify settings in `code/utils/config.py` or create a custom configuration file:

```python
from utils.config import get_config

config = get_config()
config.vif_threshold = 5.0
config.permutation_shuffles = 1000
config.cv_folds = 5
```

### Output Files

The pipeline generates the following key outputs:

- `data/processed/behavioral/subject_scores.csv`: Behavioral metrics per subject
- `data/processed/centrality/subject_id_metrics.csv`: Regional centrality metrics
- `data/processed/regression/linear_model_summary.csv`: Regression results
- `data/processed/validation/permutation_results.json`: Permutation test p-values
- `data/processed/validation/cv_results.json`: Cross-validation metrics
- `reproducibility_report.json`: Full reproducibility report

## Testing

Run the test suite:

```bash
# Contract tests
pytest tests/contract/

# Integration tests
pytest tests/integration/

# Unit tests
pytest tests/unit/
```

## Pipeline Phases

### Phase 0: Data Validation & Feasibility Check
- Validates dataset availability and completeness
- Enforces hard stops for missing data (T001-T004)

### Phase 1: Setup
- Project initialization and directory structure (T005-T008)

### Phase 2: Foundational
- Core infrastructure: logging, metrics, data models (T009-T013)

### Phase 3: User Story 1 - Data Ingestion
- fMRIPrep preprocessing and behavioral extraction (T014-T020)

### Phase 4: User Story 2 - Centrality & Modeling
- Centrality calculation, VIF check, regression fitting (T021-T032)

### Phase 5: User Story 3 - Validation
- Permutation tests and cross-validation (T033-T039)

### Phase 6: Reporting
- Final reproducibility report generation (T040)

## API Reference

### Core Modules

#### `code/analysis/centrality.py`
- `compute_centrality_metrics()`: Calculate degree, betweenness, eigenvector centrality
- `calculate_mean_fd()`: Compute mean framewise displacement
- `run_centrality_analysis()`: Full centrality pipeline

#### `code/analysis/regression.py`
- `fit_linear_regression()`: Fit linear models with covariates
- `generate_scatter_plot()`: Create visualization
- `run_regression_analysis()`: Full regression pipeline

#### `code/analysis/validation.py`
- `run_freedman_lane_permutation()`: Permutation test implementation
- `run_validation_analysis()`: Full validation pipeline

#### `code/utils/config.py`
- `get_config()`: Retrieve configuration object
- `get_vif_threshold()`: Get VIF threshold (default: 5.0)
- `get_permutation_shuffles()`: Get number of permutations (default: 1000)

## Dependencies

- Python >= 3.8
- pandas
- numpy
- networkx
- scikit-learn
- statsmodels
- nilearn
- openneuro-cli
- matplotlib
- seaborn
- pymvpa
- psutil

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `pytest`
4. Submit a pull request

## License

[License information]

## Acknowledgments

- OpenNeuro for dataset hosting
- fMRIPrep team for preprocessing tools
- NetworkX developers for centrality algorithms

## Contact

For questions or issues, please open an issue in the repository.
