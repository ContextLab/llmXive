# PROJ-819: Semantic Cache Optimization for EywaOrchestra

Follow-up study to "Heterogeneous Scientific Foundation Model Collaboration"
(arXiv:2604.27351). This project measures how a semantic similarity-based
caching layer affects the computational efficiency and scientific reasoning
accuracy of the EywaOrchestra framework on iterative, multi-turn
hypothesis-testing tasks.

## Research Question

How does the introduction of a semantic similarity-based caching mechanism
affect the computational efficiency and scientific reasoning accuracy of the
EywaOrchestra framework when processing iterative, multi-turn
hypothesis-testing tasks?

## Environment Setup

Requirements: Python 3.11+, pip, CPU-only machine (no CUDA required or used).

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Pinned dependencies include `sentence-transformers` (CPU-only),
`scikit-learn`, `numpy`, `pandas`, `pytest`, `cachetools`, and
`statsmodels`. The embedding model is `all-MiniLM-L6-v2` (384 dimensions),
downloaded automatically on first use.

If a GPU is present on your machine, force CPU execution:

```bash
export CUDA_VISIBLE_DEVICES=""
```

## Project Structure

```
code/
├── cache/
│ ├── semantic_cache.py # SemanticCache (LRU over CacheEntry objects)
│ └── utils.py # Embeddings, cosine similarity, thresholding
├── pipeline/
│ ├── eywa_orchestra.py # Deterministic, CPU-tractable EywaOrchestra mock
│ └── runner.py # Baseline / cached execution, warm-up phase
├── analysis/
│ ├── metrics.py # Runtime reduction, invocations, accuracy deviation
│ ├── stats.py # Permutation Test, OLS regression, Bonferroni
│ └── visualization.py # Trade-off curve plots
├── data/
│ ├── generator.py # Synthetic ground-truth generator (FR-007)
│ └── loaders.py # BenchmarkQuery loading
├── reproducibility/
│ └── manifest_manager.py # SHA-256 manifest of code/ and data/
└── main.py # Sensitivity analysis entry point
data/
├── raw/ # Raw benchmark data (if available)
└── derived/ # Generated datasets, results, statistics
state/
└── manifest.json # Content hashes for reproducibility
tests/
├── unit/ # Cache, generator, independence tests
└── integration/ # End-to-end pipeline tests
```

## Execution Instructions

Run all commands from the project root (`projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/`).

### 1. Generate the synthetic datasets

Produces `data/derived/synthetic_queries_test.json` (500 queries) and
`data/derived/synthetic_queries_warmup.json` (100 queries, stratified by
domain and step count):

```bash
python -m code.data.generator
```

### 2. Run the pipeline (baseline vs. cached)

The runner executes the warm-up phase (cache population) followed by the
test phase, and writes `data/derived/results.csv` with columns
`run_type`, `total_time`, `hit_rate`, `accuracy`, `total_queries`:

```bash
python -m code.pipeline.runner
```

### 3. Sensitivity analysis across thresholds

Sweeps the exact discrete threshold set {0.90, 0.95, 0.99}, clearing the
cache state between iterations. Produces
`data/derived/sensitivity_analysis.csv`, the statistical report
`data/derived/statistics.json` (permutation-test p-values with Bonferroni
correction, and OLS regression coefficients for
`runtime ~ hits + misses`), and the trade-off visualization
`data/derived/trade_off_curve.png`:

```bash
python -m code.main --weight 10
```

The `--weight` argument (default 10) controls the optimization rule
`score = runtime_reduction - weight * accuracy_deviation` used to identify
the optimal threshold. See `docs/research_decisions.md` for the
justification of this mechanism.

### 4. Reproducibility manifest

Regenerate or verify the SHA-256 manifest of all files under `code/` and
`data/` (writes `state/manifest.json`):

```bash
python -m code.reproducibility.manifest_manager
```

### 5. Verify data artifacts

Final sanity check that all artifacts in `data/derived/` match
`state/manifest.json`:

```bash
python code/verify_artifacts.py
```

## Running Tests

```bash
pytest tests/ -v
```

Unit tests cover cache hit/miss logic, cosine similarity, the synthetic
generator, and the epistemological independence constraint (FR-008). An
integration test covers the full sensitivity-analysis loop.

## Expected Outputs

| Artifact | Description |
|----------|-------------|
| `data/derived/synthetic_queries_test.json` | 500-query test set (BenchmarkQuery entities) |
| `data/derived/synthetic_queries_warmup.json` | 100-query warm-up set |
| `data/derived/results.csv` | Aggregated metrics for baseline and cached runs |
| `data/derived/sensitivity_analysis.csv` | Metrics per threshold {0.90, 0.95, 0.99} |
| `data/derived/statistics.json` | Permutation-test p-values (Bonferroni-corrected) and regression coefficients |
| `data/derived/trade_off_curve.png` | Hit-rate / runtime / accuracy trade-off curve |
| `data/derived/cache_events.log` | JSON Lines log of cache hits, misses, and evictions |
| `state/manifest.json` | SHA-256 hashes of all code and data files |

## Methodology Notes

- **Statistical tests**: A Permutation Test (n_permutations = 10000) is
 used for accuracy differences and a multi-variable linear regression
 (`runtime ~ hits + misses`, via `statsmodels.api.OLS`) for runtime,
 replacing the originally proposed McNemar's / paired t-tests due to
 contingency-table degeneracy. Bonferroni correction is applied across
 the three thresholds.
- **Ground-truth independence**: Synthetic ground truth is generated from
 documented analytical solutions with novel parameter combinations,
 verified via static code inspection to be independent of the
 EywaOrchestra inference logic (FR-007 / FR-008).
- **Resource constraints**: All models run on CPU in default precision;
 the cache implements LRU eviction (logged to
 `data/derived/cache_events.log`) when the memory limit is exceeded.

## Troubleshooting

- **Memory Error**: Ensure ≥ 7GB RAM; the LRU cache bounds memory usage.
- **Slow Runtime**: The baseline run is the most expensive step; reduce
 the query count in the generator if needed.
- **CUDA Error**: Set `CUDA_VISIBLE_DEVICES=""` to force CPU usage.