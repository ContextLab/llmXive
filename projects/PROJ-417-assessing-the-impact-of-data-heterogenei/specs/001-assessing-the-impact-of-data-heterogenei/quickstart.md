# Quickstart: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## 1. Prerequisites
*   Python 3.11+
*   `pip` (Python package manager)
*   Access to a terminal or GitHub Actions runner.

## 2. Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## 3. Running the Simulation

### 3.1 Full Execution
To run the full simulation (5 levels $\times$ 500 replicates):
```bash
python code/main.py --mode full --seed 42
```
*   **Output**: Results saved to `data/results/simulation_full_*.json` and `data/results/aggregated_*.csv`.
*   **Visualization**: Plots saved to `data/results/plots/`.

### 3.2 Dry Run (Small Subset)
To test the pipeline with a small subset (2 levels $\times$ 10 replicates) for quick verification:
```bash
python code/main.py --mode dry-run --seed 42
```
*   **Expected**: Exit code 0 within 2 minutes. Output files created in `data/results/`.

## 4. Verification Steps

1.  **Check Output Files**:
    ```bash
    ls -lh data/results/
    ```
    Ensure JSON and CSV files are generated.
2.  **Validate Schemas**:
    ```bash
    python code/main.py --validate-contracts
    ```
    This runs the contract validation against the generated data.
3.  **Run Unit Tests**:
    ```bash
    pytest tests/unit/
    ```
    Ensure all estimator and generator tests pass.

## 5. Troubleshooting

*   **Memory Error**: If running out of RAM, reduce the `--replicates` flag or run in batch mode (default behavior).
*   **REML Convergence Warnings**: These are expected in high heterogeneity/low N scenarios. The system logs them but continues. Check `data/results/logs/reml_failures.log`.
*   **Missing Data**: If the base Cochrane data is missing, the system will generate a synthetic base. Check `data/processed/base_data.csv` to confirm.
