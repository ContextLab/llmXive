# Quickstart Guide

This guide provides step-by-step instructions to set up the environment and run the full data pipeline for the "Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety" project.

## 1. Environment Setup

### 1.1. Create Virtual Environment
Ensure you have Python 3.8 or higher installed.

```bash
# Navigate to project root
cd projects/PROJ-487-the-impact-of-social-media-doomscrolling

# Create virtual environment
python -m venv venv

# Activate the environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 1.2. Install Dependencies
Install all required Python packages.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: If `pytrends` fails to install due to API changes, ensure you have the latest version:
```bash
pip install --upgrade pytrends
```

### 1.3. Verify Installation
Run the CPU compliance check to ensure no GPU dependencies are accidentally introduced.

```bash
python code/data/verify_cpu_compliance.py
```

## 2. Running the Pipeline

The pipeline is executed in three sequential stages. Ensure each stage completes successfully before proceeding to the next.

### Stage 1: Data Acquisition (US1)
Fetches raw data from GDELT and Google Trends.

```bash
# Fetch GDELT negative sentiment events
python code/data/fetch_gdelt.py

# Fetch Google Trends data for anxiety keywords
python code/data/fetch_google_trends.py
```

**Expected Output**:
- `data/raw/gdelt_events.csv`
- `data/raw/google_trends.csv`

**Validation**:
Run integrity checks to ensure data was fetched correctly.
```bash
python code/data/validate_integrity.py
```

### Stage 2: Data Preprocessing (US2)
Cleans, aligns, and normalizes the time-series data.

```bash
python code/data/preprocess.py
```

**Expected Output**:
- `data/processed/aligned_timeseries.csv`
- `data/processed/stationarity_check.csv`

**Validation**:
Verify data completeness after interpolation.
```bash
python code/data/post_interpolation_check.py
```

### Stage 3: Statistical Analysis (US3)
Computes correlations, Granger causality, and generates reports.

```bash
python code/data/analyze.py
```

**Expected Output**:
- `data/processed/granger_results.csv`
- `data/reports/analysis_report.pdf`

**Note**: This script will exit with a non-zero code if the statistical validity check (Bonferroni correction) fails.

## 3. Troubleshooting

### API Rate Limiting
If you encounter rate limit errors during data fetching, the scripts include built-in retry logic with exponential backoff. If issues persist, check your network connection or API key status.

### Missing Dependencies
If a script fails to import a module, ensure your virtual environment is activated and `requirements.txt` was installed:
```bash
pip install -r requirements.txt
```

### Data Not Found
Ensure that previous stages have completed successfully and that the `data/raw/` and `data/processed/` directories contain the expected CSV files.

## 4. Reproducibility

To ensure full reproducibility, run the entire pipeline from scratch:

```bash
# Clean previous data (optional)
rm -rf data/raw/* data/processed/* data/reports/*

# Run full pipeline
python code/data/fetch_gdelt.py && \
python code/data/fetch_google_trends.py && \
python code/data/preprocess.py && \
python code/data/analyze.py
```

All scripts are designed to run on a CPU-only environment within 6 hours.