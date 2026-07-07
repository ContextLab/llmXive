# Quickstart: Predicting Molecular Descriptors

## Prerequisites

- Python 3.11+
- Access to a GitHub Actions runner (or local environment with sufficient RAM)
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <project-dir>
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
    *Note: `requirements.txt` pins `rdkit`, `scikit-learn`, `pandas`, `numpy`, `pyarrow`.*

## Running the Pipeline

The pipeline is executed sequentially. Each step handles data download, feature generation, training, and analysis.

### Step 1: Download and Validate Data
```bash
python code/01_data_download.py
```
*Output*: `data/raw/qm9_subset.parquet` (Checksum verified).

### Step 2: Feature Extraction
```bash
python code/02_feature_extraction.py
```
*Output*: `data/processed/features_2d.npy`, `data/processed/features_3d.npy`, `data/processed/labels.csv`.
*Note*: This step includes a memory monitor. If RAM usage > 6.5 GB, it will automatically reduce the subset size.

### Step 3: Model Training
```bash
python code/03_model_training.py
```
*Output*: `models/model_2d.pkl`, `models/model_3d.pkl`, `results/cv_2d.json`, `results/cv_3d.json`.
*Duration*: ~2-4 hours on a standard CPU.

### Step 4: Analysis and Visualization
```bash
python code/04_analysis.py
```
*Output*: `results/metrics.json`, `results/parity_plots.png` (2D vs 3D), `results/failure_boundary_report.md`.

## Verification

To verify the pipeline:
1.  Check `results/metrics.json` for the presence of `relative_error_increase` for `mu`, `homo`, and `lumo`.
2.  Ensure `results/parity_plots.png` exists and shows distinct clusters for 2D vs 3D predictions.
3.  Run `pytest tests/` to validate unit tests.

## Troubleshooting

- **OOM Error**: The script should auto-downsample. If it fails, manually reduce the `SUBSET_SIZE` in `code/02_feature_extraction.py`.
- **Missing Dependencies**: Ensure `rdkit` is installed via `conda` or `pip` (sometimes requires `conda install -c rdkit rdkit` for full functionality).
- **Dataset Download Failure**: The script retries a limited number of times. If it fails, check internet connectivity or the HuggingFace source status.
