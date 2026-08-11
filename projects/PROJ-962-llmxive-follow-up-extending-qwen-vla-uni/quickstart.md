# llmXive Quickstart Guide

## Overview
This guide provides step-by-step instructions to execute the full Non-Neural VLA Approximation pipeline, from dataset ingestion to final evaluation report generation.

## Prerequisites
- Python 3.9+
- pip installed
- Sufficient disk space (~15GB for data and artifacts)
- CPU-only environment (GPU detection will cause the pipeline to fail as per SC-003)

## Installation

1. **Clone and Setup**
 ```bash
 git clone <repository-url>
 cd llmXive-project
 ```

2. **Install Dependencies**
 ```bash
 pip install -r requirements.txt
 ```

3. **Create Directory Structure**
 Run the setup script to create required directories:
 ```bash
 python code/setup_directories.py
 ```

## Execution Pipeline

The pipeline consists of the following stages. Execute them in order.

### 1. Dataset Ingestion and Clustering (User Story 1)
Downloads the Qwen-VLA dataset, extracts kinematic features, and performs adaptive K-means clustering.

```bash
python code/01_ingest_cluster.py \
 --dataset "Qwen/Qwen-VLA" \
 --output-dir data/processed \
 --max-clusters 50 \
 --silhouette-threshold 0.25
```

**Output Artifacts:**
- `data/processed/clusters.json`
- `data/processed/assignments.parquet`
- `data/results/clustering_method_log.json`

### 2. Embedding Generation and Model Training (User Story 2)
Generates BERT embeddings for text instructions and trains lightweight models (Decision Tree or GMM) per cluster.

```bash
python code/02_train_models.py \
 --input-dir data/processed \
 --output-dir artifacts/models \
 --bert-model "bert-base-uncased" \
 --r2-threshold 0.6
```

**Output Artifacts:**
- `data/processed/train_embeddings.parquet`
- `artifacts/models/cluster_{id}_selected.pkl`
- `data/results/model_selection_decision.md`

### 3. VLA Proxy Baseline Generation (User Story 3)
Generates the VLA Proxy baseline from ground-truth data for comparison.

```bash
python code/04_simulate_eval.py \
 --mode generate_baseline \
 --input-dir data/processed \
 --output data/processed/vla_proxy_baseline.parquet
```

**Output Artifacts:**
- `data/processed/vla_proxy_baseline.parquet`

### 4. Simulation and Evaluation (User Story 3)
Executes simulated trajectories, compares against baselines, and runs statistical tests.

```bash
python code/04_simulate_eval.py \
 --mode evaluate \
 --input-dir data/processed \
 --models-dir artifacts/models \
 --baseline data/processed/vla_proxy_baseline.parquet \
 --output-dir data/results
```

**Output Artifacts:**
- `data/results/simulation_logs.csv`
- `data/results/fidelity_metrics.json`
- `data/results/evaluation_report.md`

## Command-Line Flags Reference

| Flag | Description | Default |
|------|-------------|---------|
| `--dataset` | HuggingFace dataset ID | `Qwen/Qwen-VLA` |
| `--output-dir` | Output directory for processed data | `data/processed` |
| `--max-clusters` | Maximum number of clusters (k) | `50` |
| `--silhouette-threshold` | Minimum silhouette score for clustering | `0.25` |
| `--bert-model` | Pretrained BERT model name | `bert-base-uncased` |
| `--r2-threshold` | Minimum R² score for model selection | `0.6` |
| `--mode` | Execution mode (generate_baseline, evaluate) | `evaluate` |
| `--models-dir` | Directory containing trained models | `artifacts/models` |
| `--baseline` | Path to VLA Proxy baseline file | `data/processed/vla_proxy_baseline.parquet` |

## Verification

To verify the pipeline execution and artifact integrity:

```bash
python code/validate_quickstart.py \
 --log-path data/results/e2e_run_log.txt
```

This script validates that all required output files exist and contain valid data.

## Troubleshooting

- **Memory Errors**: Ensure you have at least 7GB of RAM available. Use `--streaming` flag if available.
- **Clustering Failure**: If silhouette score remains low, check data normalization or reduce `--max-clusters`.
- **Model Selection Failure**: If no model meets R² threshold, lower `--r2-threshold` or check data quality.
- **GPU Detected**: The pipeline enforces CPU-only execution. If a GPU is detected, the script will raise a `RuntimeError`.

## Next Steps
After successful execution, review `data/results/evaluation_report.md` for detailed performance metrics and statistical analysis.
