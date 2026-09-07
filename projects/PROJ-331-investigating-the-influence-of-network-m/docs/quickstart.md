# Quick Start Guide: Investigating Network Motifs on Resting-State Functional Connectivity

This guide provides step-by-step instructions to run the full pipeline on a fresh environment.
It assumes you have a UNIX-like environment (Linux/macOS) with Python 3.9+ installed.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Git (for cloning the repository)
- At least 20GB of free disk space (for raw HCP data and processed artifacts)
- Network access to the HCP S3 bucket (anonymous read access)

## 1. Clone the Repository

```bash
git clone
cd PROJ-331-investigating-the-influence-of-network-m
```

## 2. Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

## 3. Install Dependencies

Install all required Python packages defined in `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Verify HCP Data Access

Before running the full pipeline, verify that you can access the HCP S3 bucket:

```bash
bash scripts/verify_hcp_access.sh
```

This script will create a `data/raw/.access_verified` flag if successful.

## 5. Initialize Project Structure

Ensure all necessary directories are created:

```bash
python -c "from setup_project import create_directories; create_directories()"
```

## 6. Run the Full Pipeline

Execute the main pipeline script which orchestrates data download, preprocessing, motif analysis, and reporting:

```bash
python code/download.py
python code/preprocess.py
python code/motifs.py
python code/stats.py
python code/report.py
```

**Note**: The full pipeline may take several hours depending on the number of subjects and network speed.

## 7. Validate Outputs

After the pipeline completes, run the validation script to ensure all artifacts were generated correctly:

```bash
bash scripts/validate_quickstart.sh
```

This script verifies:
- All expected output files exist in `data/processed/` and `results/`
- Checksums match recorded values
- The PDF report was generated successfully
- Log files contain required statistical parameters

## 8. View Results

- **Processed Data**: `data/processed/`
 - `subject_metrics.csv`: Aggregated metrics for all subjects
 - `motif_profiles.json`: Z-scores for all 13 directed 3-node motifs
 - `structural_connectome_metadata.json`: Status flags for each subject
- **Analysis Results**: `results/`
 - `correlation_results.json`: Bonferroni-corrected correlation results
 - `permutation_results.json`: Empirical p-values from permutation tests
 - `power_analysis.json`: Power analysis details
 - `results.pdf`: Final report with visualizations and methods
- **Logs**: `data/logs/pipeline.log`
 - Contains all processing steps, warnings, and statistical parameters

## Troubleshooting

### HCP Access Issues
If `verify_hcp_access.sh` fails, ensure your network allows access to the HCP S3 bucket and that you have not exceeded any rate limits.

### Memory Errors
If you encounter memory errors during motif enumeration, the pipeline includes a fallback to `igraph` (see `code/motifs.py`). Ensure `igraph` is installed.

### Timeout Errors
If a subject exceeds the 300-second timeout for motif enumeration, the pipeline will log a warning and skip that subject for that specific motif, continuing with the rest of the cohort.

## Next Steps

- Review the `results.pdf` for the final analysis
- Examine `data/logs/pipeline.log` for detailed processing information
- Run individual components separately for debugging or incremental analysis
- Consult `README.md` for project overview and architecture details