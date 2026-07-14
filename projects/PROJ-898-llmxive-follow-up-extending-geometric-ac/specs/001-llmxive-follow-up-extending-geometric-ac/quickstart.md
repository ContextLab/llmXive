# Quickstart: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Prerequisites

- Python 3.11+
- pip / virtualenv
- Git (for cloning the repository)
- Access to GitHub Actions (for CI execution) or a local CPU-only environment.

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmxive-follow-up
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/code/requirements.txt
 ```
 *Note: This installs `torch` (CPU), `pybullet`, `cvxpy`, `scipy`, and other required packages.*

## Data Generation (Phase 1)

Generate the synthetic topology-shift test set:

```bash
python projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/code/data_generation.py \
 --output data/generated/topology_shift_test_set_v1.jsonl \
 --num-topologies 50 \
 --seed 42
```

- This script uses PyBullet to create 50 unique topologies (novel kinematic chains and soft materials).
- It verifies zero overlap with the original GAM training distribution.
- **Output**: `data/generated/topology_shift_test_set_v1.jsonl`.

## Inference Pipeline (Phase 2)

Run the symbolic planner and baseline GAM on the generated test set:

```bash
python projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/code/inference_pipeline.py \
 --test-set data/generated/topology_shift_test_set_v1.jsonl \
 --gfm-weights data/raw/gfm_weights.pt \
 --output data/results/trial_results.csv \
 --timeout 300 \
 --seed 42
```

- **Symbolic Mode**: Runs the symbolic solver (FR-003).
- **Baseline Mode**: Runs the original GAM neural predictor.
- **Timeout**: 300 seconds per step (prevents CI timeout).
- **Output**: `data/results/trial_results.csv` (success/failure, latency).

## Statistical Analysis (Phase 3)

Generate the comparative report:

```bash
python projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/code/analysis.py \
 --input data/results/trial_results.csv \
 --output data/results/statistical_report.json
```

- Performs Fisher's Exact Test (success rates), **Wilcoxon Signed-Rank Test** (latency for non-censored data), and **Kaplan-Meier Survival Analysis** (for censored timeout data).
- **Output**: `data/results/statistical_report.json` (p-values, effect sizes).

## Verification

1. **Check Data Integrity**:
 ```bash
 sha256sum data/generated/topology_shift_test_set_v1.jsonl
 ```
 Compare against the hash in `state/...artifact_hashes`.

2. **Run Unit Tests**:
 ```bash
 pytest tests/unit/
 ```

3. **Run Integration Tests**:
 ```bash
 pytest tests/integration/test_full_pipeline.py
 ```

## Troubleshooting

- **CUDA Error**: Ensure `torch` is installed as the CPU version (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
- **Solver Timeout**: If trials fail due to timeout, check `data/results/trial_results.csv` for `failure_reason: timeout`. Increase solver complexity limits or reduce topology complexity.
- **Memory Error**: Reduce `--num-topologies` or run trials sequentially.