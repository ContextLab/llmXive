# Quickstart Guide: Analyzing Unmaintained NPM Dependencies

This guide explains how to set up the environment, collect data, run the analysis pipeline, and generate the final report for the **Analyzing the Prevalence of Unmaintained Dependencies in Popular NPM Packages** project.

## Prerequisites

- Python 3.11 or higher
- `pip` package manager
- A valid **NPM API Key** (optional, for rate-limited access)
- A valid **GitHub Token** (optional, for detailed repository metadata)

## 1. Setup Environment

Navigate to the project root directory and install dependencies.

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the project root or set environment variables directly:

```bash
export NPM_API_KEY="your_npm_api_key_here"
export GITHUB_TOKEN="your_github_token_here"
export RATE_LIMIT="60" # Requests per minute
```

If you do not have keys, the pipeline will run with public endpoints but may hit rate limits faster.

## 2. Data Collection (User Story 1)

This step fetches data for top NPM packages, resolves dependency trees, and gathers maintenance/security metadata.

**Output**: `data/processed/dependencies_raw.csv`, `data/processed/metrics.json`, `data/processed/sensitivity_analysis.json`

```bash
python code/src/cli/collect_data.py
```

*Note: This step may take several minutes depending on the number of packages and API rate limits.*

## 3. Run Analysis (User Story 2)

This step calculates Spearman rank correlations between dependency age and vulnerability density.

**Output**: `data/processed/results_correlation.json`, `figures/correlation_scatter.png`

```bash
python code/src/cli/run_analysis.py
```

## 4. Stratified Analysis & Reporting (User Story 3)

This step performs category-based stratification, variance analysis, and generates the final summary report.

**Outputs**:
- `data/processed/results_correlation.json` (updated with stratified data)
- `figures/unmaintained_histogram.png`
- `docs/report.md`

```bash
python code/src/cli/generate_report.py
```

## 5. Verify Outputs

After running the full pipeline, verify the following artifacts exist:

- `data/processed/dependencies_raw.csv`
- `data/processed/metrics.json`
- `data/processed/results_correlation.json`
- `data/processed/sensitivity_analysis.json`
- `figures/correlation_scatter.png`
- `figures/unmaintained_histogram.png`
- `docs/report.md`

## Troubleshooting

- **Rate Limit Errors**: If you encounter 429 errors, wait a few minutes or increase `RATE_LIMIT` in your environment configuration.
- **Missing Data**: If `dependencies_raw.csv` is empty, check your network connection and API key validity.
- **Import Errors**: Ensure you are running the script from the project root and the virtual environment is activated.

## Next Steps

- Review `docs/report.md` for the final analysis summary.
- Check `data/processed/` for intermediate datasets.
- Run unit tests: `pytest code/tests/unit/`
