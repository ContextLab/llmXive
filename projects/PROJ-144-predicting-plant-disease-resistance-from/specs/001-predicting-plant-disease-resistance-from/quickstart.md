# Quickstart: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

## Prerequisites

* Python 3.11+
* Git
* Access to GitHub Actions (for CI execution) or local environment with 7GB+ RAM.

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmxive
 ```

2. **Create virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r projects/PROJ-144-predicting-plant-disease-resistance-from/code/requirements.txt
 ```

4. **Install pre-commit hooks**:
 ```bash
 pre-commit install
 ```

## Running the Pipeline

### Step 1: Data Acquisition
Download raw data from Metabolomics Workbench.
```bash
python projects/PROJ-144-predicting-plant-disease-resistance-from/code/data/download.py --study_ids ST001234 ST005678
```
*Output*: `data/raw/intensity_table.csv`, `data/raw/phenotype_metadata.csv`

### Step 2: Preprocessing
Normalize, align, and correct batch effects.
```bash
python projects/PROJ-144-predicting-plant-disease-resistance-from/code/data/preprocess.py --input data/raw --output data/processed
```
*Output*: `data/processed/batch_corrected_matrix.csv`, `data/processed/labels.csv`

### Step 3: Model Training & Evaluation
Train Random Forest, run permutation tests, and compute diagnostics.
```bash
python projects/PROJ-144-predicting-plant-disease-resistance-from/code/models/train.py --data data/processed --output results
```
*Output*: `results/metrics.json`, `results/shap_analysis.json`

### Step 4: Interpretation
Map top metabolites to pathways and generate visualizations.
```bash
python projects/PROJ-144-predicting-plant-disease-resistance-from/code/models/interpret.py --input results/shap_analysis.json --output results/pathway_analysis.json
```
*Output*: `results/pathway_analysis.json`, `results/plots/pathway_barplot.png`

### Step 5: Verification
Run tests to ensure reproducibility and schema compliance.
```bash
pytest tests/
```

## Troubleshooting

* **Missing Data**: Ensure Metabolomics Workbench study IDs are valid and public.
* **Batch Correction Failure**: If ComBat fails, check for sufficient metabolite overlap across studies.
* **Out of Memory**: If dataset > 7GB, enable streaming mode in `download.py`.
* **VIF > 5**: This is a diagnostic flag, not an error. Review `results/shap_analysis.json` for flagged metabolites.

## Output Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Raw Data | `data/raw/` | Unmodified downloads with checksums |
| Processed Data | `data/processed/` | Normalized, batch-corrected matrices |
| Metrics | `results/metrics.json` | Balanced accuracy, ROC-AUC, p-values |
| Diagnostics | `results/shap_analysis.json` | Feature importances, VIF scores |
| Pathways | `results/pathway_analysis.json` | Mapped pathways for top metabolites |
| Plots | `results/plots/` | Visualizations (e.g., `pathway_barplot.png`) |
