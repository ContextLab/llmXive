# Quick Start Guide

This guide provides step-by-step instructions to reproduce all analysis results for the Statistical Analysis of Stack Overflow Question Tags project.

## Prerequisites

- Python 3.9 or higher
- 14GB+ free disk space
- 7GB+ available RAM
- Internet connection for data download

## Step 1: Setup Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Step 2: Initialize Project Structure

Run the directory setup script:

```bash
python code/setup_directories.py
```

This creates the necessary directory structure:
- `data/raw/`
- `data/processed/`
- `data/taxonomy/`
- `data/events/`

## Step 3: Generate Taxonomy and Reference Files

```bash
python code/data/generate_taxonomies.py
```

This downloads and processes:
- Stack Overflow Developer Survey 2023 taxonomy → `data/taxonomy/survey_2023.json`
- Reference calendar for events → `data/events/reference_calendar.json`

## Step 4: Download and Preprocess Data

### Download Stack Overflow Data

```bash
python code/data/download.py
```

This fetches PostsTags data from Stack Exchange Data Dump (streaming to manage memory) and saves to `data/raw/posts_tags.jsonl`.

### Preprocess Data

```bash
python code/data/preprocess.py
```

This aggregates tag frequencies into monthly bins, normalizes tags, and filters for tags with ≥12 months of data. Output: `data/processed/processed_data.json`.

## Step 5: Run Trend Analysis (User Story 1)

### Analyze Trends

```bash
python code/analysis/trends.py
```

Performs Modified Mann-Kendall test, calculates Theil-Sen slopes, applies Benjamini-Hochberg correction, and computes power analysis. Output: `data/processed/trend_intermediate.json`.

### Fetch External Metrics

```bash
python code/data/external.py
```

Fetches GitHub stars and NPM downloads for mapped tags. Output: `data/processed/external_metrics.json`.

### Map Tags to Repositories

```bash
python code/analysis/correlation.py
```

Maps tags to GitHub repos and NPM packages. Output: `data/processed/tag_mappings.json`.

### Calculate Correlations

The correlation calculation is integrated in the correlation module. Output: `data/processed/correlation_results.json`.

### Bootstrap Confidence Intervals

```bash
python code/analysis/bootstrapping.py
```

Calculates 95% confidence intervals for Theil-Sen slopes. Output: `data/processed/confidence_interval.json`.

### Aggregate Trend Results

```bash
python code/analysis/generate_trend_results.py
```

Merges all trend analysis outputs. Output: `data/processed/trend_results.json`.

## Step 6: Run Decomposition Analysis (User Story 2)

### Run Decomposition Pipeline

```bash
python code/analysis/decomposition.py
```

Performs ADF tests, STL/Hodrick-Prescott decomposition, Ljung-Box tests, and Rayleigh tests. Output: `data/processed/decomposition_intermediate.json`.

### Generate Decomposition Results

```bash
python code/analysis/generate_decomposition_results.py
```

Aggregates decomposition outputs. Output: `data/processed/decomposition_results.json`.

### Generate Plots

```bash
python code/viz/plots.py
```

Creates decomposition visualizations. Output: `figures/decomposition_plots/`

## Step 7: Run Clustering Analysis (User Story 3)

### Run Clustering Pipeline

```bash
python code/analysis/clustering.py
```

Computes Jaccard similarity matrix, performs hierarchical clustering, runs permutation tests, and calculates cluster alignment scores. Output: `data/processed/cluster_results.json`.

### Generate Cluster Results

```bash
python code/analysis/generate_cluster_results.py
```

Finalizes cluster analysis outputs.

## Step 8: Verify Results

### Check Limitation Disclosures

```bash
python code/verification/verify_limitations.py
```

Verifies all generated files contain mandatory limitation headers/footers.

### Validate Contracts

```bash
python code/utils/contract_validation.py
```

Validates all artifacts against their schema contracts.

## Step 9: Run Notebooks (Optional)

For interactive exploration, run the Jupyter notebooks:

```bash
jupyter notebook notebooks/02_trend_analysis.ipynb
jupyter notebook notebooks/03_decomposition.ipynb
jupyter notebook notebooks/04_clustering.ipynb
```

## Expected Outputs

After completing all steps, you should have:

```
data/
├── processed/
│ ├── processed_data.json
│ ├── trend_intermediate.json
│ ├── external_metrics.json
│ ├── tag_mappings.json
│ ├── correlation_results.json
│ ├── confidence_interval.json
│ ├── trend_results.json
│ ├── decomposition_intermediate.json
│ ├── decomposition_results.json
│ └── cluster_results.json
├── taxonomy/
│ └── survey_2023.json
└── events/
 └── reference_calendar.json

figures/
└── decomposition_plots/
 └── [various PNG files]
```

## Troubleshooting

### Memory Issues

If you encounter memory errors, ensure you're using the streaming download option and have at least 7GB RAM available.

### Network Issues

If data download fails, check your internet connection and ensure you can access:
- Stack Exchange Data Dump
- GitHub API
- NPM API

### Missing Dependencies

Re-run `pip install -r code/requirements.txt` to ensure all dependencies are installed.

## Performance Notes

- Full pipeline execution: ~4-6 hours on CPU-only runner
- Data download: ~30 minutes (streaming)
- Trend analysis: ~1-2 hours
- Decomposition: ~1 hour
- Clustering: ~1-2 hours

## Next Steps

After reproducing results, you can:
- Modify analysis parameters in the configuration files
- Add new tags for analysis
- Extend the taxonomy with additional categories
- Create custom visualizations in the notebooks