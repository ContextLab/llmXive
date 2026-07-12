# Quickstart Guide: Interdisciplinary Bridging Coefficient Analysis

This guide walks you through the setup and execution of the bridging coefficient analysis pipeline. The pipeline ingests OpenAlex data, computes topological metrics (Louvain clustering, bridging coefficients), derives outcome variables (citations, novelty scores), and performs statistical validation.

## Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **Memory**: Minimum 7GB RAM (for batched embedding processing)
- **Disk**: At least 5GB free space for data and artifacts
- **CPU**: Multi-core processor recommended for parallel processing

### Dependencies
Install the required Python packages:

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:
- `pyalex` - OpenAlex API client
- `networkx` - Graph analysis
- `scikit-learn` - K-means clustering, embeddings
- `sentence-transformers` - Title embeddings
- `pandas`, `numpy` - Data manipulation
- `scipy` - Statistical tests
- `pyarrow` - Parquet file support
- `ruff`, `black` - Code linting and formatting
- `pytest` - Testing framework

### Project Setup
1. Clone the repository and navigate to the project directory.
2. Ensure the project structure is created (run `python code/scripts/setup_project.py` if needed):
 ```bash
 mkdir -p code/src/{models,services,cli,lib}
 mkdir -p code/tests/{contract,integration,unit}
 mkdir -p code/data/{raw,processed}
 mkdir -p code/artifacts/{results,plots}
 ```
3. Configure linting and formatting (see `pyproject.toml`):
 ```bash
 pip install ruff black
 ```

## Running the Pipeline

The pipeline consists of four main stages. Execute them in order:

### Stage 1: Data Ingestion and Graph Construction
Fetch a degree-stratified sample from OpenAlex and build the graph:

```bash
python code/scripts/ingest_and_build_graph.py
```

**Output**: `code/data/processed/subgraph_with_clusters.parquet`
- Contains nodes with `bridging_coefficient`, `primary_cluster`, and citation counts.

### Stage 2: Embedding and Novelty Calculation
Generate title embeddings and compute novelty scores:

```bash
python code/scripts/generate_embeddings_and_novelty.py
```

**Output**: `code/data/processed/final_analysis_dataset.parquet`
- Includes `topic_cluster` assignments and `novelty_score` for each node.

### Stage 3: Statistical Analysis
Perform correlation, regression, and binned analysis:

```bash
python code/scripts/save_statistical_metrics.py --correction-method fdr_bh
```

**Outputs**:
- `code/artifacts/results/statistical_metrics.json` - Coefficients and p-values
- `code/artifacts/results/analysis_report.md` - Human-readable report

### Stage 4: Generate Final Report
Compile all results into a comprehensive report:

```bash
python code/scripts/generate_analysis_report.py
```

## Verification and Testing

Run the test suite to validate the pipeline:

```bash
pytest code/tests/ -v
```

Key tests:
- `tests/contract/test_node_schema.py` - Validates node data structure
- `tests/integration/test_ingest_pipeline.py` - Tests end-to-end ingestion
- `tests/unit/test_graph_utils.py` - Verifies bridging coefficient calculations
- `tests/unit/test_novelty_calculation.py` - Checks novelty score computation

## Output Files

| File | Description |
|------|-------------|
| `data/processed/subgraph_with_clusters.parquet` | Graph with Louvain clusters and bridging coefficients |
| `data/processed/final_analysis_dataset.parquet` | Final dataset with novelty scores and topic clusters |
| `artifacts/results/statistical_metrics.json` | Statistical analysis results (coefficients, p-values) |
| `artifacts/results/analysis_report.md` | Comprehensive analysis report |
| `artifacts/validation_report.md` | Pipeline execution log and artifact hashes |

## Configuration

Edit `code/src/lib/config.py` to modify:
- Random seeds for reproducibility
- Data and artifact paths
- Sampling parameters for OpenAlex
- Clustering hyperparameters (e.g., number of k-means clusters)

## Troubleshooting

### Memory Errors
If you encounter memory issues:
- Reduce the sample size in `config.py`
- Ensure batch processing is enabled in `embeddings.py`
- Close other applications to free RAM

### API Rate Limits
OpenAlex may rate-limit requests. Implement exponential backoff in `ingest.py` if needed.

### Missing Dependencies
If imports fail, verify `requirements.txt` is installed:
```bash
pip install -r requirements.txt --upgrade
```

## Next Steps

- Explore the `artifacts/results/` directory for detailed findings
- Review `analysis_report.md` for interpretive insights
- Extend the pipeline with additional analysis modules as needed