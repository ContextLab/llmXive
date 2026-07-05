# The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

**Project ID**: PROJ-134-the-cognitive-mognitive-mechanisms-underlying-intu

This project implements an automated science pipeline to investigate the cognitive mechanisms underlying intuitive moral judgments using simulated and real VR data. It combines Moral Foundations Questionnaire (MFQ) data, moral story scenarios, and VR interaction logs to test hypotheses about visual salience effects on moral judgment.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Data Schema Reference](#data-schema-reference)
- [Running the Pipeline](#running-the-pipeline)
- [Configuration](#configuration)
- [Testing](#testing)
- [Contributing](#contributing)

---

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git

### Step-by-Step Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 The `requirements.txt` file includes:
 - `pymc>=5.0.0`: Bayesian modeling
 - `pandas`: Data manipulation
 - `numpy`: Numerical computing
 - `scikit-learn`: Machine learning utilities
 - `pyyaml`: YAML configuration parsing
 - `requests`: HTTP requests for data fetching
 - `seaborn`: Statistical visualization
 - `statsmodels`: Statistical modeling
 - `pydantic`: Data validation
 - `pytest`: Testing framework

4. **Initialize project directories**:
 ```bash
 python code/setup_directories.py
 python code/setup_subdirectories.py
 ```

5. **Configure random seeds and paths** (optional, defaults are provided):
 Edit `code/config.py` if custom paths or seeds are needed.

---

## Usage

### Quick Start

To run the full pipeline from data simulation to report generation:

```bash
# Step 1: Generate synthetic MFQ data
python code/data/simulation_mfq.py

# Step 2: Generate synthetic moral stories and VR logs
python code/data/simulation_stories.py

# Step 3: Ingest and merge datasets
python code/data/ingest.py

# Step 4: Preprocess data (map stories to VR scenes)
python code/data/preprocess.py

# Step 5: Run Bayesian model
python code/models/bayesian.py

# Step 6: Run regression analysis
python code/models/regression.py

# Step 7: Validate results
python code/analysis/validation.py

# Step 8: Generate final report
python code/reports/generate_report.py
```

### Simulation Mode

By default, the pipeline runs in `simulation` mode using synthetic data. To switch to real data mode (requires real data sources configured):

1. Set `RUN_MODE = 'real'` in `code/config.py`
2. Ensure real data is available at the configured paths or API endpoints

---

## Project Structure

```
.
├── code/
│ ├── config.py # Configuration: paths, seeds, constants
│ ├── setup_directories.py # Root directory initialization
│ ├── setup_subdirectories.py # Subdirectory initialization
│ ├── utils/
│ │ ├── hashing.py # SHA-256 checksums and state management
│ │ ├── logging_utils.py # Logging infrastructure
│ │ ├── norms.py # Psychometric norms reference
│ │ └── schema.py # Pydantic data schemas
│ ├── data/
│ │ ├── simulation_mfq.py # Synthetic MFQ data generation
│ │ ├── simulation_stories.py # Synthetic moral stories & VR logs
│ │ ├── ingest.py # Data loading and merging
│ │ ├── ingest_real.py # Real data fetch architecture
│ │ └── preprocess.py # VR scene mapping and salience assignment
│ ├── models/
│ │ ├── bayesian.py # PyMC Bayesian model
│ │ └── regression.py # Mixed-effects regression
│ ├── analysis/
│ │ ├── model_comparison.py # AIC/WAIC and PPC
│ │ └── validation.py # Parameter recovery and sensitivity
│ ├── reports/
│ │ └── generate_report.py # Final report generation
│ └── tests/
│ ├── test_ingest_mfq.py # MFQ generator tests
│ ├── test_ingest_stories.py# Story norms tests
│ ├── test_schema.py # Schema validation tests
│ ├── test_model.py # Regression tests
│ ├── test_model_convergence.py # Convergence tests
│ └── test_model_recovery.py # Parameter recovery tests
├── data/
│ ├── raw/ # Raw input data
│ ├── processed/ # Preprocessed datasets
│ └── logs/ # Pipeline execution logs
├── state/ # Pipeline state and checksums
├── reports/ # Generated reports
├── requirements.txt # Python dependencies
├── README.md # This file
└── docs/ # Additional documentation
```

---

## Data Schema Reference

The pipeline uses Pydantic models for strict data validation. Below are the key schemas:

### MFQ Dataset (`MFQDataset`)

| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | str | Unique participant identifier |
| `responses` | List[`MFQResponse`] | List of MFQ item responses |
| `timestamp` | datetime | Data collection timestamp |

### MFQ Response (`MFQResponse`)

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | str | MFQ item identifier (e.g., "mfq_01") |
| `score` | int | Likert score (0-5) |
| `foundation` | str | Moral foundation (care, fairness, loyalty, authority, purity) |

### Moral Story (`MoralStory`)

| Field | Type | Description |
|-------|------|-------------|
| `story_id` | str | Unique story identifier |
| `text` | str | Moral scenario text |
| `foundation` | str | Primary moral foundation |
| `intended_judgment` | float | Ground truth judgment score |

### VR Interaction Log (`VRInteractionLog`)

| Field | Type | Description |
|-------|------|-------------|
| `log_id` | str | Unique log identifier |
| `participant_id` | str | Participant identifier |
| `story_id` | str | Associated story |
| `response_time` | float | Reaction time in seconds |
| `gaze_data` | Dict | Gaze tracking coordinates |
| `judgment` | float | Moral judgment score |
| `salience_level` | `SalienceLevel` | Low or high visual salience |

### Salience Level (`SalienceLevel`)

- `LOW`: Minimal visual cues (baseline condition)
- `HIGH`: Enhanced visual cues (experimental condition)

---

## Running the Pipeline

### Full Pipeline Execution

```bash
# Execute all steps in sequence
bash scripts/run_pipeline.sh # If available, or run scripts individually
```

### Individual Module Execution

Each module can be run independently:

```bash
# Data Generation
python code/data/simulation_mfq.py --output data/raw/synthetic_mfq.csv
python code/data/simulation_stories.py --output data/raw/synthetic_stories.csv

# Ingestion
python code/data/ingest.py --input data/raw/ --output data/processed/merged.csv

# Preprocessing
python code/data/preprocess.py --input data/processed/merged.csv --output data/processed/preprocessed.csv

# Modeling
python code/models/bayesian.py --input data/processed/preprocessed.csv --output state/bayesian_results.json
python code/models/regression.py --input data/processed/preprocessed.csv --output state/regression_results.json

# Validation
python code/analysis/validation.py --input state/ --output state/validation_results.json

# Reporting
python code/reports/generate_report.py --input state/ --output reports/final_report.md
```

### Checksum Verification

To verify data integrity using SHA-256 checksums:

```bash
python code/utils/hashing.py --verify
```

---

## Configuration

### `code/config.py`

Key configuration options:

- `RUN_MODE`: `'simulation'` (default) or `'real'`
- `RANDOM_SEED`: Integer for reproducibility (default: 42)
- `DATA_PATHS`: Dictionary of input/output directories
- `MODEL_PARAMS`: Bayesian model hyperparameters
- `VALIDATION_THRESHOLDS`: Sensitivity analysis thresholds {2, 10, 20}

Example:

```python
# code/config.py
RUN_MODE = 'simulation'
RANDOM_SEED = 42
DATA_PATHS = {
 'raw': 'data/raw/',
 'processed': 'data/processed/',
 'logs': 'data/logs/'
}
```

---

## Testing

Run the test suite using pytest:

```bash
# Run all tests
pytest code/tests/ -v

# Run specific test module
pytest code/tests/test_schema.py -v

# Run with coverage
pytest code/tests/ --cov=code --cov-report=html
```

### Test Coverage

- **Data Generation**: Validates synthetic data against psychometric norms
- **Schema Validation**: Ensures data conforms to Pydantic models
- **Model Convergence**: Checks MCMC convergence (R-hat < 1.05)
- **Parameter Recovery**: Verifies ground truth effects are recovered within 95% CI
- **Sensitivity Analysis**: Tests robustness across decision thresholds

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Coding Standards

- Use `black` for formatting
- Use `ruff` or `flake8` for linting
- Write tests for new features
- Update documentation as needed

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- Gervais et al. (2011) for MFQ psychometric norms
- PyMC team for Bayesian modeling tools
- Open Science Framework (OSF) for data hosting infrastructure

---

## Support

For issues, questions, or contributions, please open an issue on the repository or contact the maintainers.
