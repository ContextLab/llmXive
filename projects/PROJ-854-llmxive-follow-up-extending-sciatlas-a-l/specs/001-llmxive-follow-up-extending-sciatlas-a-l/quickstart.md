# Quickstart Guide: Interdisciplinary Bridging Coefficient Analysis

This guide provides instructions for setting up, running, and validating the complete analysis pipeline for computing bridging coefficients, novelty scores, and statistical correlations using OpenAlex data.

## Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended for full graph processing)
- **Disk**: 10GB free space for datasets and artifacts
- **CPU**: Multi-core processor (parallel processing enabled)

### Dependencies
Install all required packages using pip:

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:
- `networkx`: Graph construction and manipulation
- `scikit-learn`: Clustering (KMeans) and metrics
- `sentence-transformers`: Embedding generation (all-MiniLM-L6-v2)
- `pandas`, `numpy`: Data manipulation
- `scipy`: Statistical tests
- `pyalex`: OpenAlex API client
- `memory-profiler`: Memory usage tracking
- `pytest`, `ruff`, `black`: Testing, linting, and formatting
- `pyarrow`: Parquet file support

### Environment Setup
1. Clone the repository
2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4. Verify OpenAlex connectivity:
 ```bash
 python -m pytest tests/unit/test_data_source.py -v
 ```

## Running the Pipeline

The pipeline is executed in sequential stages. Each stage produces artifacts required by subsequent stages.

### Step 1: Project Initialization
(Run only if starting fresh)
```bash
python code/scripts/setup_project.py
```
This creates the directory structure: `src/`, `tests/`, `data/`, `artifacts/`.

### Step 2: Data Ingestion and Graph Construction
Fetches OpenAlex data, performs degree-stratified sampling, and builds the subgraph.
```bash
python code/scripts/ingest_pipeline.py
```
**Output**: `data/processed/subgraph_with_clusters.parquet`
**Time**: ~10-30 minutes depending on sample size
**Memory**: Peak ~6-7GB

### Step 3: Embedding Generation and Novelty Calculation
Generates sentence embeddings, performs KMeans clustering, and computes novelty scores.
```bash
python code/scripts/embeddings_pipeline.py
```
**Output**: `data/processed/novelty_scores.parquet`, `data/logs/excluded_nodes.csv`
**Time**: ~5-15 minutes
**Memory**: Peak ~4-5GB (batch processing enabled)

### Step 4: Final Dataset Assembly
Merges graph data with novelty scores and temporal lags.
```bash
python code/scripts/save_final_dataset.py
```
**Output**: `data/processed/final_analysis_dataset.parquet`

### Step 5: Statistical Analysis
Computes correlations, regression, and binned analysis with multiple-comparison correction.
```bash
python code/scripts/save_statistical_metrics.py --correction-method bh
```
**Options**:
- `--correction-method`: `bonferroni` or `bh` (Benjamini-Hochberg, default)
**Output**: `artifacts/results/statistical_metrics.json`, `artifacts/results/corrected_pvalues.json`

### Step 6: Report Generation
Generates the final analysis report with associational labeling.
```bash
python code/scripts/generate_analysis_report.py
```
**Output**: `artifacts/results/analysis_report.md`

### Step 7: Validation
Runs the full pipeline validation and generates a reproducibility report.
```bash
python code/scripts/run_validation.py
```
**Output**: `artifacts/validation_report.md`

## Testing

Run the full test suite to verify correctness:
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

Run specific test categories:
- **Unit tests**: `pytest tests/unit/ -v`
- **Integration tests**: `pytest tests/integration/ -v`
- **Contract tests**: `pytest tests/contract/ -v`
- **Benchmarks**: `pytest tests/bench/ -v`

## Output Artifacts

The pipeline produces the following key artifacts:

| Artifact | Location | Description |
|----------|----------|-------------|
| Subgraph with Clusters | `data/processed/subgraph_with_clusters.parquet` | Graph with `primary_cluster` and `bridging_coefficient` |
| Final Analysis Dataset | `data/processed/final_analysis_dataset.parquet` | Merged dataset with novelty scores and temporal lags |
| Statistical Metrics | `artifacts/results/statistical_metrics.json` | Correlation coefficients, p-values, regression results |
| Corrected P-values | `artifacts/results/corrected_pvalues.json` | Multiple-comparison corrected p-values |
| Analysis Report | `artifacts/results/analysis_report.md` | Human-readable report with "associational" label |
| Validation Report | `artifacts/validation_report.md` | Pipeline reproducibility verification |
| Memory Profile | `artifacts/results/memory_profile.log` | Peak RAM usage per stage |

## Troubleshooting

### Memory Errors
If you encounter `MemoryError`:
1. Reduce the sample size in `src/services/ingest.py` (adjust `target_size`)
2. Ensure batch processing is enabled in `src/services/embeddings.py`
3. Close other applications to free RAM

### OpenAlex Connectivity
If tests fail to reach OpenAlex:
```bash
python -c "import pyalex; print(pyalex.config)"
```
Ensure you have internet access and no firewall restrictions.

### Missing Dependencies
If import errors occur:
```bash
pip install -r requirements.txt --force-reinstall
```

## Notes

- **Spec Drift**: The original spec references "PubGraph", but the implementation uses "OpenAlex" via `pyalex`.
- **Reproducibility**: All random seeds are pinned (42) in `tests/conftest.py` and `src/lib/config.py`.
- **Associational Findings**: All statistical results are explicitly labeled as "associational" (not causal) in the final report.