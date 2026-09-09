# Quickstart: Assessing the Validity of Statistical Significance in RCTs with Missing Data

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or local environment with 7GB+ RAM.

## Installation

1. **Clone and Setup**:
   ```bash
   git checkout 001-assessing-the-validity-of-significance
   cd projects/PROJ-436-assessing-the-validity-of-statistical-si
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins specific versions of `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`.*

## Running the Simulation

### 1. Download Data
```bash
python code/data_loader.py --download
```
This fetches the verified datasets (Malawi, CAD) and checksums them.

### 2. Run Full Simulation Sweep
```bash
python code/main.py --full-sweep
```
This executes an iterative loop across all mechanisms, rates, and methods.

### 3. Run Single Condition (Debug)
```bash
python code/main.py --dataset malawi --mechanism MAR --rate 0.20 --method CC --iterations 10
```

## Viewing Results

- **Error Rates**: `results/simulation_outputs/error_rates.csv`
- **P-Value Distributions**: `results/simulation_outputs/p_values.csv`
- **Tipping Points**: `results/simulation_outputs/tipping_points.json`

## Validation

To verify the null hypothesis setup:
```bash
python code/main.py --validate-null --dataset malawi
```
This checks that the permuted treatment has no association with the outcome (p-value ~ 0.5).

## Troubleshooting

- **Memory Error**: Ensure you are using the `streaming=True` flag in `data_loader.py` for large datasets.
- **Missing Source**: If a dataset is not found, check the "Verified datasets" list in `research.md`. The system will fall back to synthetic generation for MNAR.
- **Slow Execution**: The full sweep is designed for 2 CPU cores. If running locally on a single core, it may take longer. Use `--parallel` to utilize all cores.