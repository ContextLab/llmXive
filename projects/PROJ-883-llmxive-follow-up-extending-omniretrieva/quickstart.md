# Quickstart Guide: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites
- Python 3.11+
- Linux environment (GitHub Actions or local)
- 7 GB+ RAM, multiple CPU cores
- Internet access for dataset download (optional – synthetic fallback is used)

## Installation

1. **Clone and set up the virtual environment**
 ```bash
 cd projects/PROJ-883-llmxive-follow-up-extending-omniretrieva
 python -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Verify dependencies**
 ```bash
 python -c "import pandas, scipy, statsmodels, networkx, rdflib; print('All dependencies OK [UNRESOLVED-CLAIM: c_4d3b1f65 — status=not_enough_info]')"
 ```

3. **Linting**
 ```bash
 ruff check code/
 ```

## Running the Benchmark

### 1. Data preparation
```bash
python code/data_loader.py --prepare
```

### 2. Generate queries & ground truth
```bash
python code/query_generator.py --levels 1 2 3 4 --count [sufficient sample size] --seed 42
python code/ground_truth_engine.py --input data/processed/generation_log.json --output data/processed/generation_log.json
```

### 3. Execute benchmark
```bash
python code/benchmark_runner.py --throttle cgroups --timeout 60
```

### 4. Statistical analysis
```bash
python code/analysis/stats.py --input data/processed/execution_logs.csv
```

### 5. Visualization (optional)
```bash
python code/visualize.py --input data/processed/execution_logs.csv --output data/results/interaction_plot.png
```

## Full pipeline (module entry point)
```bash
python -m code.main
```

## Notes
- If cgroups cannot be applied, the benchmark runner falls back to a synthetic
 mode and logs a warning – the pipeline still produces the required CSV.
- The synthetic data used for queries is deterministic (seed = 42) and
 conforms to ``query_instance.schema.yaml`` (schema creation is handled in T004).
- All generated artifacts are written under the ``data/`` hierarchy.
