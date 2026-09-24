# Statistical Discrepancies in Publicly Available Election Data (PROJ-064)

This project analyzes statistical discrepancies between precinct-level vote sums and county-reported totals in publicly available election data.

## Project Structure

```
projects/PROJ-064-statistical-discrepancies-in-publicly-av/
├── code/ # Source code
│ ├── main.py # Entry point
│ ├── ingestion.py # Data ingestion pipeline
│ ├── discrepancy.py # Discrepancy calculation
│ ├── simulation.py # Null model simulation
│ ├── analysis.py # Statistical analysis
│ ├── viz.py # Visualization
│ ├── models.py # Data models
│ ├── logger.py # Logging setup
│ ├── exceptions.py # Custom exceptions
│ ├── error_handling.py # Error handling utilities
│ ├── setup_project.py # Project initialization
│ └── utils/ # Utility modules
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed data
├── tests/ # Test suite
├── docs/ # Documentation
├── state/ # Checksums and state files
└── config/ # Configuration files
```

## Setup

1. Initialize the project structure:
 ```bash
 python code/setup_project.py
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Run the pipeline:
 ```bash
 python code/main.py
 ```

## Reproducibility

To verify reproducibility:
```bash
python code/main.py --verify-reproducible
```