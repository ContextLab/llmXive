# Quickstart Guide

## Prerequisites

- Python 3.10+
- ADNI credentials (set in `.env` file)
- Required dependencies installed via `pip install -r requirements.txt`

## Setup

1. Clone the repository and navigate to the project directory.
2. Create a `.env` file in the project root with the following variables:
 ```
 ADNI_USER=your_username
 ADNI_PASS=your_password
 ADNI_SUBJECT_LIST=subject1,subject2,subject3
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The full pipeline can be executed by running the main orchestrator script:

```bash
python code/main.py --log-level INFO
```

This will execute:
1. **User Story 1**: Download ADNI data, preprocess fMRI, compute connectivity matrices, and extract centrality metrics.
2. **User Story 2**: Merge data, run regression analysis, and perform statistical diagnostics.
3. **User Story 3**: Generate visualizations and compile the final report.

### Output Files

After successful execution, the following files will be generated:

- `data/analysis/centrality_metrics.csv` - Centrality metrics for all participants
- `data/analysis/qc_log.json` - Quality control exclusion log
- `data/analysis/regression_results.csv` - Regression analysis results
- `data/analysis/diagnostics.json` - Statistical diagnostics
- `outputs/final_report.pdf` - Final analysis report with visualizations

## Individual User Story Execution

If you wish to run individual user stories separately:

```bash
# Run User Story 1 only
python code/main_us1.py

# Run User Story 2 only (requires US1 completion)
python code/main_us2.py

# Run User Story 3 only (requires US2 completion)
python code/main_us3.py
```

## Troubleshooting

- **Missing ADNI credentials**: Ensure `.env` file is correctly configured.
- **Memory errors**: Reduce the number of subjects in `ADNI_SUBJECT_LIST`.
- **Missing output files**: Check `logs/pipeline.log` for error messages.