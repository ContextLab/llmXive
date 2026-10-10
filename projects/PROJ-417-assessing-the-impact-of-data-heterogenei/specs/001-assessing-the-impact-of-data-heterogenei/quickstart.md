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
    (For running the test suite, install `pytest` separately:
    `pip install pytest`.)

## 3. Base Data

Fetch the base dataset (T001). The script first attempts the real
Cochrane data from Zenodo DOI ``; if that fetch
fails it raises loudly and then writes the verified synthetic base
(mu=0.0, sigma=1.0, N=20, parameters cited from Jackson et al., 2010):

```bash
bash code/scripts/setup_project.sh
python code/scripts/fetch_cochrane.py
```

The pipeline resolves its base dataset from `data/raw/` in this order:

1. `data/raw/cochrane_base.csv` — real Cochrane data from Zenodo,
   produced by `python code/scripts/fetch_cochrane.py`.
2. `data/raw/cochrane_base_synthetic.csv` — the **verified synthetic
   base** documented in T001 (mu=0.0, sigma=1.0, N=20, parameters cited
   from Jackson et al., 2010). If neither file exists, the pipeline
   generates this verified base via
   `python code/scripts/generate_synthetic_base.py` so a fresh
   environment is reproducible.

## 4. Running the Simulation

### 4.1 Full Execution
To run the full simulation (5 levels $\times$ 500 replicates):
```bash
python code/main.py --mode full --seed 42
```
*   **Output**: `data/results/simulation_raw.json`,
    `data/results/estimation_results.csv`,
    `data/results/reml_failures.json`, and
    `data/results/run_summary.json`.

### 4.2 Dry Run (Small Subset)
To test the pipeline with a small subset (2 levels $\times$ 10 replicates)
for quick verification (this is the T005 end-to-end trial,
$\tau^2 \in \{0, 0.1\}$):
```bash
python code/main.py --mode dry-run --seed 42
```
*   **Expected**: Exit code 0 within 2 minutes. Output files created in
    `data/results/`, including `estimation_results.csv` with non-null
    `pooled_effect`, `i_squared`, and `q_statistic` for all replicates.

## 5. Verification Steps

1.  **Check Output Files**:
    ```bash
    ls -lh data/results/
    ```
    Ensure JSON and CSV files are generated.
2.  **Validate Schemas**:
    ```bash
    python code/main.py --validate-contracts
    ```
    This validates `data/results/estimation_results.csv` against the
    T005 schema (required columns `pooled_effect`, `ci_lower`,
    `ci_upper`, `estimator_type`, `sweep_type`, `convergence_warning`,
    and non-null `i_squared` / `q_statistic`).
3.  **Run Unit Tests**:
    ```bash
    pytest tests/unit/
    ```
    Ensure all estimator, generator, and metrics tests pass.

## 6. Troubleshooting

*   **Memory Error**: If running out of RAM, reduce the `--replicates`
    flag or run in batch mode (default behavior).
*   **REML Convergence Warnings**: These are expected in high
    heterogeneity/low N scenarios. The system logs them to
    `data/results/reml_failures.json` and continues.
*   **Missing Base Data**: If `data/raw/cochrane_base.csv` is absent,
    the pipeline uses the verified synthetic base
    (`data/raw/cochrane_base_synthetic.csv`, Jackson et al., 2010),
    generating it first if necessary.