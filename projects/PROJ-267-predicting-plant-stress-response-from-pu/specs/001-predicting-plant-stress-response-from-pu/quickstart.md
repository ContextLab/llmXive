# Quickstart: Predicting Plant Stress Response

## 1. Prerequisites

*   Python 3.11+
*   R 4.3+ (optional, if `biomaRt` fallback is needed)
*   Git
*   Access to a terminal (Linux/Mac/WSL)

## 2. Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-267-predicting-plant-stress-response-from-pu
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
    *Note: Ensure `rpy2` is installed if using R integration, or install R separately if running `merge.py` as a standalone script. `impyute` is required for MinProb imputation.*

## 3. Data Configuration

Since no verified URLs for plant data exist in the prompt's dataset block, you must manually provide accession numbers.

1.  Create `data/config.yaml`:
    ```yaml
    datasets:
      - accession_id: "GSE12345"  # Example: Replace with valid Arabidopsis drought data
        source: "NCBI_GEO"
        species: "Arabidopsis"
        stress_type: "Drought"
      - accession_id: "PXD000123" # Example: Replace with valid ProteomeXchange data
        source: "ProteomeXchange"
        species: "Arabidopsis"
        stress_type: "Drought"
    ```
    *Warning: The pipeline will fail if these accession numbers do not exist or do not contain paired data.*

## 4. Running the Pipeline

### Step 1: Data Ingestion & Preprocessing
```bash
python code/data_ingestion/download.py --config data/config.yaml
python code/data_ingestion/normalize.py --input data/raw/ --output data/processed/
python code/data_ingestion/merge.py --input data/processed/ --output data/processed/unified_matrix.csv
```

### Step 2: Model Training & Evaluation
```bash
python code/modeling/train.py --input data/processed/unified_matrix.csv --output results/metrics.json
python code/modeling/evaluate.py --input results/metrics.json --output results/cross_stress_report.json
```
*Note: The training script will automatically perform the Stress-Blind Baseline and Target-Permutation Test.*

### Step 3: Visualization & Reporting
```bash
python code/reporting/plots.py --input results/ --output results/figures/
python code/reporting/metrics.py --input results/ --output results/runtime_metrics.json
```

## 5. Verifying Results

Check `results/runtime_metrics.json` to ensure:
*   `total_runtime` < 6 hours.
*   `peak_memory` < 7 GB.

Check `results/cross_stress_report.json` for R² scores. A valid model should have R² > 0 (better than mean prediction) and significantly outperform the Target-Permutation Test (p < 0.05).

## 6. Troubleshooting

*   **Error: "No data found for accession..."**: Verify the accession ID in `config.yaml`. The prompt's verified dataset list does not contain plant data; manual curation is required.
*   **Error: "biomaRt not found"**: Ensure R is installed and `rpy2` is correctly configured, or switch to `mygene` in `merge.py`.
*   **Error: "Memory Limit Exceeded"**: Reduce the dataset size by filtering for the most abundant proteins only, or reduce `n_estimators` in `train.py`.
*   **Error: "E001_NO_PAIRED_DATA"**: No paired proteomic/transcriptomic datasets were found for the specified species/stress. Check the curated list or pivot to meta-analysis.