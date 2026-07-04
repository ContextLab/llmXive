# Quickstart: Assessing the Validity of p-Values in High-Dimensional Data

## Prerequisites

- Python 3.11+
- Git
- 4 GB free disk space

## Installation

1. **Clone and Setup**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-054-assessing-the-validity-of-p-values-in-hi
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Simulation

### 1. Generate Synthetic Data
Run the data generation script for a specific configuration (e.g., $n=100, p=1000, \rho=0.5$):
```bash
python code/generate_data.py --n 100 --p 1000 --rho 0.5 --dist normal --seed 42
```
*Output*: `data/synthetic/{uuid}.npz` and metadata JSON.

### 2. Run Hypothesis Tests
Execute the testing pipeline on generated data:
```bash
python code/run_tests.py --input data/synthetic/{uuid}.npz --iterations 100
```
*Output*: `data/results/pvalues/{uuid}_iter*.csv`.

### 3. Analyze Results
Compute KS statistics and generate QQ-plots:
```bash
python code/analyze_pvalues.py --input-dir data/results/pvalues --output-dir data/results/summary
```
*Output*: Summary JSONs, QQ-plots (`.png`), and KS statistic tables.

### 4. Full Sweep (CI Mode)
To run the full parameter sweep (may take several hours):
```bash
python code/main.py --full-sweep
```
*Note*: This respects the CI time limit and 7 GB RAM constraint.

## Verification

- **Unit Tests**:
  ```bash
  pytest tests/unit/
  ```
- **Integration Test**:
  ```bash
  pytest tests/integration/test_full_sweep.py
  ```

## Troubleshooting

- **Singular Matrix Error**: If `LinAlgError` occurs, the regularization parameter $\epsilon$ in `utils/regularization.py` may need adjustment (default $10^{-6}$).
- **OOM (Out of Memory)**: Reduce $p$ or $n$ in the configuration. The default sweep is optimized for moderate RAM constraints.
