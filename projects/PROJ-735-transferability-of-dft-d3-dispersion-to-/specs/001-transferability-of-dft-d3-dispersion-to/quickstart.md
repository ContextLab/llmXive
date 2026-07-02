# Quickstart: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local CPU-only environment with multiple cores, sufficient RAM).
- **Required Data**: You must provide the `il_benchmark.csv` and `xyz` files in `data/raw/`, and `nist_il_properties.csv` and `lattice_energy_benchmark.csv` in `data/external/`.

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-735-Transferability-DFT-D3-IL
    ```

2.  **Create a virtual environment** and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `psi4` to a CPU-compatible version.*

3.  **Prepare the data**:
    Ensure the following files are present in the `data/` directory:
    - `data/raw/il_benchmark.csv` (Must contain `pair_id`, `xyz_file`, `ccsd(t)_energy`)
    - `data/external/nist_il_properties.csv` (Optional; if missing, correlation step is skipped)
    - `data/external/lattice_energy_benchmark.csv` (Optional; if missing, lattice step is skipped)

## Execution

### Step 1: Run DFT-D3 Calculations
Execute the Psi4 benchmark. This step may take several hours on a 2-core CPU (N=30 pairs).
```bash
python code/run_psi4.py
```
*Output*: `outputs/raw_energies.csv` containing DFT energies and errors.

### Step 2: Analyze Scaling Factor
Compute the optimal scaling factor for the D term using an 80/20 hold-out split and a bootstrap CI.
```bash
python code/analyze_energies.py
```
*Output*: `outputs/scaling_factor.txt`, `outputs/benchmark_report.md`.

### Step 3: Correlate with Bulk Properties
Analyze the relationship between dispersion terms and experimental properties.
```bash
python code/analyze_bulk.py
```
*Output*: `outputs/correlation_report.md`.

### Step 4: Compare with Lattice Energies
Compare computed interaction energies with experimental lattice energies.
```bash
python code/analyze_lattice.py
```
*Output*: `outputs/lattice_energy_report.md`.

## Verification

To verify the results:
1.  Check `outputs/benchmark_report.md` for MAE/RMSE values and 95% CIs.
2.  Check `outputs/correlation_report.md` for Pearson/Spearman coefficients and p-values.
3.  Check `outputs/lattice_energy_report.md` for MAE/MSE against lattice energies.
4.  Run the test suite:
    ```bash
    pytest tests/
    ```

## Troubleshooting

- **Missing Coordinates**: If the input dataset lacks `xyz` files, the pipeline will abort with a clear error. No fallback is attempted.
- **Psi4 Convergence Failure**: The script automatically retries up to 3 times. If it fails, the entry is marked "failed" in `raw_energies.csv`.
- **Memory Error**: If the job exceeds 7GB RAM, reduce the number of parallel threads in `run_psi4.py` (currently set to 2).
- **Missing Bulk Data**: If `data/external/nist_il_properties.csv` is missing, the correlation step is skipped with a warning.
- **Missing Lattice Data**: If `data/external/lattice_energy_benchmark.csv` is missing, the lattice step is skipped with a warning.
