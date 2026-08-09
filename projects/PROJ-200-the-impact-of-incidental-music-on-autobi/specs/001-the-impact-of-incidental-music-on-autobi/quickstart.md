# Quickstart: The Impact of Incidental Music on Autobiographical Memory Retrieval

## Prerequisites

- Python 3.11+
- `pip` or `conda`

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-200-the-impact-of-incidental-music-on-autobi
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

### 1. Download Data
Fetch the MSD track metadata (streamed) and generate simulated AMT data.
```bash
python code/main.py --step download
```
*Output*: `data/raw/msd_tracks.jsonl`, `data/simulated_amt_data.parquet` (generated).

### 2. Ingest & Aggregate
Parse data, match cues, calculate exposure ratios, and filter.
```bash
python code/main.py --step ingest
```
*Output*: `data/processed/ingested_cohort.parquet`, `data/processed/user_track_pairs.parquet`.

### 3. Run Analysis
Fit the LMM, run sensitivity analysis, and perform permutation tests.
```bash
python code/main.py --step analyze
```
*Output*: `data/final/regression_summary.csv`, `data/final/sensitivity_analysis.csv`, `data/final/permutation_results.csv`, `data/final/plots/`.

### 4. Update State
Verify checksums and update `state.yaml`.
```bash
python code/main.py --step verify
```

## Full Run (Single Command)
To run the entire pipeline from scratch:
```bash
python code/main.py --full-run
```

## Expected Outputs

- `data/processed/user_track_pairs.parquet`: The core analysis dataset.
- `data/final/regression_summary.csv`: Primary results (coefficient for `logit_ratio`).
- `data/final/plots/residuals.png`: Diagnostic plot.
- `state.yaml`: Updated with artifact hashes.

## Troubleshooting

- **Missing Birth Years**: If >50% of birth years are missing, the pipeline will log a warning and use the "Global Exposure" fallback for sensitivity analysis only.
- **Low Match Rate**: If match rate < 80%, a warning is logged, but the pipeline proceeds.
- **Memory Error**: Ensure `streaming=True` is used in `datasets` (handled automatically by `download.py`).
- **Ratio Instability**: Users with `total_listens < 3` are excluded from the primary analysis.
- **Missing Output Files**: If `data/processed/*.parquet` files are missing, ensure the `ingest` step completed successfully. The pipeline validates their existence before analysis.
