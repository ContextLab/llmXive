# Quickstart Guide: The Influence of Emotional Contagion on Collective Decision-Making

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Access to Reddit API credentials (for data download)

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd PROJ-139-the-influence-of-emotional-contagion-on-
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

3. Set up environment variables (optional, for API keys):
 ```bash
 export REDDIT_CLIENT_ID="your_client_id"
 export REDDIT_CLIENT_SECRET="your_client_secret"
 export REDDIT_USER_AGENT="your_user_agent"
 ```

## Running the Pipeline

### Data Download

**IMPORTANT**: The data download script uses the following arguments:
- `--subreddits`: List of subreddits to fetch (e.g., `askScience fdr`)
- `--limit`: Maximum number of threads to fetch (optional)
- `--output`: Output file path (optional, defaults to `data/raw/reddit_threads.jsonl`)

**Correct Command**:
```bash
python code/data/download.py --subreddits askScience fdr --limit 100
```

**Note**: The previous command `--source askScience --source fdr` was incorrect and has been fixed. The script now uses `--subreddits` to specify multiple subreddits.

### Full Pipeline Execution

Run the complete analysis pipeline:
```bash
python code/analysis/run_pipeline.py
```

This will:
1. Download data (if not already present)
2. Extract seed posts and validate ground truth
3. Apply sentiment analysis
4. Compute emotional contagion index
5. Fit statistical models
6. Generate final reports

### Individual Stage Execution

You can also run individual stages:

```bash
# Data download
python code/data/download.py --subreddits askScience fdr

# Data extraction and validation
python code/data/extract.py
python code/data/validation.py

# Sentiment analysis
python code/data/sentiment.py

# Metrics calculation (T059: Uses filtered dataset from T009)
python code/data/metrics.py

# Modeling and analysis
python code/data/modeling.py

# Final reports
python code/analysis/generate_final_reports.py
```

## Expected Outputs

After successful execution, the following artifacts will be generated:

### Data Files (`data/processed/`)
- `threads_with_seeds.csv`: Filtered threads with ≥3 seed posts
- `valid_threads.csv`: Threads with valid ground truth
- `thread_metrics.csv`: Emotional contagion index and decision quality metrics
- `sensitivity_analysis.csv`: Sensitivity analysis results
- `ground_truth_stats.json`: Ground truth coverage statistics
- `vader_validation_report.json`: VADER sentiment validation results
- `external_validation_correlation.csv`: Correlation with external validation
- `collinearity_diagnostics.json`: VIF scores for predictors

### State Files (`state/`)
- `sc_006_compliance_report.json`: Ground truth threshold compliance
- `final_validation.json`: All success criteria validation results
- `reproducibility_report.json`: Reproducibility verification results
- `artifact_hashes.yaml`: Checksums of all artifacts

### Documentation (`docs/`)
- `paper.md`: Final research paper
- `analysis_summary.md`: Analysis summary with limitations
- `quickstart.md`: This guide

## Memory and Streaming

### Memory Constraints
The pipeline is designed to run on standard CPU-only runners with limited memory (~7 GB RAM, ~14 GB disk). To handle large datasets:

1. **Streaming**: The download and processing stages use streaming to avoid loading entire datasets into memory.
2. **Sampling**: If the dataset exceeds memory limits, the pipeline automatically samples a representative subset (logged in `data/processed/sampling_strategy_log.json`).
3. **Chunk Processing**: Metrics and modeling stages process data in chunks where possible.

### Monitoring
Monitor memory usage during execution:
```bash
python code/analysis/validate_streaming_rules.py
```

This will generate `state/streaming_validation.json` with memory profile information.

## Troubleshooting

### Data Download Fails
If data download fails:
1. Check API credentials
2. Verify network connectivity
3. Review `data/processed/download_attempts.log` for error details

### Pipeline Stage Fails
If a specific stage fails:
1. Check the corresponding log file (e.g., `data/processed/metrics_pipeline.log`)
2. Verify input files exist and are valid
3. Ensure dependencies from previous stages are complete

### Missing Artifacts
If expected artifacts are missing:
1. Run `python code/analysis/final_validation.py` to check for missing files
2. Review `state/final_validation.json` for detailed error messages

## Validation and Verification

### Run Full Validation
```bash
python code/analysis/final_validation.py
```

### Verify Reproducibility
```bash
python code/analysis/verify_reproducibility.py
```

### Verify Data Sources
```bash
python code/analysis/verify_data_sources.py
```

## T059 Specific: Corrected Data Flow

**Important Fix**: Task T059 corrected the data flow in `code/data/metrics.py` to ensure it reads from the **filtered dataset** (`threads_with_seeds.csv`) rather than the raw dataset. This prevents the inclusion of threads that should have been excluded by T010 (threads with <3 top-level posts).

The `load_processed_data()` function now explicitly loads from `data/processed/threads_with_seeds.csv` and raises a `FileNotFoundError` if this file does not exist, ensuring the pipeline fails loudly rather than processing incorrect data.