# Quick Start Guide

## Prerequisites

- Python 3.11 or higher
- pip package manager
- 64GB RAM recommended
- ~50GB disk space for raw data
- Internet connection for data fetching

## Step 1: Clone and Setup

```bash
# Navigate to project root
cd projects/PROJ-298-statistical-analysis-of-publicly-availab

# Create virtual environment
python -m venv venv
source venv/bin/activate # Linux/Mac
# venv\\Scripts\\activate # Windows

# Install dependencies
pip install -r code/requirements.txt
```

## Step 2: Initialize Data Structure

This step creates the required directory structure and fetches taxonomy data.

```bash
python code/data/setup_data_structure.py
```

**Expected Output**:
- `data/events/reference_calendar.json`
- `data/taxonomy/survey_2023.json`
- Directory structure: `data/raw/`, `data/processed/`, `data/events/`, `data/taxonomy/`

## Step 3: Download Stack Overflow Data

Fetches PostsTags data from Stack Exchange dump or HuggingFace fallback.

```bash
python code/data/download.py
```

**Expected Output**:
- `data/raw/posts_tags.json` (or chunked files for large datasets)
- Progress logs showing download status

**Note**: This may take 30-60 minutes depending on network speed.

## Step 4: Preprocess Data

Aggregates raw data into monthly frequencies and filters tags with ≥12 months of data.

```bash
python code/data/preprocess.py
```

**Expected Output**:
- `data/processed/monthly_frequencies.json`
- Summary statistics of processed tags

## Step 5: Run Analysis Pipelines

Execute the three main analysis modules in sequence:

### 5.1 Trend Analysis (User Story 1)

```bash
# Detect trends using Modified Mann-Kendall
python code/analysis/trends.py

# Calculate confidence intervals via bootstrapping
python code/analysis/bootstrapping.py

# Compute correlations with GitHub/NPM metrics
python code/analysis/correlation.py

# Generate final trend results
python code/analysis/generate_trend_results.py
```

**Expected Output**: `data/processed/trend_results.json`, `data/processed/confidence_interval.json`

### 5.2 Decomposition (User Story 2)

```bash
# Perform STL/Hodrick-Prescott decomposition
python code/analysis/decomposition.py

# Generate decomposition results
python code/analysis/generate_decomposition_results.py
```

**Expected Output**: `data/processed/decomposition_results.json`

### 5.3 Clustering (User Story 3)

```bash
# Compute co-occurrence clusters
python code/analysis/clustering.py

# Generate cluster results
python code/analysis/generate_cluster_results.py
```

**Expected Output**: `data/processed/cluster_results.json`

## Step 6: Reproduce Notebooks

Ensure all Jupyter notebooks execute successfully with the generated data:

```bash
# Execute trend analysis notebook
jupyter nbconvert --to notebook --execute notebooks/02_trend_analysis.ipynb --inplace

# Execute decomposition notebook
jupyter nbconvert --to notebook --execute notebooks/03_decomposition.ipynb --inplace

# Execute clustering notebook
jupyter nbconvert --to notebook --execute notebooks/04_clustering.ipynb --inplace
```

**Validation**: Each notebook should complete without errors and display visualizations.

## Step 7: Run Tests

```bash
# Contract tests
pytest tests/contract/ -v

# Integration tests
pytest tests/integration/ -v
```

## Step 8: Verify State

Check that all artifacts have valid checksums:

```bash
python code/utils/state_manager.py
```

## Troubleshooting

### Memory Issues
If you encounter MemoryError:
- Reduce the number of tags processed (modify `code/data/preprocess.py`)
- Increase swap space
- Use a machine with more RAM

### API Rate Limits
If GitHub/NPM API calls fail:
- Add authentication tokens to environment variables
- Implement retry logic with exponential backoff

### Missing Dependencies
Ensure all packages are installed:
```bash
pip install -r code/requirements.txt --upgrade
```

## Expected Runtime

- Full pipeline (download → analysis → notebooks): ~4-6 hours on CPU-only runner
- Individual analysis modules: 30-90 minutes each
- Notebook execution: 15-30 minutes each

## Output Verification

After completion, verify these files exist:
- `data/processed/trend_results.json`
- `data/processed/confidence_interval.json`
- `data/processed/decomposition_results.json`
- `data/processed/cluster_results.json`
- `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml`

All notebooks should have `.nbconvert.ipynb` or updated timestamps indicating successful execution.