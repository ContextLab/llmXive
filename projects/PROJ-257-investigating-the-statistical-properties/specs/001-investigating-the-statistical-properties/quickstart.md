# Quickstart: Statistical Properties of Simulated Black Hole Mergers

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to the internet (for downloading GWTC data)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-257-investigating-the-statistical-properties
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `numpy`, `scipy`, `pandas`, `matplotlib`, `requests`, `tqdm`.*

## Execution

### 1. Run the Full Pipeline

Execute the main entry point. This will:
- Download GWTC data (if available).
- Generate synthetic data (if no external source).
- Perform KDE and KS tests.
- Run sensitivity analysis.
- Perform formal power analysis (MDES).
- Generate plots and reports.

```bash
python src/main.py
```

### 2. Expected Outputs

Upon successful completion, the following files will be generated in the `output/` directory:

- `results/statistical_tests.json`: KS statistics, p-values, and scope (detection/intrinsic).
- `results/power_analysis.json`: MDES (simulation-based) and power limitation notes.
- `figures/kde_mass_ratio.png`: Distribution plot for mass ratio.
- `figures/kde_effective_spin.png`: Distribution plot for effective spin.
- `report/summary.md`: Final human-readable report.

### 3. Verification

To verify the pipeline runs within constraints:

```bash
# Run with timing
time python src/main.py
```

Check `output/logs/pipeline.log` for:
- `CHECKSUM_VERIFIED: True`
- `POWER_LIMITATION: [True/False]`
- `MDES_CALCULATED: True`
- `RUNTIME: < 6h`

## Troubleshooting

- **GWTC Download Failed**: If Zenodo is unreachable, the pipeline will retry 3 times. If it still fails, check your internet connection. The pipeline will halt with an explicit error.
- **Memory Error**: If you encounter `MemoryError`, reduce the `SAMPLES_PER_EVENT` in `src/config.py` (default 1000).
- **Schema Mismatch**: If the synthetic data generation fails, ensure `numpy` is installed and the random seed is valid.
- **Selection Bias**: If the formal selection function files are missing, the report will explicitly state that the analysis is restricted to "detection space" and no intrinsic population claims are made.