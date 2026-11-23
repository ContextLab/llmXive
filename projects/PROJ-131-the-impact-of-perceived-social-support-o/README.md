# The Impact of Perceived Social Support on Resilience to Online Harassment

## Methodological Approach

This project implements a **Single-Dataset Analysis** using the Cyberbullying Survey 2021 as the sole data source. The original plan for a "Synthetic Cohort" (dual-dataset matching with GSS 2022) was methodologically invalid and has been excluded per the project's Revised Approach.

## Prerequisites

- Python 3.9+
- pip package manager
- Git (for version control)

## Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Sources

- **Cyberbullying Survey 2021**: The primary dataset for analysis.
 - Location: `data/raw/cyberbullying_2021.csv` (after ingestion)
 - Source: Verified via `code/config/data_sources.yaml`

## Expected Outputs

After running the pipeline, the following files will be generated:

- `data/results/analysis_cohort.csv`: The cleaned analysis dataset
- `data/results/regression_results.csv`: Regression model outputs
- `data/results/regression_summary.md`: Human-readable summary report
- `data/results/sensitivity_analysis.csv`: Sensitivity analysis results
- `data/results/pipeline_run.log`: Execution log

## Running the Pipeline

```bash
python code/main_pipeline.py
```

## Project Structure

```
.
├── code/
│ ├── data/ # Data ingestion and preprocessing
│ ├── analysis/ # Statistical modeling and results
│ ├── config/ # Configuration files
│ └── tests/ # Test suites
├── data/
│ ├── raw/ # Raw data files
│ └── results/ # Generated analysis outputs
└── specs/ # Project specifications
```
