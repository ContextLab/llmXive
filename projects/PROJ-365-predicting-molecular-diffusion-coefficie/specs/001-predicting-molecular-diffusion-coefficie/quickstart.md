# Quickstart: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with 7GB+ RAM)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd projects/PROJ-365-predicting-molecular-diffusion-coefficie
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` pins CPU-only versions of PyTorch, PyTorch Geometric, and `thermo`.*

## Data Preparation

1. **Prepare your dataset**:
 - The pipeline uses the NIST TRC database via the `thermo` library.
 - Ensure you have internet access to query NIST.
 - If offline, place a CSV file with columns: `smiles`, `solvent`, `diffusion_coeff`, `viscosity`, `dielectric` in `data/raw/diffusion_data.csv`.

2. **Run the ingestion script**:
 ```bash
 python code/ingestion.py --input data/raw/diffusion_data.csv --output data/processed/featurized_data.jsonl
 ```
 - This script validates SMILES, handles missing data, and generates graph representations.
 - Check `logs/ingestion.log` for excluded records.

## Training

1. **Train the models**:
 ```bash
 python code/train.py --data data/processed/featurized_data.jsonl --epochs 50 --folds 5 --seed 42
 ```
 - This runs 5-fold cross-validation for the MPNN, Linear Baseline 1, and Linear Baseline 2.
 - Models are saved to `code/models/`.

## Evaluation

1. **Generate results**:
 ```bash
 python code/eval.py --models code/models/ --data data/processed/featurized_data.jsonl
 ```
 - Outputs `docs/reports/results.json` with Pearson r, RMSE, and Wilcoxon test results.

## Sensitivity Analysis

1. **Run sensitivity sweep**:
 ```bash
 python code/sensitivity.py --models code/models/ --data data/processed/featurized_data.jsonl --steps 1,2,3
 ```
 - Tests different message passing steps and performs ablation (removing solvent descriptors).

## Verification

To verify the pipeline on a small scale:
```bash
pytest tests/unit/ -v
pytest tests/integration/test_pipeline.py -v
```

## Troubleshooting

- **Memory Error**: Reduce the dataset size in `ingestion.py` or increase the `--sample-size` flag.
- **SMILES Error**: Check `logs/ingestion.log` for invalid SMILES strings.
- **CUDA Error**: Ensure `torch.cuda.is_available()` returns `False` in your environment; the script should enforce CPU usage.
- **NIST Connection Error**: Check internet connectivity; if offline, use the local CSV fallback.