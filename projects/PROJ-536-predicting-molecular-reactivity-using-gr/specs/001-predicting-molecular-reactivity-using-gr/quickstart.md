# Quickstart: Predicting Molecular Reactivity Using Graph Neural Networks and Reaction Datasets

## Prerequisites

- Python 3.11+
- Git
- GB+ Free RAM (during execution)
- GB+ Free Disk

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-536-predicting-molecular-reactivity-using-gr
    python -m venv venv
    source venv/bin/activate  # or `venv\Scripts\activate` on Windows
    ```

2.  **Install Dependencies**:
    ```bash
    # Ensure CPU-only torch is installed
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install torch-geometric
    pip install -r requirements.txt
    ```

3.  **Verify Environment**:
    ```bash
    python -c "import torch; import rdkit; print('CPU:', torch.cuda.is_available())"
    # Output should be: CPU: False
    ```

## Running the Pipeline

### 1. Data Download & Parsing
Download the USPTO subset and convert SMILES to graphs. This step validates data and logs invalid entries.
**Note**: This step includes a schema check for the `yield` column. If missing, the pipeline will halt.
```bash
python src/data/download.py --source ufukhaman
python src/data/parse.py --input data/raw/uspto_subset.parquet --output data/processed/graphs.h5
```
*Check `logs/parse.log` for skipped entries and schema validation results.*

### 2. Training
Train the GNN and baselines using 5-Fold Cross-Validation.
```bash
python src/models/train.py --epochs 200 --patience 5 --device cpu --cv-folds 5
```
*Output: `models/mpnn_fold_{N}.pt`, `models/baselines_fold_{N}.pkl`, `logs/training_history.json`*

### 3. Evaluation & Comparison
Evaluate performance, compute statistical significance, and compare models.
```bash
python src/analysis/evaluate.py
```
*Output: `results/metrics_comparison.json` (includes p-values and CIs), `results/significance_report.txt`*

### 4. Explainability & Uncertainty
Generate subgraph explanations (with disclaimers) and prediction intervals.
```bash
python src/models/explainers.py --model models/mpnn_fold_1.pt
python src/analysis/uncertainty.py --model models/mpnn_fold_1.pt
```
*Output: `results/subgraph_patterns.csv` (includes mandatory warning), `results/prediction_intervals.csv`*

## Validation

- **Check Metrics**: Ensure MAE < 15.0 and R² is reported for all models.
- **Check Intervals**: Verify `upper_bound > lower_bound` in `prediction_intervals.csv`.
- **Check Coverage**: Ensure the empirical coverage rate is reported in the logs.
- **Check Time**: The full run should complete within 6 hours on a 2-core CPU.
- **Check Disclaimers**: Verify that all subgraph pattern outputs include the mandatory associational disclaimer.