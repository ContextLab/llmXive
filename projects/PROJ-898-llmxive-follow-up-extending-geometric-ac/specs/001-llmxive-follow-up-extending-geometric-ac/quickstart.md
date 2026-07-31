# Quickstart: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Prerequisites

- **Python**: 3.10 or higher
- **System Dependencies**: `gcc`, `g++` (for compiling PyBullet extensions if necessary)
- **Hardware**: 2-core CPU, 8GB RAM (minimum), no GPU required.

## Installation

1. **Clone the Repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-898-llmxive-follow-up-extending-geometric-ac
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note*: Ensure `pybullet`, `torch`, `cvxpy`, and `scipy` are installed.

4. **Verify Environment**:
   ```bash
   python -c "import pybullet; import torch; print('Environment OK')"
   ```

## Configuration

Edit `code/config.yaml` to set:
- `random_seed`: Fixed integer (e.g., 42).
- `solver_timeout`: Max seconds per step (default: 300).
- `num_trials`: Number of trials per condition (default: 50).
- `gfm_weights_path`: Path to the frozen GFM weights (must exist in `data/raw/`).

## Running the Pipeline

The pipeline is executed in three stages.

### Stage 1: Generate Topology-Shift Test Set
```bash
python code/data_generation/topology_generator.py
```
- **Output**: `data/raw/novel_topology_set.json`.
- **Check**: Ensure `total_count` in the JSON is >= 50. If the script exits with `error_code: 1`, the generation failed (not enough unique topologies found).

### Stage 2: Run Experiments (Symbolic vs. Baseline)
```bash
python code/main.py
```
- **Process**:
  1. Loads the novel topology set.
  2. Runs multiple trials for the **Symbolic** approach.
  3. Runs multiple trials for the **Baseline** GAM.
  4. Records results in `data/results/trial_log.csv`.
  5. Verifies gradient flow and logs to `data/results/gradient_flow_log.json`.
- **Duration**: Estimated -4 hours on a 2-core CPU.

### Stage 3: Statistical Analysis
```bash
python code/analysis/statistics.py
```
- **Input**: `data/results/trial_log.csv`.
- **Output**: Prints the p-values, confidence intervals, and effect sizes to the console.
- **Report**: Generates a summary JSON in `data/results/statistical_summary.json`.

## Verification

To verify the integrity of the run:
1. **Schema Validation**:
   ```bash
   pytest tests/contract/test_schema_validation.py
   ```
2. **Reproducibility Check**:
   Re-run `python code/main.py` with the same `random_seed` and verify that the checksum of `data/results/trial_log.csv` matches the previous run.

## Troubleshooting

- **Solver Timeout**: If many trials fail with `timeout=true`, consider reducing the complexity of the generated topologies or increasing the `solver_timeout` in `config.yaml` (if the CI window allows).
- **Latent Drift**: If `ood_flag` is frequently true, the GFM may not be robust to the generated topologies. This is a valid result and should be reported as a failure mode.
- **Missing GFM Weights**: Ensure `data/raw/gfm_weights.pth` exists. If not, the original GAM weights must be downloaded and placed there.