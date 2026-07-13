# Quickstart: Lottery Draw Integrity and Anomaly Detection

## Prerequisites
- Python 3.11+
- `pip`
- Access to the project repository.

## 1. Environment Setup
```bash
cd projects/PROJ-095-statistical-analysis-of-lottery-number-f/code/
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Data Preparation
The system expects raw data in `data/raw/`. If not present, run the ingestion script (which downloads from verified sources):
```bash
python -m ingestion --download
```
*Note: This will fetch data from verified sources listed in `research.md` and save to `data/raw/lottery_history.csv`.*

## 3. Running the Analysis
Execute the full pipeline (Ingestion -> Metrics -> Correlation -> Validation):
```bash
python -m main
```

## 4. Outputs
Upon completion, the following files will be generated:
- `data/processed/draws_metrics.csv`: Raw draws with calculated `birthday_cluster_ratio` and `consecutive_pattern_count`.
- `data/processed/correlation_results.json`: Statistical findings, CIs, and sensitivity analysis.
- `reports/summary.txt`: Human-readable summary of findings.

## 5. Verification
To verify the `birthday_cluster_ratio` calculation (SC-001):
```bash
pytest tests/unit/test_metrics.py::test_birthday_ratio_reference
```

## 6. Troubleshooting
- **Memory Error**: Ensure the dataset is not > 500MB. If so, the script automatically samples.
- **Missing Data**: Check `data/raw/` for the source file. If `total_sales` is missing for > 20% of rows, the correlation step will be skipped for sales-dependent metrics.