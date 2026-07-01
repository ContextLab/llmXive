# Quickstart: Evaluating the Statistical Significance of A/B Test Results with Non-Independent Observations

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Git

## Installation

1.  **Clone the repository** (if applicable) or navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `numpy`, `pandas`, `scipy`, `statsmodels`, `pytest`.*

## Running the Simulation

The simulation is designed to run end-to-end on a standard CPU.

1.  **Run the full simulation suite**:
    This executes the Monte Carlo process for all ICC levels [0.0, 0.5] and alpha levels {0.01, 0.05, 0.10}.
    ```bash
    python code/simulation_runner.py
    ```
    *Note: This may take 15-30 minutes depending on the number of clusters and iterations.*

2.  **Run a specific configuration** (Optional):
    ```bash
    python code/simulation_runner.py --icc 0.1 --alpha 0.05 --iterations 100
    ```

3.  **Verify results**:
    Check the generated files in `data/derived/`:
    - `simulation_results_raw.csv`: Detailed p-values for every run.
    - `aggregated_metrics.csv`: The final Type I error rates and confidence intervals.

## Running Tests

Ensure the simulation logic is correct before running the full suite.

```bash
pytest tests/ -v
```

## Interpreting Results

- **Standard T-Test**: If the `empirical_type1_error` is significantly higher than `alpha` (e.g., 0.15 when alpha=0.05), it indicates Type I error inflation due to ICC.
- **Robust Methods**: If `cluster_robust` or `block_permutation` error rates are close to `alpha` (e.g., 0.05 ± 0.01), the method successfully corrects for the correlation.
