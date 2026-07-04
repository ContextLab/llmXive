# Quickstart: Residue Distribution of Euler's Totient Function Modulo Small Primes

## Prerequisites

- Python 3.11 or higher.
- Access to a terminal with `pip` and `venv`.
- (Optional) `make` for running convenience targets.

## Installation

1. **Clone and Navigate**:
   ```bash
   cd projects/PROJ-771-residue-distribution-of-euler-s-totient-/code
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Dependencies include: `numpy`, `scipy`, `matplotlib`, `pytest`, `psutil`.*

## Running the Analysis

### Basic Usage
To run the analysis for a specific prime and range:

```bash
python run_analysis.py --prime 3 --n 1000000
```

**Arguments**:
- `--prime`: The prime modulus ($p$).
- `--n`: The upper bound $N$ (default: [deferred]).
- `--seed`: Random seed for reproducibility (default: a fixed integer).

### Running All Primes
To run the full study for all supported primes with $N=5,000,000$:

```bash
python run_analysis.py --primes 3,5,7,11 --n 5000000
```

### Output Location
Results will be saved to:
- **Raw Data**: `../data/raw/residues_{p}_{N}.json`
- **Statistics**: `../data/processed/stats_{p}_{N}.json`
- **Plots**: `../results/plots/`
- **Reports**: `../results/reports/summary.md`

## Verification

### Unit Tests
Run the test suite to verify the sieve and statistical logic:
```bash
pytest tests/unit/
```

### Integration Test
Run the full pipeline on a small sample ($N=1000$) to ensure end-to-end correctness:
```bash
pytest tests/integration/
```

### Manual Verification
You can manually verify $\phi(n)$ values for small $n$:
```python
from sieve import compute_totients
# Verify n=1 to 10
values = compute_totients(10)
print(values) # No rewrite possible: The provided passage contains only an expected data sequence and a removal instruction, lacking a research question, method, or references as required by the planning document structure. (index 0 unused)
```

## Troubleshooting

- **Memory Error**: If the job fails due to memory, reduce `--n`. The default limit is a fixed storage capacity.; for $N=5,000,000$, memory usage should be < 1 GB. If the `limit_reached` flag is set in the output, the process was terminated gracefully by the memory guard.
- **Slow Execution**: Ensure you are running on a CPU with reasonable clock speed. The algorithm is $O(N)$ but Python has overhead.
- **Statistical Warnings**: If you see warnings about small $N$ for Block Bootstrap, the system will report the raw deviation magnitude without a p-value. This is expected behavior for small sample sizes where block resampling is not feasible.
- **Dependence Correction**: The system automatically applies Block Bootstrap to account for the dependence in $\phi(n)$. No manual intervention is required.
