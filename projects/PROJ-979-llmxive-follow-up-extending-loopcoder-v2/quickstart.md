# Quickstart Guide: llmXive Follow-up - Extending LoopCoder-v2

This guide provides instructions for running the entropy-convergence analysis pipeline in two modes:
1. **CPU Validation Mode (N=50)**: A lightweight run for verifying pipeline correctness and reproducibility.
2. **Full GPU Analysis**: The complete analysis on the full dataset for production results.

## Prerequisites

- Python 3.10+
- CUDA-capable GPU (for Full GPU Mode)
- Hugging Face `transformers` and `datasets` libraries
- Docker (for code execution sandbox)

## Setup

1. **Clone and Install Dependencies**
 ```bash
 cd projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2
 pip install -r code/requirements.txt
 ```

2. **Configure Environment**
 Ensure `code/config.yaml` exists with valid paths for the model.
 Set environment variables if not using defaults:
 ```bash
 export CODELLAMA_CPU_PATH="path/to/cpu/model"
 export CODELLAMA_GPU_PATH="path/to/gpu/model"
 ```

3. **Prepare Data**
 Run the data preparation pipeline to generate splits and unseen validation sets:
 ```bash
 python code/src/data_loader.py
 ```
 This creates:
 - `data/processed/filtered_splits.json`
 - `data/processed/unseen_validation_set.csv`
 - `data/processed/strata_log.json`

---

## Mode 1: CPU Validation Mode (N=50)

Use this mode to validate the pipeline logic, ensure reproducibility, and verify artifact generation without heavy compute costs.

### Step 1: Run Entropy Extraction (Sample)
```bash
python code/src/entropy.py --input data/processed/filtered_splits.json --output data/processed/entropy_results.csv --sample-size 50
```
- **Output**: `data/processed/entropy_results.csv`
- **Expected**: 50 rows with `task_id` and `entropy` values.

### Step 2: Run Convergence Inference (Sample)
```bash
python code/src/inference.py --input data/processed/filtered_splits.json --output data/processed/convergence_results_core.csv --k_range [1,2,3] --sample-size 50
```
- **Output**: `data/processed/convergence_results_core.csv`
- **Expected**: 150 rows (50 tasks × 3 k-values) with convergence metrics.

### Step 3: Run Analysis & Router Simulation
```bash
python code/src/analysis.py --entropy data/processed/entropy_results.csv --convergence data/processed/convergence_results_core.csv --output data/processed/router_simulation.csv
```
- **Output**: `data/processed/router_simulation.csv` and `data/processed/correlation_results.json`

### Step 4: Verify Metrics
Run the resource monitor to capture lightweight metrics:
```bash
python code/src/utils.py --mode validation --output data/processed/resource_metrics.json
```

**Validation Check**:
- All output files exist in `data/processed/`.
- `data/processed/correlation_results.json` contains a valid Spearman rho and p-value.
- Exit codes for all commands are 0.

---

## Mode 2: Full GPU Analysis

Use this mode for the complete study with the full dataset to generate final research results.

### Step 1: Run Full Entropy Extraction
```bash
python code/src/entropy.py --input data/processed/filtered_splits.json --output data/processed/entropy_results.csv
```
- **Output**: `data/processed/entropy_results.csv` (Full dataset)

### Step 2: Run Full Convergence Inference
```bash
python code/src/inference.py --input data/processed/filtered_splits.json --output data/processed/convergence_results_core.csv --k_range [1,2,3]
```
- **Output**: `data/processed/convergence_results_core.csv`

### Step 3: Run Sensitivity Analysis (k=4)
```bash
python code/src/inference.py --input data/processed/filtered_splits.json --output data/processed/convergence_results_sensitivity.csv --k_range [4]
```
- **Output**: `data/processed/convergence_results_sensitivity.csv`

### Step 4: Run Full Analysis Pipeline
```bash
python code/src/analysis.py --entropy data/processed/entropy_results.csv --convergence data/processed/convergence_results_core.csv --output data/processed/router_simulation.csv
```
- **Output**: `data/processed/correlation_results.json`, `data/processed/router_metrics.json`

### Step 5: Run Robustness & Survival Analysis
```bash
python code/src/survival.py --input-entropy data/processed/entropy_results.csv --input-convergence data/processed/convergence_results_core.csv --output data/processed/correlation_results.json
```
```bash
python code/src/robustness.py --output data/processed/robustness_summary.json
```

### Step 6: Capture Full Analysis Metrics (SC-005)
```bash
python code/src/sc005_runner.py --mode gpu --output data/processed/sc005_metrics.json
```
- **Output**: `data/processed/sc005_metrics.json` containing runtime, GPU utilization, and memory usage.

### Step 7: Final Feasibility Report
```bash
python code/src/aggregation.py --output data/processed/sc005_final_report.json
```

**Final Deliverables**:
- `data/processed/entropy_results.csv`
- `data/processed/convergence_results_core.csv`
- `data/processed/correlation_results.json`
- `data/processed/robustness_summary.json`
- `data/processed/sc005_final_report.json`

---

## Troubleshooting

- **Model Not Found**: Ensure `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH` points to a valid local directory or that you are logged into Hugging Face (`huggingface-cli login`).
- **Docker Errors**: Ensure the Docker daemon is running and the `entropy-sandbox` image is built (`docker build -f code/Dockerfile.unseen -t entropy-sandbox:latest.`).
- **Memory Errors**: Reduce `--sample-size` in CPU mode or ensure sufficient GPU memory for Full Mode.