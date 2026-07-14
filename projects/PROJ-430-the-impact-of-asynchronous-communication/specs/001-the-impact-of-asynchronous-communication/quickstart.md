# Quickstart: The Impact of Asynchronous Communication Delays on Team Cohesion

## Prerequisites

- Python 3.11+
- Git
- A GitHub Personal Access Token (PAT) with `public_repo` scope.
- 7 GB+ RAM, 14 GB+ Disk (for CI runner).

## Setup

1.  **Clone the Repository**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-430-the-impact-of-asynchronous-communication
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r code/requirements.txt
    python -m nltk.downloader vader_lexicon
    python -m nltk.downloader punkt
    ```

3.  **Configure Environment**
    Create a `.env` file in the root or set environment variables:
    ```bash
    export GITHUB_TOKEN="your_github_pat_here"
    export SAMPLE_SIZE=50  # Deferred value; adjust as needed
    export MIN_EVENTS=100  # Deferred value; adjust as needed
    ```

## Running the Pipeline

The pipeline is executed via the main orchestration script. It handles data fetching, metric derivation, sentiment analysis, and statistical testing.

```bash
python code/main.py
```

### Expected Output

1.  **Data Files**: Generated in `data/derived/`.
    - `project_metrics.csv`: The core dataset for analysis.
    - `statistical_results.csv`: Correlation and regression outputs.
2.  **Visualizations**: PNG files in `figures/`.
    - `delay_cohesion_scatter.png`: The primary visualization.
3.  **Logs**: Execution logs in `logs/` including API rate limit warnings and VIF diagnostics.

## Testing

Run the unit and contract tests to verify data integrity and schema compliance:

```bash
pytest tests/ -v
```

### Contract Tests
These tests validate that the generated CSVs match the schemas defined in `contracts/`.

```bash
pytest tests/contract/ -v
```

## Troubleshooting

- **API Rate Limit**: If the script halts with a 403 error, wait 15 minutes or increase `GITHUB_TOKEN` permissions.
- **Memory Error**: If RAM usage exceeds 6 GB, reduce `SAMPLE_SIZE` or `MIN_EVENTS` in the environment variables.
- **Non-English Text**: The script automatically logs the exclusion rate. If > 50% of data is excluded, consider adjusting the `langdetect` threshold.
