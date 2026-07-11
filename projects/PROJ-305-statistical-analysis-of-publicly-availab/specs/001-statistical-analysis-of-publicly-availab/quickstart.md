# Quickstart: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Prerequisites

- Python 3.11+
- 7GB RAM available
- Internet access (for data download)

## Installation

```bash
# Clone repository
git clone <repo-url>
cd projects/PROJ-305-statistical-analysis-of-publicly-availab

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline

### Step 1: Download Data

```bash
python code/ingestion/download.py
```

> **Note**: This script downloads VAERS data from the official CDC source (`).

### Step 2: Preprocess Data

```bash
python code/ingestion/preprocess.py
python code/ingestion/merge.py
```

### Step 3: Run Analysis

```bash
python code/main.py
```

This will:
1. Calculate ROR, PRR, IC for all SOCs (with minimum count threshold).
2. Apply Benjamini-Hochberg correction (on filtered SOCs).
3. Identify signals based on multi-metric consistency + bias adjustment.
4. Perform **Calendar-Time Anomaly Detection** (Poisson regression with Media Event Flag).
5. Generate forest plot.

### Step 4: View Results

- **Statistical Results**: `data/outputs/soc_clusters.csv`, `data/outputs/signals.csv`
- **Forest Plot**: `data/outputs/forest_plot.png`

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/
```

## Troubleshooting

### Memory Error

If you encounter a memory error:
1. Ensure you are using Polars (not Pandas) for large datasets.
2. Check that chunked processing is enabled in `preprocess.py`.
3. Reduce the date range or sample the data.

### Missing Data

If VAERS data is missing:
1. Verify internet connection.
2. Check the official CDC VAERS website for data availability.
3. Ensure the URL ` is accessible.