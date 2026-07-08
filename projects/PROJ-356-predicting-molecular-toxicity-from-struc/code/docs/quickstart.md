# Quick Start Guide

## Prerequisites
- Python 3.8+
- Required packages listed in `requirements.txt`

## Installation
```bash
pip install -r requirements.txt
```

## Running the Pipeline
The full pipeline can be executed via:
```bash
python code/src/pipeline/run.py
```

## Data Acquisition
The pipeline automatically downloads real mutagenicity data from verified sources (HuggingFace/UCI) with SHA-256 checksum validation.

## Expected Outputs
After execution, results will be available in:
- `code/results/metrics_baseline.json`: ROC-AUC, F1, and statistical test results
- `code/results/oof_predictions_fold_*.json`: Out-of-fold predictions
- `code/results/oof_predictions_final.json`: Aggregated OOF predictions

## Validation
The pipeline enforces:
- Minimum sample size (N > 1000)
- Specific assay identification (e.g., PubChem AID 1851)
- Reproducibility standard (5-fold CV x 3 repeats)

## Statistical Analysis
DeLong's test is performed on Out-of-Fold predictions to determine statistical significance at α=0.05.

## Error Analysis
False negatives from the rule-based model are analyzed via Murcko scaffold extraction to identify missing structural motifs.
