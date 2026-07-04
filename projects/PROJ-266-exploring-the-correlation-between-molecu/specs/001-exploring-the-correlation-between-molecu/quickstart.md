# Quickstart: Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes

## Prerequisites

- Python 3.11+  
- pip  
- Git  

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-266-exploring-the-correlation-between-molecu
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

## Running the Pipeline

### 0. Feasibility Gate (Benchmark)
```bash
python code/main.py --benchmark --subset-size 100
```
- Estimates total runtime on a subset of 100 molecules.  
- If estimated runtime > 4 hours, dataset will be sampled to 500 molecules.  
- Pass/fail criterion: Estimated runtime ≤ 6 hours.

### 1. Fetch and Validate Data
```bash
python code/fetch_chembl.py --output data/raw/chembl_caco2_raw.csv
python code/validate_data.py --input data/raw/chembl_caco2_raw.csv --output data/processed/validated_molecules.csv
```
- Outputs ≥500 valid records (SMILES + logPapp non-NULL).  
- Logs excluded records due to protocol heterogeneity.

### 2. Generate Conformers and Compute Descriptors
```bash
python code/generate_conformers.py --input data/processed/validated_molecules.csv --output data/processed/conformers.parquet --conformers 20
python code/compute_flexibility.py --input data/processed/conformers.parquet --output data/processed/flexibility_descriptors.csv
```
- Generates 20 conformers per molecule (CPU-feasible).  
- Computes bond, angle, dihedral variance (Å² for bonds, rad² for angles/dihedrals).  
- Requires ≥450 valid descriptors.  
- Performs convergence check on a subset to ensure variance stability.

### 3. Correlation Analysis
```bash
python code/correlation_analysis.py --input data/processed/flexibility_descriptors.csv --output data/processed/correlation_results.json
```
- Computes Pearson/Spearman correlations with p-values and FDR correction.  
- Flags results as associational.

### 4. Model Building and Visualization
```bash
python code/regression_model.py --input data/processed/flexibility_descriptors.csv --output data/processed/model_results.json
python code/visualize.py --input data/processed/correlation_results.json --output figures/flexibility_vs_permeability.png
```
- Scaffold-based 5-fold cross-validation (R², RMSE, MAE).  
- VIF diagnosis and Ridge regression fallback if collinearity detected.  
- Generates scatter plot with 95% CI (300 dpi).

## Output Artifacts

- `data/processed/validated_molecules.csv`  
- `data/processed/flexibility_descriptors.csv`  
- `data/processed/correlation_results.json`  
- `data/processed/model_results.json`  
- `figures/flexibility_vs_permeability.png`  

## Troubleshooting

- **Conformer generation fails**: Check SMILES validity; skip invalid molecules.  
- **Runtime exceeds 6h**: Reduce sample size to 500 molecules in `fetch_chembl.py`.  
- **Memory error**: Sample dataset to 500 molecules; reduce conformers to 10.  
- **Collinearity detected**: Ridge regression fallback will be automatically applied.  
- **Variance not stable**: Convergence check will flag this; consider increasing conformer count if feasible.

## Notes

- **Conformer Limit**: 20 conformers (not 50) for CPU feasibility.  
- **Associational Only**: No causal claims; results framed as correlations.  
- **Reproducibility**: Random seeds pinned; re-run from scratch for validation.  
- **Feasibility Gate**: Benchmark task ensures runtime ≤ 6 hours before full execution.
