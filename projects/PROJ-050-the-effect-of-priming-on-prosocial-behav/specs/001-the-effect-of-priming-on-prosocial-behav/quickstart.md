# Quickstart: The Effect of Priming on Prosocial Behavior in Online Communities

## Prerequisites
- Python 3.11+
- Access to the `pushshift/reddit` dataset on HuggingFace (verified multi-subreddit source).
- A `gold_standard.csv` file with ≥ 3 raters (if validation is required).

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note*: `requirements.txt` pins `pandas`, `nltk`, `vaderSentiment`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `pytest`, `pydantic`.

## Dataset Setup
**CRITICAL**: The study uses the `pushshift/reddit` dataset from HuggingFace, which contains all 5 required subreddits.

1. Ensure you have access to HuggingFace (login if required).
2. Update `code/config.py` with the correct dataset path or URL for `pushshift/reddit`.
3. The pipeline will automatically filter for `r/AskReddit`, `r/relationships`, `r/socialscience`, `r/psychology`, `r/dataisbeautiful`.

## Running the Pipeline

### 1. Run the Full Pipeline
Execute the main script to ingest, score, analyze, and visualize:
```bash
python code/main.py --output-dir output/
```
*Note*: The pipeline will automatically fetch and filter data from `pushshift/reddit`.

### 2. Validation (Optional but Recommended)
If you have a `gold_standard.csv`:
```bash
python code/main.py --validate --gold-standard data/validation/gold_standard.csv
```
This will compute Cohen's Kappa and generate a validation report in `output/validation/`.

### 3. Power Analysis
Run a standalone power analysis check:
```bash
python code/main.py --power-analysis
```

## Outputs
- **`output/results.json`**: Statistical results (p-values, coefficients, CI) from the GLMM.
- **`output/figures/boxplot.png`**: Visualization of prosocial action counts.
- **`output/logs/pipeline.log`**: Detailed execution logs, including negation exclusions and power warnings.
- **`data/processed/cleaned_data.parquet`**: Anonymized, scored dataset.

## Troubleshooting
- **Error: "Missing subreddits"**: The dataset does not contain all 5 required subreddits. Check your data source (should be `pushshift/reddit`).
- **Error: "Insufficient samples"**: A limited number of comments in a group. The pipeline will abort.
- **Runtime > 4 hours**: Reduce `TARGET_N` in `code/config.py` or optimize the bootstrap iterations.
- **Statistical Warning**: If the model uses a Gaussian family instead of Negative Binomial, check the `glmm.py` implementation. The plan mandates Negative Binomial for count data.