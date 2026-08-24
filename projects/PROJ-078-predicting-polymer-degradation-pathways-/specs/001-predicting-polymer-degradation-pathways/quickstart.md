# Quickstart: Polymer Degradation Pipeline Feasibility Study

## Prerequisites

- Python 3.11 or higher
- Git
- Access to a Linux environment (or WSL on Windows)
- ~14GB free disk space

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-078-predicting-polymer-degradation-pathways-/code
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
    *Note: `requirements.txt` pins specific versions of `rdkit`, `torch`, `torch-geometric`, and `scikit-learn`.*

## Data Setup

1.  **Download raw data**:
    Run the ingestion script to download available SMILES data (note: degradation labels are missing):
    ```bash
    python pipelines/ingest.py --source smiles-proxy
    ```
    *This will populate `data/raw/` with downloaded files.*

2.  **Verify checksums**:
    The script will automatically verify checksums against the project's state file.

## Running the Pipeline

1.  **Preprocess data**:
    Convert SMILES to molecular graphs and handle missing values:
    ```bash
    python pipelines/preprocess.py
    ```

2.  **Flag missing labels**:
    Validate and flag records with missing degradation pathways:
    ```bash
    python pipelines/flags.py
    ```

3.  **Run Feasibility Study**:
    Execute the pipeline with a randomly initialized model to demonstrate code paths:
    ```bash
    python models/trainer.py
    ```

4.  **Generate attribution and validation**:
    Compute Integrated Gradients and run Null Attribution Tests:
    ```bash
    python analysis/null_test.py
    ```

5.  **Generate the final report**:
    ```bash
    python analysis/report_gen.py
    ```

## Expected Outputs

- `data/processed/graphs.parquet`: Processed molecular graphs.
- `analysis/results/motif_importance.json`: Feature importance scores (technical demonstration only).
- `analysis/results/chi_square_test.json`: Motif distribution statistics.
- `reports/final_report.md`: Comprehensive report with structural analysis and pipeline validation results.

## Troubleshooting

- **Missing Labels**: If the pipeline reports "No degradation labels found", this is expected due to the lack of verified open datasets. The pipeline will proceed with structural analysis only, and the report will note this limitation.
- **Memory Errors**: If you encounter memory errors, reduce the `hidden_dim` in `models/gnn.py` or further subsample the dataset.
- **RDKit Errors**: Invalid SMILES strings will be logged in `logs/rdkit_errors.log`. Check this file for specific examples.

## Reproducibility

To ensure reproducibility, set the random seed before running any script:
```bash
export PYTHONHASHSEED=42
export RANDOM_SEED=42
```
The `trainer.py` and `null_test.py` scripts will use this seed.
