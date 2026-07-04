# Quickstart: Assessing Statistical Significance of Observed Correlations in Public Databases

## Prerequisites

*   Python 3.11+
*   `git`
*   Access to GitHub Actions (for CI) or local environment with substantial RAM capacity.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-297-assessing-statistical-significance-of-ob
    ```

2.  **Create virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Dependencies include: `pandas`, `numpy`, `scipy`, `networkx`, `matplotlib`, `seaborn`, `pytest`.*

## Running the Analysis

### 1. Download and Prepare Data
Run the data loader to fetch datasets from UCI (via verified URLs) and clean them:
```bash
python code/loaders.py --output data/processed/
```
*This step will skip datasets with < 20 variables or missing data issues. If fewer than a sufficient number of valid datasets remain, the pipeline halts.*

### 2. Execute Permutation Engine
Run the main analysis script:
```bash
python code/main.py --permutations [variable] --threshold 0.3 --sweep
```
*   `--permutations`: Number of permutations (default 1000).
*   `--threshold`: Primary correlation threshold (default 0.3).
*   `--sweep`: Enable sensitivity analysis (0.1 to 0.5).

### 3. View Results
Output files are generated in `output/`:
*   `output/results/significance_table.csv`: Raw and adjusted p-values.
*   `output/plots/null_distribution_histogram.png`: Example null distribution.
*   `output/plots/correlation_heatmap.png`: Observed correlation matrix.
*   `output/reports/sensitivity_analysis.csv`: Results across thresholds.
*   `output/exploratory/spearman_matrices/`: Spearman correlation matrices (exploratory only).

## Testing

Run unit tests to verify permutation logic and BY correction:
```bash
pytest tests/unit/ -v
```

Run integration tests (requires data download):
```bash
pytest tests/integration/ -v
```
