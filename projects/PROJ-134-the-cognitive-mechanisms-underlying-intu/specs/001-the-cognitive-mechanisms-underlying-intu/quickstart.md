# Quickstart: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

## Prerequisites

*   Python 3.11+
*   Git
*   Access to HuggingFace (not required for synthetic data, but required for future real data)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-134-the-cognitive-mechanisms-underlying-intu
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` will include `pymc`, `pandas`, `numpy`, `scikit-learn`, `pyyaml`, `statsmodels`.*

## Running the Pipeline

The pipeline is executed via the `code/` scripts in order.

### Step 1: Ingest and Simulate Data
This step generates synthetic MFQ data (based on norms) and synthetic VR logs with a known ground truth.
```bash
python code/data/ingest.py
python code/data/simulation.py
```
*Output*: `data/raw/synthetic_mfq.parquet`, `data/processed/vignettes.csv`, `data/processed/vr_logs.csv`.

### Step 2: Preprocess and Merge
This step merges the datasets, handles missing values, and prepares the final analysis dataframe.
```bash
python code/data/preprocess.py
```
*Output*: `data/processed/final_analysis.csv`.

### Step 3: Run Bayesian Model
This step fits the Bayesian decision model using PyMC3.
```bash
python code/models/bayesian.py
```
*Output*: `data/processed/model_results.nc` (Posterior samples), `data/logs/convergence.log`.

### Step 4: Model Comparison & Validation
This step calculates AIC/WAIC, performs sensitivity analysis, and runs mixed-effects regression.
```bash
python code/analysis/model_comparison.py
python code/analysis/validation.py
```
*Output*: `data/processed/model_metrics.csv`, `data/figures/ppc_plot.png`.

### Step 5: Artifact Hashing & State Update
This step calculates checksums and updates the project state file.
```bash
python code/utils/hashing.py
```
*Output*: `state/projects/PROJ-134-.../state.yaml` (updated with `artifact_hashes`).

### Step 6: Generate Report
This step compiles all results into the final report.
```bash
python code/reports/generate_report.py
```
*Output*: `reports/final_report.md`.

## Verification

*   **Check Convergence**: Verify `data/logs/convergence.log` for R-hat < 1.05.
*   **Check Parameter Recovery**: Verify `data/processed/model_metrics.csv` for `ground_truth_effect` recovery (95% CI must include the true value).
*   **Check Psychometric Validity**: Verify `data/logs/norms_validation.log` for match with Gervais et al. (2011).
*   **Check Plot**: Open `data/figures/ppc_plot.png` to visually inspect model fit.

## Troubleshooting

*   **Convergence Failure**: If R-hat > 1.05, check `data/logs/convergence.log`. The script will automatically fall back to MLE and log the run as "inconclusive".
*   **Parameter Recovery Failure**: If the model fails to recover the `ground_truth_effect`, the pipeline is flagged as "Failed". Check model specification.
*   **Memory Error**: If running out of RAM, reduce the sample size in `code/config.py` (e.g., `MAX_PARTICIPANTS = 100`).