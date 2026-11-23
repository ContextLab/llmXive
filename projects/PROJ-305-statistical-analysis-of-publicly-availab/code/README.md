# Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Project Description

This project implements an automated statistical analysis pipeline for publicly available COVID-19 vaccine adverse event reports from the Vaccine Adverse Event Reporting System (VAERS). The pipeline performs data acquisition, preprocessing, disproportionality analysis (ROR, PRR, IC), and temporal profiling to identify potential safety signals while adhering to strict memory constraints and statistical validity requirements.

## Key Features

- **Data Acquisition**: Automated download and validation of VAERS datasets (2020-2023)
- **Data Preprocessing**: Cleaning, filtering by vaccine type, and MedDRA to SOC mapping
- **Disproportionality Analysis**: Calculation of Reporting Odds Ratio (ROR), Proportional Reporting Ratio (PRR), and Information Component (IC) with confidence intervals
- **Signal Detection**: 2-out-of-3 rule application for signal flagging
- **Sensitivity Analysis**: Comparison of different baseline groups (Full Non-COVID, Flu-only, Non-COVID Non-Flu)
- **Temporal Profiling**: Weekly reporting profiles for top signals
- **Memory Optimization**: Chunked processing and 7GB RAM limit enforcement

## Project Structure

```
.
├── src/ # Source code
│ ├── data/ # Data acquisition and preprocessing
│ ├── analysis/ # Statistical analysis modules
│ ├── utils/ # Utility functions
│ └── main.py # Pipeline orchestrator
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Cleaned and processed data
├── output/ # Analysis outputs (reports, figures)
├── contracts/ # Data schemas and validation contracts
├── logs/ # Pipeline execution logs
└── docs/ # Documentation
```

## Requirements

- Python 3.11+
- See `requirements.txt` for dependencies

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Run the full pipeline
python src/main.py

# Run specific phases
python src/main.py --phase data
python src/main.py --phase analysis
```

## License

This project is for research purposes only.

## Disclaimer

This analysis uses publicly available VAERS data. The temporal analysis is labeled as "Reporting Time" due to the lack of vaccination date data. Results should not be interpreted as establishing causality between vaccines and adverse events.
