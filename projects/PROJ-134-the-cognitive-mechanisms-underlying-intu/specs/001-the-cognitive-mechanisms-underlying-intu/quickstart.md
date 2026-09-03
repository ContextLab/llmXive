# Quickstart: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments (Methodological Validation)

## Prerequisites

-   Python 3.11+
-   Git
-   Access to HuggingFace (for dataset download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd your-repo/specs/001-the-cognitive-mechanisms-underlying-intu
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

## Running the Pipeline

### Step 1: Data Ingestion & MDES
Fetch the raw datasets, generate the MDES report, and create the Unity config.
```bash
python code/data/ingestion/fetch_real.py
python code/analysis/validation.py --generate-mdes  # Generates state/mdes_report.yaml
python code/data/config/generate_unity_config.py   # Generates data/config/unity_blend_shapes.yaml
```
*Output*: `data/raw/mfq.parquet`, `data/raw/moral_stories.parquet`, `state/mdes_report.yaml`, `data/config/unity_blend_shapes.yaml`.

**Note**: `state/mdes_report.yaml` must exist before proceeding. A pre-commit hook will enforce this.

### Step 2: VR Mapping & Simulation
Map stories to salience levels and generate simulated VR logs.
```bash
python code/data/processing/vr_mapping_logic.py
python code/data/processing/simulate_logs.py
```
*Output*: `data/processed/merged_data.csv` (contains `simulated` logs), `data/logs/ingest.log`, `data/logs/vr_mapping.log`.

**Note**: `code/utils/logging.py` must implement `get_logger` to generate these log files.

### Step 3: Bayesian Model Execution
Run the Bayesian decision model (PyMC5).
```bash
python code/analysis/bayesian_model.py
```
*Output*: `data/results/bayesian_results.json`, `state/mdes_report.yaml` (if MDES step is run).

### Step 4: Validation & Reporting
Run mixed-effects regression, parameter recovery, and generate the final report.
```bash
python code/analysis/regression.py
python code/analysis/validation.py  # Runs Bonferroni, Sensitivity, Parameter Recovery
```
*Output*: `data/results/final_report.md`.

**Note**: `code/analysis/validation.py` must perform `assert N_simulated == 200` and raise `ValueError` if the sample size does not match.

## Testing

Run the unit tests to verify the pipeline.
```bash
pytest code/tests/unit/
```

## Troubleshooting

-   **Dataset Download Fails**: Ensure you have an internet connection and HuggingFace access.
-   **Model Convergence Issues**: Reduce the sample size or increase the number of iterations in `bayesian_model.py`.
-   **Memory Error**: Use the `streaming=True` flag in `fetch_real.py` if the dataset is too large.
-   **Log Files Missing**: Ensure `code/utils/logging.py` is fully implemented (T009).
-   **MDES Report Missing**: Ensure `code/analysis/validation.py --generate-mdes` has been run and `state/mdes_report.yaml` exists.