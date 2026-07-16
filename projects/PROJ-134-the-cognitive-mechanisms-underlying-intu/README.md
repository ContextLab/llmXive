# The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

A research pipeline to simulate and analyze moral decision-making data using Bayesian inference and mixed-effects regression, validated against psychometric norms.

## Project Overview

This project implements a computational pipeline to investigate how visual salience in virtual environments affects intuitive moral judgments. The pipeline:
1. Ingests synthetic Moral Foundations Questionnaire (MFQ) and Moral Stories data
2. Maps text scenarios to VR scenes with controlled salience levels
3. Executes Bayesian models to estimate salience effects
4. Validates results against known psychometric norms and ground-truth parameters
5. Generates comprehensive validation reports

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager
- A Unix-like environment (Linux/macOS) recommended for path compatibility

### Setup Steps

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-134-the-cognitive-mechanisms-underlying-intu
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

 **Required Dependencies**:
 - `pymc>=5.0.0`: Bayesian modeling
 - `pandas`: Data manipulation
 - `numpy`: Numerical operations
 - `scikit-learn`: Machine learning utilities
 - `pyyaml`: Configuration parsing
 - `requests`: HTTP requests for data fetching
 - `seaborn`: Statistical visualization
 - `statsmodels`: Statistical modeling (mixed-effects)
 - `pydantic`: Data validation
 - `pytest`: Testing framework

4. Verify installation:
 ```bash
 python -c "import pymc; import pandas; print('Dependencies OK')"
 ```

## Usage Examples

### Running the Full Pipeline

The pipeline consists of three main stages: Data Ingestion, Model Execution, and Validation.

```bash
# 1. Generate Synthetic Data (Simulation Mode)
python code/data/simulation_mfq.py
python code/data/simulation_stories.py

# 2. Ingest and Merge Data
python code/data/ingest.py

# 3. Preprocess Data (Salience Mapping)
python code/data/preprocess.py

# 4. Run Bayesian Model
python code/models/bayesian.py

# 5. Run Regression Analysis
python code/models/regression.py

# 6. Run Validation Pipeline
python code/analysis/validation.py

# 7. Generate Final Report
python code/reports/generate_report.py
```

### Running Individual Components

#### Data Simulation
```bash
# Generate MFQ data based on Gervais et al. (2011) norms
python code/data/simulation_mfq.py

# Generate Moral Stories and VR logs with known ground truth
python code/data/simulation_stories.py
```

#### Model Execution
```bash
# Run Bayesian analysis with parameter recovery validation
python code/models/bayesian.py

# Run mixed-effects regression with Bonferroni correction
python code/models/regression.py
```

#### Validation
```bash
# Check parameter recovery and sensitivity analysis
python code/analysis/validation.py
```

### Configuration

All configuration is managed via `code/config.py`. Key settings include:
- `RANDOM_SEED`: Reproducibility seed (default: 42)
- `RUN_MODE`: 'simulation' or 'real'
- `DATA_PATHS`: Locations for raw and processed data

To modify settings, edit `code/config.py` directly or set environment variables.

## Data Schema Reference

The project uses Pydantic models for strict data validation. Below are the core schemas.

### MFQ Dataset (`code/utils/schema.py`)

**MFQResponse**:
| Field | Type | Description |
|-------|------|-------------|
| `respondent_id` | str | Unique identifier |
| `foundation` | str | One of: Care, Fairness, Loyalty, Authority, Purity |
| `score` | float | 0-5 Likert scale score |
| `item_text` | str | Question text |

**MFQDataset**:
| Field | Type | Description |
|-------|------|-------------|
| `metadata` | dict | Dataset metadata (source, date, n) |
| `responses` | List[MFQResponse] | List of responses |

### Moral Stories Dataset

**MoralStory**:
| Field | Type | Description |
|-------|------|-------------|
| `story_id` | str | Unique identifier |
| `scenario_text` | str | The moral dilemma description |
| `foundation_violated` | str | Primary foundation violated |
| `severity` | float | 1-10 severity rating |

**VRInteractionLog**:
| Field | Type | Description |
|-------|------|-------------|
| `log_id` | str | Unique identifier |
| `story_id` | str | Reference to story |
| `response_time` | float | Reaction time in ms |
| `gaze_dwell_time` | float | Visual attention duration |
| `judgment` | float | Moral judgment score |
| `salience_level` | str | 'low' or 'high' |

### Merged Dataset

The final processed dataset merges MFQ scores with story judgments:
| Field | Type | Description |
|-------|------|-------------|
| `respondent_id` | str | Linked ID |
| `story_id` | str | Linked ID |
| `foundation_score` | float | Aggregated foundation score |
| `salience_level` | str | 'low' or 'high' |
| `judgment` | float | Moral judgment |
| `response_time` | float | Reaction time |

## Project Structure

```
.
├── code/
│ ├── config.py # Configuration and constants
│ ├── utils/
│ │ ├── schema.py # Pydantic data models
│ │ ├── norms.py # Psychometric norm handling
│ │ ├── hashing.py # Checksum and state management
│ │ └── logging_utils.py # Logging infrastructure
│ ├── data/
│ │ ├── simulation_mfq.py # Synthetic MFQ generator
│ │ ├── simulation_stories.py # Synthetic stories/VR logs
│ │ ├── ingest.py # Data merging pipeline
│ │ ├── preprocess.py # Salience mapping
│ │ └── unity_verification.py # Fidelity checks
│ ├── models/
│ │ ├── bayesian.py # PyMC3 Bayesian models
│ │ └── regression.py # Mixed-effects regression
│ ├── analysis/
│ │ ├── model_comparison.py # AIC/WAIC calculations
│ │ └── validation.py # Parameter recovery checks
│ ├── reports/
│ │ └── generate_report.py # Final report generation
│ └── tests/ # Unit tests
├── data/
│ ├── raw/ # Raw input data
│ ├── processed/ # Processed datasets
│ └── logs/ # Execution logs
├── state/ # Pipeline state checksums
├── requirements.txt # Dependencies
└── README.md # This file
```

## Validation & Testing

Run the test suite:
```bash
pytest code/tests/ -v
```

Key validation metrics:
- **Parameter Recovery**: Ground truth effect within 95% CI
- **Psychometric Norms**: Synthetic data within 1 SD of Gervais et al. (2011)
- **Model Fit**: Posterior Predictive Checks (PPC)
- **Statistical Significance**: Bonferroni-corrected p-values

## License

This project is for research purposes. See LICENSE file for details.
