# Quickstart: Predicting Gene Expression from Chromatin Accessibility

## Prerequisites

-   Python 3.11+
-   `git`
-   System dependency: `bedtools` (optional, can be simulated in Python).
-   Internet access (not required for data, as synthetic data is generated locally).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-211-predicting-gene-expression-from-chromati
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

The pipeline is executed via a main entry point script.

### Step 1: Generate and Preprocess Data
```bash
python code/generate_data.py --output data/raw/
python code/preprocess.py --input data/raw/ --output data/processed/
```
*This step generates synthetic paired RNA-seq and DNase-seq data with valid genomic coordinates, maps peaks to TSS windows (±50kb), and filters zero-expression genes.*

### Step 2: Train Models
```bash
python code/train.py --input data/processed/ --output data/models/
```
*Trains Elastic Net models for each cell line with 5-fold cross-validation.*

### Step 3: Evaluate and Interpret
```bash
python code/evaluate.py --models data/models/ --output results/
python code/interpret.py --models data/models/ --output results/
```
*Generates R² scores, Bonferroni-corrected p-values, and feature importance rankings.*

### Step 4: Validate Contracts
```bash
pytest tests/contract/
```
*Ensures all output files match the schemas defined in `contracts/`.*

## Troubleshooting

-   **Memory Error**: If the pipeline fails due to RAM, reduce the number of peaks selected in `code/preprocess.py` (adjust `MAX_PEAKS` constant).
-   **Data Generation Error**: If the synthetic data generator fails, check that the random seed is pinned and the environment has sufficient disk space.
-   **Runtime Limit**: If the job exceeds 6 hours, enable the `--sample` flag in `code/train.py` to use a subset of genes for the initial run.