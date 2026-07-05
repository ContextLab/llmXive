# Quickstart: Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions

## Prerequisites

- Python 3.11+
- Docker (for fMRIPrep)
- Substantial Disk Space

The research question remains: [Research Question].
The method remains: [Method].
References: [References].
- Sufficient RAM (Recommended for full batch; minimum threshold for streaming)
- OpenNeuro Account (optional, for larger downloads, though public access is available)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-361-investigating-the-relationship-between-b
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Install Git Hooks (for Versioning)**:
    To ensure Constitution Principle V (Versioning) is met, install the pre-commit hook:
    ```bash
    cp git_hooks/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    ```
    *This hook triggers `code/utils/update_state.py` on every commit to update the `state/` file.*

5.  **Pull fMRIPrep container** (if not already cached):
    ```bash
    docker pull poldracklab/fmriprep:23.1.0
    ```

## Running the Pipeline

### Step 1: Download Data (OpenNeuro ds004285)
Download the dataset using the OpenNeuro Python library.
```bash
python code/preprocessing/download_openneuro.py --dataset ds004285 --subjects sub-001,sub-002,sub-003,sub-004,sub-005
```
*Note: For CI, a small number of subjects are downloaded. For full analysis, specify all subjects.*

### Step 2: Preprocessing (fMRIPrep)
Run the preprocessing pipeline. This step is CPU-intensive.
```bash
# For a subset of subjects (recommended for CI)
python code/preprocessing/run_fmriprep.sh --subjects sub-001,sub-002,sub-003,sub-004,sub-005
```
*Note: For a full run of a substantial number of subjects, this should be executed on a local machine or a cloud VM, not the GitHub Actions free tier, due to the time limit.*

### Step 3: Extract Time Series & Compute Metrics
```bash
python code/topology/compute_connectivity.py --input-dir data/processed/
python code/topology/compute_metrics.py --input-dir data/processed/
python code/topology/reduce_dimensions.py --input-dir data/processed/
```

### Step 4: Extract Behavioral Data
Extract illusion scores from the OpenNeuro behavioral files.
```bash
python code/behavioral/export_scores.py --dataset-dir data/raw/ds004285/
```

### Step 5: Run Correlation Analysis
```bash
python code/analysis/correlation_analysis.py
python code/analysis/generate_plots.py
```

## Verification

To verify the pipeline:
1.  Check `data/processed/` for `sub-XXX_metrics.json` and `sub-XXX_components.json`.
2.  Verify `results/correlation_table.csv` contains FDR-adjusted p-values.
3.  Ensure no `NaN` values exist in the final metrics table (except where expected for disconnected graphs).
4.  Confirm `state/projects/PROJ-361-investigating-the-relationship-between-b.yaml` has been updated with the latest artifact hashes.

## Troubleshooting

- **fMRIPrep fails**: Ensure Docker is running and you have sufficient disk space. Use the pinned version `poldracklab/fmriprep:23.1.0`.
- **Memory Error**: Reduce the number of subjects processed in parallel. The pipeline is designed to process one subject at a time by default.
- **No Significant Results**: This is a valid outcome. Check the `results/analysis_report.md` for the "No significant correlations found" message.
- **Git Hook Error**: If the `state/` file is not updating, check that the `pre-commit` hook is executable and `update_state.py` is in `code/utils/`.