# Quickstart Guide: Non-Neural Approximation of VLA Priors

## Overview

This project implements a CPU-only pipeline to approximate Qwen-VLA behavior using non-neural models (Decision Trees and Gaussian Mixture Models). The pipeline ingests trajectory data, clusters behaviors, trains lightweight models, and evaluates them against baselines using statistical tests.

## Prerequisites

- Python 3.9+
- System RAM: ≥ 16GB recommended (7GB minimum for full pipeline)
- Disk Space: ≥ 20GB for datasets and artifacts

## Installation

1. Clone the repository and navigate to the project root.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Pipeline Execution

The pipeline consists of four main stages. Run them sequentially or use the end-to-end script.

### Step 1: Ingestion and Clustering (User Story 1)

Downloads the Qwen-VLA dataset, extracts kinematic features, normalizes them, and performs adaptive K-means clustering.

```bash
python code/01_ingest_cluster.py \
 --dataset qwen-vla/Hy-Embodied \
 --output-dir data/processed \
 --silhouette-threshold 0.25 \
 --k-reduction-step 1 \
 --max-iterations 50
```

**Outputs**:
- `data/processed/streaming_stats.json` (Global mean/std for normalization)
- `data/processed/clustering_state.json` (Final k, silhouette score)
- `data/processed/clusters.json` (Cluster centers)
- `data/processed/assignments.parquet` (Cluster assignments per sample)
- `data/results/coverage_report.json` (Clustering coverage metric)

**Note**: This step uses streaming to handle large datasets. It will fail loudly if the dataset cannot be downloaded.

### Step 2: Model Training (User Story 2)

Generates BERT embeddings, validates construct validity, and trains Decision Trees or GMMs per cluster.

```bash
python code/02_train_models.py \
 --embeddings data/processed/train_embeddings.parquet \
 --assignments data/processed/assignments.parquet \
 --clusters data/processed/clusters.json \
 --output-dir artifacts/models \
 --r2-threshold 0.6 \
 --inference-time-threshold 2.0
```

**Outputs**:
- `data/processed/train_embeddings.parquet` (BERT embeddings)
- `artifacts/models/cluster_{id}_selected.pkl` (Selected model per cluster)
- `artifacts/models/cluster_{id}_selection.json` (Selection criteria)
- `data/results/model_selection_decision.md` (Rationale for DT vs GMM)
- `data/results/hypothesis_failure_report.md` (If R² < 0.1)

**Constraint**: This script enforces CPU-only execution. It will exit with an error if a GPU is detected.

### Step 3: Inference and Simulation (User Story 3)

Runs the non-neural models, random baselines, and VLA proxy baselines in simulation, then performs paired t-tests.

```bash
python code/04_simulate_eval.py \
 --models-dir artifacts/models \
 --baseline data/processed/vla_proxy_baseline.parquet \
 --output-dir data/results \
 --seed 42
```

**Outputs**:
- `data/results/simulation_logs.csv` (Success/collision metrics)
- `data/results/fidelity_scores_per_sample.json` (Continuous fidelity scores)
- `data/results/statistical_test_results.json` (Paired t-test p-values)
- `data/results/memory_profile_e2e.json` (Peak RAM usage)

**Note**: Requires the VLA Proxy baseline to be present at the specified path.

### Step 4: Final Report Generation

Aggregates all results into a comprehensive evaluation report.

```bash
python code/08_generate_report.py \
 --results-dir data/results \
 --models-dir artifacts/models \
 --output data/results/evaluation_report.md
```

**Output**:
- `data/results/evaluation_report.md` (Final report with p-values, fidelity, complexity reduction)

## End-to-End Validation

To run the entire pipeline from ingestion to final report:

```bash
python code/09_run_final_validation.py \
 --dataset qwen-vla/Hy-Embodied \
 --baseline data/processed/vla_proxy_baseline.parquet \
 --output-dir data/results
```

This script verifies all artifacts are generated correctly and logs the full execution to `data/results/final_validation.log`.

## Configuration

Configuration parameters can be set via command-line arguments or by editing `code/utils/config.yaml`.

Key parameters:
- `SILHOUETTE_THRESHOLD`: Minimum silhouette score for clustering (default: 0.25)
- `K_REDUCTION_STEP`: Step size for k-reduction loop (default: 1)
- `R2_THRESHOLD`: Minimum R² for model acceptance (default: 0.6)
- `INFERENCE_TIME_THRESHOLD`: Maximum inference time per prompt (default: 2.0s)

## Troubleshooting

- **Data Fetch Error**: Ensure internet connectivity and that the HuggingFace dataset is accessible. The script will not use synthetic fallbacks.
- **GPU Detected**: The training script enforces CPU-only mode. Set `CUDA_VISIBLE_DEVICES=""` if needed.
- **Clustering Degeneracy**: If the silhouette score remains below threshold, the pipeline logs a warning and proceeds with k=1.

## Research Handoff

For detailed methodology, model selection rationale, and CPU-specific limitations, see `research.md` and `data/results/research_handoff.md`.
