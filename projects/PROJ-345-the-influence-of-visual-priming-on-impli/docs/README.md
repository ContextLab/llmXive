# The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## Project Overview

This research project investigates how visual priming influences implicit attitudes towards ambiguous social stimuli. The study utilizes a multi-phase approach to data ingestion, statistical modeling, and reporting, ensuring rigorous adherence to scientific principles and reproducibility.

## Key Features

- **Data Ingestion**: Automated downloading and processing of IAT datasets from verified OSF/HF sources.
- **Stimulus Metadata Extraction**: Mapping trial data to visual stimulus metadata with integrity checks.
- **Statistical Modeling**: Linear Mixed-Effects Models (LMM) with proper random effects structure and confounding checks.
- **Reporting**: Automated generation of PDF reports with interaction plots, coefficient tables, and sensitivity analyses.

## Project Structure

```
.
├── code/ # Source code
│ ├── data/ # Data ingestion and preprocessing
│ ├── models/ # Statistical modeling
│ ├── reports/ # Report generation
│ ├── viz/ # Visualization
│ ├── state/ # State management
│ ├── security/ # Security and PII scanning
│ ├── validation/ # Validation scripts
│ ├── config.py # Configuration and paths
│ └── main.py # Entry point
├── data/ # Data directories
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed data
│ ├── primes/ # Prime stimuli
│ └── targets/ # Target stimuli
├── docs/ # Documentation
├── state/ # State management files
├── tests/ # Test suite
├── requirements.txt # Dependencies
├── quickstart.md # Quick start guide
└── README.md # This file
```

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create a Python 3.11 virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Running the Pipeline

The main entry point is `code/main.py`. It orchestrates the entire pipeline from data ingestion to report generation.

```bash
python code/main.py
```

### Individual Components

- **Data Ingestion**: `python code/data/ingest.py`
- **Preprocessing**: `python code/data/preprocess.py`
- **Modeling**: `python code/models/lmm.py`
- **Reporting**: `python code/reports/generate_report.py`
- **Validation**: `python code/validation/validate_quickstart.py`

### Configuration

Edit `code/config.py` to modify paths, random seeds, and other configuration parameters.

## Testing

Run the test suite with:

```bash
pytest tests/
```

## Reproducibility

This project adheres to strict reproducibility guidelines:

- All random seeds are pinned.
- Data sources are verified and checksums are recorded.
- State management ensures version control of all artifacts.
- All analyses are associational, with explicit limitations noted.

## Limitations

- **Observational Nature**: Findings are associational, not causal.
- **Derived Prime Valence**: Prime valence scores are derived via CPU-optimized VAD regression models, which may introduce approximation errors.
- **Synthetic Ambiguity**: When human-rated ambiguity is unavailable, synthetic derivation is used, which may not fully capture human perception.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please follow the project's coding standards and submit pull requests for review.
