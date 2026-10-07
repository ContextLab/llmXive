# Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Project Description

This project implements a reproducible pipeline for the statistical analysis of publicly available VAERS (Vaccine Adverse Event Reporting System) data. The primary goal is to identify potential safety signals by comparing adverse event reporting rates for COVID-19 vaccines against a baseline of non-COVID vaccines using disproportionality analysis methods (ROR, PRR, IC).

## Key Features

- **Data Acquisition**: Automated download and validation of VAERS datasets (2020-2023).
- **Preprocessing**: Cleaning, filtering, and MedDRA-to-SOC mapping.
- **Disproportionality Analysis**: Calculation of Reporting Odds Ratio (ROR), Proportional Reporting Ratio (PRR), and Information Component (IC) with 95% confidence intervals.
- **Signal Detection**: Application of the 2-out-of-3 rule to flag potential safety signals.
- **Temporal Profiling**: Descriptive analysis of reporting trends over time.
- **Memory Safety**: Strict memory constraints (7GB limit) with chunked processing support.

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

Run the full pipeline:
```bash
python code/src/main.py
```

## Output

- `data/processed/`: Cleaned and processed datasets.
- `output/signals.csv`: Disproportionality metrics and signal flags.
- `output/temporal_profiles/`: Visualizations of reporting trends.
- `output/report.md`: Final analysis report.

## Limitations

- This analysis uses internal dataset counts as the denominator; external background incidence rates are not calculated.
- Temporal analysis is based on report dates, not vaccination dates, and is labeled accordingly ("Reporting Time").
- Results are descriptive and do not establish causality.

## License

[Insert License Information]