# The Impact of Social Media Consumption Patterns on Cognitive Flexibility

**Project ID**: PROJ-453
**Status**: Active Research Pipeline

## Overview

This project investigates the relationship between social media consumption patterns (specifically platform switching frequency and diversity) and cognitive flexibility, measured via standardized executive function tasks. The pipeline is designed to ingest public survey data, engineer variables, fit associational regression models with rigorous diagnostics, and generate publication-ready visualizations while strictly enforcing non-causal language in interpretations.

## Key Objectives

1. **Data Ingestion**: Automatically download and parse raw data from verified public sources (HILDA, ESS, AddHealth).
2. **Variable Engineering**: Compute derived metrics such as the `switching_index` (platform count × switching frequency).
3. **Associational Analysis**: Fit multiple linear regression models to estimate associations while controlling for age and total screen time.
4. **Diagnostics & Robustness**: Calculate Variance Inflation Factors (VIF), perform sensitivity analyses on variable definitions, and verify robustness criteria (SC-003).
5. **Safety & Compliance**: Programmatically scan all generated interpretations for causal language (e.g., "causes", "leads to") to ensure the research remains strictly associational.

## Project Structure

```text
PROJ-453-the-impact-of-social-media-consumption-p/
├── code/ # Pipeline implementation scripts
│ ├── 00_feasibility_check.py # Phase 0: Data source verification
│ ├── 01_ingest.py # Phase 3: Data download and parsing
│ ├── 02_engineer.py # Phase 3: Variable engineering
│ ├── 03_model.py # Phase 4: Statistical modeling
│ ├── 04_visualize.py # Phase 5: Visualization
│ ├── config.py # Global constants
│ ├── utils.py # Helper functions (logging, checksums)
│ └── requirements.txt # Python dependencies
├── data/
│ ├── raw/ # Downloaded raw dataset files
│ └── processed/ # Cleaned, engineered CSVs
├── results/
│ ├── models/ # JSON model summaries and diagnostics
│ └── figures/ # Publication-ready plots (PNG/PDF)
├── contracts/ # Schema definitions for data and output
├── logs/ # Execution logs and validation reports
├── tests/ # Unit, contract, and integration tests
├── docs/ # Documentation (README, quickstart)
└── specs/ # Design documents and user stories
```

## Prerequisites

- Python 3.9+
- `pip` or `conda`
- Access to the internet (for data ingestion)

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Usage

The pipeline is executed sequentially. Run the following scripts in order:

1. **Feasibility Check** (Phase 0): Verifies data source accessibility and variable presence.
 ```bash
 python code/00_feasibility_check.py
 ```
2. **Data Ingestion** (Phase 3): Downloads and parses raw data.
 ```bash
 python code/01_ingest.py
 ```
3. **Variable Engineering** (Phase 3): Computes derived variables and cleans data.
 ```bash
 python code/02_engineer.py
 ```
4. **Modeling** (Phase 4): Fits regression models and performs diagnostics.
 ```bash
 python code/03_model.py
 ```
5. **Visualization** (Phase 5): Generates plots and final reports.
 ```bash
 python code/04_visualize.py
 ```

## Data Sources

The pipeline targets the following public datasets (verified for required variables):
- **HILDA** (Household, Income and Labour Dynamics in Australia)
- **ESS** (European Social Survey)
- **AddHealth** (National Longitudinal Study of Adolescent to Adult Health) - Fallback source

## Validation & Testing

- **Contract Tests**: Validate that data schemas match `contracts/dataset.schema.yaml`.
- **Unit Tests**: Verify individual function logic (e.g., VIF calculation, causal language scanning).
- **Robustness Checks**: Automated verification of SC-003 criteria (beta sign stability).

## Contributing

1. Create a feature branch.
2. Ensure all tests pass (`pytest tests/`).
3. Submit a Pull Request with a clear description of changes.

## License

[Insert License Here]