# Quickstart Guide: The Influence of Emotional Contagion on Collective Decision-Making

This guide provides instructions for setting up and running the full research pipeline for PROJ-139.

## Prerequisites

- Python 3.11 or higher
- `pip` package manager
- Access to the required APIs (Pushshift, Reddit OAuth) or HuggingFace account for dataset access.

## Installation

1. Clone the repository and navigate to the project root.
2. Install the required dependencies:

```bash
pip install -r code/requirements.txt
```

Ensure you have the necessary environment variables set if you are using the Reddit API (see `code/config/settings.py` for details).

## Running the Pipeline

To execute the full analysis pipeline (data download, extraction, sentiment analysis, modeling, and reporting):

```bash
python code/analysis/run_pipeline.py --threads
```

### Pipeline Stages
The pipeline executes the following stages sequentially:
1. **Data Download**: Fetches raw thread data.
2. **Extraction**: Filters threads, extracts seed posts, and validates metadata.
3. **Validation**: Classifies ground truth availability and computes validation scores.
4. **Sentiment Analysis**: Applies VADER sentiment scoring.
5. **Metrics Computation**: Calculates emotional contagion indices and decision quality metrics.
6. **Modeling**: Fits GLMMs, performs sensitivity analysis, and computes correlations.
7. **Reporting**: Generates final reports (`docs/paper.md`, `docs/analysis_summary.md`).

## Expected Outputs

Upon successful completion, the following artifacts will be generated:

- **Raw Data**: `data/raw/reddit_threads.jsonl`
- **Processed Data**:
 - `data/processed/all_threads_classified.csv`
 - `data/processed/valid_threads.csv`
 - `data/processed/threads_with_seeds.csv`
 - `data/processed/thread_metrics.csv`
 - `data/processed/sensitivity_analysis.csv`
 - `data/processed/external_validation_correlation.csv`
- **State & Logs**:
 - `state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml` (Artifact checksums)
 - `state/sc_006_compliance_report.json`
 - `state/final_validation.json`
 - `state/reproducibility_report.json`
- **Reports**:
 - `docs/paper.md`
 - `docs/analysis_summary.md`

## Data Sources

This project relies on specific external data sources. The pipeline attempts to fetch data in the following order:

### 1. Primary Source: Pushshift API
- **Endpoint**: ` (or equivalent archival endpoint)
- **Method**: Direct HTTP GET requests with query parameters for subreddits and time ranges.
- **Notes**: This is the preferred source for historical Reddit data. If this endpoint is unavailable, the pipeline automatically attempts the fallbacks below.

### 2. Fallback 1: Reddit Official API
- **Method**: OAuth 2.0 flow.
- **Configuration**: Requires `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and `REDDIT_USER_AGENT` environment variables.
- **Endpoint**: `https://oauth.reddit.com/`
- **Notes**: Requires an active Reddit developer account. Rate limits apply.

### 3. Fallback 2: HuggingFace Archives (Verified)
- **Dataset ID**: `reddit-research/threads-2024`
- **Access Method**: Using the `datasets` library:
 ```python
 from datasets import load_dataset
 dataset = load_dataset('json', data_files={'train': 'hf://datasets/reddit-research/threads-2024/train.jsonl'})
 ```
- **Notes**: This is a static, verified snapshot of Reddit threads. It is used if live API access fails.
- **Verification**: Ensure you have internet access to fetch from the HuggingFace Hub.

### Data Fetching Policy
The `code/data/download.py` script implements a strict "fail-loud" policy. If all three sources (Pushshift, Reddit API, HuggingFace) fail, the script will raise a `RuntimeError` and halt the pipeline. **No synthetic or mock data will be generated.**

## Troubleshooting

- **Data Download Failure**: Check your internet connection and API key configurations. If using HuggingFace, ensure you are logged in (`huggingface-cli login`) if the dataset requires authentication.
- **Missing Dependencies**: Re-run `pip install -r code/requirements.txt`.
- **Pipeline Timeout**: If the pipeline exceeds the 6-hour limit (SC-005), check the `state/performance_log.json` for resource usage details.

## Reproducibility

To verify the reproducibility of results, run:

```bash
python code/analysis/verify_reproducibility.py
```

This will re-run the pipeline on the existing raw data (without re-downloading) and compare artifact checksums against the recorded values in `state/projects/...yaml`.