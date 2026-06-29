# Quickstart: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

## Prerequisites

- Python 3.11+
- Sufficient CPU Cores (minimum)
- Adequate RAM (minimum)
- Internet access (for dataset fetch)

## Installation

1.  **Clone Repository**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-545-the-influence-of-visual-salience-on-atte
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Verify Environment**
    ```bash
    python -c "import cv2; import numpy; print('OK')"
    ```

## Running the Pipeline

1.  **Download Data** (Note: URL unverified per system constraints; multiple fallback sources available)
    ```bash
    python code/data/download.py
    ```

2.  **Detect Culpability Labels** (FR-008)
    ```bash
    python code/data/preprocess.py --detect-culpability
    ```

3.  **Compute Salience**
    ```bash
    python code/data/salience.py --input data/raw/moral_machine.csv --output data/processed/scenarios_salient.parquet
    ```

4.  **Fit Model** (Grid Search on a substantial sample, 5-fold CV)
    ```bash
    python code/models/fit.py --input data/processed/scenarios_salient.parquet --sample 10000 --cv-folds 5
    ```

5.  **Run Simulation Calibration**
    ```bash
    python code/models/simulate.py --output results/simulation_ground_truth.json
    ```

6.  **Compare Models**
    ```bash
    python code/analysis/compare.py --input results/model_params.json
    ```

## Troubleshooting

- **Runtime Error**: Ensure `numba` is installed. If memory error, reduce `--sample` size.
- **Dataset Fetch Fail**: If primary URL is blocked, the script will automatically try Harvard Dataverse and GitHub mirrors.
- **Convergence Fail**: Check `results/logs/fit.log` for non-convergence warnings. If >5% of folds fail, investigate dataset quality.
- **Culpability Detection**: If explicit culpability labels are found, the pipeline will halt and require manual review (unexpected for this dataset).

## Known Limitations

- **RT Data**: The aDDM implementation is a choice-only variant without response time data. This constrains parameter identifiability.
- **Dataset Verification**: The Moral Machine dataset source is unverified per system constraints. Multiple fallback sources are provided for continuity.
- **Representative Agent**: The analysis assumes a representative agent model; individual parameter variance is not estimable.

