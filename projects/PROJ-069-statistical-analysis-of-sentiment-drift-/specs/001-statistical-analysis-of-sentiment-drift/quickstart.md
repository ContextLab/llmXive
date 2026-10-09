# Quickstart: Sentiment Drift Analysis

## Prerequisites
1. **GitHub Actions runner** (CPU‑only) or a local Linux environment with ≥ 2 CPU cores and ≥ 7 GB RAM.
2. **Python 3.11** installed.
3. **API credentials**:
   - FRED API key → set `FRED_API_KEY` in a `.env` file.
   - (Optional) HuggingFace token → set `HF_TOKEN` if needed for private datasets.

## Step‑by‑Step

```bash
# 1. Clone the repository
git clone https://github.com/your-org/sentiment-drift.git
cd sentiment-drift

# 2. Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins all versions

# 3. Populate .env (example)
cat <<EOF > .env
FRED_API_KEY=YOUR_FRED_KEY_HERE
HF_TOKEN=YOUR_HF_TOKEN_HERE   # optional
EOF

# 4. Download NBER recession dates (required before modeling)
python -m code.ingest.download_nber

# 5. Run data ingestion
python -m code.ingest.fetch_fred
python -m code.ingest.fetch_sentiment   # uses verified sentiment140 dataset
python -m code.ingest.merge_align

# 6. Execute the full analysis notebook
jupyter nbconvert --to notebook --execute \
    code/notebook/sentiment_drift_analysis.ipynb \
    --output outputs/sentiment_drift_analysis.ipynb

# 7. Inspect results
#   - Aligned data: data/processed/aligned_quarterly.csv
#   - Model summary: outputs/model_results.json
#   - Figures: outputs/figures/*.png
```

### What to Expect
- The pipeline aborts with a clear error if the `sentiment140` dataset cannot be fetched.
- All random processes are seeded (`seed=42`), so repeated runs produce identical outputs.
- The final notebook contains narrative, tables, and figures ready for inclusion in the paper.

---

