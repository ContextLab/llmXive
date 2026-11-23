# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Sensorimotor Performance

## Prerequisites

- **Python**: 3.11+
- **System Tools**: `git`, `curl`, `wget`
- **Dependencies**: `requirements.txt` (pinned versions)
- **HCP Access**: Valid HCP credentials required for behavioral data download. For fMRI data, an OpenNeuro account is sufficient for programmatic access.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-284-investigating-the-relationship-between-b
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

The pipeline is executed via the main script `code/main_pipeline.py`.

### Step 1: Data Download
```bash
python code/download/fetch_openneuro.py --subjects 50 --output data/raw
python code/download/fetch_hcp_behavioral.py --subjects 50 --output data/raw
```
*Note: This uses the official OpenNeuro API (`openneuro-py`) and HCP ConnectomeDB. It streams data to avoid memory issues.*

### Step 2: Preprocessing (QC Only)
```bash
python code/preprocess/run_qc_only.py --input data/raw --output data/processed
```
*This step calculates tSNR and FD. Subjects failing QC are logged and excluded. No re-preprocessing is performed.*

### Step 3: Analysis
```bash
python code/main_pipeline.py --batch-size 5 --mode cpu
```
*This runs connectivity, metric extraction, PCA (2 components), correlation, and visualization in a single pass. `--batch-size` can be adjusted if memory errors occur.*

### Step 4: Generate Report
```bash
python code/viz/generate_report.py --input data/analysis/correlation_results.csv --output reports/summary.md
```

## Verification

To verify the pipeline integrity:
1. **Check Checksums**:
   ```bash
   python code/utils/checksums.py verify
   ```
2. **Run Contract Tests**:
   ```bash
   pytest tests/contract/
   ```
3. **Check Output Files**:
   Ensure the following files exist in `data/analysis/`:
   - `pca_loadings.csv` (2 components)
   - `factor_scores.csv` (2 scores per subject)
   - `full_metrics.csv` (merged metrics + PCA)
   - `correlation_results.csv` (contains columns: `metric`, `r`, `p`, `q`, `significant`)

## Troubleshooting

- **Memory Error**: If the script crashes with `MemoryError`, reduce `--batch-size` to 2 or 1. The pipeline will automatically retry with the smaller batch.
- **Missing Data**: If a subject is missing behavioral data, it is skipped and logged. The final report will reflect the reduced N.
- **GPU Fallback**: If running on a local machine with a GPU and memory errors persist, set `export CUDA_VISIBLE_DEVICES=0` and run with `--mode gpu`.
