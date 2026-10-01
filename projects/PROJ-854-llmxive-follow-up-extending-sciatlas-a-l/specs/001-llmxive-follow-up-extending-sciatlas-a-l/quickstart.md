# Quickstart: Interdisciplinary Bridging Coefficient Analysis

## Prerequisites

- Python 3.11+
- Git
- 7GB+ RAM (for processing the subgraph)
- 2 CPU cores (minimum)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd PROJ-854-llmxive-follow-up-extending-sciatlas-a-l
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins all versions for reproducibility.*

## Data Preparation

Ensure the input data exists:
- `data/processed/subgraph.parquet` must be present.
- If missing, run the data ingestion script (if provided in `code/`) or download the OpenAlex subgraph as per the project documentation.

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python -m src.cli.main --input data/processed/subgraph.parquet --output data/processed/subgraph_with_clusters.parquet
```

### Options

- `--input`: Path to the input Parquet file (default: `data/processed/subgraph.parquet`).
- `--output`: Path for the enriched output (default: `data/processed/subgraph_with_clusters.parquet`).
- `--correction-method`: Multiple-comparison correction method. Options: `bonferroni`, `benjamini-hochberg` (default: `benjamini-hochberg`).
- `--seed`: Random seed for reproducibility (default: 42).

## Expected Outputs

1. **Enriched Data**: `data/processed/subgraph_with_clusters.parquet` containing all metrics.
2. **Logs**: `data/processed/excluded_nodes.json` (if any nodes were excluded).
3. **Reports**: A summary report printed to stdout or saved to `artifacts/results/summary_report.txt`.

## Validation

To verify the results:

1. **Schema Validation**:
   ```bash
   python -m tests.contract.test_schemas
   ```
   This ensures the output file matches the defined schema.

2. **Independence Check**:
   Run the unit test for US-002:
   ```bash
   python -m pytest tests/unit/test_embeddings.py::test_novelty_independence
   ```
   This confirms that novelty scores are not dependent on cluster assignments.

## Troubleshooting

- **Memory Error**: If you encounter `MemoryError`, reduce the sample size or ensure the input data is not larger than expected.
- **CUDA Error**: The pipeline is CPU-only. If you see CUDA errors, ensure `device="cpu"` is set in the embedding configuration (default).
- **Schema Mismatch**: Verify that the input `subgraph.parquet` contains all required columns (`id`, `title`, `cited_by_count`, `publication_date`, `field`).
