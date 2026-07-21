# Quickstart Guide: The Influence of Emotional Contagion on Collective Decision-Making

This guide provides instructions for setting up and running the full analysis pipeline for Project PROJ-139.

## Prerequisites

- **Python**: Version 3.11 or higher is required.
- **Operating System**: Linux, macOS, or Windows (with WSL recommended).
- **Dependencies**: The project requires `pandas`, `nltk`, `scikit-learn`, `statsmodels`, `pyyaml`, `requests`, `scipy`, and other standard scientific libraries.

## Installation

1. Clone the repository and navigate to the project root.
2. Install the required Python packages using pip:

```bash
pip install -r code/requirements.txt
```

3. (Optional) Configure API keys if you intend to use the Reddit Official API as a fallback. Create a `.env` file or set environment variables for `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, etc., as defined in `code/config/settings.py`.

## Running the Full Pipeline

The pipeline is orchestrated by a single entry point script that executes the data download, validation, extraction, sentiment analysis, metrics computation, and modeling stages in the correct order.

To run the full analysis on a specified number of threads (default or via argument):

```bash
python code/analysis/run_pipeline.py --threads
```

*Note: If your project structure places the runner in `code/data/run_full_pipeline.py` as per the task list, the command is:*

```bash
python code/data/run_full_pipeline.py
```

The script will:
1. Fetch raw data from Pushshift/Reddit/HuggingFace.
2. Classify ground truth availability.
3. Extract seed posts and validate metadata.
4. Compute VADER sentiment and the Emotional Contagion Index.
5. Calculate decision quality metrics (agreement, entropy, etc.).
6. Fit GLMMs and perform sensitivity analysis.
7. Generate the final report and checksums.

## Expected Outputs

Upon successful completion, the following artifacts will be generated:

### Data Artifacts (`data/processed/`)
- `valid_threads.csv`: Threads with valid ground truth.
- `all_threads_classified.csv`: All threads with validity classification.
- `threads_with_seeds.csv`: Extracted threads with seed posts.
- `thread_metrics.csv`: Contagion index and reply counts.
- `decision_quality_metrics.csv`: Agreement, entropy, and efficiency scores.
- `model_results.csv`: GLMM coefficients and p-values.
- `sensitivity_analysis.csv`: Results of threshold sweeps.
- `external_validation_correlation.csv`: Correlation analysis results.
- `collinearity_diagnostics.json`: VIF scores for predictors.
- `validity_status.json`: SC-006 compliance status.

### State & Logs (`state/`)
- `performance_log.json`: Runtime statistics and resource usage.
- `project_checksums.yaml`: SHA-256 hashes of all artifacts for reproducibility.
- `pipeline_log.log`: Detailed execution logs.

### Documentation (`docs/`)
- `paper.md`: Final research report including model results and SC-006 status.
- `annotation_protocol.md`: Protocol for human annotation (if applicable).

## Troubleshooting

- **Data Fetching Errors**: If the pipeline fails to download data, it will raise a `RuntimeError`. Ensure your network connection is active and that the fallback sources (HuggingFace) are accessible.
- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed in your Python environment.
- **API Rate Limits**: If using the Reddit API, you may encounter rate limits. The pipeline includes retry logic, but you may need to wait or configure API keys.