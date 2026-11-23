# Quick Start Guide

## Prerequisites
- Python 3.9+
- pip

## Installation
```bash
pip install -r requirements.txt
```

## Running the Pipeline
The full pipeline can be executed using the master script:
```bash
python code/run_pipeline.py
```

## Individual Steps
If you want to run steps individually:

1. **Ingest Data**
 ```bash
 python code/ingest.py
 ```

2. **Calculate Descriptors**
 ```bash
 python code/descriptors.py
 ```

3. **Standardize and Stratify**
 ```bash
 python code/standardize.py
 ```

4. **Run Analysis**
 ```bash
 python code/analysis.py
 ```

5. **Generate Visualizations**
 ```bash
 python code/viz.py
 ```

6. **Generate Report**
 ```bash
 python code/report.py
 ```

7. **Verify Outputs (T036)**
 ```bash
 python code/verify_outputs.py
 ```

## Output Artifacts
- `data/processed/merged_drugs.csv`
- `data/processed/standard_subset.csv`
- `data/processed/analysis_results.json`
- `data/outputs/scatter_tpsa_vs_half_life.png`
- `data/outputs/residuals.png`
- `data/outputs/qq_plot.png`
- `results_report.md` (or `data/data_insufficiency_report.md`)
- `reproducibility_log.json`