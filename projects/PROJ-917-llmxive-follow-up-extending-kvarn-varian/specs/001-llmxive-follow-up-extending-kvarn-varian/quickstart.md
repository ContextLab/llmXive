# Quickstart: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline consists of four sequential phases. Run them in order:

### Phase 1: Data Generation
Generates a large set of synthetic attention matrices and computes ground-truth scaling factors.
```bash
python code/data_generation/synthetic_matrix_generator.py The specific value to remove/generalize: a large-scale sample size

Rewritten passage:
The research question remains: [Insert Research Question]. The method will be: [Insert Method]. References: [Insert References]. This study will employ a large-scale sample size to ensure statistical power and generalizability, without predetermining the exact count at this planning stage. --output data/raw/synthetic_attention.json
python code/data_generation/sinkhorn_solver.py --input data/raw/synthetic_attention.json --output data/processed/labels.json
```

### Phase 2: Model Training
Trains the multi-layer perceptron and evaluates against the baseline.
```bash
python code/model_training/train_and_eval.py --train_data data/processed/labels.json --epochs sufficient for convergence --output data/analysis/model_metrics.json
```

### Phase 3: Simulation
Runs multiple independent autoregressive simulations of sufficient length to ensure convergence.
```bash
python code/simulation/autoregressive_loop.py --runs 30 --steps a sufficient number to ensure convergence --output data/simulation/accumulated_kl_divergence.csv
```

### Phase 4: Analysis
Performs statistical tests, sensitivity analysis, and theoretical bound computation.
```bash
python code/analysis/statistical_tests.py --input data/simulation/accumulated_kl_divergence.csv --output data/analysis/final_report.json
```

## Verification

To verify the setup:
1. Run the unit tests:
   ```bash
   pytest code/tests/ -v
   ```
2. Check that the output files exist in the `data/` directory.
3. Verify the `final_report.json` contains a p-value < 0.05 (if the hypothesis holds).

## Troubleshooting

- **Numerical Instability**: If you encounter `NaN` values, check the `epsilon` floor setting in `sinkhorn_solver.py`.
- **OOM Errors**: The synthetic dataset is small, but if you increase the count, consider reducing the matrix size or enabling streaming.
- **Convergence Failures**: The Sinkhorn solver may fail on extreme outliers. These are flagged in the logs and excluded from training.