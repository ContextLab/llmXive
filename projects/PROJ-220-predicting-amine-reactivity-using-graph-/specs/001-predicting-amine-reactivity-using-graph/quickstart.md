# Quickstart: Predicting Amine Reactivity Using Graph Neural Networks

## Prerequisites

- Python 3.11+
- `pip`
- Access to a GitHub Actions runner (or local environment with 7GB+ RAM)
- (Optional) API keys for ChEMBL/NIST if rate-limited (usually not required for public access)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` includes pinned versions of `rdkit`, `torch` (CPU), `torch-geometric`, `shap`, `datasets`, `chembl_webresource_client`, `mordred`.*

## Data Ingestion & Preprocessing

Run the ingestion pipeline to download and process the ChEMBL/NIST dataset:

```bash
python src/data/ingestion.py --output data/processed/reaction_records.parquet
```

*   This script fetches data from the verified ChEMBL/NIST sources.
*   It filters for primary/secondary amines, normalizes rates, and calculates pKa.
*   It logs excluded records to `logs/ingestion_audit.log`.

## Descriptor Computation

Compute the external descriptors for validation:

```bash
python src/data/descriptors.py --input data/processed/reaction_records.parquet --output data/processed/descriptor_vectors.parquet
```

*   This generates a `DescriptorVector` for every record using `mordred` and `rdkit`.

## Graph Construction

Convert the processed reaction records into graph objects:

```bash
python src/data/preprocessing.py --input data/processed/reaction_records.parquet --output data/processed/graph_dataset.pt
```

*   This generates a PyTorch Geometric dataset with heterogeneous node/edge features.

## Model Training

Train both the baseline and the GNN model:

```bash
python src/train.py --config config/training_config.yaml
```

*   **Output**:
    *   `artifacts/baseline_model.pkl`
    *   `artifacts/gnn_model.pt`
    *   `artifacts/predictions.csv`
    *   `artifacts/metrics.json` (R², MAE for both models)

## Interpretability Analysis

Run SHAP analysis on the trained GNN:

```bash
python src/models/interpret.py --model artifacts/gnn_model.pt --data data/processed/graph_dataset.pt --output artifacts/shap_analysis.json
```

*   This generates a ranked list of atomic features and visualizations.
*   It also computes the correlation with the descriptor vectors and checks for collinearity.

## Verification

Run the test suite to ensure data integrity and model performance:

```bash
pytest tests/ -v
```

*   Includes contract tests against the YAML schemas in `contracts/`.
*   Includes unit tests for chemistry utilities (pKa, SMILES validation, descriptor computation).

## Troubleshooting

*   **OOM Error**: If you encounter Out-of-Memory errors, reduce the `max_molecule_size` in `config/training_config.yaml` or enable `streaming=True` in the ingestion script.
*   **Invalid SMILES**: Check `logs/ingestion_audit.log` for records skipped due to invalid SMILES.
*   **CUDA Error**: If running locally with a GPU, ensure `torch` is installed with CUDA support. On GitHub Actions, the script will default to CPU.
*   **Descriptor Calculation Failed**: Ensure `mordred` is installed and the molecule has 3D conformers generated (if required).