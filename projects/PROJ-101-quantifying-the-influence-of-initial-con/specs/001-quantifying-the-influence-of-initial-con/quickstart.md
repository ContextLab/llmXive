# Quickstart: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Prerequisites

- Python 3.11+
- `pip`
- `git`

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-101-quantifying-the-influence-of-initial-con
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Environment**:
    ```bash
    pytest tests/unit/ -v
    ```

## Running the Pipeline

### Option 1: Full Analysis (Recommended)
Runs generation, baseline validation, FTLE computation, and regression analysis.
```bash
# Example with illustrative values; exact levels and counts are deferred to config.py
python code/main.py --N-values 3,5 --noise-levels 0.001,0.01,0.1,1.0 --trials 30
```

### Option 2: Generate Data Only
Generates synthetic trajectories without analysis.
```bash
python code/main.py --mode generate --N 5 --sigma 0.01 --steps 10000 --trials 10
```

### Option 3: Analyze Existing Data
Skips generation and runs analysis on existing `data/raw/`.
```bash
python code/main.py --mode analyze
```

## Configuration

Key parameters can be set via CLI arguments or edited in `code/config.py`:
- `--N-values`: Comma-separated list of oscillator counts (e.g., `3,5`).
- `--noise-levels`: Comma-separated list of $\sigma$ values (e.g., `0.001,0.01,1.0`).
- `--trials`: Number of independent runs per configuration.
- `--seed`: Global random seed (default: 42).

## Output

Results are saved to `data/processed/`:
- `ftle_results.json`: Raw FTLE estimates (includes `window_size` and `status`).
- `regression_stats.json`: Statistical summary, scaling exponents, and effect sizes.
- `plots/`: Convergence and bias scaling figures.

## Validation

To ensure reproducibility, run:
```bash
python code/utils/validate.py --check-all
```
This verifies checksums, baseline convergence (using Rosenstein), and data integrity.