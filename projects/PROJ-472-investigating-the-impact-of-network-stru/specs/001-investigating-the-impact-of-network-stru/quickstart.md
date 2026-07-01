# Quickstart: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

## Prerequisites

- Python 3.11+
- **System Dependency**: `MRtrix3` installed in the system PATH (e.g., via `apt install mrtrix3` or `conda install -c conda-forge mrtrix3`).
- `git`
- Access to OpenNeuro (no token required for public datasets, but rate limits apply).

## Installation

1.  **Clone and Setup Environment**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-472-investigating-the-impact-of-network-stru
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import mne; import networkx; import powerlaw; import mrtrix3; print('Dependencies OK')"
    ```
    *Note: `mrtrix3` is a system tool; ensure it is in PATH.*

## Running the Pipeline

The pipeline is executed via a single entry point script.

```bash
# Run the full pipeline (Download -> Preprocess -> Metrics -> Analysis)
# Note: This will take approximately several hours on a local machine or GitHub Actions runner.
python code/main.py --subjects 50 --thresholds 0.70,0.75,0.80
```

### Step-by-Step Execution (Optional)

1.  **Download Data**:
    ```bash
    python code/data/download.py --dataset ds004230,ds004231
    ```
    *This downloads raw data to `data/raw/` and generates checksums.*

2.  **Preprocess dMRI**:
    ```bash
    python code/data/preprocess_dMRI.py
    ```
    *Generates connectivity matrices in `data/processed/connectomes/`.*

3.  **Preprocess EEG**:
    ```bash
    python code/data/preprocess_EEG.py
    ```
    *Generates cleaned EEG files in `data/processed/eeg_clean/`.*

4.  **Compute Metrics**:
    ```bash
    python code/metrics/network.py
    python code/metrics/avalanche.py
    ```
    *Outputs CSVs in `data/processed/metrics/`.*

5.  **Run Analysis**:
    ```bash
    python code/analysis/correlation.py
    python code/analysis/robustness.py
    ```
    *Outputs final results in `data/processed/results/`.*

## Expected Outputs

- `data/processed/metrics/network_metrics.csv`: Structural metrics per subject.
- `data/processed/metrics/avalanche_metrics.csv`: Avalanche exponents per subject.
- `data/processed/results/correlation_results.csv`: Spearman correlations, p-values, VIF, Bootstrap CI.
- `data/processed/results/sensitivity_analysis.csv`: Correlation stability across thresholds and bin sizes.

## Troubleshooting

- **Memory Error**: Reduce the number of streamlines in `code/config.py` (default 50k -> 20k).
- **OpenNeuro Timeout**: The download script includes retries. If it fails, check network connectivity.
- **Power-Law Convergence**: If `powerlaw` fails for a subject, that subject is automatically excluded. Check `data/processed/logs/avalanche_logs.txt` for details.
- **Disk Space**: Ensure raw files are deleted after preprocessing. If space is low, reduce the number of subjects processed.