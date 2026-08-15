# Quickstart: llmXive Follow-up (Wan-Streamer Extension)

This guide provides instructions to set up, run, and validate the llmXive automated science pipeline for the Wan-Streamer extension project.

## Prerequisites

- Python 3.9+
- pip
- 16GB+ RAM (for full dataset processing)
- Disk space: ~15GB for raw data, ~5GB for processed artifacts

## 1. Setup Environment

```bash
# Clone the project
git clone <repo-url>
cd projects/PROJ-964-llmxive-follow-up-extending-wan-streamer

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Project Structure Verification

Run the setup verification script to ensure all directories are created:

```bash
python code/setup_project_structure.py
pytest tests/unit/test_setup_verification.py
```

## 3. Data Preparation

### 3.1 Initialize Data Directories
```bash
python code/setup_data_directories.py
```

### 3.2 Validate Data Source
The pipeline checks for existing Wan-Streamer v0.1 logs. If missing, it fetches the canonical VoxCeleb2 dataset:
```bash
python code/data/validate_logs.py
```
- If `data/raw/wan-streamer-logs` exists: Uses existing logs
- If `data/raw/voxceleb2` exists: Uses cached VoxCeleb2
- If neither exists: Fetches VoxCeleb2 via HuggingFace datasets

### 3.3 Extract Latent Vectors
Parse logs and extract time-series latent vectors:
```bash
python code/data/extract_latents.py
```
**Output**: `data/processed/raw_latents.parquet`

### 3.4 Preprocess and Sample
Filter events, compute latent deltas, and perform stratified sampling:
```bash
python code/data/preprocess.py
```
**Output**: `data/processed/sampled_dataset.parquet` (≤ 1GB)

### 3.5 Validate Sampling
Verify distribution preservation:
```bash
python code/data/validate_sampling.py
```

## 4. Model Training (User Story 2)

### 4.1 Train GRU Estimator
```bash
python code/models/trainer.py
```
**Outputs**:
- `data/models/estimator_checkpoint_pending.pt` (pending validation)
- Memory usage monitored (≤ 7GB limit)

### 4.2 Uncertainty Calibration
Validate uncertainty correlation and finalize checkpoint:
```bash
python code/metrics/uncertainty_calibration.py
```
**Outputs**:
- `data/models/estimator_checkpoint_final.pt` (if correlation ≥ 0.7)
- Updates `state.yaml` with validation status

### 4.3 Baseline Comparison
Compare against zero-delta predictor:
```bash
python code/metrics/baseline_comparison.py
```
**Output**: `data/metrics/baseline_comparison.json`

## 5. Hybrid Inference Simulation (User Story 3)

### 5.1 Generate Counterfactual Indices
Create randomized subset for forced-skip intervention:
```bash
python code/inference/generate_counterfactual_indices.py
```
**Output**: `data/processed/counterfactual_indices.parquet`

### 5.2 Run Hybrid Simulation
Execute full hybrid inference pipeline:
```bash
python code/inference/hybrid_sim.py
```
**Output**: `data/processed/hybrid_output.parquet`

### 5.3 Analyze Latency Bias
Perform stratified bootstrap with propensity-score matching:
```bash
python code/inference/analyze_latency_bias.py
```
**Output**: `data/metrics/latency_bootstrap_results.csv`

### 5.4 Equivalence Testing
Run TOST tests for quality metrics:
```bash
python code/metrics/tost_equivalence.py
```
**Output**: `data/metrics/tost_results.csv`

### 5.5 Validate Proxy MOS
Check correlation with human ratings (if available):
```bash
python code/metrics/validate_proxy_mos.py
```

### 5.6 FID Stability Correlation
Calculate correlation between predicted delta magnitude and FID stability:
```bash
python code/metrics/fid_stability_corr.py
```

## 6. Validation & Testing

### 6.1 Run Contract Tests
```bash
pytest tests/contract/
```

### 6.2 Run Integration Tests
```bash
pytest tests/integration/
```

### 6.3 Run Unit Tests
```bash
pytest tests/unit/
```

## 7. State Management

After each major step, update the state file with artifact hashes:
```bash
python code/utils/update_state_yaml.py
```

## 8. Troubleshooting

### Memory Limit Exceeded
If training exceeds 7GB RAM, the system will attempt to reduce sample size:
```bash
python code/tasks/reduce_sample_size.py --target-size <MB>
```

### Missing Human Ratings
If `data/raw/human_ratings.json` is missing, the proxy MOS validation will log "Assumption Validated" and skip correlation testing.

### Power Limitation Errors
If minimum sample size is reached during reduction, the system will fail gracefully with "Power Limitation" error.

## 9. Next Steps

- Review `docs/research.md` for detailed methodology
- Check `state.yaml` for artifact validation status
- Run `pytest tests/` for full validation suite

## Support

For issues, check the project logs in `state/logs/` or consult the research documentation.
