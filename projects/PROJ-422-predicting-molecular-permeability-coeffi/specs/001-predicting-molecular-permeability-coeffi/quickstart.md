# Quickstart: Molecular Permeability GNN Pipeline

## Prerequisites
- Python 3.11+
- Git
- Access to Hugging Face (for dataset download)

## Installation
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-422-predicting-molecular-permeability-coeffi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Data Preparation
The pipeline automatically downloads data from the verified Hugging Face sources.
```bash
# Run the download script
python code/data/download.py
```
*Note: If the target column is missing in the downloaded dataset, the script will log a warning and proceed with the calculated logP as a proxy target.*

## Running the Pipeline
Execute the full pipeline (Preprocess -> Train -> Evaluate -> Explain):
```bash
python code/analysis/train.py --config config.yaml
```

## Manual Steps
1. **Preprocess**: `python code/data/preprocess.py`
2. **Train GNN**: `python code/models/gnn.py --epochs 50`
3. **Train RF**: `python code/models/rf.py`
4. **Train RF Ablation**: `python code/models/rf.py --mode ablation`
5. **Evaluate**: `python code/analysis/evaluate.py`
6. **Explain**: `python code/analysis/explain.py`

## Output
- `data/processed/processed_data.parquet`: Cleaned features.
- `results/metrics.json`: RMSE, MAE, R², p-value, bias_warning.
- `results/interpretability/`: SHAP/GNNExplainer plots.