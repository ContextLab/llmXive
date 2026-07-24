# Quickstart: Predicting Molecular Permeability Coefficients

## Prerequisites

- Python 3.10+
- Git
- Access to GitHub Actions (for CI) or local environment with sufficient RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-522-predicting-molecular-permeability-coeffi
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `torch-geometric` must be installed for CPU only. Do not install CUDA versions.*

## Running the Pipeline

### Step 1: Data Ingestion & Graph Construction
This step downloads the dataset, parses SMILES, and computes descriptors.
```bash
python code/ingestion.py --dataset "fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors" --output data/processed/molecules.csv
```
- **Output**: `data/processed/molecules.csv` (contains graphs and descriptors).
- **Time**: < 15 minutes (enforced by timeout).

### Step 2: Model Training (5-Fold CV)
Trains GNN, RF, and LR models.
```bash
python code/training.py --input data/processed/molecules.csv --output data/processed/predictions.csv --seed 42
```
- **Output**: `data/processed/predictions.csv` (metrics and predictions).
- **Time**: < 2 hours on CPU (enforced by timeout).
- **Note**: If this step times out on CPU, the system will flag for GPU offload (Kaggle).

### Step 3: Sensitivity Analysis
Performs uncertainty quantification.
```bash
python code/analysis.py --predictions data/processed/predictions.csv --output data/processed/sensitivity_results.json
```
- **Output**: `data/processed/sensitivity_results.json`.

### Step 4: Generate Report
Compiles the final findings.
```bash
python code/report.py --predictions data/processed/predictions.csv --sensitivity data/processed/sensitivity_results.json --output results/final_report.md
```
- **Output**: `results/final_report.md` (includes required associational disclaimer and domain shift note).

## Testing

Run the unit and integration tests:
```bash
pytest tests/ -v
```

## Troubleshooting

- **RDKit Parse Error**: Logs will show the specific SMILES string that failed. Check for invalid valency.
- **Memory Error**: If `torch` runs out of RAM, reduce the dataset size or use `streaming=True` in the ingestion script.
- **Timeout**: If training exceeds 2 hours, the run is terminated. Consider reducing the number of epochs or using the GPU escape hatch.
- **Domain Shift**: Note that the study uses general ADMET data as a proxy for polymeric membrane permeability due to data availability.