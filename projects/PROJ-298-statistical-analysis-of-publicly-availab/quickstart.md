# Quick Start Guide

This guide walks you through reproducing the entire statistical analysis pipeline for Stack Overflow tag trends.

## Step 1: Environment Setup

```bash
# Navigate to project root
cd projects/PROJ-298-statistical-analysis-of-publicly-availab

# Create virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Step 2: Directory Structure Initialization

Run the setup script to create required directories:
```bash
python code/setup_directories.py
```

This creates:
- `data/`, `data/raw/`, `data/processed/`
- `data/events/`, `data/taxonomy/`

## Step 3: Generate Reference Data

Download and generate taxonomy and calendar files:
```bash
python code/data/generate_taxonomies.py
```

This produces:
- `data/taxonomy/survey_latest.json`
- `data/events/reference_calendar.json`

## Step 4: Download and Preprocess Data

Fetch Stack Overflow tag data:
```bash
python code/data/download.py
```

Preprocess into monthly frequencies:
```bash
python code/data/preprocess.py
```

## Step 5: Run Trend Analysis (User Story 1)

Execute the full trend analysis pipeline:
```bash
python code/analysis/trends.py
python code/analysis/bootstrapping.py
python code/data/external.py
python code/analysis/correlation.py
python code/analysis/generate_trend_results.py
```

Outputs:
- `data/processed/trend_intermediate.json`
- `data/processed/confidence_interval.json`
- `data/processed/external_metrics.json`
- `data/processed/tag_mappings.json`
- `data/processed/correlation_results.json`
- `data/processed/trend_results.json`

## Step 6: Run Decomposition Analysis (User Story 2)

Execute decomposition pipeline:
```bash
python code/analysis/decomposition.py
python code/analysis/generate_decomposition_results.py
```

Outputs:
- `data/processed/decomposition_intermediate.json`
- `data/processed/decomposition_results.json`

Generate visualizations:
```bash
python code/viz/plots.py
```

## Step 7: Run Clustering Analysis (User Story 3)

Execute clustering pipeline:
```bash
python code/analysis/clustering.py
python code/analysis/generate_cluster_results.py
```

Outputs:
- `data/processed/cluster_results.json`

## Step 8: Verify Limitations and Documentation

Check that all artifacts include limitation disclosures:
```bash
python code/verification/verify_limitations.py
```

## Step 9: Run Notebooks

Execute all notebooks to ensure reproducibility:
```bash
jupyter nbconvert --execute notebooks/02_trend_analysis.ipynb
jupyter nbconvert --execute notebooks/03_decomposition.ipynb
jupyter nbconvert --execute notebooks/04_clustering.ipynb
```

## Step 10: Run Tests

Execute the test suite:
```bash
pytest tests/
```

## Expected Outputs

After successful completion, verify these files exist:
- `data/processed/trend_results.json`
- `data/processed/decomposition_results.json`
- `data/processed/cluster_results.json`
- `notebooks/02_trend_analysis.ipynb` (with outputs)
- `notebooks/03_decomposition.ipynb` (with outputs)
- `notebooks/04_clustering.ipynb` (with outputs)

## Troubleshooting

### Memory Issues
If running out of memory, the streaming processor in `code/data/streaming_processor.py` handles large datasets in chunks.

### API Rate Limits
External data fetching (GitHub/NPM) may hit rate limits. The scripts include retry logic with exponential backoff.

### Missing Data Files
Ensure `code/data/download.py` completes successfully before running analysis scripts.

## Performance Notes

- Full pipeline runs in under 6 hours on CPU-only runners
- Streaming processing avoids loading entire dataset into memory
- Parallel execution possible for independent user stories

## State Management

All artifact checksums are tracked in `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml`.
Update after any data changes:
```bash
python code/utils/hygiene.py
```