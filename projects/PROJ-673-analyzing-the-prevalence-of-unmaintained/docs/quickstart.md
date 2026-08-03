# Quickstart Guide: Analyzing Unmaintained NPM Dependencies

This guide provides step-by-step instructions to run the full pipeline for analyzing the prevalence of unmaintained dependencies in popular NPM packages.

## Prerequisites

- Python 3.11 or higher
- `pip` (Python package installer)
- NPM API Key (optional, for higher rate limits)
- GitHub Token (optional, for repository metadata)

## 1. Installation

Clone the repository and install dependencies:

```bash
# Clone the repository
git clone <repository-url>
cd <project-directory>

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configuration

Set up environment variables for API keys (optional but recommended):

```bash
# Create a.env file or set environment variables directly
export NPM_API_KEY="your_npm_api_key_here"
export GITHUB_TOKEN="your_github_token_here"
```

If no keys are provided, the pipeline will use public endpoints with rate limiting.

## 3. Running the Pipeline

The pipeline consists of several stages. You can run them individually or execute the full pipeline at once.

### Option A: Run the Full Pipeline

```bash
python code/src/cli/optimize_pipeline.py
```

This script orchestrates the entire workflow:
1. Data collection (NPM packages, GitHub metadata, audit data)
2. Dependency resolution and age calculation
3. Statistical correlation analysis
4. Stratified analysis by package category
5. Visualization generation
6. Sensitivity analysis
7. Final report generation

### Option B: Run Individual Stages

#### Stage 1: Data Collection

```bash
python code/src/cli/collect_data.py
```

Outputs:
- `data/raw/` (cached API responses)
- `data/processed/dependencies_raw.json`

#### Stage 2: Age Metrics Calculation

```bash
python code/src/cli/calculate_age_metrics.py
```

Outputs:
- `data/processed/dependencies_raw.csv` (with `age_in_days` column)

#### Stage 3: Metrics Calculation

```bash
python code/src/cli/calculate_metrics.py
```

Outputs:
- `data/processed/metrics.json` (proportion of missing release metadata)

#### Stage 4: Statistical Analysis

```bash
python code/src/cli/run_analysis.py
```

Outputs:
- `data/processed/results_correlation.json` (Spearman correlation results)

#### Stage 5: Significance Flagging

```bash
python code/src/cli/flag_significance.py
```

Updates:
- `data/processed/results_correlation.json` (adds significance flags)

#### Stage 6: Visualization

```bash
python code/src/analysis/visualizer.py
```

Outputs:
- `figures/` (scatter plots, histograms, category distributions)

#### Stage 7: Sensitivity Analysis

```bash
python code/src/analysis/sensitivity_analysis.py
```

Outputs:
- `data/processed/sensitivity_analysis.json`

#### Stage 8: Report Generation

```bash
python code/src/cli/generate_report.py
```

Outputs:
- `docs/report.md` (comprehensive analysis report)

## 4. Output Artifacts

After running the full pipeline, you will find the following outputs:

### Data Files
- `data/raw/` - Cached API responses (immutable, checksummed)
- `data/processed/dependencies_raw.csv` - Raw dependency data with calculated metrics
- `data/processed/metrics.json` - Summary metrics (missing release proportion)
- `data/processed/results_correlation.json` - Correlation analysis results
- `data/processed/sensitivity_analysis.json` - Sensitivity analysis results
- `data/processed/power_analysis_notes.md` - Statistical power assumptions

### Visualizations
- `figures/scatter_age_vs_vulnerability.png` - Age vs. vulnerability count
- `figures/histogram_unmaintained_by_category.png` - Unmaintained proportions by category
- `figures/category_distribution.png` - Package category distribution

### Reports
- `docs/report.md` - Final analysis report with all findings

## 5. Validation

To verify that the pipeline ran correctly and all artifacts were generated:

```bash
python code/src/cli/validate_quickstart.py
```

This script checks:
- All required output files exist
- Checksums are valid for raw data
- Data integrity is maintained

## 6. Troubleshooting

### Rate Limiting
If you encounter rate limit errors, consider:
- Setting valid API keys in environment variables
- Adding a delay between requests (configured in `src/config/settings.py`)
- Running the pipeline during off-peak hours

### Missing Dependencies
Ensure all dependencies are installed:
```bash
pip install -r requirements.txt --upgrade
```

### Memory Issues
For large datasets, the pipeline uses streaming where possible. If you encounter memory errors:
- Reduce the sample size in `src/config/settings.py`
- Ensure sufficient swap space is available

## 7. Next Steps

- Review the generated report in `docs/report.md`
- Explore the visualizations in the `figures/` directory
- Modify parameters in `src/config/settings.py` for custom analysis
- Run unit tests: `pytest code/tests/unit/`
- Run integration tests: `pytest code/tests/integration/`

## Support

For issues or questions, please refer to the project documentation or open an issue in the repository.
