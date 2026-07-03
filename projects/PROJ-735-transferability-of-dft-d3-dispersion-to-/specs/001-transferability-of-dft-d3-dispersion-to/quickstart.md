# Quickstart: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Prerequisites
- Python 3.11+
- `pip`
- Access to a GitHub Actions runner or a local Linux environment with sufficient RAM.
- **Note**: This project requires `psi4` which may require compilation or a specific conda environment.

## Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-735-transferability-of-dft-d3-dispersion-to-
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   # Install Psi4 (CPU-only) and Python packages
   # Note: On GitHub Actions, use the pre-built wheel or conda-forge channel if available
   pip install -r code/requirements.txt
   
   # If using conda for Psi4 (recommended for complex deps):
   # conda install -c psi4 psi4
   ```

4. **Prepare Data**
   - Ensure `data/IL-Benchmark-local.zip` is present (Primary Source).
   - Ensure `data/experimental_bulk_properties.csv` is present (Primary Source).
   - The pipeline will **not** attempt to download from Zenodo/NIST as these URLs are empty in the spec.

## Running the Pipeline

Execute the full workflow:
```bash
python code/load_data.py && \
python code/run_psi4.py && \
python code/analyze_energies.py && \
python code/derive_scaling.py && \
python code/correlate_bulk.py && \
python code/generate_reports.py
```

Or run the master script (if provided):
```bash
python code/main.py
```

## Expected Outputs

- `data/derived/raw_energies.csv`: Benchmark results.
- `data/derived/scaling_factor.txt`: The fitted scaling factor `s`.
- `data/derived/correlation_results.csv`: Statistical analysis.
- `docs/benchmark_report.md`: Final report with MAE, RMSE, and correlation plots.

## Troubleshooting

- **Psi4 Convergence Failures**: The script retries up to 3 times. If it fails, the entry is logged as "failed" and skipped.
- **Memory Errors**: If RAM exceeds 7 GB, reduce the batch size in `code/run_psi4.py` (default is 5 pairs per batch).
- **Data Errors**: Ensure the local fallback files contain the required columns (`pair_id`, `reference_energy`, etc.).