# Quickstart: The Impact of Parasocial Relationships with AI Companions on Loneliness

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution) or a local environment with 7 GB+ RAM.

## Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd projects/PROJ-426-the-impact-of-parasocial-relationships-w
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
   *Note: `requirements.txt` pins `statsmodels`, `pandas`, `scikit-learn`, `datasets`, `requests`.*

## Running the Pipeline

### 1. Data Ingestion & Matching
Run the main pipeline script to download data, match users, and engineer features.
```bash
python src/main.py --mode ingest_and_match
```
- **Output**: `data/processed/matched_users.parquet`
- **Logs**: `logs/ingest.log` (includes retry attempts and match rates).

### 2. Model Fitting & Bootstrapping
Execute the statistical analysis.
```bash
python src/main.py --mode fit_model
```
- **Output**: `data/results/model_summary.json`
- **Note**: This step may take up to 6 hours on a CPU-only runner.

### 3. Validation
Run the contract tests to ensure data integrity.
```bash
pytest tests/contract/
```

## Expected Outputs

- **Match Rate**: ≥80% of users in the loneliness dataset should have matching Pushshift logs.
- **Model Convergence**: The LMM should converge without errors.
- **Bootstrap CIs**: 95% confidence intervals for all fixed effects.

## Troubleshooting

- **"Data Linkage Impossible"**: The Zenodo dataset DOI is invalid or the dataset is missing required columns (`username`, `baseline_text`).
- **"Power Insufficient"**: A limited number of matched users were found.
- **"Lexicon Missing"**: The ECAR Lexicon file could not be loaded from the verified URL.
