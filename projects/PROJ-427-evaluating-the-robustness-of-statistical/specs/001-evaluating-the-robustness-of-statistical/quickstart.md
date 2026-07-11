# Quickstart: Evaluating the Robustness of Statistical Methods to Common Data Errors

## Prerequisites

- Python 3.11+
- `pip` (Python package manager)
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-427-evaluating-the-robustness-of-statistical
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

### 1. Download Datasets
Fetch the verified datasets and store them in `data/raw/`.
```bash
python code/download.py
```
*Output*: `data/raw/uci_har.csv`, `data/raw/shopper.parquet`, etc.

### 2. Generate Ground Truth (Synthetic Data)
Create synthetic datasets with known parameters for validation.
```bash
python code/main.py --mode generate_synthetic
```
*Output*: `data/synthetic/` with known $\mu$ and $\delta$.

### 3. Run Full Simulation
Execute the error injection, analysis, and aggregation pipeline.
```bash
python code/main.py --mode run_simulation
```
*Parameters*:
- `--error_rates 0.01 0.05 0.10 0.20`
- `--iterations 1000`
- `--seed 42`

*Output*:
- `data/corrupted/`: Injected datasets.
- `data/results/`: JSON logs of all test results.
- `figures/`: PNG degradation curves.

### 4. Validate Results
Run the contract tests to ensure output schemas are correct.
```bash
pytest tests/contract/
```

## Troubleshooting

- **Missing Dependencies**: Ensure `requirements.txt` is installed in the active virtual environment.
- **Memory Errors**: The pipeline is optimized for moderate RAM constraints. If OOM occurs, reduce `--iterations` or process datasets in chunks.
- **Reproducibility**: If results differ between runs, check that the `--seed` flag is set and `numpy.random.seed` is called in `main.py`.
