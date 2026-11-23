# Quickstart Guide: Analyzing Unmaintained NPM Dependencies

This guide walks you through setting up and running the full analysis pipeline to measure the prevalence of unmaintained dependencies in popular NPM packages.

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Valid API keys (see Environment Setup below)

## Environment Setup

Before running the pipeline, you must configure your environment variables. Create a `.env` file in the project root or export these variables in your shell:

```bash
# Required API Keys
export NPM_API_KEY="your_npm_registry_api_key"
export GITHUB_TOKEN="your_github_personal_access_token"

# Optional: Rate limiting (requests per minute)
export RATE_LIMIT="60"

# Optional: Override default number of top packages to analyze
export TOP_PACKAGES="100"
```

**Important**: Ensure your GitHub token has `public_repo` scope (or equivalent) to read repository metadata. The NPM API key is typically not required for public package metadata but is recommended for higher rate limits.

## Installation

1. Navigate to the project root:
 ```bash
 cd PROJ-673-analyzing-the-prevalence-of-unmaintained
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline consists of three main stages: Data Collection, Analysis, and Reporting. You can run them individually or all at once using the validation script.

### Option 1: Run Full Pipeline (Recommended)

Execute the complete pipeline end-to-end:

```bash
python code/src/cli/validate_quickstart.py
```

This script orchestrates:
1. Data collection from NPM and GitHub APIs
2. Dependency tree resolution and metadata extraction
3. Statistical correlation analysis (Spearman's rho)
4. Stratified analysis by package category
5. Sensitivity analysis
6. Report generation

### Option 2: Run Stages Individually

#### Stage 1: Data Collection

Fetch top NPM packages and their dependency metadata:

```bash
python code/src/cli/collect_data.py --export --metrics --top-packages 100
```

**Outputs**:
- `data/processed/dependencies_raw.csv`: Raw dependency data with age and vulnerability metrics
- `data/processed/metrics.json`: Summary metrics including missing metadata ratios

#### Stage 2: Power Analysis

Calculate statistical power for the correlation analysis:

```bash
python code/src/analysis/power.py
```

**Output**: `data/processed/power_analysis.json`

#### Stage 3: Correlation Analysis

Compute Spearman rank correlation between dependency age and vulnerability count:

```bash
python code/src/analysis/correlation.py
```

**Output**: `data/processed/results_correlation.json`

#### Stage 4: Visualization

Generate scatter plots and category distributions:

```bash
python code/src/analysis/visualizer.py --plot-scatter
```

**Output**: `data/processed/scatter_plot.png`

#### Stage 5: Stratified Analysis

Compute per-category correlation coefficients:

```bash
python code/src/analysis/stratified_stats.py
```

**Output**: `data/processed/results_stratified.json`

#### Stage 6: Variance Analysis

Calculate variance across category correlations:

```bash
python code/src/analysis/stratified_stats.py --variance
```

**Output**: Appends variance data to `data/processed/results_correlation.json`

#### Stage 7: Sensitivity Analysis

Perform threshold sweep analysis:

```bash
python code/src/analysis/sensitivity.py
```

**Output**: `data/processed/sensitivity_analysis.json`

#### Stage 8: Report Generation

Aggregate all results into a comprehensive report:

```bash
python code/src/cli/generate_report.py
```

**Output**: `docs/report.md`

## Output Artifacts

After successful execution, the following artifacts will be available:

| Artifact | Description |
|----------|-------------|
| `data/processed/dependencies_raw.csv` | Raw dependency dataset with age and vulnerability metrics |
| `data/processed/metrics.json` | Data quality metrics and summary statistics |
| `data/processed/power_analysis.json` | Statistical power analysis results |
| `data/processed/results_correlation.json` | Spearman correlation coefficient and p-value |
| `data/processed/results_stratified.json` | Per-category correlation coefficients |
| `data/processed/sensitivity_analysis.json` | Threshold sweep results |
| `data/processed/scatter_plot.png` | Visualization of age vs. vulnerability |
| `docs/report.md` | Comprehensive analysis report |

## Rate Limiting and Caching

The pipeline implements:
- **Exponential backoff** (max 3 retries, initial delay 1s, multiplier 2.0, max delay 60s)
- **Local file caching** in `data/raw/` to avoid redundant API calls
- **Rate limit awareness** based on `RATE_LIMIT` environment variable

If you encounter rate limit errors, the pipeline will automatically retry with exponential backoff. If errors persist, consider reducing the `TOP_PACKAGES` count or waiting between runs.

## Troubleshooting

### API Authentication Errors
- Verify your `NPM_API_KEY` and `GITHUB_TOKEN` are correctly set
- Ensure your GitHub token has the necessary scopes
- Check that your tokens have not expired

### Missing Output Files
- Ensure all previous stages completed successfully
- Check the console logs for specific error messages
- Verify that `data/processed/` directory exists and is writable

### Memory Constraints
- Reduce `TOP_PACKAGES` count for smaller datasets
- The pipeline is optimized for ~7GB RAM; large datasets may require more resources

### Fabrication Guard
The pipeline enforces a "fail loud" policy: if real data cannot be fetched, it will raise an error rather than generating synthetic data. This ensures all reported results are genuine measurements.

## Next Steps

After running the pipeline, review the generated `docs/report.md` for detailed findings and insights about the prevalence of unmaintained dependencies in the NPM ecosystem.
