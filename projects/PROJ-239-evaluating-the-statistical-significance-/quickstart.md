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

## Running the Simulation

The simulation is designed to run end‑to‑end on a standard CPU.

1. **Generate Synthetic Cluster Structure**

 This script generates synthetic cluster sizes based on UCI Online Retail summary statistics. [UNRESOLVED-CLAIM: c_b9663c65 — status=not_enough_info]
 ```bash
 python code/synthetic_cluster_params.py
 ```
 **Output**: `data/derived/synthetic_cluster_structure.csv`

2. **Run Baseline Simulation**

 Executes the naive t‑test simulation (violates cluster‑aware inference for baseline comparison).
 ```bash
 python code/run_simulation_baseline.py
 ```
 **Output**: `data/derived/baseline_results.csv`

3. **Run Robust Simulation**

 Runs the cluster‑robust and block permutation test simulations.
 ```bash
 python code/run_simulation_robust.py
 ```
 **Output**: `data/derived/robust_results.csv`

4. **Run Full Simulation & Generate Final Report**

 Orchestrates the full Monte‑Carlo run across all ICC levels and writes the consolidated
 report (`final_report.csv`). This step replaces the previous ad‑hoc merging script and
 guarantees the report is produced without schema mismatches.
 ```bash
 python code/simulation_runner.py \
 --icc-range 0.0,0.1,0.2,0.3,0.4,0.5 \
 --iterations 1000
 ```
 **Output**: `data/derived/final_report.csv`

5. **Generate Research Report**

 Creates the final research report with visualizations.
 ```bash
 python code/generate_report.py
 ```
 **Outputs**:
 - `specs/001-evaluating-the-statistical-significance/research.md`
 - `data/derived/error_rate_vs_icc.png`

## Running Tests

Ensure the simulation logic is correct before running the full suite.

```bash
pytest tests/ -v
```

## Interpreting Results

- **Standard T‑Test**: If the `empirical_error_rate` is significantly higher than `alpha`
 (e.g., 0.15 when `alpha=0.05`), it indicates Type I error inflation due to ICC.
- **Robust Methods**: If `cluster_robust` or `block_permutation` error rates are close to
 `alpha` (e.g., 0.05 ± 0.01), the method successfully corrects for the correlation.