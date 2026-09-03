# llmXive: Heterogeneous Scientific Foundation Model Collaboration

A research pipeline implementing a lightweight semantic caching layer for scientific query processing, evaluating the trade-off between runtime efficiency and accuracy in heterogeneous model collaboration.

## Project Overview

This project implements the "Heterogeneous Scientific Foundation Model Collaboration" study, focusing on:
- **Semantic Caching**: Intercepting queries using embedding-based similarity to reuse cached LLM outputs.
- **Efficiency Analysis**: Quantifying runtime reduction and invocation savings via a mock EywaOrchestra pipeline.
- **Accuracy Trade-offs**: Using Permutation Tests and Linear Regression to validate statistical significance.
- **Threshold Sensitivity**: Analyzing performance across similarity thresholds (0.90, 0.95, 0.99).

## Prerequisites

- **Python**: 3.9 or higher
- **OS**: Linux/macOS (tested on CI environments)
- **Hardware**: CPU-only execution (no GPU required).

## Installation

1. **Clone the repository** and navigate to the project directory:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-819-llmxive-follow-up-extending-heterogeneou
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 *Dependencies include*: `sentence-transformers`, `scikit-learn`, `numpy`, `pandas`, `pytest`, `cachetools`, `statsmodels`, `black`, `ruff`.

4. **Verify installation**:
 ```bash
 python -m pytest --version
 python -c "import sentence_transformers; print('OK')"
 ```

## Project Structure

```text
.
├── code/
│ ├── cache/ # Semantic caching logic (LRU, embeddings)
│ ├── data/ # Data generation and loading utilities
│ ├── pipeline/ # EywaOrchestra mock and execution runner
│ ├── analysis/ # Metrics, statistics, and visualization
│ ├── reproducibility/ # Manifest and checksum management
│ └── setup_project.py # Project initialization script
├── data/
│ ├── raw/ # Raw input data (if applicable)
│ └── derived/ # Generated queries, results, and plots
├── tests/
│ ├── unit/ # Unit tests for core logic
│ └── integration/ # Integration tests for pipeline flows
├── state/
│ └── manifest.json # Reproducibility manifest (auto-generated)
├── docs/
│ └── research_decisions.md # Documentation of optimization weights
├── requirements.txt
├── README.md
└── pyproject.toml # Linting and testing configuration
```

## Execution Instructions

### 1. Data Generation (Phase 2)

Generate the synthetic test set and warm-up set required for benchmarking.

```bash
python code/data/generator.py
```

*Outputs*:
- `data/derived/synthetic_queries_test.json` (500 queries)
- `data/derived/synthetic_queries_warmup.json` (100 queries)

*Note*: This step also triggers the manifest generation hook (`state/manifest.json`).

### 2. Run the Full Pipeline (Phase 3-5)

Execute the full sensitivity analysis loop, including baseline and cached runs across thresholds `[0.90, 0.95, 0.99]`.

```bash
python code/main.py
```

*Arguments*:
- `--weight`: Optimization weight for the score function (default: `10`).
- `--thresholds`: Comma-separated list of thresholds (default: `0.90,0.95,0.99`).

*Outputs*:
- `data/derived/results.csv`: Aggregated metrics per run.
- `data/derived/sensitivity_analysis.csv`: Metrics per threshold.
- `data/derived/statistics.json`: P-values and regression coefficients.
- `data/derived/trade_off_curve.png`: Visualization of the trade-off curve.
- `data/derived/cache_events.log`: JSON Lines log of eviction events.

### 3. Run Baseline vs. Cached Comparison (Phase 4)

To run a specific comparison without the full sensitivity loop:

```bash
# Baseline run (cache ignored)
python code/pipeline/runner.py --mode baseline

# Cached run (warm-up cache populated)
python code/pipeline/runner.py --mode cached --threshold 0.95
```

### 4. Run Tests

Execute the full test suite:

```bash
pytest tests/ -v
```

Run specific unit tests for cache logic:

```bash
pytest tests/unit/test_cache.py -v
```

Run integration tests for the pipeline:

```bash
pytest tests/integration/test_pipeline.py -v
```

## Configuration

- **Similarity Thresholds**: Defined in `code/main.py` (default: `0.90, 0.95, 0.99`).
- **Cache Size Limit**: Configured in `code/cache/semantic_cache.py` (default: 1GB or 1000 entries).
- **Optimization Weight**: Passed via CLI `--weight` or configured in `docs/research_decisions.md`.

## Reproducibility

The project maintains a `state/manifest.json` file that records SHA-256 hashes of all code and data artifacts. This file is automatically updated after data generation and code modifications.

To verify artifact integrity:

```bash
python code/verify_artifacts.py
```

## Troubleshooting

- **Import Errors**: Ensure you are running from the project root and the virtual environment is activated.
- **Memory Issues**: The cache eviction policy triggers at 1GB. If running on low-memory systems, reduce the limit in `semantic_cache.py`.
- **Embedding Model Failures**: The pipeline uses CPU-only sentence transformers. If the model fails to load, check internet connectivity for the initial download.

## Contributing

1. Ensure `black` and `ruff` pass before committing:
 ```bash
 black --check code/ tests/
 ruff check code/ tests/
 ```
2. Add tests for new functionality in `tests/unit/` or `tests/integration/`.
3. Update `README.md` if new CLI arguments or data artifacts are added.

## License

This project is part of the llmXive research initiative. See the LICENSE file for details.