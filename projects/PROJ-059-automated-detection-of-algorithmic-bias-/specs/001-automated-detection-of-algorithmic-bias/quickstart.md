# Quickstart: Automated Detection of Algorithmic Bias in Public Code Repositories

## Prerequisites

- Python 3.11+
- `git` installed and in PATH
- Access to the internet (for downloading repos and dependencies)
- Sufficient free disk space for data storage and model training.

## Installation

1.  **Clone the Project**
    ```bash
    git clone <project-url>
    cd projects/PROJ-059-automated-detection-of-algorithmic-bias-/code
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` will pin `nltk`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `fairlearn`.*

4.  **Download NLTK Data**
    The VADER sentiment analyzer requires specific data files.
    ```bash
    python -c "import nltk; nltk.download('vader_lexicon')"
    ```

## Running the Pipeline

The pipeline is designed to run end-to-end on a single command.

### 1. Standard Run (500 Repositories)
This command will:
- Download sample Python repos (defined in `data/config/repos_list.txt` or generated randomly).
- Extract textual artifacts.
- Run the simulation.
- Perform correlation analysis.
- Save results to `data/derived/`.

```bash
python src/pipeline/runner.py --num-repos 500 --seed 42
```

### 2. Test Mode (Single Repository)
To verify the extraction logic on a single repo without downloading 500:

```bash
python src/pipeline/runner.py --repo-list data/test_repos.json --mode test
```

### 3. Robustness Test (SC-005)
To run the robustness test harness on the curated set of broken repos:

```bash
python src/pipeline/runner.py --mode robustness --input data/test/broken_repos.jsonl
```

### 4. Sensitivity Analysis
To run the alpha sweep (FR-008) and generate the sensitivity report:

```bash
python src/analysis/sensitivity.py --input data/derived/correlation_results.csv
```

## Output Artifacts

After a successful run, check the following files in `data/derived/`:

- `artifacts.jsonl`: Per-file extraction data.
- `repo_aggregates.jsonl`: Per-repo bias scores.
- `simulation_results.jsonl`: Fairness metrics.
- `robustness_report.json`: SC-005 test results.
- `independence_assertion.json`: SC-004 test results.
- `final_results.csv`: Correlation coefficients, p-values, and significance flags.
- `sensitivity_report.md`: Table of results across alpha thresholds.

## Troubleshooting

- **Rate Limit Errors**: If GitHub API rate limits are hit, the pipeline will retry with exponential backoff. If it fails, wait for a period of time.
- **Syntax Errors in Repo**: Repos with syntax errors are skipped, and a warning is logged. The pipeline continues.
- **Memory Errors**: If RAM exceeds a high threshold, reduce `--num-repos` or enable streaming mode (if implemented).
- **Independence Assertion Failed**: If `independence_assertion.json` shows "FAIL", check `src/simulation/bias_injector.py` for any accidental data flow from the text stream to the bias generator.

## Verification

To verify the pipeline against the contract:

```bash
pytest tests/contract/ -v
pytest tests/unit/test_independence.py -v
pytest tests/unit/test_metric_validation.py -v
```

This ensures all JSON schemas match the defined contracts and that the independence and metric validation assertions pass.
