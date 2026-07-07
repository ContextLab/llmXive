# Quickstart: The Impact of Incidental Music on Autobiographical Memory Retrieval

## Prerequisites

- Python 3.11+
- Access to GitHub Actions (for CI) or a local Linux environment.
- Internet access to download datasets from Hugging Face.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-200-the-impact-of-incidental-music-on-autobi
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### 1. Download Data
The script will fetch data from the verified URLs defined in `config.py`.
```bash
python code/main.py --step download
```
*Note: If `birth_year` is missing in the MSD source, the system will log a warning and prepare for the Global Exposure fallback.*

### 2. Process & Match
Run the full ingestion, matching, and aggregation pipeline.
```bash
python code/main.py --step process
```
*Outputs: `data/processed/aggregated_analysis.parquet`*

### 3. Run Analysis
Fit the mixed-effects model and run sensitivity/permutation tests.
```bash
python code/main.py --step analyze
```
*Outputs: `data/final/results_summary.csv`, `data/final/diagnostics.json`*

## Verification

To verify the pipeline on a small subset (Unit Test):
```bash
pytest tests/unit/ -v
```

To run the full integration test (requires full dataset):
```bash
pytest tests/integration/ -v
```

## Expected Outputs

- **`data/processed/aggregated_analysis.parquet`**: The final dataset ready for modeling.
- **`data/final/results_summary.csv`**: Regression coefficients, p-values, and VIF scores.
- **`data/final/diagnostics.json`**: Sensitivity analysis results and permutation test statistics.

## Troubleshooting

- **Missing `birth_year`**: If the log indicates >50% missing, the system automatically switches to the Global Exposure metric. Check `logs/pipeline.log` for details.
- **Low Match Rate**: If <80% of cues match, check the `match_distance` distribution in the output CSV. You may need to adjust the Levenshtein threshold in `config.py` (though 4 is the spec default).
- **Memory Error**: If RAM exceeds 7 GB, reduce the dataset subset size in `config.py` or enable chunked processing.
