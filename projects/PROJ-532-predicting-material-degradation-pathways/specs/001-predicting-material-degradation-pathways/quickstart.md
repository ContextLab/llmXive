# Quickstart: Predicting Material Degradation Pathways from Compositional Data

## Prerequisites

- Python 3.11+
- Access to the specific Zenodo corrosion dataset (, to be verified in `research.md`).
- A minimal number of CPU cores, 7GB RAM (GitHub Actions Free Tier compatible).

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Execution Steps

### Step 1: Data Ingestion & Validation
Run the ingestion script. This will attempt to fetch the Zenodo dataset, filter for alloys, and log retention stats.
```bash
python code/ingestion.py
```
*Output*: `data/processed/cleaned_alloys.csv`, `data/processed/retention_audit.json`

### Step 2: Literature Review & Vector Construction
Construct the Reference Importance Vector from the review papers.
```bash
python code/literature_review.py
```
*Output*: `data/contracts/literature_vector.json`

### Step 3: Data Splitting (OOD)
Split data by alloy class to create the OOD test set.
```bash
python code/preprocessing.py --split-strategy class-based
```
*Output*: `data/processed/train_set.parquet`, `data/processed/test_ood_set.parquet`

### Step 4: Model Training
Train the Random Forest classifier.
```bash
python code/training.py
```
*Output*: `results/model_artifact.pkl`

### Step 5: Evaluation & Explainability
Run the full evaluation suite including permutation tests and SHAP analysis.
```bash
python code/evaluation.py
python code/explainability.py
```
*Output*: `results/metrics/performance_report.json`, `results/plots/shap_summary.png`, `results/report.md`

## Success Criteria Check

- **Retention**: `retention_audit.json` must show ≥ 70% retention and ≥ 200 records.
- **Performance**: `performance_report.json` must show Macro-F1 ≥ 0.6 and p < 0.05 against baseline.
- **Validation**: `performance_report.json` must show Spearman ρ ≥ 0.6 against `literature_vector.json`.
