# Quickstart: Residue Distribution of Euler's Totient Function Modulo Small Primes

## Prerequisites
- Python 3.11+  
- Git (to clone the repository)  
- `make` (optional, for convenience targets)

## Installation

```bash
# Clone the repository (adjust the URL as needed)
git clone <repository-url>
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
| `--seed` | Random seed for Monte‑Carlo simulations (must be an integer) | `12345` |
| `--benchmark` | Emit a benchmark JSON in `results/reports/benchmark_dummy.json` | `False` |
| `--mc-samples` | Number of Monte‑Carlo simulations (default = 10 000) | `10000` |
| `--mem-poll-interval` | Fraction of `N` at which memory usage is polled (default = 0.05) | `0.05` |

## Outputs
- **Raw residues**: `../data/raw/residues_{p}_{N}.json`  
- **Statistical results**: `../data/processed/stats_{p}_{N}.json`  
- **Plots**: `../results/plots/bar_{p}_{N}.png`, `../results/plots/qq_{p}_{N}.png`  
- **Summary report**: `../results/reports/summary.md` (includes raw and Bonferroni‑adjusted p‑values, uniformity test pass/fail flag) – the plot legends reference the **uniform expectation** $N/p$.  
- **Benchmark dummy**: `../results/reports/benchmark_dummy.json` (numeric `wall_time_sec` and `peak_memory_mb`)  

## Verification Commands

```bash
# Unit tests (including the newly added test_config and test_mypy)
pytest tests/unit/

# Integration tests (including synthetic stats and visualization checks)
pytest tests/integration/

# Static type checking (provides evidence for T005)
mypy code/
```

## Troubleshooting
- **MemoryLimitExceeded**: Reduce `--n` or increase the polling interval via `--mem-poll-interval`.  
- **Small expected counts**: If any $E_i<5$, the pipeline automatically switches to the exact multinomial test; a warning appears in the summary.  
- **Monte‑Carlo convergence**: Increase `--mc-samples` for a more precise p‑value at the cost of runtime.  
- **Benchmark generation**: Run `python scripts/run_dummy.py` to produce `benchmark_dummy.json` manually; the script now correctly imports `benchmark` from `code.benchmark`.  

---

