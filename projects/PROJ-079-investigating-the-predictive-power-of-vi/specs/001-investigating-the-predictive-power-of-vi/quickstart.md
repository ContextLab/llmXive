# Quickstart: Predictive Modeling of Host Immune Response

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Internet access (for dataset downloads)
- **Required**: Specific GEO accessions and NCBI Virus search terms (or local data paths).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-079-investigating-the-predictive-power-of-vi/code/
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `rpy2` requires an R installation with `edgeR` package installed.*

## Running the Pipeline

The pipeline is orchestrated via `main.py`.

### 1. Full Pipeline Execution (Real Data Required)
You must provide the specific GEO accessions and NCBI Virus search terms. The pipeline will attempt to fetch real data. If data is missing, it will abort.

```bash
python src/main.py --geo-accessions GSE12345,GSE67890 --ncbi-search "Influenza A" --output data/processed
```

### 2. Output
- **Metrics**: `artifacts/metrics.json` (R², RMSE, p-values)
- **Plots**: `artifacts/plots/`
- **Model**: `artifacts/model.pkl`
- **Manifest**: `data/manifest.yaml` (NCBI accessions and release version)

## Troubleshooting

- **Missing Data Error**: If the pipeline aborts due to missing verified datasets, ensure you have provided the specific GEO accessions and NCBI Virus search terms. No simulation mode is available.
- **Memory Error**: If RAM usage exceeds 6GB, reduce the number of k-mers (e.g., skip k=6) or downsample the dataset.
- **GPU Error**: The pipeline is CPU-only. If ESM-1b is attempted and fails, it will prompt for `--proxy_mode` or abort.
- **Power Error**: If the effective sample size is insufficient for the target R², the pipeline will abort with a specific error message.