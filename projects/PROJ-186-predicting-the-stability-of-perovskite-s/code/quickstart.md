# Quickstart Guide

This guide outlines the steps to run the full pipeline and verify artifacts.

## Prerequisites
- Python 3.11+
- Virtual environment activated
- Dependencies installed (`pip install -r requirements.txt`)

## Execution Steps

1. **Data Download**
 Fetches real data from Materials Project and OQMD.
 ```bash
 python code/data/download.py
 ```
 *Output: `data/raw/mp_oqmd_combined.json` (or similar raw format)*

2. **Descriptor Calculation**
 Calculates physical descriptors (tolerance factor, octahedral factor, etc.).
 ```bash
 python code/data/descriptors.py
 ```
 *Output: `data/raw/descriptors_calculated.csv`*

3. **Preprocessing**
 Cleans data, handles nulls, and saves the final features dataset.
 ```bash
 python code/data/preprocess.py
 ```
 *Output: `data/processed/features.csv`*

4. **Verification (T018)**
 Verifies that `decomposition_energy` has zero nulls.
 ```bash
 python code/data/verify_nulls.py
 ```
 *Output: Console assertion result, logs to `logs/pipeline.log`*

5. **Model Training**
 Trains the RandomForest model with grid search.
 ```bash
 python code/models/train.py
 ```
 *Output: `results/model.pkl`, `results/metrics.json`, `results/feature-importance.png`*

6. **Virtual Screening**
 Generates hypothetical library and predicts stability.
 ```bash
 python code/data/generate_library.py
 python code/models/predict.py
 python code/models/screening_full.py
 ```
 *Output: `data/processed/hypothetical_library.csv`, `results/screening_full.csv`*

7. **Report Generation**
 Generates the markdown report of top candidates.
 ```bash
 python code/models/generate_candidates_report.py
 ```
 *Output: `results/screening_candidates.md`*

8. **Visualization**
 Generates plots.
 ```bash
 python code/viz/plot.py
 ```
 *Output: `results/predicted-vs-true.png`*

## Validation
Run the final validation script to ensure all artifacts are present and valid.
```bash
python code/quickstart_validate.py
```
