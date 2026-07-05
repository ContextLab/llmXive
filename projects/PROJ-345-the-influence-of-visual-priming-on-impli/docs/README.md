# PROJ-345: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## Overview
This project implements a reproducible pipeline to investigate how visual priming influences implicit attitudes towards ambiguous social stimuli. It ingests public IAT datasets, derives stimulus metadata (valence and ambiguity), and fits Linear Mixed-Effects Models (LMM) to analyze response times.

## Architecture
- **Data Ingestion**: `code/data/ingest.py` downloads and validates raw IAT data.
- **Linkage**: `code/data/linkage.py` maps trial IDs to stimulus images.
- **Preprocessing**: `code/data/preprocess.py` derives valence/ambiguity and checks for confounding.
- **Modeling**: `code/models/lmm.py` fits LMMs with retry logic.
- **Metrics**: `code/models/metrics.py` calculates VIF, effect sizes, and sensitivity analysis.
- **Visualization**: `code/viz/plots.py` generates interaction plots and coefficient tables.
- **Reporting**: `code/reports/generate_report.py` compiles results into a PDF.

## Directory Structure
```
.
├── code/ # Source code modules
│ ├── data/ # Ingestion, preprocessing, linkage
│ ├── models/ # Statistical modeling and metrics
│ ├── reports/ # Report generation
│ ├── viz/ # Visualization utilities
│ ├── config.py # Configuration and paths
│ └── main.py # Entry point with PII scanning
├── data/ # Data storage
│ ├── raw/ # Downloaded raw datasets
│ ├── processed/ # Cleaned and linked data
│ ├── primes/ # Prime stimulus images
│ └── targets/ # Target stimulus images
├── state/ # Versioning and checksums
├── docs/ # Documentation
└── tests/ # Unit and integration tests
```

## Setup Instructions
1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd PROJ-345-the-influence-of-visual-priming-on-impli
 ```

2. **Create a virtual environment**:
 ```bash
 python3.11 -m venv venv
 source venv/bin/activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Run setup scripts**:
 ```bash
 python code/run_setup.py
 python code/run_state_init.py
 ```

## Usage
### Full Pipeline
Run the entire pipeline from ingestion to reporting:
```bash
python code/main.py
```

### Individual Components
- **Ingest Data**: `python code/data/ingest.py`
- **Preprocess**: `python code/data/preprocess.py`
- **Model**: `python code/models/lmm.py`
- **Generate Report**: `python code/reports/generate_report.py`

## Output Artifacts
- `data/processed/linked_trials.csv`: Trial-level data with stimulus linkage.
- `data/processed/stimulus_metadata.csv`: Derived valence and ambiguity scores.
- `data/processed/confounding_report.json`: Confounding check results.
- `data/processed/sensitivity_analysis.csv`: Alpha sensitivity analysis.
- `state/model_convergence_metrics.json`: Model convergence statistics.
- `reports/output_report.pdf`: Final analysis report.

## Contributing
1. Ensure all tests pass: `pytest tests/`
2. Format code: `black code/`
3. Lint code: `ruff check code/`

## License
This project is for research purposes only.
