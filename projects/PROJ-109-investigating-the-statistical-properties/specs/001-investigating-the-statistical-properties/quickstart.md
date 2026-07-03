# Quickstart: Investigating Statistical Properties of Simulated Dark Matter Halos

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-109-investigating-the-statistical-properties
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

## Running the Pipeline

The pipeline is designed to run end-to-end on CPU-only CI.

### Step 1: Data Generation (Simulation)
Since real data URLs are unavailable, run the synthetic data generator:
```bash
python code/main.py --mode generate
```
*This creates `data/raw/synthetic_tng.h5` and `data/raw/synthetic_millennium.h5`.*

### Step 2: Pre-processing & Metric Computation
```bash
python code/main.py --mode compute
```
*This filters halos (≥300 particles), computes shape, spin, concentration, and overdensity using memory-mapped particle streams.*

### Step 3: Statistical Analysis
```bash
python code/main.py --mode analyze
```
*This runs KS tests, Spearman correlations, and multiple-comparison corrections.*

### Step 4: Visualization
```bash
python code/main.py --mode plot
```
*Generates scatter plots, KDE curves, and heatmaps in `results/plots/`.*

## Verification

- **Check Results**: Inspect `results/statistics.json` for p-values, effect sizes, and convergence rates.
- **Check Plots**: Verify `results/plots/` contains PNG/PDF files.
- **Reproducibility**: Re-run `python code/main.py` with `--seed 42` to ensure identical results.
- **Schema Validation**: The code validates data against schemas in `code/contracts/` before writing results.

## Troubleshooting

- **Memory Error**: If running on local machine with large data, reduce `--sample-size` in `config.py`.
- **Convergence Failure**: If NFW fits fail, check `results/fit_failures.log`.
- **Missing Dependencies**: Ensure `scipy` and `scikit-learn` are installed.