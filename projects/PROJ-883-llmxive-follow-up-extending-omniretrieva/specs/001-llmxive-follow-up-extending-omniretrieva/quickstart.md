# Quickstart: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites
- Python 3.11+
- Linux environment
- 7GB+ RAM, Multiple CPU cores

## Installation
1. Setup venv and install:
   ```bash
   pip install -r requirements.txt
   ```
2. Verify linting:
   ```bash
   ruff check code/
   ```

## Running the Pipeline
The entire pipeline can be executed as a module:
```bash
python -m code.main
```

## Manual Steps
1. Data Preparation: `python code/data_loader.py --prepare`
2. Query Generation: `python code/query_generator.py --levels 1 2 3 4 --count 100`
3. Ground Truth: `python code/ground_truth_engine.py --input data/processed/generation_log.json --output data/processed/generation_log.json`
4. Benchmark: `python code/benchmark_runner.py --throttle cgroups`
5. Stats: `python code/stats.py --input data/processed/execution_logs.csv`
6. Viz: `python code/visualize.py --input data/processed/execution_logs.csv --output data/results/interaction_plot.png`