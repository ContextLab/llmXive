# Quickstart Guide: The Influence of Emotional Contagion on Collective Decision-Making

This guide provides instructions for setting up and running the full analysis pipeline for the emotional contagion study.

## Prerequisites

- **Python**: Version 3.11 or higher is required.
- **System**: Linux/macOS environment recommended.
- **Dependencies**: See `requirements.txt`.

## Installation

1. **Clone the repository** and navigate to the project root:
 ```bash
 cd PROJ-139-the-influence-of-emotional-contagion-on-
 ```

2. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

3. **Configure Environment Variables** (optional, for API access):
 Create a `.env` file in the project root or set the following environment variables:
 - `REDDIT_CLIENT_ID`: Your Reddit API client ID.
 - `REDDIT_CLIENT_SECRET`: Your Reddit API client secret.
 - `REDDIT_USER_AGENT`: A unique user agent string (e.g., `research:emotional_contagion:v1 (by /u/yourusername)`).

## Memory and Streaming Strategy

The pipeline is designed to handle large datasets by employing a **streaming and chunking strategy** to stay within the memory constraints of the target runner (approx. 7 GB RAM, 14 GB disk).

### Streaming Rules

- **Data Download**: The `code/data/download.py` script fetches data in batches. It does not load the entire raw dataset into memory at once. Instead, it writes data incrementally to `data/raw/reddit_threads.jsonl`.
- **Processing**: Downstream scripts (e.g., `code/data/metrics.py`, `code/data/validation.py`) read from `data/raw/reddit_threads.jsonl` or intermediate CSV files in chunks where possible.
- **Sampling**: If the dataset exceeds the operational limits (e.g., >500 threads for the performance check), the pipeline automatically reduces the sample size. The exact sample size and strategy are logged in `data/processed/sampling_strategy_log.json`.
- **Memory Limits**: The pipeline monitors memory usage. If usage approaches the limit, it may trigger a retry with a smaller sample size or fail loudly if the data cannot be processed within the constraints.

### Limitations

- **Representativeness**: If a sample is taken due to size constraints, the results are based on that specific sample. The `sampling_strategy_log.json` documents the sample size and any limitations.
- **Memory**: Ensure sufficient RAM is available. If running locally, close other memory-intensive applications.

## Execution

The full pipeline can be executed via the main entry point script.

### Running the Pipeline

To run the entire pipeline end-to-end (Data Download -> Extraction -> Sentiment -> Modeling -> Reporting):

```bash
python code/analysis/run_pipeline.py
```

**Note**: This command will:
1. Fetch data from the primary source (Pushshift) or fallbacks.
2. Extract seed posts and validate ground truth.
3. Perform sentiment analysis and compute contagion indices.
4. Fit statistical models and perform sensitivity analysis.
5. Generate final reports (`docs/paper.md`, `docs/analysis_summary.md`).

### Running Individual Stages

If you wish to run specific stages independently (e.g., for debugging):

- **Download Data**:
 ```bash
 python code/data/download.py
 ```
 *Optional arguments*:
 - `--subreddits`: Specify subreddits (e.g., `--subreddits AskScience fdr`).
 - `--limit`: Limit the number of threads to download.

- **Extraction & Validation**:
 ```bash
 python code/data/extract.py
 python code/data/validation.py
 ```

- **Sentiment & Metrics**:
 ```bash
 python code/data/sentiment.py
 python code/data/metrics.py
 ```

- **Modeling**:
 ```bash
 python code/data/modeling.py
 ```

## Output Artifacts

Upon successful completion, the following artifacts will be generated:

### Data (`data/processed/`)
- `all_threads_classified.csv`: All threads with ground truth classification.
- `valid_threads.csv`: Threads with valid ground truth.
- `threads_with_seeds.csv`: Threads with extracted seed posts.
- `thread_metrics.csv`: Contagion index and confidence intervals.
- `sensitivity_analysis.csv`: Results of the threshold sensitivity analysis.
- `collinearity_diagnostics.json`: VIF scores and correlation diagnostics.
- `external_validation_correlation.csv`: Correlation between external validation and metrics.
- `ground_truth_stats.json`: Statistics on ground truth coverage.
- `vader_validation_report.json`: VADER tool validation results.

### State (`state/`)
- `final_validation.json`: Compliance report for all Success Criteria (SC-001 to SC-006).
- `reproducibility_report.json`: Verification of artifact checksums.
- `performance_log.json`: Runtime and resource usage metrics.
- `artifact_hashes.yaml`: Map of file paths to SHA-256 hashes.

### Documentation (`docs/`)
- `paper.md`: Final research paper draft.
- `analysis_summary.md`: Detailed analysis summary including power analysis.
- `quickstart.md`: This guide.

## Troubleshooting

- **Data Source Failure**: If the pipeline fails to download data from all sources, it will raise a `RuntimeError`. Ensure your internet connection is stable and API keys (if used) are correct.
- **Memory Errors**: If you encounter memory errors, check the `data/processed/sampling_strategy_log.json` to see if the sample size was reduced. You may also need to increase system RAM or reduce the `--limit` flag when downloading.
- **Missing Artifacts**: If a specific output file is missing, check the logs in `state/` or `data/processed/` for error messages indicating which stage failed.

## Data Sources

The pipeline attempts to fetch data from the following sources in order:
1. **Pushshift API** (Primary)
2. **Reddit Official API** (Fallback 1)
3. **HuggingFace Archives** (Fallback 2)
4. **Internet Archive / Common Crawl** (Fallback 3)

If all sources fail, the pipeline will halt with an error. No synthetic data is generated.