# Quickstart: Statistical Analysis of Publicly Available Election Poll Aggregates

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to a GitHub Actions runner (or local machine with similar specs).

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   git clone <repo-url>
   cd projects/PROJ-206-statistical-analysis-of-publicly-availab
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
   *Note: `requirements.txt` pins all versions to ensure reproducibility.*

## Running the Pipeline

### Step 1: Data Download
Download raw data from verified sources.
```bash
python src/data/download.py
```
*This script fetches data from FiveThirtyEight. RealClearPolitics (RCP) is explicitly excluded from the scope due to the lack of a verified source URL. No runtime fallback or scraping is attempted.*

### Step 2: Data Harmonization
Clean and bin the data.
```bash
python src/data/harmonize.py
```
*Output: `data/processed/poll_data_cleaned.csv`*

### Step 3: Run Aggregation Models
Execute the three forecasting methods.
```bash
python src/main.py --run-all
```
*This runs Simple, Weighted, and Bayesian models. Bayesian may take several hours depending on data volume.*

### Step 4: Evaluation
Generate metrics and plots.
```bash
python src/evaluation/metrics.py
```
*Output: `data/processed/evaluation_results.json` and `figures/`*

## Validation

Run the contract tests to ensure data integrity:
```bash
pytest tests/contract/
```

## Troubleshooting

- **Bayesian Convergence**: If R-hat > 1.05, increase `tune` and `draws` in `src/models/bayesian.py` or reduce data volume.
- **Memory Error**: If RAM usage exceeds a predefined high threshold, the script will automatically sample data. Check logs for "Sampling enabled" messages.
- **Missing Data**: If a specific year is missing, the system will skip it and log a warning.