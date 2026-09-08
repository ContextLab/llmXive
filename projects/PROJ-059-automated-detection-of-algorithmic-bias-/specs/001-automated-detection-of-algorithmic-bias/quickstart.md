# Quickstart: Automated Detection of Algorithmic Bias in Public Code Repositories

## Prerequisites

-   Python 3.11+
-   `git` installed and configured
-   GitHub account (for rate-limited API access)
-   Sufficient disk space (~5-10 GB for 500 repos)

## Installation

1.  **Clone the Project**
    ```bash
    git clone https://github.com/your-org/PROJ-059-automated-detection-of-algorithmic-bias-.git
    cd PROJ-059-automated-detection-of-algorithmic-bias-
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Download NLTK Data**
    ```bash
    python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt')"
    ```

## Running the Pipeline

### 1. Setup Validation Dataset (One-time)
Generate the manual validation set of 200 comments (or load the curated one).
```bash
python code/validation.py --setup-only
```
*Output*: `data/curated/validation_comments.csv`

### 2. Run Full Analysis
Execute the main pipeline. This will:
-   Clone 500 repositories (or the configured list).
-   Extract textual features.
-   Validate VADER thresholds.
-   Run simulations.
-   Compute correlations.

```bash
python code/main.py --repos 500 --seed 42
```

**Note**: Ensure you have a stable internet connection. The script includes retry logic for GitHub API rate limits.

### 3. Inspect Results

-   **Textual Bias Scores**: `data/derived/repo_scores.csv`
-   **Simulation Metrics**: `data/derived/simulation_results.csv`
-   **Correlation Results**: `data/derived/correlation_results.csv`
-   **Validation Report**: `data/derived/validation_metrics.json`

### 4. Reproducibility Check
To verify reproducibility, delete the `data/derived/` folder and re-run:
```bash
rm -rf data/derived/
python code/main.py --repos 500 --seed 42
```
The output should be identical (up to floating-point precision) due to pinned seeds.

## Troubleshooting

-   **GitHub Rate Limit**: If you hit `403 Forbidden`, wait 1 hour or use a GitHub token. Set `GITHUB_TOKEN` env var.
-   **Memory Error**: If RAM > 7 GB, reduce `--repos` count to 100 or enable `--streaming` mode (if implemented).
-   **Syntax Errors in Repo**: The pipeline logs these but continues. Check `data/derived/execution_errors.log`.
