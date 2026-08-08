# Quickstart: Predicting Molecular Reactivity

## Prerequisites
- Python 3.10+
- Git
- (Optional) Docker for local testing

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-243-predicting-molecular-reactivity-using-gr
 ```

2. **Create virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify environment**:
 ```bash
 python -c "import torch; import rdkit; print('Dependencies OK')"
 ```

## Data Setup

1. **Create directories**:
 ```bash
 mkdir -p data/raw data/processed data/assets artifacts/logs
 touch data/raw/.gitkeep data/processed/.gitkeep data/assets/.gitkeep artifacts/logs/.gitkeep
 ```

2. **Curate Static Assets**:
 - **Reference Substructures**: Create `data/raw/reference_substructures_raw.csv` with known reactive substructures extracted from *J. Chem. Inf. Model.* 2020, 60, 12, 5785–5796 (). **Extract Table 2, Entries 1-50**.
 - **Kinetic Dataset**: Create `data/raw/kinetic_dataset_raw.csv` with ≥20 molecules and experimental rates extracted from *J. Phys. Chem. A* 2018, 122, 15, 4053–4062 (). **Extract Table 3, Entries 1-20**.
 - *See `specs/001-predicting-molecular-reactivity/research.md` for sources.*

3. **Download QM9**:
 The `code/data/download.py` script handles this.
 ```bash
 python code/data/download.py --dataset qm9 --output data/raw
 ```
 *Note: This uses `torch_geometric.datasets.QM9` to ensure canonical source.*

4. **Generate Checksums**:
 ```bash
 python code/utils/checksums.py --dir data/raw --output data/raw/checksums.json
 ```

## Running the Pipeline

### 1. Preprocessing
Convert SMILES to graphs and split data.
```bash
python code/data/preprocess.py --input data/raw/qm9_subset.parquet --output data/processed
```
*Note: This will generate `exclusion_report.json` and `memory_adjustment.log` if needed.*

### 2. Training
Train Spectral GNN, Heterophily GNN, and Random Forest.
```bash
python code/train/trainer.py --epochs 50 --device cpu
```
*Note: This will automatically detect memory usage and adjust batch size.*

### 3. Evaluation & Attribution
Generate metrics and feature importance maps.
```bash
python code/train/eval.py --model-path artifacts/models/ --output artifacts/
python code/interpret/explainer.py --model-path artifacts/models/ --output artifacts/
```
*Note: The explainer output is validated against `contracts/attribution.schema.yaml`.*

### 4. Validation
Validate HOMO-LUMO proxy against kinetic data.
```bash
python code/interpret/validate_proxy.py --predictions artifacts/predictions.parquet --kinetic data/raw/kinetic_dataset_raw.csv
```

### 5. SSoT Enforcement
Ensure all figures trace to the artifacts.
```bash
python code/utils/ssot.py --metrics artifacts/metrics.json --predictions artifacts/predictions.parquet
```

## Expected Artifacts
After a successful run, `artifacts/` should contain:
- `metrics.json`: MSE, MAE, Pearson R for all models.
- `predictions.parquet`: Test set predictions.
- `attribution_maps.json`: Feature importance scores.
- `exclusion_report.json`: Log of invalid SMILES.
- `logs/pipeline.log`: Detailed execution log.

## Troubleshooting
- **Memory Error**: The script should auto-reduce batch size. If it fails, manually set `--batch-size 32` in `trainer.py`.
- **Download Failed**: Check network connectivity. The script retries 3 times.
- **Invalid SMILES**: Check `artifacts/exclusion_report.json`. If > 0.1%, investigate the `data/raw` source.
