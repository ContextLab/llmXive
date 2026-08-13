# llmXive: Heterogeneous Scientific Foundation Model Collaboration

Automated science pipeline for evaluating semantic caching in heterogeneous scientific model orchestration.

## Overview

This project implements a lightweight semantic caching layer that intercepts queries, computes embeddings, and retrieves cached outputs to reduce runtime and computational cost while maintaining accuracy.

## Prerequisites

- Python 3.9+
- pip (package installer)
- CPU-only environment (no CUDA required)

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-819-llmxive-follow-up-extending-heterogeneou
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

The `requirements.txt` includes:
- `sentence-transformers`: For embedding generation
- `scikit-learn`: For statistical utilities
- `numpy`, `pandas`: For data handling
- `pytest`, `pytest-benchmark`: For testing
- `cachetools`: For LRU cache implementation
- `statsmodels`: For linear regression analysis

## Project Structure

```
code/
├── cache/
│ ├── semantic_cache.py # LRU cache with semantic similarity
│ └── utils.py # Embedding and similarity utilities
├── data/
│ ├── generator.py # Synthetic query generation
│ ├── loaders.py # Benchmark query loading
│ └── schema.py # BenchmarkQuery dataclass
├── pipeline/
│ ├── eywa_orchestra.py # Mock EywaOrchestra pipeline
│ └── runner.py # Orchestration and metrics
├── analysis/
│ ├── metrics.py # Performance metrics calculation
│ ├── stats.py # Statistical tests (Permutation, Linear Regression)
│ └── visualization.py # Trade-off curve plotting
├── reproducibility/
│ └── manifest_manager.py # SHA-256 manifest generation
├── setup_data_dirs.py # Directory and checksum setup
└── setup_project.py # Project initialization

data/
├── raw/ # Raw input data (if any)
└── derived/ # Generated datasets and results
 ├── synthetic_queries_test.json
 ├── synthetic_queries_warmup.json
 ├── results.csv
 ├── sensitivity_analysis.csv
 ├── statistics.json
 ├── trade_off_curve.png
 └── cache_events.log

state/
└── manifest.json # File integrity manifest

tests/
├── unit/ # Unit tests
└── integration/ # Integration tests
```

## Quick Start

### 1. Generate Datasets

Generate the test set (500 queries) and warm-up set (100 queries):

```bash
python code/data/generator.py --dataset test --output data/derived/synthetic_queries_test.json
python code/data/generator.py --dataset warmup --output data/derived/synthetic_queries_warmup.json
```

### 2. Run the Pipeline

Execute the full pipeline with cache enabled, running sensitivity analysis across thresholds `[0.90, 0.95, 0.99]`:

```bash
python code/main.py
```

This will:
- Populate the cache using the warm-up set
- Run baseline execution (no cache)
- Run cached execution with varying thresholds
- Perform statistical analysis (Permutation Test, Linear Regression)
- Generate visualizations and reports

### 3. Analyze Results

Output files in `data/derived/`:
- `results.csv`: Aggregated metrics for baseline vs. cached runs
- `sensitivity_analysis.csv`: Metrics per threshold
- `statistics.json`: P-values and regression coefficients
- `trade_off_curve.png`: Visualization of hit-rate vs. runtime vs. accuracy
- `cache_events.log`: JSON Lines log of cache events

## Configuration

### Optimization Weight

The optimal threshold is determined by maximizing:
```
score = runtime_reduction - weight * accuracy_deviation
```

The `weight` parameter can be set via CLI:
```bash
python code/main.py --weight 10
```

Default weight is `10`.

### Similarity Thresholds

The sensitivity analysis iterates through discrete thresholds: `[0.90, 0.95, 0.99]`.

## Testing

Run all tests:
```bash
pytest tests/
```

Run specific test suites:
```bash
pytest tests/unit/ # Unit tests
pytest tests/integration/ # Integration tests
```

Run with benchmarking:
```bash
pytest --benchmark-only
```

## Code Quality

Format code:
```bash
black code/
```

Lint code:
```bash
ruff check code/
```

Check formatting (without modifying):
```bash
black --check code/
```

## Reproducibility

The project maintains a `state/manifest.json` file that tracks SHA-256 hashes of all files in `code/` and `data/`. This ensures reproducibility and detects any modifications.

Generate or verify the manifest:
```bash
python code/reproducibility/manifest_manager.py
```

## Statistical Methodology

- **Permutation Test**: Used for accuracy differences (replaces paired t-test due to degeneracy)
- **Linear Regression**: `runtime ~ hits + misses` to quantify runtime reduction
- **Bonferroni Correction**: Applied for multiple comparisons across thresholds

## Contributing

1. Ensure all tests pass: `pytest`
2. Format code: `black code/`
3. Lint code: `ruff check code/`
4. Update `README.md` if new features are added

## License

[Specify license here]

## References

- arXiv:2509.23775 (Context for synthetic query generation)