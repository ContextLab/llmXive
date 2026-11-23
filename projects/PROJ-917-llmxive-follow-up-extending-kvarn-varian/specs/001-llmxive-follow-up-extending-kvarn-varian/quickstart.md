# Quickstart: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Git

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-917-llmxive-follow-up-extending-kvarn-varian
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` is located in `code/` and pins all dependencies.*

## Running the Pipeline

### Step 1: Generate Synthetic Data

Generate synthetic attention matrices and compute ground-truth scaling factors.

```bash
python code/main.py --task generate_data
```

- **Output**: `data/raw/synthetic_attention_matrices.jsonl`
- **Time**: A short duration (depends on CPU speed).

### Step 2: Train the Static Prior Model

Train the 2-layer MLP on the generated data.

```bash
python code/main.py --task train_model
```

- **Output**: `code/models/static_prior_mlp.pt`
- **Metrics**: Training loss, test MSE (printed to console).

### Step 3: Run Simulation

Run the autoregressive simulation for both methods.

```bash
python code/main.py --task run_simulation --runs multiple_runs
```

- **Output**: `data/results/simulation_run_001.json` to `simulation_run_030.json`
- **Time**: Several hours (Multiple runs of [deferred] steps

Research question: [To be defined]
Method: [To be defined]
References: [To be defined]).

### Step 4: Analyze Results

Run statistical tests, sensitivity analysis, and theoretical lower bound comparison.

```bash
python code/main.py --task analyze_results
```

- **Output**: Summary statistics, t-test results, sensitivity plots, and theoretical bound comparison (saved to `data/results/analysis/`).

## Verification

### Unit Tests

Run the test suite to ensure correctness.

```bash
pytest tests/unit/
```

### Integration Tests

Run end-to-end tests for the simulation loop.

```bash
pytest tests/integration/
```

## Troubleshooting

- **Sinkhorn Solver Non-Convergence**: If many matrices fail to converge, increase `max_iterations` in `code/data_generation/sinkhorn_solver.py`.
- **Out of Memory**: Reduce `num_matrices` in `generate_data` task (e.g., [deferred] instead of [deferred]).
- **Time Limit Exceeded**: Reduce `steps` in `run_simulation` task (e.g., 500 instead of [deferred]) and note the power limitation.

## Next Steps

- Review `research.md` for detailed methodology and results.
- Check `data-model.md` for data structure details.
- Examine `contracts/` for schema definitions.