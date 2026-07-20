# Quickstart: The Impact of Simulated Social Feedback on Self-Esteem Fluctuations

## Prerequisites
- Python 3.11+
- pip
- Sufficient free disk space (for dataset and cache)
- Internet connection (for dataset download and model weights)

## 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Data Download (Automated)

The ingestion script (`code/01_ingest.py`) automatically downloads the `pushshift_reddit` dataset.
To run manually:

```bash
cd code
python 01_ingest.py
```
*Output*: `data/raw/pushshift_reddit.parquet` and `data/processed/interactions_sentiment.csv`

## 3. Running the Pipeline

Execute the full pipeline in sequence:

```bash
# Step 1: Ingest & Sentiment
python 01_ingest.py

# Step 2: Calculate Metrics & Self-Esteem Indicator
python 02_metrics.py

# Step 3: Run Analysis & Sensitivity
python 03_analysis.py

# Step 4: Generate Report
python 04_report.py
```

## 4. Verification

Check the output report:
-   `output/regression_report.md`
-   `output/sensitivity_analysis.md`

Verify that:
1.  `SC-001`: >95% records processed.
2.  `SC-002`: >90% users have valid volatility metrics.
3.  `SC-005`: VIF < 5.0 (check logs for "VIF OK").
4.  `Methodology Check`: The report confirms `mean_post_valence` was included as a control variable.

## 5. Troubleshooting

-   **Memory Error**: Reduce `BATCH_SIZE` in `code/utils/config.py`.
-   **Dataset Missing**: Ensure `PUSHSHIFT_DATASET_ID` in `config.py` matches the verified source (`pushshift_reddit`).
-   **Model Load Error**: Ensure `transformers` and `torch` are installed.