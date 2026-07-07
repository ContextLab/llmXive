# Quickstart Guide

## 1. Setup Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Download Data
Run the data download script to fetch a representative sample of subjects.
```bash
python code/download_data.py
```
*Note: This step requires internet access and may take time depending on bandwidth.*

## 3. Preprocess Data
Run the preprocessing pipeline to clean behavioral data and compute functional connectivity.
```bash
python code/preprocess_fmri.py
```

## 4. Build Graphs & Compute Modularity
Construct functional graphs and calculate modularity Q.
```bash
python code/build_graphs.py
```

## 5. Statistical Analysis
Perform regression analysis and sensitivity checks.
```bash
python code/analyze_stats.py
```

## 6. Verify Outputs
Check the `data/results/` directory for `primary_analysis.csv` and `sensitivity_analysis.csv`.
