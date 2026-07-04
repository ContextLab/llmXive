# Quickstart: The Effect of Priming on Prosocial Behavior in Online Communities

## Prerequisites
- Python 3.11+
- `pip`
- Access to HuggingFace datasets (internet connection required for download).

## Installation

1. **Clone the repository** and navigate to the project root.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `nltk`, `vaderSentiment`, `statsmodels`, `pandas`, `numpy`, `scikit-learn`, `datasets`.*

## Data Preparation
The pipeline automatically downloads the dataset from the verified HuggingFace source on first run.
- **Primary Source**: `pushshift/reddit` (via `datasets.load_dataset`).
- **Multi-subreddit Check**: The script will verify the presence of `r/AskReddit`, `r/relationships`, `r/socialscience`, `r/psychology`, `r/dataisbeautiful`.
- **Warning**: If the dataset does not contain all 5 subreddits, the script will abort. You may need to provide a verified multi-subreddit source URL.

## Running the Pipeline

Execute the pipeline in sequence:

1. **Ingest & Anonymize**:
   ```bash
   python code/01_ingest.py
   ```
   *Output*: `data/processed/anonymized.csv`

2. **Score & Validate**:
   ```bash
   python code/02_score.py
   ```
   *Output*: `data/processed/scored.csv`, `results/validation_report.json`

3. **Analyze & Report**:
   ```bash
   python code/03_analyze.py
   ```
   *Output*: `results/stats_report.json`, `results/sensitivity_report.json`, `results/boxplot.png`

## Validation (Human Annotation)
If you have a `gold_standard.csv` (≥3 raters):
1. Place it in `data/validation/`.
2. Run:
   ```bash
   python code/validation/run_validation.py
   ```
   *Output*: Cohen's Kappa score and `neg_score` Pearson r in `results/validation_report.json`.

## Troubleshooting
- **Dataset Error**: "Missing subreddits". Ensure the HuggingFace dataset used actually contains the 5 target subreddits.
- **Memory Error**: Reduce `TARGET_N` in `code/01_ingest.py` (though 10k should fit in 7GB RAM).
- **Singular Fit**: If `user_id` variance is near zero, the script automatically refits without it (FR-005b).

