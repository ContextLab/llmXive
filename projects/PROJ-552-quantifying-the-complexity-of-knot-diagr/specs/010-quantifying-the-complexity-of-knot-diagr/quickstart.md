# Quickstart: Knot Complexity Analysis Pipeline

These instructions assume a fresh GitHub Actions runner or a local Unix‑like environment with Python 3.11 installed.

## 1. Clone the repository
```bash
git clone https://github.com/your-org/quantifying-knot-complexity.git
cd quantifying-knot-complexity
```

## 2. Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Run the full pipeline
```bash
python -m code.__main__ run_all
```
`run_all` executes the following sub‑commands in order:
1. `download` – fetches Knot Atlas data (with retry & caching).  
2. `parse` – extracts core invariants and applies tie‑breaking.  
3. `validate` – flags data quality issues, applies staged validation (≤ 10 crossings full, 11‑13 exploratory), and filters to hyperbolic knots.  
4. `explore` – generates **1200 × 900 px** PNG scatter plots and descriptive statistics.  
5. `regress` – fits ridge‑regularised linear, polynomial, and logarithmic models, includes `alternating` as covariate, and outputs a model‑comparison table.  
6. `residuals` – performs family‑level residual analysis.

## 4. Inspect results
- Cleaned data: `data/processed/knots_cleaned.csv`
- Validated data (model input): `data/processed/knots_validated.csv`
- Plots: `data/plots/*.png` (all ≥ 1200 × 900 px)
- Regression summary: `data/processed/regression_summary.csv`
- Reproducibility logs: `docs/reproducibility/*.log`

## 5. Run tests (optional)
```bash
pytest -v
```

All random seeds are pinned; re‑running the pipeline yields identical outputs (modulo external data updates).
