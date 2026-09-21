# Quickstart: Normalized Gaps Between Consecutive Squarefree Numbers

## Prerequisites

- Python 3.11+
- `pip`
- `git`

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-722-normalized-gaps-between-consecutive-squa
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

## Running the Pipeline

### 1. Generate Squarefree Numbers
Run the sieve for a specific $N$ (e.g., $10^6$):
```bash
python code/main.py --sieve --N 1000000
```
Output: `data/raw/squarefree_1000000.parquet` (Parquet format)

### 2. Compute Gaps
Calculate raw and normalized gaps:
```bash
python code/main.py --gaps --N 1000000
```
Output: `data/processed/gaps_1000000.parquet` (Parquet format)

### 3. Run Statistical Test
Perform the Lilliefors test (Monte Carlo):
```bash
python code/main.py --test --N 1000000 --resamples 10000
```
Output: `data/processed/test_result_1000000.json`

### 4. Generate Visualizations
Create CDF, QQ-plot, and convergence chart:
```bash
python code/main.py --viz --N 1000000 5000000 10000000
```
Output: `data/figures/` (CDF, QQ, Convergence plots)

### 5. Run Control Experiments
- **Random Thinning Control**:
  ```bash
  python code/main.py --control --N 1000000
  ```
- **Gamma Control (Secondary)**:
  ```bash
  python code/main.py --control --N 1000000 --type gamma
  ```

## Verification

Run the test suite to verify correctness:
```bash
pytest tests/ -v
```

## Troubleshooting

- **Memory Error**: If $N > 10^8$, the sieve may exceed 2 GB. Reduce $N$ or use streaming (not implemented for this scope).
- **Division by Zero**: The normalization step includes a guard. If mean gap is 0, the script will log a warning and exit.
- **Slow Monte Carlo**: The 10,000 resamples are CPU-bound. For faster results, reduce `--resamples` to 1,000 (not recommended for final results).
