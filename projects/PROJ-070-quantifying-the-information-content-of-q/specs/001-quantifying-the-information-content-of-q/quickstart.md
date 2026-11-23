# Quickstart: Quantifying the Information Content of Quantum Entanglement in Many-Body Systems

## Prerequisites

- Python 3.11+
- Git
- Access to a CPU-only environment (GitHub Actions free-tier compatible).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-070-quantifying-the-information-content-of-q
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Setup

### Primary: Internal Generation (Recommended)
Since no verified external dataset exists for N=10-40, the pipeline generates data internally:
1. Run the generation script:
   ```bash
   python code/data_loader.py --generate --max-spins 40 --count 50
   ```
   *Note: This uses Exact Diagonalization for N<=20 and DMRG (TeNPy) for N>20.*

### Option B: Use External Dataset (Fallback)
If a verified dataset is later discovered:
1. Set the environment variable `DATASET_ID` to the dataset identifier.
2. Run the data fetch script:
   ```bash
   python code/data_loader.py --fetch --dataset-id <ID>
   ```
   *Note: The script will validate the download and checksum.*

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py
```

This will:
1. Load or generate wavefunctions.
2. Compute entanglement entropy (sparse SVD) and compression complexity (on reduced representations).
3. Generate null models (random product, Haar).
4. Perform correlation analysis (stratified/partial) and bootstrap resampling.
5. Generate visualizations in `data/processed/figures/`.

## Verification

To verify the results:
```bash
pytest tests/
```

Check the output logs for:
- `E_DATA_INSUFFICIENT` if valid data points < 8.
- `E_DATASET_MISSING` if no data source was found (should not occur with internal generation).

## Expected Output

- **Console**: Summary of correlation coefficients and p-values (including partial correlation controlling for N).
- **Files**:
  - `data/processed/metrics.parquet`: Raw metrics (including NCD).
  - `data/processed/correlation_results.json`: Statistical outcomes.
  - `data/processed/figures/scatter_plot.png`: Visualization of entropy per spin vs. NCD.

## Troubleshooting

- **Memory Error**: If running on N>30 spins, ensure sparse matrix handling is enabled in `metrics.py`.
- **DMRG Convergence**: If DMRG fails for N>20, reduce the target truncation error or increase sweep count in `data_loader.py`.
- **Compression Failure**: Check file permissions and disk space in `/tmp/`.
- **Numerical Instability**: If many NaNs appear, check the quantization step in `metrics.py`.