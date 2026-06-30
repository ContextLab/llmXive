# Quickstart: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Prerequisites

- Python 3.11+
- `git`
- Access to a terminal (Linux/macOS/WSL)

## Installation

1. **Clone the repository** and navigate to the project directory:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-476-quantifying-correlations-between-solar-w
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Dependencies include: `pandas`, `numpy`, `scipy`, `matplotlib`, `requests`, `pytest`.*

## Running the Pipeline

### Step 1: Data Acquisition (Real Data)

The pipeline uses the verified OMNI2 dataset which contains real solar wind composition and geomagnetic indices.

```bash
python code/main.py --mode run --data-source ""
```

*Flags:*
- `--data-source`: URL to the OMNI2 CSV data.

### Step 2: Analysis & Validation

The command above executes the full pipeline:
1. Downloads real OMNI2 data.
2. Verifies required variables (`N_p`, `T_p`, `He2+_ratio`, `Kp`, `Dst`).
3. Aligns to 1-hour grid.
4. Computes lagged correlations (0–6h) on the full series.
5. Applies global Bonferroni correction (derived from full series Neff).
6. Validates on the 2018–2020 test set using the global threshold.
7. Generates visualizations and the validation report.

### Step 3: Inspect Results

- **Correlation Table**: `data/processed/correlation_results.csv`
- **Visualizations**: `artifacts/figures/` (PNG files)
- **Validation Report**: `artifacts/reports/validation.md`

### Running Tests

```bash
pytest tests/ -v
```

## Troubleshooting

- **Missing Variables**: If the OMNI2 file lacks `N_p`, `T_p`, or `He2+_ratio`, the pipeline will abort with an error (SC-002).
- **Large Gaps**: If gaps > 6h are detected, they are excluded from correlation, and a warning is logged.
- **Memory**: The pipeline is optimized for < 1 GB RAM. If you encounter memory issues, check your local environment for other heavy processes.
