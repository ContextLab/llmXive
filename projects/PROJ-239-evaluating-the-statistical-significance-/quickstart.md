# Quickstart Guide: Evaluating Statistical Significance with Non-Independent Observations

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Git

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory.
2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Dependencies include: `numpy`, `pandas`, `scipy`, `statsmodels`, `pytest`, `pyyaml`, `ucimlrepo`.*

## Running the Simulation End‑to‑End

The command below runs a **reduced** simulation that is quick enough for the quickstart
while still exercising the full pipeline (data generation, baseline & robust methods,
aggregation, and final report).

```bash
python code/simulation_runner.py \
 --icc-range 0.0,0.1 \
 --iterations 20
```

**Outputs** (generated in the `data/derived/` folder):
- `simulation_results_raw.csv` – detailed per‑iteration results.
- `final_report.csv` – aggregated Type I error rates with 95 % Clopper‑Pearson CIs.

You can inspect the final report with:

```bash
head data/derived/final_report.csv
```

The reduced configuration finishes in under a minute on a standard CPU. [UNRESOLVED-CLAIM: c_0d09012b — status=not_enough_info]

## Running the Full Simulation (optional)

For a complete analysis (may take several minutes to hours depending on hardware):

```bash
python code/simulation_runner.py \
 --icc-range 0.0,0.1,0.2,0.3,0.4,0.5 \
 --iterations 1000
```

## Running Tests

Ensure the simulation logic is correct before running the full suite.

```bash
pytest tests/ -v
```

## Interpreting Results

- **Standard T‑Test**: If the `Empirical_Error_Rate` is significantly higher than `Alpha`
 (e.g., 0.15 when `Alpha=0.05`), it indicates Type I error inflation due to ICC.
- **Robust Methods**: If `cluster_robust` or `block_permutation` error rates are close to
 `Alpha` (e.g., 0.05 ± 0.01), the method successfully corrects for the correlation.
