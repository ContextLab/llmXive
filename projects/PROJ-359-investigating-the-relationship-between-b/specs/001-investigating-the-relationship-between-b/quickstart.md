# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Response to Cognitive Training (Pivoted: Baseline Association)

## Prerequisites

- Python 3.11+
- Docker (required for fMRIPrep) or fMRIPrep binary installed.
- Sufficient free disk space (for dataset download and preprocessing).
- Internet connection (to download `ds000277`).

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins versions for `nibabel`, `pandas`, `networkx`, `bctpy`, `scikit-learn`, `matplotlib`, `requests`, `tqdm`, `pytest`, `statsmodels`.*

## Data Setup

1. **Download the dataset**:
   Run the download script. This will fetch `ds000277` from OpenNeuro.
   ```bash
   python code/download.py --dataset ds000277 --output data/raw
   ```
   *Note: If the dataset is not available at the expected URL, the script will raise a `RuntimeError`. Verify the URL in `research.md` if this fails.*

2. **Verify checksums**:
   The script automatically verifies file integrity. Ensure the log shows `Checksum OK`.

## Running the Pipeline

Execute the full pipeline from preprocessing to regression:

```bash
python code/main.py
```

This will:
1. Preprocess rs-fMRI data (fMRIPrep).
2. Exclude participants with mean FD > 0.3mm. (Corrected from 3.0).
3. Compute network metrics (Global Efficiency, Modularity, FPN/DMN Strength).
4. Fit the regression model predicting **Baseline WM** (not Gain) with 1,000 permutations.
5. Apply Holm-Bonferroni correction.
6. Generate `effect_sizes.pdf`, `model_summary.csv`, `power_analysis.txt`, `runtime.log`, and `reproducibility_report.txt`.

### Output Files

- `data/derived/baseline_metrics.csv`: Network metrics per participant.
- `data/derived/model_summary.csv`: Regression coefficients and p-values.
- `data/derived/effect_sizes.pdf`: Visualization of effect sizes.
- `data/derived/power_analysis.txt`: A priori and achieved power analysis.
- `data/logs/pipeline_log.json`: Runtime, exclusion counts, and warnings.
- `runtime.log`: Total runtime in seconds (SC-005). **Note**: This is the definitive file for SC-005 compliance.
- `reproducibility_report.txt`: Hash verification results (SC-004).

## Troubleshooting

- **fMRIPrep fails**: Ensure Docker is running and has sufficient memory (≥4GB). Check `data/logs/fmriprep.log`.
- **Out of Memory**: The pipeline automatically downsamples to N=30 if the full run exceeds 6 hours or memory limits. Check `data/logs/pipeline_log.json` for the `sample_size_reduction` warning.
- **Missing Behavioral Data**: If the dataset lacks `baseline_wm`, the pipeline will halt with a `FatalError`. This indicates a dataset mismatch (see `research.md`).

## Reproducibility

To reproduce results exactly:
1. Set the random seed in `code/main.py` (default: `42`).
2. Ensure the same version of fMRIPrep (23.1.3) is used.
3. Re-run the pipeline on the same raw data.
4. Verify `reproducibility_report.txt` matches the original run.
