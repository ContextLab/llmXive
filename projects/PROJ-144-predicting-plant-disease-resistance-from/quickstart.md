# Quickstart Guide for llmXive Plant Disease Resistance Pipeline

This guide outlines the steps to run the full analysis pipeline.

## Prerequisites

- Python 3.9+
- Install dependencies: `pip install -r code/requirements.txt`
- Ensure you have network access to download data (if not already present).

## Step-by-Step Execution

### 1. Data Discovery & Filtering
Run these scripts to identify and filter studies.

```bash
python code/data/discover_studies.py
python code/data/filter_studies.py
```

### 2. Temporal Validation
Verify that studies contain pre-challenge metadata.

```bash
python code/data/validate_temporal.py
```

### 3. Heterogeneity Detection
Analyze label heterogeneity across studies.

```bash
python code/data/detect_heterogeneity.py
```

### 4. Label Harmonization (T015b)
Harmonize labels based on the heterogeneity report.

```bash
python code/data/harmonize.py
```

### 5. Preprocessing
Perform log-transformation, alignment, and batch correction.
**Note:** The quickstart command must match the script's argparse.
The script `code/data/preprocess.py` expects `--study_ids` or `--output`, not `--input`.

```bash
python code/data/preprocess.py --output data/processed
```

### 6. Modeling & Validation
Split data, train model, and validate.

```bash
python code/modeling/split_data.py
python code/modeling/train.py
python code/modeling/validate_model.py
```

### 7. Interpretation
Map top metabolites to pathways.

```bash
python code/modeling/interpret.py --input results/pathway_analysis.json --output results/pathway_report.json
```
*Note: Adjust arguments based on the specific script's requirements.*

## Verification

Check that the following artifacts exist:
- `data/processed/heterogeneity_report.json`
- `data/processed/harmonized_labels.csv`
- `data/processed/batch_corrected_matrix.csv`
- `results/model_validation.json`
- `results/pathway_analysis.json`

## Limitations
These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made.
