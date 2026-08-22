# Quickstart: Predicting Molecular Interactions in Protein-Ligand Complexes

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner or local machine with sufficient RAM for the proposed method.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Initialize Git & Create .gitignore**:
   ```bash
   git init
   echo "*.pyc" > .gitignore
   echo "__pycache__/" >> .gitignore
   echo "data/raw/*" >> .gitignore
   echo "data/processed/*" >> .gitignore
   echo "data/results/*" >> .gitignore
   echo "*.pt" >> .gitignore
   echo "*.pkl" >> .gitignore
   echo ".venv/" >> .gitignore
   ```

3. **Set Up Virtual Environment**:
   ```bash
   python -m venv code/.venv
   source code/.venv/bin/activate  # On Windows: code\.venv\Scripts\activate
   ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Dependencies include: `torch`, `torch_geometric`, `rdkit`, `datasets`, `scikit-learn`, `pandas`, `pyyaml`, `biopython`, `numpy`, `scipy`, `requests`, `flake8`, `black`.

5. **Configure Linting**:
   Create `pyproject.toml` with Black and Flake8 settings:
   ```toml
   [tool.black]
   line-length = 88
   target-version = ['py311']

   [tool.flake8]
   max-line-length = 88
   ignore = E203, W503
   ```

6. **Verify Installation**:
   ```bash
   python -c "import torch; import rdkit; print('Dependencies OK')"
   ```

## Data Preparation

1. **Download Dataset**:
   The script `code/data/ingest.py` will automatically download the PDBbind v2020 refined set from Hugging Face.
   ```bash
   python code/data/ingest.py --download
   ```

2. **Construct Graphs**:
   Run the ingestion script to build molecular graphs.
   ```bash
   python code/data/ingest.py --build-graphs
   ```

3. **Run Sensitivity Analysis** (Optional):
   ```bash
   python code/data/sensitivity.py
   ```

## Training

1. **Train the GNN**:
   ```bash
   python code/train/trainer.py --epochs 50 --timeout 4h
   ```
   - The script will automatically stop after 4 hours or 50 epochs.
   - If the run exceeds memory limits, it will attempt to offload to a Kaggle GPU (if configured).

2. **Monitor Training**:
   Check `data/results/training_log.json` for loss curves and convergence status.

## Interpretation & Validation

1. **Generate Feature Importance**:
   ```bash
   python code/interpret/attribution.py
   ```

2. **Cluster Motifs**:
   ```bash
   python code/interpret/clustering.py --min-cluster-size 5
   ```

3. **Validate Motifs**:
   ```bash
   python code/interpret/validation.py --permutations 1000
   ```

4. **View Results**:
   - Motif clusters: `data/results/motifs.json`
   - Statistical validation: `data/results/statistical_validation.json`
   - Memory profile: `data/results/memory_profile.json`
   - Inference benchmark: `data/results/inference_benchmark.json`

## Testing

Run the full test suite:
```bash
pytest tests/ -v --cov=code
```

## Troubleshooting

- **Memory Error**: Ensure `streaming=True` is used in `ingest.py`. Reduce batch size if training fails.
- **CUDA Error**: If the run requires a GPU, ensure the Kaggle GPU escape hatch is configured. The pipeline will automatically retry on Kaggle if the CPU run fails.
- **Missing Data**: Verify the Hugging Face dataset is accessible. Check network connectivity.
