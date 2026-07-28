# Quickstart Guide: Emotional Contagion Analysis Pipeline

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Internet connectivity (for data download)
- (Optional) Reddit API credentials for higher rate limits

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-139-the-influence-of-emotional-contagion-on-
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

3. (Optional) Set Reddit API credentials as environment variables:
 ```bash
 export REDDIT_CLIENT_ID="your_client_id"
 export REDDIT_CLIENT_SECRET="your_client_secret"
 export REDDIT_USER_AGENT="your_user_agent"
 ```

## Running the Pipeline

### Step 1: Download Data

The download script supports multiple sources with automatic fallback:
- Primary: Pushshift API
- Fallback 1: Reddit Official API (requires credentials)
- Fallback 2: HuggingFace archives

**Command:**
```bash
python code/data/download.py --subreddits AskScience FDR --limit 500
```

**Arguments:**
- `--subreddits`: Space-separated list of subreddit names (default: AskScience FDR)
- `--limit`: Maximum threads per source (default: 500)
- `--output`: Custom output path (default: data/raw/reddit_threads.jsonl)

**Note:** The script implements a strict "fail-loud" policy. If all data sources fail, it raises a `RuntimeError` instead of generating synthetic data.

### Step 2: Run Full Pipeline

Execute the complete analysis pipeline:
```bash
python code/analysis/run_pipeline.py
```

This will:
1. Extract seed posts from downloaded data
2. Validate ground truth availability
3. Apply VADER sentiment analysis
4. Compute emotional contagion indices
5. Fit GLMM models
6. Perform sensitivity analysis
7. Generate final reports

## Expected Outputs

After successful execution, the following artifacts will be generated:

### Data Files (`data/processed/`)
- `reddit_threads.jsonl`: Raw downloaded data
- `threads_with_seeds.csv`: Extracted threads with seed posts
- `all_threads_classified.csv`: Thread classification (valid/valid_no_gt/invalid)
- `valid_threads.csv`: Threads with ground truth
- `thread_metrics.csv`: Sentiment and contagion metrics
- `sensitivity_analysis.csv`: Threshold sensitivity results
- `ground_truth_stats.json`: Ground truth availability statistics
- `collinearity_diagnostics.json`: VIF scores for predictors
- `external_validation_correlation.csv`: Correlation with external validation

### State Files (`state/`)
- `projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml`: Project state and checksums
- `sc_006_compliance_report.json`: Ground truth threshold compliance
- `reproducibility_report.json`: Reproducibility verification results
- `final_validation.json`: Final success criteria validation

### Documentation (`docs/`)
- `paper.md`: Final research paper
- `analysis_summary.md`: Analysis summary with limitations
- `quickstart.md`: This guide

## Data Sources

The pipeline fetches data from the following sources in order:

1. **Pushshift API**: `
 - Free, no authentication required
 - May have rate limits or availability issues

2. **Reddit Official API**: Requires OAuth credentials
 - More reliable but requires registration
 - Set via environment variables or CLI flags

3. **HuggingFace Archives**: `cardiffnlp/reddit-tweet-sentiment`
 - Pre-processed Reddit sentiment dataset
 - Used as last resort fallback

## Troubleshooting

### Data Download Fails
If you see `RuntimeError: All data sources failed`, check:
- Internet connectivity
- Pushshift API availability (may be down temporarily)
- Reddit API credentials (if using)
- HuggingFace dataset accessibility

### Pipeline Execution Errors
- Ensure all dependencies are installed: `pip install -r code/requirements.txt`
- Check that `data/raw/reddit_threads.jsonl` exists before running the full pipeline
- Verify sufficient disk space (minimum 14 GB recommended)

### Performance Issues
- The pipeline is optimized for CPU-only execution
- Default thread limit is 500; reduce for faster testing
- Runtime should complete within 6 hours on standard hardware

## Verification

After running, verify success:
```bash
python code/analysis/final_validation.py
```

This checks all success criteria (SC-001 to SC-006) and reports compliance status.