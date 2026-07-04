# Quickstart: The Impact of Social Media "Doomscrolling" on Anticipatory Anxiety

## Prerequisites

- Python 3.11+
- Git
- (Optional) GDELT API credentials (if using live API)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-487-the-impact-of-social-media-doomscrolling
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Fetching (Manual Step for CI)

Since GDELT and Google Trends APIs may require manual setup or have rate limits on free tiers:

1. **Option A (Recommended for CI)**: Download sample CSVs from the GDELT archive and Google Trends export and place them in `data/raw/`.
   - `gdelt_sentiment.csv`: Columns `date`, `AVGTONE`.
   - `trends_anxiety.csv`: Columns `date`, `anticipatory_anxiety`.

2. **Option B (Live Fetch)**: Run the fetch script (requires API keys in env vars):
   ```bash
   export GDELT_API_KEY=your_key
   export GOOGLE_TRENDS_API_KEY=your_key
   python code/fetch_data.py --start 2020-01-01 --end 2023-12-31
   ```

## Running the Pipeline

Execute the full pipeline:

```bash
python code/preprocess.py
python code/analysis.py
```

## Expected Output

- `data/processed/aligned_timeseries.csv`: Cleaned, normalized data.
- `output/results/analysis_results.json`: Correlation and Granger results.
- `output/reports/summary.pdf`: Visualizations and statistical summary.

## Validation

Run tests to ensure data integrity:

```bash
pytest tests/
```
