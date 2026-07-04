# Quickstart: Analyzing the Prevalence of Unmaintained Dependencies in Popular NPM Packages

## Prerequisites
- Python 3.11+
- Git
- A GitHub Personal Access Token (with `public_repo` scope) for API rate limits.
- NPM Registry access (public, no token required for basic metadata).

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd <repo-name>
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` will pin `scipy`, `pandas`, `requests`, `matplotlib`, `pyyaml`, and `statsmodels`.*

## Configuration

1. **Set Environment Variables**:
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   ```

2. **Verify Connectivity**:
   Ensure you can reach the NPM and GitHub APIs from your environment.

## Running the Analysis

### 1. Data Collection
Run the data collection script to fetch top packages and resolve dependencies. This will cache raw API responses.
```bash
python -m src.cli collect --top-n 1000 --output data/raw/packages_seed.json
```
*This step may take 30-60 minutes depending on rate limits.*

### 2. Data Processing
Process the raw data into the analysis-ready format.
```bash
python -m src.cli process --input data/raw/packages_seed.json --output data/processed/dependencies_cleaned.csv
```

### 3. Statistical Analysis
Run the correlation and stratified analysis (including ZINB regression).
```bash
python -m src.cli analyze --input data/processed/dependencies_cleaned.csv --output data/processed/results.json
```

### 4. Visualization
Generate the scatter plot and histogram.
```bash
python -m src.cli visualize --input data/processed/results.json --output figures/
```

## Expected Output
- `data/processed/dependencies_cleaned.csv`: The unified dataset.
- `data/processed/results.json`: Correlation coefficients, p-values, and ZINB results.
- `figures/scatter_age_vuln.png`: Visual correlation plot.
- `figures/histogram_category.png`: Distribution of unmaintained deps by category.

## Troubleshooting
- **Rate Limiting**: If you hit GitHub API limits, the script will automatically back off. If the job times out, reduce `--top-n` or run in chunks.
- **Missing Data**: Dependencies without GitHub repos are excluded from age calculations but included in vulnerability counts. Check `data_completeness_flags` in the CSV.
- **Zero-Inflation**: If the Spearman result is weak, check the `zinb_coefficient` in the results file, which may show a stronger relationship for the non-zero subset.