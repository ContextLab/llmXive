# Quickstart: Residue Distribution of Euler's Totient Function Modulo Small Primes

## Prerequisites
- Python 3.11+  
- Git (to clone the repository)  
- `make` (optional, for convenience targets)

## Installation

```bash
# Clone the repository (adjust path if needed)
git clone 
cd projects/PROJ-771-residue-distribution-of-euler-s-totient-/code

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Study

```bash
# Run for all supported primes with N = 5,000,000
python run_analysis.py --primes 3,5,7,11 --n 5000000
```

### Command‑line Options
| Option | Description | Default |
|--------|-------------|---------|
| `--primes` | Comma‑separated list of primes (must be subset of `3,5,7,11`) | `3,5,7,11` |
| `--n` | Upper bound $N$ (positive integer) | `1000000` |
| `--seed` | Random seed for Monte‑Carlo simulations | `42` |
| `--benchmark` | Emit a benchmark JSON in `results/reports/benchmark.json` | `False` |

## Outputs
- **Raw residues**: `../data/raw/residues_{p}_{N}.json`  
- **Statistical results**: `../data/processed/stats_{p}_{N}.json`  
- **Plots**: `../results/plots/bar_{p}_{N}.png`, `../results/plots/qq_{p}_{N}.png`  
- **Summary report**: `../results/reports/summary.md` (includes pass/fail flags)  

## Verification Commands

```bash
# Unit tests
pytest tests/unit/

# Integration test on a tiny sample (N=1000)
pytest tests/integration/

# Static type checking
mypy code/
```

## Troubleshooting
- **MemoryLimitExceeded**: Reduce `--n` or increase the polling interval via `--mem-poll-interval` (see `code/config.py`).  
- **Small expected counts**: If any $E_i < 5$, the pipeline automatically switches to the exact multinomial test; a warning will appear in the summary.  
- **Monte‑Carlo convergence**: Increase `--mc-samples` (default = 10 000) for a more precise p‑value at the cost of runtime.

---
