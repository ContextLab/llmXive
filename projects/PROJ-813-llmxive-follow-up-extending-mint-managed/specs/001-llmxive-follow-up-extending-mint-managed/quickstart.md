# Quickstart: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

## Prerequisites

- Python 3.11+
- pip
- (Optional) `virtualenv` or `conda`

## Installation

1. **Clone and Setup**:
   ```bash
   cd projects/PROJ-813-llmxive-follow-up-extending-mint-managed
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Verify Dependencies**:
   ```bash
   python -c "import simpy; import numpy; import scipy; print('Dependencies OK')"
   ```

## Running the Pipeline

The pipeline is executed in three stages: Data Generation, Topology Construction, and Simulation.

### Step 1: Generate Synthetic Data

```bash
# Generate 10,000 adapters in 50 clusters
python code/data/generate_adapters.py --seed 42 --count 10000 --clusters 50

# Generate the overlap matrix
python code/data/compute_overlap.py --input data/raw/adapters.parquet --output data/processed/overlap_matrix.csv

# Generate a single trace for testing (or use the experiment runner for full traces)
python code/data/generate_trace.py --seed 42 --count 1000000 --output data/processed/test_trace.parquet
```

### Step 2: Run Simulations

Run a single replication for testing:
```bash
python code/simulation/run_simulation.py --policy fcfs --replication 1 --trace data/processed/test_trace.parquet
```

Run the full experiment (30 replications, 3 policies):
```bash
python code/simulation/run_experiment.py --policies fcfs greedy topological --replications 30 --trace-size 1000000
```
*Note: This may take up to 6 hours on a 2-core runner. Each replication uses a unique trace, but the same trace is used for all policies within that replication.*

### Step 3: Analyze Results

```bash
python code/analysis/stats.py --input data/logs/ --output data/processed/results_summary.csv
python code/analysis/visualize.py --input data/processed/results_summary.csv
```

## Validation

To verify the setup:
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Troubleshooting

- **Memory Error**: Reduce `--trace-size` or `--count` in generation. Ensure `float32` is used for the overlap matrix.
- **Timeout**: If the simulation exceeds 6 hours, the CI job will fail. Check `code/simulation/engine.py` for inefficient loops.

