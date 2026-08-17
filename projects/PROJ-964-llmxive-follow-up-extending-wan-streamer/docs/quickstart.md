# Quickstart: llmXive Follow-up (Extending Wan-Streamer)

This guide provides the minimal steps to run the **llmXive** automated science pipeline for the "Extending Wan-Streamer" project (PROJ-964).
It assumes you have Python 3.9+ and a CPU-only environment (no CUDA required).

## 1. Environment Setup

Install the required dependencies:

```bash
cd PROJ-964-llmxive-follow-up-extending-wan-streamer
pip install -r code/requirements.txt
```

## 2. Project Initialization

Ensure the directory structure and configuration are in place:

```bash
python code/setup_project_structure.py
python code/setup_state_docs.py
```

## 3. Data Source Verification

The pipeline checks for existing Wan-Streamer logs or falls back to fetching the VoxCeleb2 dataset.

```bash
python code/data/validate_logs.py
```

* **Success**: Creates `data/raw/voxceleb2` (if fetched) or registers existing logs, updates `state.yaml` with checksums, and sets `data_source` in `code/config.py`.
* **Failure**: If neither source is found and fetch fails, the script exits with a clear error.

## 4. End-to-End Execution

Run the core pipeline stages sequentially. These tasks generate the data artifacts, train the estimator, and run the hybrid simulation.

### Step 4.1: Data Extraction & Preprocessing (US1)
```bash
# Extract latents from the configured data source
python code/data/extract_latents.py

# Calibrate thresholds for event detection
python code/tasks/calibrate_thresholds.py

# Power Analysis (fails loudly if no data)
python code/data/generate_power_analysis.py

# Preprocess and sample the dataset
python code/data/preprocess.py

# Validate sampling distribution
python code/data/validate_sampling.py
```

### Step 4.2: Estimator Training (US2)
```bash
# Train the GRU estimator (CPU-optimized)
python code/models/trainer.py

# Calibrate uncertainty scores
python code/metrics/uncertainty_calibration.py
```

### Step 4.3: Hybrid Simulation & Evaluation (US3)
```bash
# Generate counterfactual indices
python code/inference/generate_counterfactual_indices.py

# Run hybrid inference simulation
python code/inference/hybrid_sim.py

# Compute metrics (FID, MOS, Latency Bias, TOST)
python code/evaluation/metrics.py
python code/inference/analyze_latency_bias.py
python code/metrics/tost_equivalence.py
```

## 5. Verification

Check the final state of the project:

```bash
# Verify all artifacts exist and state.yaml is updated
python tests/unit/test_setup_verification.py
```

## 6. Data Flow Summary

1. **Raw Data**: `data/raw/` (Wan-Streamer logs or VoxCeleb2)
2. **Extracted**: `data/processed/raw_extract.parquet`
3. **Processed**: `data/processed/sampled_dataset.parquet`
4. **Model**: `data/models/estimator_checkpoint_final.pt`
5. **Simulation**: `data/processed/hybrid_output.parquet`
6. **Metrics**: `data/metrics/` (Power analysis, TOST, FID, etc.)
7. **State**: `state.yaml` tracks artifact hashes and pipeline status.

For detailed research methodology and statistical assumptions, see `docs/research.md`.
