# Quickstart: Flight Delay Distribution Analysis

## Prerequisites
- Python 3.11+
- `pip`
- Access to the verified dataset URL (internet connection required for download).

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The entire analysis is orchestrated by `code/src/main.py`.

```bash
cd code
python src/main.py --year 2022
```

### Arguments
- `--year`: Target year for BTS data (default: 2022).

### Expected Output
1. **Console**: Progress logs, summary statistics (mean delay, N records), retention rate, model ranking, and tail validity status.
2. **Files**:
   - `data/processed/delays_cleaned.parquet`
   - `output/results.json`
   - `output/plots/loglog_survival.png`
   - `output/plots/qq_plot_best_model.png`
   - `output/plots/hill_stability.png`
   - `state/artifact_hashes.json` (Updated with new hashes)

## Verification
To verify the pipeline without re-downloading (if data is cached):
```bash
python -m pytest tests/
```

## Troubleshooting
- **Memory Error**: If RAM usage exceeds 7GB, ensure no other heavy processes are running. The pipeline is optimized for 7GB; if the dataset is larger than expected (e.g., full 2022+2023 combined), reduce the year scope.
- **Download Failed**: Check internet connection. The dataset is hosted on HuggingFace; ensure your network allows access to `huggingface.co`. **Note**: If the full-year verified URL is unavailable, the pipeline will exit with an error to comply with data integrity rules. No override arguments are available.
- **Tail Validity Failed**: If no models pass the Tail Validity Gate, the report will indicate "No Heavy-Tail Model Found" rather than forcing a fit.