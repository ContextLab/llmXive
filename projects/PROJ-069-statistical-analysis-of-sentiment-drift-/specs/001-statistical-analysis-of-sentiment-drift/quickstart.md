# Quickstart: Sentiment Drift Analysis

## Prerequisites
1. **GitHub Actions runner** (CPU‑only) **or** a local Linux/macOS environment with ≥ 2 CPU cores, ≥ 7 GB RAM, and Python 3.11.  
2. **API credentials**  
   - **FRED API key** – obtain from <https://fred.stlouisfed.org/> and set `FRED_API_KEY`.  
   - **(Optional) HuggingFace token** – set `HF_TOKEN` if you encounter rate limits.  

## Setup Steps
```bash
# 1. Clone the repository
git clone 
cd sentiment-drift

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins all versions

# 3. Create a .env file (required for API access)
cat <<EOF > .env
FRED_API_KEY=YOUR_FRED_KEY_HERE
HF_TOKEN=YOUR_HF_TOKEN_HERE   # optional
EOF

# 4. Download NBER recession dates (required before modeling)
python -m code.ingest.download_nber

# 5. Run the ingestion pipeline
python -m code.ingest.fetch_fred
python -m code.ingest.fetch_sentiment   # only works if a verified sentiment URL has been added
python -m code.ingest.sentiment_extraction
python -m code.ingest.merge_align

# 6. Validate intermediate files
python -m code.ingest.validate_schema   # validates aligned_monthly.csv
python -m code.ingest.generate_merged    # creates and validates merged_timeseries.csv

# 7. Execute the analysis notebook (produces all artifacts)
jupyter nbconvert --to notebook --execute \
    code/notebook/sentiment_drift_analysis.ipynb \
    --output outputs/sentiment_drift_analysis.ipynb

# 8. Inspect results
#   - Aligned data (SSoT): data/processed/aligned_quarterly.csv
#   - Model summary: outputs/model_results.json
#   - Figures: outputs/figures/*.png
```

### What to Expect
- The pipeline aborts with a clear error if any required **verified** dataset is missing, if the placeholder sentiment dataset has not been added to the verified list, or if API keys are not supplied.  
- All random processes are seeded (`np.random.seed(42)`), guaranteeing reproducibility (Constitution Principle I).  
- The final notebook contains narrative, tables, and figures ready for inclusion in the manuscript.

---


