# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher.
- `pip` (Python package installer).
- Internet connection (for downloading Knot Atlas data).
- At least 2GB of free disk space.

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` is located at `projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/requirements.txt`.*

## Execution

The pipeline is executed via the main orchestration script:

```bash
cd code
python main.py
```

### Execution Steps

1.  **Download**: Fetches data from Knot Atlas with retry logic.
    - Output: `data/raw/knot_atlas_raw.json`
2.  **Parse & Clean**: Extracts invariants, applies tie-breaking rules.
    - Output: `data/processed/knots_cleaned.csv`
    - *Note*: `knot_id` is normalized to `^[0-9]+_[0-9]+$` format.
3.  **Validate**: Checks against KnotInfo, flags missing data.
    - Output: `data/processed/knots_validated.csv`
4.  **Analyze**: Fits regression models, computes correlations, generates plots.
    - Output: `docs/reproducibility/` (reports, plots, logs).

## Verification

To verify the pipeline ran correctly:

1.  **Check Data Integrity**:
    ```bash
    python -c "import sys; sys.path.append('data'); from reproducibility import check_checksums; check_checksums('data/raw/knot_atlas_raw.json')"
    ```
2.  **View Reports**:
    - Data Quality: `docs/reproducibility/data_quality_report.md`
    - Validation Scope: `docs/reproducibility/validation_scope.md`
    - Core Precision Consistency: `docs/reproducibility/core_precision_consistency.md`
    - Tie-Breaking Rules: `docs/reproducibility/tie_breaking_rules.md`
    - Plot Validation: `docs/reproducibility/plot_validation_report.md`
    - Residual Analysis: `docs/reproducibility/residual_analysis.md`
3.  **Check Plots**:
    - Navigate to `data/plots/` for PNG files (min 1200x900 px).

## Troubleshooting

- **API Failure**: If Knot Atlas is unreachable, the script will retry with exponential backoff. If it fails after 3 attempts, partial results are cached. Check `docs/reproducibility/logs/` for error details.
- **Missing Invariants**: Records with missing invariants are not dropped but flagged. Check `docs/reproducibility/data_quality_report.md` for counts.
- **Memory Error**: The full dataset should fit in 7GB RAM. If issues arise, ensure no other heavy processes are running.
- **Schema Validation**: Ensure `contracts/knot_record.schema.yaml` is used for validation. Deprecated files are ignored.