# Quickstart: Exploring the Impact of Data Imputation Methods on Causal Inference

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a terminal with sufficient free RAM and CPU cores.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-047-exploring-the-impact-of-data-imputation-
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: This installs `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `matplotlib`, and `pytest`.*

## Running the Simulation

### 1. Run a Single Simulation (Debug Mode)
To test the pipeline with a single seed and $\beta$ value:
```bash
python code/main.py --seed 42 --beta 0.5 --runs 1
```
*   Output: `data/raw/synth_42_0.5.csv`, `data/processed/`, `data/results/estimates_42_0.5.csv`.

### 2. Run the Full Sensitivity Analysis
To run the full study (200 runs per $\beta$, 5 $\beta$ values = 1,000 total runs):
```bash
python code/main.py --full-sweep
```
* **Expected Runtime**: [deferred] on a standard CPU.
*   **Output**: `data/results/sensitivity_analysis.csv`, `data/results/summary_plots/`.

### 3. Verify Results
Check the generated summary file:
```bash
python -c "import pandas as pd; df = pd.read_csv('data/results/sensitivity_analysis.csv'); print(df[['beta', 'method', 'mean_bias', 'coverage_rate']].head())"
```

## Reproducibility Check

To ensure reproducibility, run the simulation with a fixed seed and compare the output hash:
```bash
python code/main.py --seed 12345 --beta 0.5 --runs 1
sha256sum data/results/estimates_12345_0.5.csv
```
The hash should match the recorded hash in `state/projects/PROJ-047-exploring-the-impact-of-data-imputation-.yaml`.

## Troubleshooting

*   **Memory Error**: Reduce `N_SAMPLES` in `code/simulation/config.py` (default value).
*   **Convergence Warning (MICE)**: Increase `max_iter` in `code/analysis/imputation.py` or switch to `BayesianRidge` estimator.
*   **Runtime Exceeds 6h**: Reduce the number of replications in `code/simulation/config.py` from a higher baseline to a lower count. (note: this affects statistical power).