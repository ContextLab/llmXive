# Quickstart: llmXive follow-up: extending "Wan-Streamer v0.1"

## Prerequisites

*   Python 3.11+
*   GB+ RAM (Free Tier CI compatible)
*   Access to HuggingFace (for VoxCeleb2) or local Wan-Streamer logs.

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-964-llmxive-follow-up-extending-wan-streamer
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Datasets**:
    Ensure you have access to the data source.
    *   **Option A (Local Logs)**: Place Wan-Streamer v0.1 logs in `data/raw/`. **If these are missing, the system will exit with "Data Unavailable" (FR-022).**
    *   **Option B (Proxy)**: The system can use VoxCeleb2 for turn-taking labels *only if* the Wan-Streamer logs are present to provide latent trajectories.

## Execution Workflow

The pipeline is executed sequentially via the `code/tasks/` modules.

### Step 1: Data Extraction
Extracts turn-taking events and latent deltas.
```bash
python code/tasks/extract_data.py --output data/processed/turn_events.parquet
```
*   *Output*: `turn_events.parquet` (sampled, ≤1 GB).
*   *Validation*: Checks for a substantial number of interruption/pause events. Handles "Data Unavailable" (FR-022).

### Step 2: Validate Sampling Distribution
Verifies that stratified sampling preserves the distribution of turn-taking events (FR-015).
```bash
python code/tasks/validate_sampling_distribution.py --input data/processed/turn_events.parquet
```

### Step 3: Estimator Training
Trains the lightweight RNN/Transformer.
```bash
python code/tasks/train_estimator.py \
  --input data/processed/turn_events.parquet \
  --output data/processed/estimator_checkpoint.pt \
  --max-ram [appropriate system limit]
```
*   *Output*: `estimator_checkpoint.pt`.
*   *Monitoring*: Logs RAM usage and training time. Handles "Power Limitation" (FR-023).

### Step 4: Hybrid Inference Simulation
Runs the simulation with randomized counterfactuals.
```bash
python code/tasks/simulate_inference.py \
  --estimator data/processed/estimator_checkpoint.pt \
  --input data/processed/turn_events.parquet \
  --output data/processed/hybrid_metrics.parquet
```
*   *Output*: `hybrid_metrics.parquet` (includes FID, latency, skip decisions).

### Step 5: Execute Fallback (Counterfactual Re-run)
For the randomized subset, re-runs the full solver to generate ground truth (FR-009, FR-017).
```bash
python code/tasks/execute_fallback.py \
  --input data/processed/hybrid_metrics.parquet \
  --output data/processed/counterfactual_full.parquet
```

### Step 6: Calculate FID Stability Correlation
Calculates the correlation between predicted delta and observed FID degradation (FR-011).
```bash
python code/tasks/calculate_fid_stability_corr.py \
  --input data/processed/counterfactual_full.parquet \
  --output data/processed/fid_stability_corr.yaml
```

### Step 7: Statistical Analysis
Performs TOST, propensity-score matching, and correlation checks.
```bash
python code/tasks/analyze_latency_bias.py \
  --input data/processed/counterfactual_full.parquet \
  --output results/statistical_report.yaml
```
*   *Output*: `statistical_report.yaml` (contains p-values, correlation coefficients).

### Step 8: Validate Proxy MOS
Validates proxy MOS or logs "Assumption Validated" (FR-013, FR-024).
```bash
python code/tasks/validate_proxy_mos.py \
  --input data/processed/hybrid_metrics.parquet \
  --output results/mos_validation.yaml
```

### Step 9: Update State
Updates the project state with artifact hashes (FR-020).
```bash
python code/tasks/update_state_yaml.py
```

## Verification

Run the contract tests to ensure data integrity:
```bash
pytest tests/contract/ -v
```
This validates that `turn_events.parquet` matches `contracts/dataset.schema.yaml` and that `statistical_report.yaml` matches `contracts/metrics.schema.yaml`. **Note**: Ensure `contracts/dataset.schema.yaml`, `contracts/estimator_output.schema.yaml`, and `contracts/metrics.schema.yaml` are the only active schemas (FR-021).

## Troubleshooting

*   **"Power Limitation" Error**: If training exceeds a predetermined duration threshold, the script will automatically reduce the sample size. If it fails at the minimum size, check `code/config.py` for `MIN_SAMPLE_SIZE`.
*   **"Data Unavailable" Error**: If local logs are missing, the system exits gracefully. **No fallback to re-generation is attempted.**
*   **"No Human Data" Log**: If `validate_proxy_mos` logs "Assumption Validated (No Human Data Available)", this is expected if the MOS dataset does not contain human ratings for this specific domain.
*   **Schema Mismatch**: Ensure `data/processed/` files are not manually edited. Re-run `extract_data.py` if corruption is suspected.