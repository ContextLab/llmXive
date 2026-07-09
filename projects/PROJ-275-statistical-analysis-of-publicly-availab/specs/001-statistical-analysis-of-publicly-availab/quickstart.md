# Quickstart: Statistical Analysis of Publicly Available Movie Review Sentiment and Box Office Revenue

## Prerequisites

- Python 3.11+
- `git`
- Access to HuggingFace (for dataset download)

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` includes `nltk`, `fuzzywuzzy`, and their data packages.*

## Data Download

The pipeline automatically downloads the verified datasets on first run. Alternatively, run:
```bash
python code/data_ingestion.py --download-only
```
This will fetch:
- TMDB 5000 (Filtered) from HuggingFace.
- IMDb Reviews from HuggingFace.
Data will be stored in `data/raw/`.

**Note**: The pipeline includes a "Verified Accuracy Gate" that checks dataset URLs and schemas before processing.

## Running the Analysis

Execute the full pipeline:
```bash
python code/main.py
```

This will:
1. Ingest and merge data (with fuzzy title alignment).
2. Compute sentiment scores (VADER).
3. Calculate Lagged Correlation Profiles and Decay Rates.
4. Generate plots and summary tables.
5. Save results to `results/`.
6. Validate outputs against `contracts/*.schema.yaml`.

## Output

- `results/summary_tables.csv`: Genre-stratified lag and decay metrics.
- `results/plots/`: Lag-decay visualizations.
- `results/report.md`: Human-readable summary.

## Troubleshooting

- **Memory Error**: If running out of RAM, reduce the bootstrap resamples in `code/lag_decay_analysis.py` (default 1000).
- **Dataset Mismatch**: If the IMDb dataset lacks `movie_title` or alignment fails, the script will halt with a clear error message indicating the data gap.
- **Validation Error**: If outputs do not match `contracts/*.schema.yaml`, the pipeline will fail. Check the `contracts/` directory for the expected schema.