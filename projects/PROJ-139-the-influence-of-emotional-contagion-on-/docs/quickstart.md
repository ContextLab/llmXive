# Quickstart Guide: The Influence of Emotional Contagion on Collective Decision-Making

## Prerequisites

- Python 3.11 or higher
- `pip` package manager
- Access to the internet (for data fetching)
- (Optional) Reddit API credentials (for primary data source fallback)

## 1. Environment Setup

### Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r code/requirements.txt
```

## 2. Configuration

The project uses a JSON configuration file or environment variables to manage API keys and paths.

### Option A: Environment Variables (Recommended)
Set the following environment variables before running the pipeline:
```bash
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export REDDIT_USER_AGENT="your_user_agent"
```

### Option B: Configuration File
Create a file named `config.json` in the project root (or specify a custom path via `--config`):
```json
{
 "api_keys": {
 "reddit_client_id": "your_client_id",
 "reddit_client_secret": "your_client_secret",
 "reddit_user_agent": "your_user_agent"
 },
 "dataset_paths": {
 "raw_data_dir": "data/raw",
 "processed_data_dir": "data/processed",
 "state_dir": "state",
 "figures_dir": "figures"
 }
}
```

## 3. Running the Pipeline

The full pipeline consists of sequential stages: Data Download, Validation, Extraction, Sentiment Analysis, Metrics Computation, and Statistical Modeling.

### Run the Full Pipeline
Execute the main pipeline script:
```bash
python code/analysis/run_pipeline.py
```

**Note:** This script automatically handles:
1. **Data Download (T008)**: Fetches from Pushshift, Reddit API, or HuggingFace archives.
2. **Ground Truth Validation (T019)**: Classifies threads and computes external validation scores.
3. **Extraction (T010, T009)**: Extracts seed posts and validates metadata.
4. **Sentiment Analysis (T013)**: Applies VADER sentiment scoring.
5. **Metrics & Modeling (T015, T018, T020)**: Computes contagion indices and fits GLMMs.
6. **Sensitivity Analysis (T023)**: Sweeps thresholds to test robustness.
7. **Report Generation (T026)**: Produces `docs/paper.md`.

### Sample Run (for quick verification)
To verify that the pipeline is correctly installed and can produce a minimal output, run:
```bash
python -m code.analysis.run_pipeline --sample 5
```
This command creates a tiny CSV file at `data/results/sample_run.csv` containing five example records. It runs quickly and does not require the full dataset.

## 4. Output Artifacts

Upon successful completion, the following artifacts will be generated:

- **Data**:
 - `data/raw/reddit_threads.jsonl`: Raw downloaded data.
 - `data/processed/valid_threads.csv`: Threads with valid ground truth.
 - `data/processed/threads_with_seeds.csv`: Extracted seed posts.
 - `data/processed/thread_metrics.csv`: Contagion indices and reply counts.
 - `data/processed/sensitivity_analysis.csv`: Results of threshold sweeps.
 - `data/processed/external_validation_correlation.csv`: Correlation with external validation.
 - `data/processed/vader_validation_report.json`: VADER sentiment validation results.
 - `data/results/sample_run.csv`: **Sample CSV produced by the `--sample` command.**
- **Reports**:
 - `docs/paper.md`: Final research paper draft.
 - `docs/analysis_summary.md`: Analysis summary with limitations.
 - `state/performance_log.json`: Execution timing and status.
 - `state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml`: Artifact checksums.

## 5. Verification

1. **Check Outputs**:
 ```bash
 ls data/results/
 # Expected: sample_run.csv (and other result files after full run)
 ```

2. **Run Tests**:
 ```bash
 pytest code/tests/ -v
 ```

3. **Reproducibility Check**:
 Re-run the pipeline. Verify that `data/processed/` files have identical checksums (recorded in `state/`).

## 6. Troubleshooting

- **Data Fetch Failures**: If the primary Pushshift API fails, the script automatically attempts fallback sources (Reddit API, HuggingFace). Check logs in `state/logs/` for details.
- **Ground Truth Threshold**: If valid threads are < 30%, the pipeline logs a warning but continues (T019b).
- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.
