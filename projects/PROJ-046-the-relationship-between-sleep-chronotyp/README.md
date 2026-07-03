# The Relationship Between Sleep Chronotype and Moral Judgement

## Project Overview
This project investigates the relationship between sleep chronotype (MEQ, MFQ) and moral judgment, controlling for sleep quality (PSQI) and acute sleepiness.

## Directory Structure
- `data/raw/`: Raw input data (user-provided CSVs)
- `data/processed/`: Cleaned and preprocessed data
- `data/derived/`: Analysis results, metrics, and models
- `logs/`: Execution logs and exclusion records
- `code/`: R and Python scripts for analysis
- `tests/`: Unit and integration tests
- `reports/`: Final R-Markdown reports
- `figures/`: Generated plots and charts

## Prerequisites
- R 4.3+
- Python 3.9+
- `renv` (for R dependency management)

## Setup
1. Run the setup script to initialize directories:
 ```bash
 python code/setup_project_structure.py
 ```
2. Initialize R environment:
 ```bash
 Rscript -e "renv::init()"
 ```

## Data Source Strategy
**Note**: This project currently relies on user-provided merged datasets as per Plan.md.
The spec assumption regarding Prolific integration is flagged for plan update.
Raw data must be placed in `data/raw/` before running analysis scripts.