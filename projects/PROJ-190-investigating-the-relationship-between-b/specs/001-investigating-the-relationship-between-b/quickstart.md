# Quickstart: Brain Network Efficiency and Fluid Intelligence

## Prerequisites

- Python 3.11+
- Access to HCP -subject release (registration required at https://db.humanconnectome.org/)
- Sufficient disk space (for raw + processed data)
- Sufficient RAM (for processing; may require sampling)

## Installation

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-190-investigating-the-relationship-between-b
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

4. **Download HCP Data**:
   - Follow HCP access instructions to download rs-fMRI and behavioral data.
   - Place raw data in `data/raw/`.
   - Ensure `data/raw/` contains:
     - `sub-XXXXX/` folders with `rfMRI_REST1_LR.nii.gz`, `rfMRI_REST1_RL.nii.gz`, etc.
     - `BehavioralData.xlsx` or equivalent with fluid intelligence scores.

## Running the Pipeline

### 1. Preprocessing
```bash
python code/main.py --step preprocess --subjects all
```
- Downloads/loads data, applies nuisance regression + band-pass filter.
- Excludes subjects with missing scores or FD > 0.5 mm.
- Outputs: `data/processed/time_series/`.

### 2. Compute Graph Metrics
```bash
python code/main.py --step graph --atlas Schaefer_200 --density 0.20
```
- Parcellates brains, computes connectivity matrices, calculates efficiency metrics.
- Outputs: `data/results/efficiency_metrics.csv`.

### 3. Statistical Analysis
```bash
python code/main.py --step stats --permutations 1000
```
- Runs correlation, regression, permutation testing.
- Adapts permutation count if time > 5.5h.
- Outputs: `data/results/statistical_results.csv`.

### 4. Generate Report
```bash
python code/main.py --step report
```
- Creates figures, tables, and text report.
- Includes mandatory phrase and citations.
- Outputs: `paper/`.

## Verification

- **Check Excluded Subjects**:
  ```bash
  cat logs/exclusions.log
  ```
- **Verify Efficiency Metrics**:
  ```bash
  python code/utils/validate_metrics.py
  ```
- **Run Unit Tests**:
  ```bash
  pytest tests/unit/
  ```

## Troubleshooting

- **HCP Access Denied**: Ensure credentials are set; check network; retry with `--retry 1`.
- **Memory Error**: Reduce subject count via `--subjects sample:500`.
- **Runtime Exceeded**: Permutation count will auto-reduce; check `logs/runtime.log`.
- **Missing Atlas**: Download Schaefer/Yeo atlases to `data/atlases/`.

## Notes

- **Reproducibility**: Random seeds are pinned in `code/config.py`.
- **Data Hygiene**: All data files are checksummed; raw data is preserved.
- **Causation**: Report includes mandatory phrase: "Findings are associational and do not imply causation due to the observational study design."
