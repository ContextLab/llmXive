# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Subjective Time Perception

## Prerequisites

- Python 3.11+
- `git`
- Docker (optional, for fMRIPrep if real data is available and resources permit)

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-433-investigating-the-relationship-between-b
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file (if needed for API keys, though HCP public data may not require them for the verified subset):
    ```bash
    echo "HCP_TOKEN=your_token_if_required" > .env
    ```

## Running the Pipeline

### 1. Data Download (with Verification)
```bash
python code/download.py
```
*Note: This script attempts to load from the verified URLs. It includes a content verification step. If the files do not contain the required fMRI time-series, the script will log "Data Gap: fMRI missing" and stop. It will NOT generate synthetic data for the main analysis.*

### 2. Preprocessing (CPU Mode - Requires Real Data)
```bash
python code/preprocess.py --n-subjects 10 --mode cpu
```
*Note: This step requires real NIfTI files. If they are missing, the step is skipped with a "Data Gap" error. Running this on 2 CPU/7GB RAM for >2 subjects may fail due to memory limits.*

### 3. Metric Computation
```bash
python code/metrics.py --window-size 30 --step-size 5 --atlas schaefer-200
```
*Note: Requires preprocessed data from Step 2. If Step 2 failed, this step is skipped.*

### 4. Statistical Analysis
```bash
python code/analysis.py --permutations 1000 --seed 42
```
*Note: Outputs `data/analysis_results.tsv` (TSV format) and `data/results/plots/`. If data is missing, no results are generated.*

### 5. Verification (Unit Tests Only)
Run the test suite to ensure code logic is correct (using synthetic data for logic validation only):
```bash
pytest tests/ -v
```

## Expected Outputs

- `data/analysis_results.tsv`: Correlation coefficients, p-values, and effect sizes (TSV format).
- `data/results/plots/scatter_dsst_vs_reconfig.png`: Visualization of the relationship (if analysis ran).
- `data/preprocess_log.txt`: Log of preprocessing steps and QC metrics (or "Data Gap" message).
- **If Data is Missing**: A clear "Data Gap" message in logs and no analysis results.

## Troubleshooting

- **Memory Error**: Reduce `--n-subjects` to 2 or lower. If this fails, the CI environment is insufficient for fMRIPrep; the run is marked as "Logic Validation Only".
- **Louvain Non-Convergence**: The script automatically retries with different seeds. If it fails after 3 tries, the subject is excluded.
- **Missing DSST**: Subjects without DSST scores are automatically excluded from correlation analysis.
- **Data Gap**: If the script reports "Data Gap: fMRI missing", no analysis can be performed. This is expected given the current verified sources.