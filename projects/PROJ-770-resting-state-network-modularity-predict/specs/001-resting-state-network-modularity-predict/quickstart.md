# Quickstart: Resting-State Network Modularity Predicts Social Network Size

## Prerequisites
- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or a local Linux environment with sufficient RAM.
- **Data Access**: Ensure you have access to the HCP Large-Scale Subjects Release

The specific value to remove/generalize: 'large-scale'

Rewritten passage: (S3 bucket or verified HuggingFace mirror).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-770-resting-state-network-modularity-predict
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is designed to run end-to-end. It will download a sample of behavioral data and fMRI data from the verified HCP source.

1.  **Download Data**:
    ```bash
    python code/download_data.py --sample-size
    ```
    *Note: This script downloads behavioral data and fMRI NIfTI files from the verified HCP source. If the data is unavailable, the script will halt with an error.*

2.  **Preprocess fMRI**:
    ```bash
    python code/preprocess_fmri.py
    ```

3.  **Build Graphs & Compute Modularity**:
    ```bash
    python code/build_graphs.py --threshold-range "10,30,5"
    ```

4.  **Run Statistical Analysis**:
    ```bash
    python code/analyze_stats.py
    ```

5.  **View Results**:
    Results will be saved in `data/results/`.
    ```bash
    cat data/results/summary.csv
    ```

## Verification

To verify the pipeline:
- Check `data/processed/merged_subjects.csv` for the presence of `modularity_q` and `social_network_size`.
- Check `data/results/summary.csv` for the regression coefficient of `Modularity_Q`.
- Ensure no GPU errors appear in the logs.
- Verify that the VIF check was performed and reported in `data/results/vif_report.csv`.

## Troubleshooting
- **Memory Error**: Reduce `--sample-size` in `download_data.py`.
- **Data Missing**: Check the logs in `data/logs/` for excluded subjects (e.g., motion artifacts, missing NIfTI).
- **Louvain Convergence**: The script automatically retries with different seeds. If it fails, the subject is excluded and logged.
- **Collinearity**: If the VIF for `Total_Strength` is high, check `data/results/vif_report.csv` and review the sensitivity analysis results.
