# Quickstart Guide: Predicting Molecular Conductivity

This guide walks you through running the full pipeline to predict molecular conductivity from graph-based features.

## Prerequisites

- Python 3.9+
- Install dependencies: `pip install -r requirements.txt`

## 1. Prepare Data

Ensure you have a raw SMILES file in `data/raw/smiles.csv` with a `smiles` column.
If you don't have one, create a sample:

```bash
echo "smiles
c1ccccc1
C=CC=C
CCCCCC" > data/raw/sample_smiles.csv
```

## 2. Run Descriptor Pipeline

Compute graph-based descriptors for the molecules.

```bash
python code/run_descriptor_pipeline.py --input data/raw/sample_smiles.csv --output data/processed/descriptors.csv
```

## 3. Train Models

Train Random Forest and Gradient Boosting models on the descriptors.

```bash
python code/model_training.py --data data/processed/descriptors.csv --output data/processed/model_results.json
```

## 4. Run Sensitivity Analysis

Analyze model stability against outlier removal thresholds.

```bash
python code/analysis.py --data data/processed/descriptors.csv --output data/processed/sensitivity_analysis.json --thresholds 1.0 2.0 3.0
```

## 5. Generate Analysis Summary

Generate feature importance and correlation plots.

```bash
python code/save_analysis_outputs.py --data data/processed/descriptors.csv --results data/processed/model_results.json --output data/processed/analysis_summary.json --plots data/processed/corr_plot_top5.png
```

## 6. Validate

Check that all expected output files are generated:

- `data/processed/descriptors.csv`
- `data/processed/model_results.json`
- `data/processed/sensitivity_analysis.json`
- `data/processed/analysis_summary.json`
- `data/processed/corr_plot_top5.png`
