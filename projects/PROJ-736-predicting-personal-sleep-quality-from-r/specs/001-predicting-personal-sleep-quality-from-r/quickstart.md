# Quickstart: Predicting Personal Sleep Quality from Resting‑State fMRI Connectivity

## Prerequisites

- **Python**: 3.11+
- **Dependencies**: Install via `pip install -r requirements.txt`.
- **HCP Access**: You must have an HCP account and be approved for the 1200 Subjects Release.
  - *Note*: If you do not have credentials, the pipeline will fail at the download step. You must manually download the data and place it in `data/raw/`.

## Installation

1. **Clone the repository** (assuming standard project structure).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `code/config.py` to set:
- `HCP_DATA_PATH`: Path to raw HCP data (if downloaded manually).
- `SLEEP_SCORE_THRESHOLD`: Minimum valid sleep score (if any).
- `VARIANCE_THRESHOLD`: Default 0.01.
- `PCA_VARIANCE`: Default 0.90.
- `N_PERMUTATIONS`: Default 1000.
- `N_BOOTSTRAP`: Default 1000.
- `SEED`: Default 42.

## Execution

### Step 1: Download Data (Optional)
If you have HCP credentials, run:
```bash
python code/data/download_hcp.py
```
*If manual download*: Place `hcp_1200` folder in `data/raw/`.

### Step 2: Run the Full Pipeline
Execute the main orchestration script:
```bash
python code/main.py
```
This will:
1. Download/verify data.
2. Preprocess fMRI and compute connectivity.
3. Train the Elastic Net model with nested CV.
4. Run permutation tests and bootstrap.
5. Generate visualizations.
6. Save `ResultReport.json`.

### Step 3: Inspect Results
- **Metrics**: View `data/results/ResultReport.json`.
- **Visualization**: Open `data/results/brain_connectome.png` (or `.svg`).
- **Logs**: Check `data/logs/pipeline.log` for detailed steps.

## Testing

Run the test suite to verify contract compliance:
```bash
pytest tests/ -v
```
This includes:
- Unit tests for preprocessing steps.
- Contract tests validating output schemas.
- Integration test (sample size reduced) for end-to-end flow.

## Troubleshooting

- **Memory Error**: Reduce `PCA_VARIANCE` to 0.85 or lower `N_PERMUTATIONS`.
- **No Sleep Data**: Check `data/raw/hcp_1200/behavioral/sleep.csv` for required columns.
- **Time Out**: If running on GitHub Actions, ensure the job is not exceeding 5 hours. Reduce permutation count in `config.py`.
