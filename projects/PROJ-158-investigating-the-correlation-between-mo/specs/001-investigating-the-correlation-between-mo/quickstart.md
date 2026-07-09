# Quickstart: Investigating the Correlation Between Molecular Structure and Dye‑Sensitized Solar Cell Performance

## Prerequisites
- Python +
- Git
- GB+ RAM available

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` includes `torch` (CPU version), `torch-geometric`, `rdkit`, and `scikit-learn`.*

## Running the Pipeline

The entire pipeline can be executed via the main orchestration script:

```bash
python code/main.py
```

This script performs the following steps in order:
1. **Download & Verify**: Fetches the dataset from the verified HuggingFace URL and checks the checksum.
2. **Preprocess**: Standardizes SMILES, removes salts, canonicalizes tautomers, and generates graph features.
3. **Train**: Executes scaffold-aware cross-validation for both GCN and Random Forest.
4. **Evaluate**: Computes MAE, RMSE, R², and performs the paired t-test.
5. **Interpret**: Extracts top motifs using Integrated Gradients.

## Expected Outputs

Upon successful completion, the following files will be generated in `data/outputs/`:

- `metrics.json`: Performance metrics for all folds and models.
- `motifs.csv`: List of top recurring motifs with importance scores.
- `failed_molecules.log`: Log of any molecules that could not be parsed.
- `training_stats.json`: Runtime and resource usage statistics.

## Troubleshooting

- **Timeout**: If the job exceeds 5h 30m, the script will exit with a "Time Limit Exceeded" status. Check `training_stats.json` for partial results.
- **Dataset Error**: If the dataset download fails or checksum mismatch occurs, the script will exit with a clear error message citing the URL and expected hash.
- **Memory Error**: If OOM occurs, reduce the `hidden_size` in `code/models/gcn.py` (though the upper bound is constrained by the specification).
