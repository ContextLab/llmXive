# API Reference

This document provides a high-level overview of the core modules in the llmXive drift detection pipeline.

## Core Modules

### `code/config.py`
Manages project configuration, paths, and random seeds.

**Key Functions**:
- `set_seed(seed: int)`: Sets global random seeds.
- `get_config()`: Returns the full configuration dictionary.
- `get_path(name: str)`: Resolves a logical path (e.g., "raw_data") to a filesystem path.
- `ensure_directories()`: Creates all required directories if they do not exist.

### `code/data_loader.py`
Handles fetching and loading external datasets.

**Key Functions**:
- `fetch_advbench()`: Downloads the AdvBench dataset.
- `fetch_hf4()`: Downloads the HF4 dataset.
- `fetch_taxonomy()`: Downloads the OWASP taxonomy.
- `verify_checksum(file_path: str, expected_checksum: str)`: Validates file integrity.

### `code/taxonomy_builder.py`
Constructs centroid embeddings from the taxonomy.

**Key Functions**:
- `load_taxonomy(path: str)`: Loads the mapped taxonomy JSON.
- `build_centroids(taxonomy: List[Dict], model_name: str)`: Generates centroid vectors.
- `save_centroids(centroids: Dict, path: str)`: Persists centroids to disk.

### `code/drift_scoring.py`
Computes drift scores for log entries.

**Key Functions**:
- `load_centroids(path: str)`: Loads pre-computed centroids.
- `compute_cosine_distance(log_vectors: np.ndarray, centroids: np.ndarray)`: Calculates minimum distance.
- `batch_process_logs(logs: List[Dict], batch_size: int)`: Processes logs in memory-efficient batches.
- `export_results(results: List[Dict], path: str)`: Saves results to CSV.

### `code/annotator_interface.py`
Prepares data for human annotation.

**Key Functions**:
- `stratify_logs(df: pd.DataFrame, top_pct: float, bottom_pct: float)`: Selects high/low drift logs.
- `prepare_annotation_interface(df: pd.DataFrame)`: Formats data for annotators.
- `export_stratified_bins(df: pd.DataFrame, output_dir: str)`: Saves blinded batches.

### `code/validation.py`
Performs statistical validation of results.

**Key Functions**:
- `calculate_cohen_d(group1: np.ndarray, group2: np.ndarray)`: Computes effect size.
- `run_logistic_regression(df: pd.DataFrame)`: Fits a logistic model.
- `calculate_kappa(labels1: List, labels2: List)`: Computes inter-annotator agreement.

### `code/utils.py`
Utility helpers for schema validation and file I/O.

**Key Functions**:
- `load_schema(path: str)`: Loads a JSON/YAML schema.
- `validate_against_schema(data: Any, schema: Dict)`: Validates data structure.
- `save_csv_file(data: List[Dict], path: str)`: Helper to write CSVs.

## Usage Example

```python
from config import set_seed, ensure_directories, get_path
from data_loader import fetch_advbench
from taxonomy_builder import build_centroids
from drift_scoring import batch_process_logs, export_results

# Setup
set_seed(42)
ensure_directories()

# Load Data
logs = fetch_advbench()

# Build Taxonomy (if not cached)
taxonomy = load_taxonomy(get_path("taxonomy_mapped"))
centroids = build_centroids(taxonomy)

# Score Logs
results = batch_process_logs(logs, centroids)

# Export
export_results(results, get_path("drift_scores_csv"))
```
