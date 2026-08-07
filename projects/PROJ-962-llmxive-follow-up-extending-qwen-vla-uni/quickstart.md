# Quickstart Guide: Non-Neural VLA Approximation Pipeline

## Prerequisites

- **Python**: 3.9 or higher
- **System**: CPU-only environment (GPU detection will cause scripts to fail)
- **Dependencies**: Install via `pip install -r requirements.txt`
 - Key packages: `datasets`, `scikit-learn`, `transformers`, `pandas`, `numpy`, `scipy`, `pybullet`, `psutil`

## Directory Structure

Ensure the following structure exists (run `python code/setup_directories.py` if missing):

```
.
├── code/
│ ├── 01_ingest_cluster.py
│ ├── 02_train_models.py
│ ├── 03_inference.py
│ ├── 04_simulate_eval.py
│ └── utils/
├── data/
│ ├── raw/
│ ├── processed/
│ └── results/
├── artifacts/
│ └── models/
└── research.md
```

## Step-by-Step Execution

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize directory structure
python code/setup_directories.py
```

### 2. Data Ingestion & Clustering

Downloads the `Qwen/Qwen-VLA` dataset (streaming mode) and clusters action sequences.

```bash
python code/01_ingest_cluster.py \
 --seed 42 \
 --max-k 50 \
 --silhouette-threshold 0.25
```

**Expected Outputs**:
- `data/processed/clusters.json`
- `data/processed/assignments.parquet`
- `data/results/clustering_method_log.json`

### 3. Model Training (Sequential Selection)

Generates BERT embeddings and trains Decision Trees or CGMMs per cluster based on $R^2$ performance.

```bash
# Generate embeddings
python code/02_train_models.py --stage embeddings

# Train models with sequential fallback logic
python code/02_train_models.py --stage train
```

**Expected Outputs**:
- `data/processed/train_embeddings.parquet`
- `artifacts/models/cluster_{id}_selected.pkl`
- `data/results/model_selection_decision.md`

### 4. Inference

Generates trajectories for text prompts using the trained non-neural models.

```bash
python code/03_inference.py \
 --prompt "grasp the red cup" \
 --output data/results/inference_output.parquet
```

### 5. Simulation & Evaluation

Executes trajectories in PyBullet and runs paired t-tests against baselines.

```bash
python code/04_simulate_eval.py \
 --baseline all \
 --output data/results/evaluation_report.md
```

**Expected Outputs**:
- `data/results/simulation_logs.csv`
- `data/results/fidelity_metrics.json`
- `data/results/evaluation_report.md`

## Configuration

Configuration can be overridden via command-line arguments or `code/utils/config.py`:

- `--seed`: Global random seed (default: 42)
- `--max-k`: Max clusters (default: 50)
- `--silhouette-threshold`: Stop condition for k-reduction (default: 0.25)
- `--cpu-only`: Enforce CPU execution (default: True)

## Troubleshooting

- **"VLA Proxy Baseline artifact not found"**: Ensure `code/04_simulate_eval.py` has run successfully to generate the baseline, or verify `data/processed/vla_proxy_baseline.parquet` exists.
- **"GPU detected"**: The pipeline is CPU-only. If `torch.cuda.is_available()` is true, the script will raise a `RuntimeError`. Run with `CUDA_VISIBLE_DEVICES=""`.
- **Clustering Coverage < 98%**: The pipeline aborts. Check input data integrity and streaming logic in `code/01_ingest_cluster.py`.

## Verification

To validate the entire pipeline:

```bash
python code/validate_quickstart.py
```

This script checks for the existence of all required artifacts and logs the validation status to `data/results/e2e_run_log.txt`.