# Quickstart: Phase Transitions in Amorphous Solids Under Shear Stress

## Prerequisites

- Python 3.11+
- Git
- Access to the verified dataset source (see `research.md`).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-080-phase-transitions-amorphous-solids-un
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

## Data Setup

1.  **Download Data**:
    - Ensure the `amorphous-silicon-shear-trajectories` dataset is downloaded to `data/raw/`.
    - *Note*: If the verified source is a HuggingFace dataset, use the `datasets` library to download.
    - Verify checksums against the `state/projects/PROJ-080...yaml` file.

2.  **Verify Data Integrity**:
    ```bash
    python code/utils.py --verify-data
    ```

## Running the Pipeline

### Step 1: Preprocessing (FR-001, FR-002)
Compute $D^2_{min}$ and identify yielding points.
```bash
python code/preprocess.py --input-dir data/raw/ --output-dir data/processed/
```
- **Output**: `data/processed/precursor_metrics.csv`, `data/processed/yield_flags.json`.

### Step 2: Statistical Analysis (FR-003, FR-005)
Compare brittle vs. ductile distributions.
```bash
python code/analysis.py --input-dir data/processed/ --output-dir data/processed/
```
- **Output**: `data/processed/ks_test_results.json`, `data/processed/histograms.png`.

### Step 3: Predictive Validation (FR-004)
Validate threshold and perform sensitivity sweep.
```bash
python code/predict.py --input-dir data/processed/ --output-dir data/processed/
```
- **Output**: `data/processed/prediction_results.json`, `data/processed/sensitivity_table.csv`.

## Verification

Run the test suite to ensure correctness:
```bash
pytest tests/
```

## Troubleshooting

- **Memory Error**: If the process exceeds 7GB RAM, reduce the `--chunk-size` in `preprocess.py` or ensure only one trajectory is processed at a time.
- **No Yielding Detected**: Check the stress-drop threshold (default 5%). If the trajectory is indeterminate, the script will log a warning and skip downstream analysis.
- **Dataset Missing**: Ensure the verified dataset URL is accessible and the files are in `data/raw/`.
