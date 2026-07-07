# Quickstart: Predicting Coral Resilience to Thermal Stress

## Prerequisites

-   **OS**: Linux (Ubuntu 22.04 recommended for CI compatibility)
-   **Python**: 3.11+
-   **R**: 4.3+ (with Bioconductor)
-   **Tools**: `SRA Toolkit` (for data download), `Salmon` (for quantification)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd 001-coral-resilience-prediction
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install R dependencies** (run in R):
    ```R
    if (!require("BiocManager", quietly = TRUE))
        install.packages("BiocManager")
    BiocManager::install(c("DESeq2", "tximport"))
    ```

5.  **Install system tools** (if running locally):
    ```bash
    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y sratoolkit salmon
    ```

## Running the Pipeline

1.  **Download Data**:
    The script `code/ingest.py` will fetch data from NCBI.
    ```bash
    python code/ingest.py --project PRJNA321023
    ```
    *Note: This may take time depending on network speed.*

2.  **Quantify Expression**:
    ```bash
    python code/quantify.py --input data/raw --index data/reference_index --output data/processed
    ```

3.  **Run DGE Analysis**:
    ```bash
    Rscript code/dge_analysis.R
    ```

4.  **Generate Plots & Enrichment**:
    ```bash
    python code/enrichment.py
    python code/viz.py
    ```

5.  **View Results**:
    Check `results/plots/volcano.png` and `data/processed/dge_results.csv`.

## Testing

Run the test suite to verify contract compliance:
```bash
pytest tests/
```

## Troubleshooting

-   **Network Timeout**: The `ingest.py` script includes exponential backoff. If it fails after 3 retries, check your internet connection or NCBI status.
-   **Memory Error**: Ensure no other heavy processes are running. The pipeline is designed to stay under 7GB, but large local caches can interfere.
