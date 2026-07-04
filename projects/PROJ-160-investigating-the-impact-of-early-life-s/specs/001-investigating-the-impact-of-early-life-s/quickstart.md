# Quickstart: Investigating the Impact of Early Life Stress on Hippocampal Subfield Volumes

## Prerequisites

- **Python 3.11+**
- **Access to ABCD Study Data**: You must have valid credentials to download Release 4.0 data from the NIH Data Archive.
- **Git**

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-160-investigating-the-impact-of-early-life-s
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download Data**:
    - Log in to the ABCD Study Data Portal.
    - Download `Release 4.0` Phenotypic CSV and `subcorticalSegmentationStats` files.
    - Place them in `data/raw/`.
    - *Note*: If you cannot download from the portal, place the files in `data/raw/` manually and ensure they are named `abcd_phenotypic.csv` and `abcd_subcortical_stats.csv`.

## Running the Analysis

Execute the main pipeline script:

```bash
python code/main.py
```

This script will:
1.  Verify data integrity (MD5 checksums).
2.  Filter and normalize the dataset.
3.  Fit the three LMMs and the exploratory ratio model.
4.  Run the permutation tests (with a sufficient number of iterations).
5.  Perform sensitivity analysis.
6.  Save results to `data/processed/`.

## Expected Outputs

- `data/processed/normalized_data.csv`: The cleaned, normalized dataset.
- `data/processed/model_results.json`: Detailed statistics for all models.
- `data/processed/robustness_checks.yaml`: Permutation and sensitivity results.
- `reports/summary_report.md`: A human-readable summary of findings.

## Troubleshooting

- **Memory Error**: Ensure you are filtering the data columns immediately after loading. The default ABCD CSVs are large.
- **Permutation Timeout**: If a large number of permutations exceeds the 6-hour limit, the script will log a warning. You may reduce the count in `code/config.py` for local testing (e.g., `N_PERMUTATIONS=1000`), but the final run must use a sufficiently large sample size to ensure statistical power.
- **Missing Variables**: Verify that the ABCD Release 4.0 files contain the columns `ACE_score`, `CA3_volume`, `DG_volume`, `Subiculum_volume`, `ICV`, `family_id`.
