# Quickstart Guide: Non-Neural Approximation of VLA Priors

This guide provides step-by-step instructions to set up, run, and evaluate the non-neural approximation pipeline for Qwen-VLA priors.

## Prerequisites

- Python 3.9+
- pip (package manager)
- At least 14GB of free disk space for data artifacts
- CPU-only execution (no GPU required)

## 1. Environment Setup

### Clone and Navigate
```bash
git clone <repository-url>
cd PROJ-962-llmxive-follow-up-extending-qwen-vla-uni
```

### Install Dependencies
Install all required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```
*Note: This installs `datasets`, `scikit-learn`, `transformers`, `pybullet`, `pandas`, `numpy`, `scipy`, `pyyaml`, and `sklearn-mixture`.*

## 2. Pipeline Execution

The pipeline is executed sequentially through the following scripts located in `code/`.

### Step 1: Ingestion
Download and parse the Qwen-VLA/Hy-Embodied dataset.
```bash
python code/01_ingest.py
```
*Output:* `data/raw/` (raw dataset files)

### Step 2: Clustering
Extract kinematic features and cluster trajectories using K-means with validation.
```bash
python code/02_cluster.py
```
*Output:* `data/processed/clusters.json`, `data/processed/assignments.parquet`, `data/results/coverage_report.json`

### Step 3: Training (Embeddings & Models)
Generate BERT embeddings and train CGMM/Decision Tree models per cluster.
```bash
python code/03_train.py
```
*Output:* `data/processed/train_embeddings.parquet`, `artifacts/models/cgmm_*.pkl`, `artifacts/models/dt_*.pkl`, `artifacts/models/bert_encoder.pt`

### Step 4: Inference
Generate trajectories for new prompts using the trained models.
```bash
python code/04_inference.py
```
*Output:* `data/results/inference_benchmark.csv` (if benchmarking enabled)

### Step 5: Simulation
Execute generated trajectories in PyBullet and compare against baselines.
```bash
python code/05_simulate.py
```
*Output:* `data/results/simulation_logs.csv`

### Step 6: Evaluation
Perform statistical analysis (McNemar's Test, Paired T-Tests) and calculate fidelity.
```bash
python code/06_evaluate.py
```
*Output:* `data/results/fidelity_metrics.json`, `data/results/evaluation_report.md`

## 3. Verification

To verify the entire pipeline end-to-end:
```bash
python code/07_verify_coverage.py
```

## 4. Expected Artifacts

Ensure the following files exist after successful execution:
- `data/processed/clusters.json`
- `data/processed/train_embeddings.parquet`
- `artifacts/models/cgmm_*.pkl`
- `data/results/simulation_logs.csv`
- `data/results/evaluation_report.md`

## Troubleshooting

- **Dataset Download Fails**: Ensure internet connectivity. The script will fail loudly if the HuggingFace dataset cannot be accessed; do not attempt to use synthetic fallbacks.
- **Memory Errors**: The pipeline uses streaming for large datasets. If issues persist, reduce `k` in `code/utils/config.py`.
- **Simulation Crashes**: Check `data/results/simulation_logs.csv` for `KinematicConstraintViolation` entries.
