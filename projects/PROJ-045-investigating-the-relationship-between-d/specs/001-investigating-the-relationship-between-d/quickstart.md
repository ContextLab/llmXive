# Quickstart: Defect Chemistry and Ionic Conductivity Analysis

## Prerequisites
- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution) or a local CPU environment with sufficient RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-045-investigating-the-relationship-between-d
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
    *Note: `requirements.txt` pins `scikit-learn`, `pymatgen`, `ase`, `pandas`, `numpy`, `matplotlib`, `seaborn`, and `pytest`.*

## Running the Pipeline

### Step 1: Data Download and Validation
Download crystal structures and experimental conductivity data.
```bash
python code/download.py
python code/validate.py
```
*Output*: `data/processed/compositions.csv` and `data/processed/defect_energies.csv` (if DFT is pre-run) or a completeness report.

### Step 2: DFT/Semi-Empirical Calculations
*Note: In CI, this runs automatically with job timeouts. Locally, run for a single test system.*
```bash
python code/dft_runner.py --test-system Li7La3Zr2O12
python code/semi_empirical.py --all
```
*Output*: `data/processed/migration_barriers.csv`.

### Step 3: Statistical Analysis
Perform regression and correlation analysis.
```bash
python code/analysis.py
```
*Output*: `data/processed/analysis_results.json` (includes raw data for plots) and plots in `data/processed/plots/`.

### Step 4: Verification
Run the test suite to ensure all components are working:
```bash
pytest tests/
```

## Troubleshooting
- **RAM Error**: If DFT fails due to memory, the pipeline automatically falls back to semi-empirical methods for that composition.
- **Missing Data**: Check `logs/completeness_report.txt` to see which variables are missing for specific compositions.
- **Plot Generation**: The `analysis_results.json` file contains `x_values`, `y_values`, and `pca_components` for each defect type, allowing direct regeneration of plots without re-running the regression.