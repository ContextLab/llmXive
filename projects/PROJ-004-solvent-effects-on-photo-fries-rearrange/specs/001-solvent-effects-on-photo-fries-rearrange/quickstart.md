# Quickstart: Solvent Effects on Photo-Fries Rearrangement Kinetics

## Prerequisites

-   Python 3.11+
-   `pip` or `poetry`
-   Git

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-004-solvent-effects-on-photo-fries-rearrange
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Environment**:
    ```bash
    python code/config.py --verify
    ```

## Running the Pipeline

### Option A: Simulated Data (Default for CI)
This runs the full pipeline using generated data to validate the logic.

```bash
python code/main.py --mode simulate
```
**Output**:
-   `data/processed/lifetimes.csv`
-   `data/processed/correlation_report.json`
-   `docs/deviation_analysis.md`

### Option B: Real Data (If Available)
To use real instrument data:
1.  Place CSV files in `data/raw/` with naming convention `trace_<solvent>_<replicate>.csv`.
2.  Ensure headers match `time_ns, absorbance_mOD`.
3.  Run:
    ```bash
    python code/main.py --mode real --data-path data/raw/
    ```
**Validation**: The system will validate the uploaded files against the `dataset.schema.yaml` before processing. Any files failing validation will be flagged and excluded from the analysis. This mechanism allows the pipeline to be used with real instrument data if available, while defaulting to simulation for CI.

## Validation

Run the test suite to ensure data integrity and schema compliance:

```bash
pytest tests/
```

## Key Files

-   `code/simulate_data.py`: Generates synthetic decay traces (using independent Arrhenius model).
-   `code/fit_kinetics.py`: Extracts lifetimes (Joint NLME).
-   `code/analyze_stats.py`: Performs Bayesian Hierarchical Modeling and PCA.
-   `data/chemicals/solvents.csv`: Versioned solvent properties.

## Troubleshooting

-   **Missing Dependencies**: Ensure `requirements.txt` is installed in the virtualenv.
-   **Data Format Errors**: Check CSV headers in `data/raw/`.
-   **Statistical Warnings**: Low N ($n=3$) may trigger power warnings; these are expected and reflect the exploratory nature of the study.
-   **Real Data Upload**: Ensure files are in `data/raw/` and match the schema before running with `--mode real`.
