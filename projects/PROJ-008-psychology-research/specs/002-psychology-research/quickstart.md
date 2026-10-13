# Quickstart: Mindfulness Components and Delivery Formats in ASD Social Skills

## Prerequisites
- Python 3.11+
- `pip`
- CPU-only environment (7GB RAM)

## Installation
1. **Clone and Enter Project**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-008-psychology-research
   ```
2. **Setup Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

## Running the Research Pipeline

### 1. Data Collection & Cleaning
Fetch studies from ClinicalTrials.gov and OSF, then clean and tag them.
```bash
python code/data/collector.py --output data/raw/studies.json
python code/data/cleaner.py --input data/raw/verified_snapshot_2026.json --output data/processed/cleaned_studies.csv
```

### 2. Effect Size Calculation
Calculate Hedges' $g$ for all included studies.
```bash
python code/analysis/effect_sizes.py --input data/processed/cleaned_studies.csv --output data/processed/effect_sizes.csv
```

### 3. Meta-Analysis & Visualization
Run the random-effects model and generate the forest/funnel plots.
```bash
python code/analysis/meta_analysis.py --input data/processed/effect_sizes.csv --output data/processed/results.json --viz-dir viz/
```

## Verification
Run the test suite to verify schema compliance and calculation accuracy.
```bash
pytest tests/
```

## Troubleshooting
- **API Limits**: The collector uses exponential backoff. If it fails, check your internet connection or API keys.
- **Empty Results**: If `cleaned_studies.csv` is empty, check `data/raw/excluded_studies.log` to see why trials were excluded (e.g., age range mismatch).
- **N < 10**: If few studies are found, the pipeline will automatically skip the funnel plot and Egger's test, providing a descriptive synthesis instead.