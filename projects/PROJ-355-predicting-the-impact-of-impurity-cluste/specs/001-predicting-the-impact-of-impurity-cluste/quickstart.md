# Quickstart: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Prerequisites

- Python 3.11+
- `pip` and `venv`
- Access to GitHub Actions (for CI) or a local machine with ≥ 7 GB RAM.
- Network access to HuggingFace (for OQMD data) and Materials Project API (for fallback).
- **Optional**: MP API key (set `MP_API_KEY` environment variable for fallback source).

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
   *Note: `requirements.txt` pins `scikit-learn`, `statsmodels`, `pymatgen`, `ase`, `numpy`, `pandas`.*

## Data Preparation

The pipeline automatically downloads and processes data.

1. **Run the main pipeline**:
   ```bash
   python code/main.py --mode full
   ```
   This executes:
   - `download.py`: Fetches OQMD bulk configs (sampled to a representative subset) and MP configs (if needed).
   - `gb_builder.py`: Constructs GB supercells.
   - `descriptors.py`: Computes interface clustering descriptors.
   - `simulate_energy.py`: Computes segregation energies (NIST EAM potential, Leave-One-Out method).
   - `train_model.py`: Trains the model, runs power analysis, and performs sensitivity analysis.

2. **Verify data**:
   Check `data/processed/training_set.csv` for non-empty rows.
   Check `data/metadata.yaml` for checksums and validation results.

## Running the Analysis

If you wish to run the analysis step separately (assuming data is already prepared):

```bash
python code/train_model.py --input data/processed/training_set.csv --output results/metrics.json
```

## Expected Outputs

- `results/metrics.json`: Contains R², RMSE, p-values (raw and adjusted), VIF scores, and descriptive framing.
- `results/sensitivity.json`: RMSE variance across 3 threshold values (25th, 50th, 75th percentiles).
- `data/processed/training_set.csv`: The final dataset used for modeling.

## Troubleshooting

- **Data Unavailable**: If OQMD/MP download fails after 3 retries, the script logs `[DATA_UNAVAILABLE]` and exits. Check network connectivity or API key.
- **Simulation Unavailable**: If local simulation fails after 3 retries, the script logs `[SIMULATION_UNAVAILABLE]` and excludes the entry.
- **Memory Error**: If RAM usage exceeds 7 GB, reduce the `--sample-size` argument in `main.py`.
- **Collinearity Warning**: If VIF ≥ 10, the script logs a warning and generates a descriptive framing string. Interpret coefficients jointly.
- **P-value Error**: If the model fails to converge, check for perfect multicollinearity or zero variance features.
- **Ground Truth Mismatch**: If DFT validation error > 0.1 eV, the script flags the potential as invalid and halts.

## CI Execution

The pipeline is designed to run on GitHub Actions free-tier.
- **Time Limit**: ≤ 6 hours.
- **Resources**: 2 CPU, 7 GB RAM.
- **Command**: `python code/main.py --mode ci` (enables sampling, simplified potential, and power analysis loop).