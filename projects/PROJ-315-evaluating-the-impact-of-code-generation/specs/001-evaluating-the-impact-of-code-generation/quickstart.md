# Quickstart: Evaluating the Impact of Code Generation on Code Review Quality

## Prerequisites

- Python 3.11+
- 7 GB+ available RAM
- Internet connection (for dataset download)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `pandas`, `scikit-learn`, `scipy`, `textblob`, `radon`, `lizard`, `datasets`, `seaborn`.*

4.  **Download NLTK data** (required for `textblob`):
    ```bash
    python -m textblob.download_corpora
    ```

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py
```

This command will:
1.  Download the `prs-v2-sample` dataset.
2.  Preprocess data and compute metrics.
3.  Classify PRs as LLM/Human.
4.  Run statistical tests (Mann-Whitney U) with corrections.
5.  Generate visualizations and the final report.

### Output Artifacts

- `data/processed/analysis_ready.csv`: Cleaned dataset.
- `reports/figures/`: Boxplots and sensitivity analysis charts.
- `reports/summary.html`: Full statistical report.

## Troubleshooting

- **Memory Error**: If the process exceeds 7 GB RAM, ensure no other heavy applications are running. The pipeline is designed to process in chunks.
- **Dataset Missing**: If the download fails, check your internet connection. The script retries automatically.
- **Heuristic Accuracy Low**: If the manual audit fails (<70%), the script will halt and print "Insufficient Heuristic Accuracy". Review `code/labeling/classify.py` to adjust keywords.
