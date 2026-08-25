# Quickstart: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

## Prerequisites

*   Python 3.11+
*   `pip` and `venv`
*   Access to the project repository

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-448-quantifying-composition-dependent-grain-/
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

The full pipeline can be executed via the CLI:

```bash
python src/cli/run_pipeline.py
```

This command will:
1.  Load and validate the curated literature dataset (`data/raw/literature_dft.csv` and `data/raw/literature_apt.csv`).
2.  Compute segregation profiles for all available systems (Binary and Ternary).
3.  Fit regression models and perform cross-validation.
4.  Generate visualizations and save results to `data/derived/`.
5.  Update `data_manifest.json`.

### Running Specific Tasks

*   **Compute Profiles Only**:
    ```bash
    python src/cli/run_pipeline.py --task compute_profiles
    ```
*   **Run Regression Analysis Only**:
    ```bash
    python src/cli/run_pipeline.py --task regression --input data/derived/segregation_profiles.csv
    ```
*   **Validate Data**:
    ```bash
    python src/cli/run_pipeline.py --task validate_data
    ```

## Output

After a successful run, check the following files:

*   `data/derived/segregation_profiles.csv`: The computed equilibrium concentrations.
*   `data/derived/regression_results.json`: Model coefficients and validation metrics.
*   `data/derived/plots/`: Heatmaps of segregation energy vs. composition.
*   `data_manifest.json`: Complete list of data sources and checksums.

## Troubleshooting

*   **Missing Literature Data**: If the script reports "Missing literature data", ensure the `data/raw/literature_dft.csv` file is present and contains the required columns for the target system.
*   **CALPHAD Error**: If the CALPHAD database is missing, check the `data/raw/calphad_params.csv` or download the TCFE9 equivalent as described in `research.md`.
*   **Memory Error**: The pipeline is designed for moderate RAM capacity. If you encounter memory issues, reduce the number of temperature points or compositions in the configuration file.