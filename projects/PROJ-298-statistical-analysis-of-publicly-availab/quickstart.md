# Quick Start Guide

This guide walks you through the complete execution of the statistical analysis pipeline on a CPU-only environment.

## Prerequisites Check

Before running, ensure:
- Python 3.11+ is installed
- At least 14 GB free disk space
- At least 7 GB available RAM
- Network access for data download and external API calls

## Step 1: Environment Setup

```bash
# Navigate to project root
cd projects/PROJ-298-statistical-analysis-of-publicly-availab

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Step 2: Initialize Project Structure

```bash
# Create directories and initialize state
python code/setup_root.py
python code/setup_directories.py
python code/setup_notebooks_dir.py
python code/data/initialize_state.py
```

## Step 3: Generate Taxonomies

```bash
# Generate reference calendar and survey taxonomy
python code/data/generate_taxonomies.py
```

**Expected Output**:
- `data/events/reference_calendar.json`
- `data/taxonomy/survey_2023.json`

## Step 4: Download and Preprocess Data

```bash
# Download PostsTags data (streaming mode for memory efficiency)
python code/data/download.py

# Preprocess: normalize, aggregate monthly, filter
python code/data/preprocess.py
```

**Expected Output**:
- `data/processed/tag_frequencies.csv`
- `data/processed/tag_metadata.json`

## Step 5: Run Trend Analysis (US1)

```bash
# Compute Mann-Kendall trends and Theil-Sen slopes
python code/analysis/trends.py

# Bootstrap confidence intervals
python code/analysis/bootstrapping.py

# Fetch external metrics (GitHub stars, NPM downloads)
python code/data/external.py

# Calculate correlations
python code/analysis/correlation.py

# Generate final trend results
python code/analysis/generate_trend_results.py
```

**Expected Output**:
- `data/processed/trend_results.json`
- `data/processed/confidence_interval.json`

## Step 6: Run Decomposition Analysis (US2)

```bash
# Perform ADF tests, seasonality checks, and decomposition
python code/analysis/decomposition.py

# Generate decomposition results
python code/analysis/generate_decomposition_results.py
```

**Expected Output**:
- `data/processed/decomposition_results.json`

## Step 7: Run Clustering Analysis (US3)

```bash
# Compute Jaccard matrix, hierarchical clustering, and alignment scores
python code/analysis/clustering.py

# Generate cluster results
python code/analysis/generate_cluster_results.py
```

**Expected Output**:
- `data/processed/cluster_results.json`

## Step 8: Verify Limitations and Contracts

```bash
# Verify all artifacts contain mandatory limitation disclosures
python code/verification/verify_limitations.py

# Validate all artifacts against schema contracts
python -c "from utils.contract_validation import validate_all_artifacts; validate_all_artifacts()"
```

## Step 9: Run Notebooks (Optional)

All analysis is reproducible via notebooks:

```bash
# Start Jupyter
jupyter notebook

# Open and run each notebook in order:
# notebooks/02_trend_analysis.ipynb
# notebooks/03_decomposition.ipynb
# notebooks/04_clustering.ipynb
```

## Step 10: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/contract/ -v # Contract tests
pytest tests/integration/ -v # Integration tests
pytest tests/unit/ -v # Unit tests
```

## Expected Runtime

- **Total execution time**: ~2-4 hours on CPU-only runner
- **Memory usage**: Peak ~6 GB during streaming and bootstrapping
- **Disk usage**: ~12 GB for all artifacts

## Troubleshooting

### Out of Memory Errors
Ensure streaming mode is enabled in `download.py` and `preprocess.py`. The pipeline is designed for ~7 GB RAM.

### Network Failures
If HuggingFace or GitHub/NPM APIs are unreachable, the scripts will fail loudly (no synthetic fallback). Retry the step.

### Contract Validation Failures
Check `data/processed/` for incomplete or malformed JSON files. Re-run the corresponding analysis step.

## Output Verification

After completion, verify the following files exist in `data/processed/`:
- `tag_frequencies.csv`
- `tag_metadata.json`
- `trend_results.json`
- `confidence_interval.json`
- `decomposition_results.json`
- `cluster_results.json`

And in `state/`:
- `projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml` (updated with checksums)

## Next Steps

- Review `notebooks/` for visualizations and detailed analysis
- Check `data/processed/` for statistical results
- Refer to `README.md` for methodological details