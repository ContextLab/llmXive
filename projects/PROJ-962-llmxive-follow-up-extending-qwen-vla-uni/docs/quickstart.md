# Quickstart Guide: Non-Neural VLA Approximation Pipeline

This guide provides instructions for running the full pipeline to approximate Qwen-VLA behavior using non-neural models (Decision Trees and Gaussian Mixture Models).

## Prerequisites

- Python 3.9+
- System RAM: ≥ 16GB (recommended) for full dataset processing
- Disk Space: ≥ 20GB for datasets and artifacts
- CPU-only execution is enforced (GPU detection will halt execution)

## Installation

1. Clone the repository and navigate to the project root.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

*Note: Ensure `requirements.txt` includes `datasets`, `transformers`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `psutil`, and `pyyaml`.*

## Configuration

Edit `code/utils/config.py` or use environment variables to customize:
- `CLUSTERING_K_INITIAL`: Initial number of clusters (default: 50)
- `SILHOUETTE_THRESHOLD`: Minimum silhouette score (default: 0.25)
- `K_REDUCTION_STEP`: Step size for k-reduction (default: 1)
- `R2_THRESHOLD`: Minimum R² for model selection (default: 0.6)
- `CONSTRUCT_VALIDITY_THRESHOLD`: Minimum R² for hypothesis validity (default: 0.1)

## Execution Instructions

Run the pipeline stages sequentially using the provided scripts. Each stage produces artifacts required by the next.

### Step 1: Ingestion and Clustering (US1)

Downloads the Qwen-VLA dataset, extracts kinematic features, normalizes them via streaming, and performs adaptive k-means clustering.

```bash
python code/01_ingest_cluster.py \
 --dataset "qwen-vla/Hy-Embodied" \
 --output-dir "data/processed" \
 --k-initial 50 \
 --silhouette-threshold 0.25 \
 --k-reduction-step 1 \
 --max-iterations 50 \
 --seed 42
```

**Outputs**:
- `data/processed/streaming_stats.json`
- `data/processed/clustering_state.json`
- `data/processed/clusters.json`
- `data/processed/assignments.parquet`
- `data/results/coverage_report.json`

### Step 2: Model Training (US2)

Generates BERT embeddings and trains sequential Decision Tree / GMM models per cluster.

```bash
python code/02_train_models.py \
 --assignments "data/processed/assignments.parquet" \
 --clusters "data/processed/clusters.json" \
 --output-dir "artifacts/models" \
 --bert-model "bert-base-uncased" \
 --r2-threshold 0.6 \
 --construct-validity-threshold 0.1 \
 --seed 42
```

**Outputs**:
- `data/processed/train_embeddings.parquet`
- `data/processed/embedding_verification.json`
- `artifacts/models/cluster_{id}_selected.pkl`
- `artifacts/models/cluster_{id}_selection.json`
- `data/results/model_selection_decision.md`
- `data/results/hypothesis_failure_report.md` (if validity check fails)

### Step 3: Inference (US2)

Runs inference on new prompts to generate trajectories.

```bash
python code/03_inference.py \
 --models-dir "artifacts/models" \
 --prompts-file "data/input/prompts.jsonl" \
 --output-file "data/results/inferred_trajectories.parquet" \
 --seed 42
```

### Step 4: Simulation and Evaluation (US3)

Executes trajectories in simulation, compares against baselines, and runs statistical tests.

```bash
python code/04_simulate_eval.py \
 --trajectories "data/results/inferred_trajectories.parquet" \
 --vla-baseline "data/processed/vla_proxy_baseline.parquet" \
 --random-seed 42 \
 --output-dir "data/results"
```

**Outputs**:
- `data/results/simulation_logs.csv`
- `data/results/fidelity_metrics.json`
- `data/results/fidelity_scores_per_sample.json`
- `data/results/memory_profile_e2e.json`
- `data/results/evaluation_report.md`

## Pipeline Validation

Run the end-to-end validation script to ensure all artifacts are generated correctly:

```bash
python code/09_run_final_validation.py \
 --config "code/utils/config.yaml"
```

## Troubleshooting

- **GPU Detected**: The pipeline enforces CPU-only execution. Set `CUDA_VISIBLE_DEVICES=""` or ensure no CUDA devices are available.
- **Data Fetch Errors**: If `datasets.load_dataset` fails, the script will raise `DataFetchError`. Verify network connectivity and dataset ID.
- **Clustering Degeneracy**: If silhouette score remains < 0.25, the loop reduces k until 1. Check `data/processed/clustering_state.json` for the final k.

## Output Artifacts Summary

| Artifact | Description |
|----------|-------------|
| `data/processed/clusters.json` | Cluster centers and metadata |
| `data/processed/assignments.parquet` | Sample-to-cluster mapping |
| `artifacts/models/` | Trained DT/GMM models per cluster |
| `data/results/evaluation_report.md` | Final report with p-values and metrics |
| `data/results/fidelity_scores_per_sample.json` | Continuous fidelity scores for t-tests |

For detailed methodology, see `research.md`.
