# Quickstart Guide

## Prerequisites
- Python 3.8+
- Install dependencies: `pip install -r requirements.txt`

## 1. Data Cleaning
Run the cleaning pipeline to generate `data/processed/cleaned_sessions.csv`.
```bash
python -m code.analysis.clean_data --input data/raw --output data/processed/cleaned_sessions.csv
```

## 2. Normality Audit (T022)
Run the Shapiro-Wilk normality test on difference scores.
```bash
python -m code.analysis.run_normality_audit --input data/processed/cleaned_sessions.csv --output data/processed/normality_log.txt
```

## 3. Statistical Analysis
Run the full analysis pipeline (ANOVA, Holm-Bonferroni).
```bash
python -m code.analysis.run_analysis --input data/processed/cleaned_sessions.csv --output data/processed/metrics_summary.csv
```

## 4. Visualization
Generate publication-quality plots.
```bash
python -m code.analysis.run_visualizations --input data/processed/cleaned_sessions.csv --output figures/
```

## 5. Notebook Execution
Validate the full pipeline via Jupyter.
```bash
python -m code.analysis.run_notebook_validation
```