# Quickstart: Predicting Gene Essentiality from Protein Interaction Network Topology

## Prerequisites
- Python 3.11+
- `pip`
- Access to the internet (for downloading datasets)

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-452-predicting-gene-essentiality-from-protei
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### 1. Configuration
Edit `code/config.py` to set:
- `ORGANISMS`: List of organism IDs (e.g., `["9606", "559292"]`).
- `THRESHOLDS`: Confidence thresholds (default `[500, 700, 900]`).
- `PERMUTATIONS`: Number of permutations for null distribution (default `1000`).

### 2. Data Download
Run the download script to fetch raw data:
```bash
python code/data/download_string.py
python code/data/download_deg.py
python code/data/download_depmap.py
```
*Data is saved to `data/raw/` and checksummed.*

### 3. Execution
Run the full analysis pipeline:
```bash
python code/main.py
```
This script will:
1.  Map genes.
2.  Build graphs (GCC only).
3.  Compute centrality.
4.  Calculate correlations.
5.  Run Phylogenetic Meta-Analysis (if tree available).
6.  Perform sensitivity analysis.
7.  Run independent validation.

### 4. Results
Output files are generated in `data/results/`:
- `correlation_summary.csv`: Main results table.
- `pgls_results.csv`: Cross-species comparison stats.
- `sensitivity_analysis.csv`: Threshold stability data.
- `traceability_manifest.json`: Linking paper stats to data/code.

## Troubleshooting

| Error Code | Log Message | Resolution |
| :--- | :--- | :--- |
| `ERR-001` | "Gene ID mismatch: No mapping found for [ID]" | Check `config.py` organism ID. Ensure Ensembl BioMart is accessible. |
| `ERR-002` | "Network too sparse: < 500 edges" | Lower the confidence threshold in `config.py` or skip this organism. |
| `ERR-003` | "Power insufficient: n < 10" | Phylogenetic meta-analysis skipped for this organism. Check organism selection in `config.py`. |
| `ERR-004` | "Phylogenetic tree missing" | Ensure `data/raw/tree.nwk` exists (fetched from Open Tree of Life `ot_1578`). Meta-analysis skipped; results are descriptive only. |
| `ERR-005` | "MemoryError during centrality" | Reduce the number of organisms or use a smaller confidence threshold. |
| `ERR-006` | "DepMap data fetch failed" | Check internet connection. DepMap API may be rate-limiting; retry with `--retry` flag. |
| `ERR-007` | "Traceability manifest generation failed" | Ensure `data/` and `code/` are not modified manually; re-run `code/utils/traceability.py`. |

## Validation
To verify the pipeline:
```bash
pytest tests/contract/
pytest tests/integration/
```
Ensure all schema validations pass against `contracts/*.schema.yaml`.