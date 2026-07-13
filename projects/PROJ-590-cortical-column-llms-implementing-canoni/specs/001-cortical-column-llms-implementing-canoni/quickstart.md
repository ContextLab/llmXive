# Quickstart: Cortical Column LLMs

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a CPU-only environment (local or GitHub Actions)

## 1. Setup Environment

Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd projects/PROJ-590-cortical-column-llms-implementing-canoni/code
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Dependencies**:
-   `torch` (CPU version)
-   `numpy`
-   `scipy`
-   `pytest`
-   `pyyaml`
-   `psutil` (for resource monitoring in tests)

## 2. Generate Data

Run the data generation script to create the synthetic datasets:

```bash
python src/data/benchmarks.py --output data/raw_function_data.json --seed 42
```

This creates:
-   `data/raw_function_data.json` (Lorenz for training)
-   `data/test_functions.json` (Polynomials/Fourier for testing)

## 3. Run Baseline (Control)

Train the standard Transformer baseline:

```bash
python -m src.training.trainer --config data/configs/baseline.yaml --output data/results/baseline_run.json
```

**Expected Output**: `data/results/baseline_run.json` with `test_mae < 0.05` and `training_time_seconds < 21600`.

## 4. Run Microcircuit Experiment

Train the hybrid model with cortical columns:

```bash
python -m src.training.trainer --config data/configs/microcircuit.yaml --output data/results/microcircuit_run.json
```

## 5. Run Ablation & Scaling

Execute the ablation and scaling studies:

```bash
# Ablation: Remove recurrence
python -m src.experiments.ablation --variant ablation_recurrence --output data/results/ablation_recurrence.json

# Scaling: 2x columns
python -m src.experiments.scaling --variant scaling_2x --output data/results/scaling_2x.json

# Scaling: 4x columns (if time permits)
python -m src.experiments.scaling --variant scaling_4x --output data/results/scaling_4x.json
```

## 6. Verify Results

Run the test suite to verify constraints:

```bash
pytest tests/ -v --timeout=3600
```

**Key Checks**:
-   Baseline MAE < 0.05.
-   Microcircuit parameter count within ±1% of baseline (via padding).
-   E/I ratio maintained at 4:1 (±0.1).
-   Total training time < 6 hours.
-   Paired t-test p-value < 0.05 (with Bonferroni correction) for ablation differences.

## 7. Reproducibility

To ensure reproducibility, re-run the entire pipeline with a fixed seed:

```bash
python scripts/run_all_experiments.sh --seed 12345
```

The output artifacts will be identical (byte-for-byte) due to pinned seeds and deterministic CPU operations.