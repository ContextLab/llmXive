# Quickstart: Interdisciplinary Bridging Coefficient Analysis

## Prerequisites

- Python 3.11+
- Git
- Access to the **OpenAlex** dataset (automatically fetched via API).

## Installation

1. **Clone the repository** and navigate to the project directory.
 ```bash
 git clone <repo-url>
 cd projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l
 ```

2. **Create a virtual environment** and install dependencies.
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` pins `torch` to CPU-only version, `sentence-transformers`, and `pyalex`.*

3. **Verify dependencies**.
 ```bash
 python -c "import networkx; import sklearn; import torch; import pyalex; print('OK')"
 ```

## Data Setup

1. **Fetch Data**:
 - The pipeline automatically queries the **OpenAlex** API (` Name or service not known)"))]).
 - No manual download is required. The script will fetch a representative subgraph.
 - Ensure network access is available for the CI runner.

2. **Checksum the data** (optional but recommended for reproducibility).
 ```bash
 sha256sum data/raw/openalex_subset.parquet > data/raw/openalex_subset.parquet.sha256
 ```

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python -m src.cli.main --sample-size [deferred] --seed 42 --output data/results/analysis_output.json
```

### Parameters
- `--sample-size`: (Optional) Limit the number of nodes to process (e.g., `--sample-size 5000`) to ensure runtime < 6h on CI. Uses **degree-stratified sampling**.
- `--seed`: (Optional) Set random seed for reproducibility (default: 42).
- `--output`: Path to the JSON output file.

## Expected Output

The pipeline will generate:
1. **`data/processed/analysis_dataset.parquet`**: Processed node data with all metrics.
2. **`data/results/analysis_output.json`**: Statistical summary (correlations, p-values, binning trends).
3. **Console Logs**: Progress bars and summary statistics.

## Validation

To verify the results against the schema:

```bash
pytest tests/contract/test_schemas.py
```

## Troubleshooting

- **Memory Error**: If you encounter `MemoryError`, reduce the `--sample-size` or ensure no large intermediate objects are kept in memory.
- **Missing Title/Abstract**: Nodes with missing titles/abstracts will be skipped for novelty analysis but included in citation analysis.
- **No GPU**: The code explicitly enforces CPU execution. Do not attempt to force GPU usage.
- **API Rate Limits**: If OpenAlex API rate limits are hit, the script includes exponential backoff.