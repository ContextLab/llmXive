# Quickstart: Predicting Polymer Degradation Pathways

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with ≥7GB RAM)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-078-predicting-polymer-degradation-pathways-
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This installs CPU-only versions of PyTorch and PyTorch Geometric.*

## Running the Pipeline

### 1. Data Ingestion & Preprocessing
Download the verified datasets and convert them to graph format.
```bash
python src/main.py --step ingestion
```
*Output*: `data/processed/polymer_records.csv`, `data/processed/molecular_graphs.pt`

### 2. Data Augmentation
Expand the dataset by 2x using edge dropout and subgraph sampling.
```bash
python src/main.py --step augmentation
```
*Output*: `data/processed/augmented_graphs.pt`

### 3. Model Training
Train the GNN with 5-fold CV (or LOO if n<150).
```bash
python src/main.py --step train
```
*Output*: `models/gnn_weights.pt`, `logs/training_log.json`

### 4. Feature Attribution & Statistical Analysis
Generate Integrated Gradients and run the χ² test.
```bash
python src/main.py --step analysis
```
*Output*: `reports/statistical_report.json`, `reports/motif_report.md`

### 5. Generate Final Report
Compile all results into a human-readable report.
```bash
python src/main.py --step report
```
*Output*: `reports/final_report.md`

## Verification

To verify the pipeline on a small subset:
```bash
python tests/integration/test_pipeline.py --subset 10
```
This runs the full pipeline on 10 records to ensure no crashes occur.

## Troubleshooting

- **RAM Error**: If you encounter OOM, reduce `hidden_dim` in `src/models/gnn.py` or decrease the augmentation factor.
- **Invalid SMILES**: Check `logs/ingestion.log` for skipped records.
- **No Labels**: If the dataset size is 0, check the `synthetic_labels.py` logic or the source URLs.
