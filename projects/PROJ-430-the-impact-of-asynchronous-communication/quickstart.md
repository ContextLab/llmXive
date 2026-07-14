# Quickstart Guide

## Prerequisites
- Python 3.11+
- GitHub API token (set as `GITHUB_TOKEN` environment variable)

## Installation
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Pipeline
1. Configure `code/config.py` with your GitHub token and sample parameters.
2. Run data ingestion:
 ```bash
 python code/data_ingestion.py
 ```
3. Run metrics calculation:
 ```bash
 python code/metrics.py
 ```
4. Run sentiment analysis:
 ```bash
 python code/sentiment.py
 ```
5. Run statistical analysis and visualization:
 ```bash
 python code/analysis.py
 ```

## Output
Results will be saved in:
- `data/derived/`: Processed metrics and features
- `data/validation/`: Manual ground truth and validation results
- `figures/`: Generated plots and visualizations
