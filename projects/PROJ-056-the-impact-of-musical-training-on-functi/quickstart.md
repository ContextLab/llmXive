# Quickstart Guide: The Impact of Musical Training on Functional Connectivity

This guide explains how to run the pipeline in **Verification Mode** (using synthetic data for code validation) and **Analysis Mode** (requiring real neuroimaging data).

## Prerequisites

- Python 3.11+
- Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running Verification Mode (Synthetic Data)

Use this mode to validate the pipeline logic, check memory constraints, and ensure all modules execute without errors. No real data is required.

1. **Generate Synthetic Data**:
 The pipeline automatically generates synthetic data when running in verification mode if no real data path is provided.
2. **Execute the Pipeline**:
 ```bash
 cd code
 python main.py --mode verification
 ```
3. **Expected Outputs**:
 - `data/processed/subjects_cleaned.csv`
 - `data/processed/connectivity_results.csv`
 - `data/processed/nbs_results.csv`
 - `data/processed/correlation_results.csv`
 - `data/processed/sensitivity_analysis.csv`

**Note**: Results in this mode are **simulation results** and do not represent biological findings. They are intended solely for code verification.

## Running Analysis Mode (Real Data)

Use this mode to process real fMRI data (e.g., ABCD, HCP). **Real data is strictly required.**

1. **Prepare Real Data**:
 Ensure your raw data (NIfTI files and subject metadata) is accessible. You must provide the path to the data directory.
2. **Execute the Pipeline**:
 ```bash
 cd code
 python main.py --mode analysis --data-path /path/to/real/data
 ```
3. **Data Requirements**:
 - **Minimum Subjects**: At least 50 subjects in the "musician" group and 50 in the "non-musician" group.
 - **File Format**: Valid NIfTI files for fMRI scans and CSV/JSON for metadata.
 - **Confounders**: Metadata must include `age`, `sex`, `motion_score`, `ses_score`, and `years_of_training`.

**Failure Condition**: If the `--data-path` is invalid, missing, or contains fewer than 50 subjects per group, the pipeline will raise a `DataAccessError` or `ValueError` and halt execution. **No synthetic fallback is provided in Analysis Mode.**

## Troubleshooting

- **Memory Limit Exceeded**: The pipeline enforces a 7GB RAM limit. If you encounter `MemoryLimitExceeded`, ensure your data chunks are small enough or increase system RAM.
- **Data Access Errors**: In Analysis Mode, verify that the `--data-path` points to a directory containing valid subject data.
- **Missing Modules**: Ensure all dependencies in `code/requirements.txt` are installed.

## Next Steps

- Review `data/processed/` for output files.
- Consult `specs/001-the-impact-of-musical-training-on-functi/` for detailed design documents.
- Run unit tests: `pytest tests/`