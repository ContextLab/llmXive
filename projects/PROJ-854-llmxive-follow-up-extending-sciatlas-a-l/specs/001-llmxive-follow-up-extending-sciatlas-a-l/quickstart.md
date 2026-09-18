# Quickstart: Interdisciplinary Bridging Coefficient Analysis

## Prerequisites

- Python 3.11+
- `pip`
- Access to the OpenAlex API (public, no key required for basic usage).

## Installation

1.  **Clone the repository** and navigate to the project root.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` includes `networkx`, `sentence-transformers`, `scikit-learn`, `pandas`, `pyarrow`, `pyalex`.*

## Running the Pipeline

The pipeline is orchestrated via the `src/cli/main.py` script.

### 1. Run Data Ingestion & Sampling
Fetches a degree-stratified sample from OpenAlex and builds the initial graph.
```bash
python -m src.cli.main --step ingest --sample-size [DEFERRED]
```
*Output*: `data/raw/openalex_stream.parquet`, `data/processed/subgraph_with_clusters.parquet`.

### 2. Run Embeddings & Text Clustering
Computes embeddings and assigns text-based topic clusters.
```bash
python -m src.cli.main --step embeddings --batch-size 64
```
*Output*: `data/processed/nodes_with_embeddings.parquet`.

### 3. Run Statistical Analysis
Performs correlation, regression, and FDR correction.
```bash
python -m src.cli.main --step analysis
```
*Output*: `artifacts/results/statistical_outputs.json`.

### 4. Generate Report
(If applicable) Generates a markdown summary of the results.
```bash
python -m src.cli.main --step report
```

## Verification

To verify the pipeline on a small subset (unit test mode):
```bash
pytest tests/unit/test_ingest.py -v
pytest tests/unit/test_metrics.py -v
```

To run the full integration test on a tiny sample (e.g., 100 nodes):
```bash
python -m src.cli.main --step ingest --sample-size 100 --debug
python -m src.cli.main --step embeddings --debug
python -m src.cli.main --step analysis --debug
```
*Check*: Ensure `artifacts/results/statistical_outputs.json` exists and contains valid floats.

## Troubleshooting

- **OOM (Out of Memory)**: Reduce `--sample-size` or `--batch-size`. Ensure `streaming=True` is used in ingestion.
- **API Rate Limits**: If using `pyalex`, add `--delay 1.0` to slow down requests.
- **Missing Data**: The pipeline skips nodes with missing titles or degree 0 (assigning default values). Check logs for skipped counts.
