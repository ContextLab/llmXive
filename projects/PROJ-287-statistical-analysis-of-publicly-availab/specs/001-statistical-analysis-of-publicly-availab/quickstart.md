# Quickstart: Statistical Analysis of Topic Drift

## Prerequisites

-   Python 3.11+
-   `pip` and `venv`
-   Internet access (for dataset download and API calls)

## 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**`requirements.txt`** (Pinned versions for reproducibility):
```text
scikit-learn==1.4.0
scipy==1.12.0
pandas==2.2.0
matplotlib==3.8.2
nltk==3.8.1
spacy==3.7.2
requests==2.31.0
pyyaml==6.0.1
pytest==8.0.0
```

*Note: Download NLTK data:*
```python
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4')"
```

## 2. Download Data

The script `src/data/fetch/download_data.py` handles fetching.

```bash
# Run the download script
python src/data/fetch/download_data.py
```

This will:
1.  Fetch PubMed data from the verified HuggingFace URL.
2.  Attempt to fetch arXiv data via API (if API keys are configured in `.env`).
3.  Save raw JSONL files to `data/raw/`.

## 3. Run Analysis Pipeline

Execute the main pipeline:

```bash
python src/main.py
```

This will:
1.  Preprocess data (tokenize, lemmatize, filter <20 tokens).
2.  Split into 5-year windows.
3.  Fit LDA models (k=10) per window.
4.  Validate coherence (>=0.4).
5.  Compute JS divergence and permutation tests.
6.  Generate figures and the reproducibility manifest.

## 4. Verify Results

Check the `results/` directory:
-   `results/figures/topic_trend.png`: Line plot of topic proportions over time.
-   `results/figures/divergence_plot.png`: Divergence values with confidence intervals.
-   `results/manifest.json`: Full reproducibility record.
-   `results/divergence_stats.csv`: Statistical test results.

## 5. Run Tests

```bash
pytest tests/
```

Ensure all unit and integration tests pass before committing.
