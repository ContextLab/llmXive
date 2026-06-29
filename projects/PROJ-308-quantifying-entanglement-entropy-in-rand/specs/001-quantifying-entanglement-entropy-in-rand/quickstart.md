# Quickstart: Quantifying Entanglement Entropy

## Prerequisites

- Python 3.10 or newer.
- Git.
- A GitHub Actions account (for CI execution) or a local Linux environment with 7+ GB RAM.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-308-quantifying-entanglement-entropy-in-rand
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
   *Note: This installs TeNPy, NumPy, SciPy, Pandas, Matplotlib, and Pytest.*

## Running the Workflow

### Default Configuration (Single Run)
Run the workflow with default parameters ($L=30, \delta=0.2, N=100$). The system will first run a pilot study to verify variance.
```bash
python code/cli.py --run
```
**Output**:
- `data/raw/entropy_data.csv`
- `data/raw/metadata.json` (contains $N_{\text{real}}$, pilot variance, convergence status)
- `data/processed/scaling_fit.txt`
- `data/processed/entropy_vs_l.png`
- `data/processed/bootstrap_summary.txt`

### Grid Scan (Multiple Disorder Strengths)
1. Create a `delta_grid.csv` file in the project root:
   ```csv
   delta
   0.0
   0.1
   0.2
   0.3
   0.4
   ```
2. Run the grid scan:
   ```bash
   python code/cli.py --run --grid delta_grid.csv
   ```
**Output**:
- `data/processed/delta_vs_exponent.csv`
- Individual fit files for each $\delta$.

### Custom Parameters
Override defaults via command line:
```bash
python code/cli.py --run --L 30 --delta 0.2 --N 100 --seed 42
```

### Validation
Check for out-of-bounds parameters:
```bash
python code/cli.py --run --L 10 --delta 0.2
# Expected: Error "Chain length L=10 is out of bounds (20 <= L <= 40)"
```

## Testing

Run the unit and integration tests:
```bash
pytest tests/ -v
```

## CI Execution (GitHub Actions)

The workflow is automatically triggered on push to the feature branch.
- **Trigger**: `push` to `[PROJ-308-001-quantify-entanglement]`
- **Runner**: `ubuntu-latest`
- **Timeout**: 6 hours
- **Artifacts**: Uploaded to GitHub Actions artifacts.

To run manually in CI:
1. Push to the branch.
2. Navigate to the "Actions" tab.
3. Select "Run workflow" and choose the branch.