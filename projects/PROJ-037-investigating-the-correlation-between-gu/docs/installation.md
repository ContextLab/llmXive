# Installation Guide

## Prerequisites
- Python 3.9+
- `pip`
- System libraries: `libhdf5` (for `biom-format`)

## Step 1: Clone the Project
```bash
cd projects/PROJ-037-investigating-the-correlation-between-gu
```

## Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

## Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 4: Verify Installation
```bash
python -c "import pandas; import skbio; print('Dependencies OK')"
```

## Step 5: Download Data (Optional)
If automatic download fails, manually download AGP and OpenHumans data:
- AGP 16S data: [Canonical URL]
- AGP metadata: [Canonical URL]
- OpenHumans sleep data: [Canonical URL]
Place files in `data/raw/`.

## Step 6: Run the Pipeline
```bash
python code/ingestion.py
python code/diversity.py
python code/analysis.py
python code/validation.py
python code/report.py
```

## Troubleshooting
See `troubleshooting.md` for common issues.

## Notes
- All data must be real. No synthetic data.
- All analyses are associational.
