# Quick Start Guide: Non-Neural VLA Approximation Pipeline

## Overview
This project implements a CPU-only, non-neural approximation of Vision-Language-Action (VLA) priors. It ingests the Qwen-VLA dataset, clusters behavior into kinematic groups, fits lightweight probabilistic models (Decision Trees or GMMs), and evaluates performance against baselines using simulation and statistical tests.

## Prerequisites
- Python 3.9+
- CPU-only environment (GPU detection will cause the pipeline to abort per SC-003)
- ~14GB disk space for intermediate artifacts
- ~7GB RAM available during execution

## Installation

1. **Clone and Setup**
 ```bash
 git clone <repo-url>
 cd PROJ-962-llmxive-follow-up-extending-qwen-vla-uni
 ```

2. **Create Environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` includes pinned versions for reproducibility.*

## Execution Pipeline

The pipeline is executed in stages. Each stage produces artifacts consumed by the next.

### Step 1: Ingestion & Clustering (US1)
Downloads Qwen-VLA data, extracts kinematic features, and performs adaptive clustering.

```bash
python code/01_ingest_cluster.py --k_initial 50 --silhouette_threshold 0.25 --k_reduction_step 5
```

**Flags:**
- `--k_initial`: Initial number of clusters (default: 50).
- `--silhouette_threshold`: Minimum acceptable silhouette score (default: 0.25).
- `--k_reduction_step`: Step size for adaptive k-reduction (default: 5).

**Outputs:**
- `data/processed/clusters.json`: Cluster centers and metadata.
- `data/processed/assignments.parquet`: Sample-to-cluster assignments.
- `data/results/clustering_method_log.json`: Log of k-reduction steps and final method (K-means vs HAC).

### Step 2: Model Training (US2)
Generates BERT embeddings and trains Decision Trees or GMMs per cluster.

```bash
python code/02_train_models.py --r2_threshold 0.6 --inference_time_limit 2.0
```

**Flags:**
- `--r2_threshold`: Minimum R² required for model selection (default: 0.6).
- `--inference_time_limit`: Maximum allowed inference time in seconds (default: 2.0).

**Outputs:**
- `data/processed/train_embeddings.parquet`: Frozen BERT embeddings.
- `artifacts/models/cluster_{id}_selected.pkl`: Trained model for each cluster.
- `data/results/model_selection_decision.md`: Rationale for DT vs GMM selection per cluster.

### Step 3: Inference (US2)
Generates trajectories for new prompts.

```bash
python code/03_inference.py --prompt "pick up the red block" --output data/results/inference_sample.json
```

**Outputs:**
- `data/results/inference_sample.json`: Generated trajectory.

### Step 4: Simulation & Evaluation (US3)
Executes trajectories in PyBullet, compares against baselines, and runs statistical tests.

```bash
python code/04_simulate_eval.py --baseline vla_proxy --random_seed 42
```

**Outputs:**
- `data/results/simulation_logs.csv`: Success/collision metrics.
- `data/results/fidelity_metrics.json`: Trajectory fidelity scores.
- `data/results/evaluation_report.md`: Final report with p-values and complexity reduction factors.

## Verification

Run the full validation suite to ensure all artifacts are present and valid:

```bash
python code/09_run_final_validation.py
```

This script checks:
- Existence of all required data files.
- Integrity of clustering coverage (>98%).
- Validity of statistical test results.
- Absence of synthetic data fabrication.

## Troubleshooting

- **GPU Detected**: The pipeline enforces CPU-only execution. If `torch.cuda.is_available()` is True, the script will raise a `RuntimeError`. Ensure `CUDA_VISIBLE_DEVICES=""` is set if necessary.
- **Low Silhouette Score**: If the initial clustering score is < 0.25, the pipeline automatically reduces `k` and retries. If `k` reaches 1, it logs a "degenerate clustering" warning and proceeds.
- **Missing Baseline**: The VLA Proxy Baseline must be present at `data/processed/vla_proxy_baseline.parquet`. If missing, the simulation step will abort.

## License
This project is part of the llmXive research initiative.
