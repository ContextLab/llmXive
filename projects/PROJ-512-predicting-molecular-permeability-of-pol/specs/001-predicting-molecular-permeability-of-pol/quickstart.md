# Quickstart: Predicting Molecular Permeability of Polymers via Graph Neural Networks

## Prerequisites

- Python 3.11+
- Git
- (Optional) Docker for local testing (matches CI environment).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-512-predicting-molecular-permeability-of-pol/code/
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins versions to ensure reproducibility on CPU-only runners.*

## Data Preparation

**Important**: The verified dataset list does not include a source for experimental permeability values. The pipeline expects a local mock file for testing.

1. **Download SMILES**:
   The script will attempt to fetch SMILES from the verified PubChem URL.
   ```bash
   python data/ingestion.py --download-pubchem
   ```

2. **Generate Mock Permeability**:
   Since no verified permeability data exists, generate a mock target for pipeline validation:
   ```bash
   python data/ingestion.py --generate-mock-target
   ```
   *This creates `data/mock_permeability.csv` with synthetic values correlated to molecular weight.*

## Running the Pipeline

Execute the full training and evaluation pipeline:

```bash
python main.py
```

**What this does**:
1. Loads and cleans data.
2. Constructs graphs and splits by scaffold.
3. Trains GNN, Random Forest, and Linear Regression baselines.
4. Runs 5-fold cross-validation.
5. Performs statistical tests (Wilcoxon, VIF, Sensitivity).
6. Outputs `results/report.json`.

## Verification

Check the output:
- `results/report.json`: Contains R², MAE, p-values.
- `logs/pipeline.log`: Confirms scaffold split integrity and graph construction.

**Expected Outcome**:
- GNN R² > 0.0 (better than dummy).
- Wilcoxon p-value calculated (may be > 0.05 with mock data).
- VIF report generated.

## Troubleshooting

- **OOM Error**: Reduce `--max-records` in `main.py` to 1000.
- **No Permeability Data**: Ensure `--generate-mock-target` was run. The pipeline cannot run without a target variable.
