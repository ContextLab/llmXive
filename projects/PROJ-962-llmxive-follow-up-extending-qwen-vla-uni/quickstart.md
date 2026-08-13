# Quickstart Guide: Non-Neural VLA Approximation Pipeline

This guide provides instructions for executing the full research pipeline to approximate Qwen-VLA behaviors using non-neural models (Decision Trees and GMMs) on CPU-only hardware.

## Prerequisites

- Python 3.9+
- System with at least 8GB RAM (16GB recommended for full dataset processing)
- No GPU required (CPU-only enforcement is active)

## Installation

1. Clone the repository and navigate to the project root.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Directory Structure

The pipeline expects the following structure (created automatically by T001a):
- `code/`: Source scripts
- `data/raw/`: Raw downloaded data
- `data/processed/`: Intermediate artifacts (embeddings, clusters)
- `data/results/`: Final reports and logs
- `artifacts/models/`: Trained model pickles

## Execution Instructions

Run the pipeline stages sequentially. Each stage produces artifacts required by the next.

### Step 1: Ingestion and Clustering (User Story 1)

Downloads the Qwen-VLA dataset, extracts kinematic features, and performs adaptive clustering.

```bash
python code/01_ingest_cluster.py \
 --dataset "Qwen/Qwen-VLA" \
 --split "train" \
 --k_initial 50 \
 --silhouette_threshold 0.25 \
 --k_step 5 \
 --output_dir data/processed \
 --streaming
```

**Flags:**
- `--dataset`: HuggingFace dataset ID (default: "Qwen/Qwen-VLA")
- `--split`: Dataset split (default: "train")
- `--k_initial`: Initial number of clusters (default: 50)
- `--silhouette_threshold`: Minimum acceptable silhouette score (default: 0.25)
- `--k_step`: Step size for k-reduction loop (default: 5)
- `--output_dir`: Directory for artifacts (default: "data/processed")
- `--streaming`: Enable streaming mode for large datasets

**Outputs:**
- `data/processed/clusters.json`: Cluster centers and metadata
- `data/processed/assignments.parquet`: Sample-to-cluster mapping
- `data/results/clustering_method_log.json`: Method selection and metrics

### Step 2: Model Training (User Story 2)

Generates BERT embeddings and trains Decision Trees or GMMs per cluster.

```bash
python code/02_train_models.py \
 --embeddings_path data/processed/train_embeddings.parquet \
 --clusters_path data/processed/clusters.json \
 --assignments_path data/processed/assignments.parquet \
 --model_dir artifacts/models \
 --r2_threshold 0.6 \
 --cpu_only
```

**Flags:**
- `--embeddings_path`: Path to pre-computed BERT embeddings
- `--clusters_path`: Path to cluster metadata
- `--assignments_path`: Path to cluster assignments
- `--model_dir`: Output directory for trained models
- `--r2_threshold`: Minimum R² for model acceptance (default: 0.6)
- `--cpu_only`: Force CPU execution (enforced by default)

**Outputs:**
- `artifacts/models/cluster_{id}_selected.pkl`: Trained model per cluster
- `artifacts/models/cluster_{id}_selection.json`: Selection rationale (DT vs GMM)
- `data/results/model_selection_decision.md`: Aggregate selection report

### Step 3: Inference (User Story 2)

Generates trajectories for new prompts using the trained non-neural models.

```bash
python code/03_inference.py \
 --prompt "grasp the red block" \
 --model_dir artifacts/models \
 --clusters_path data/processed/clusters.json \
 --output_path data/results/inference_trajectory.json
```

**Flags:**
- `--prompt`: Text instruction for trajectory generation
- `--model_dir`: Path to trained models
- `--clusters_path`: Path to cluster metadata
- `--output_path`: Output file for generated trajectory

**Outputs:**
- `data/results/inference_trajectory.json`: Generated action sequence

### Step 4: Simulation and Evaluation (User Story 3)

Executes trajectories in PyBullet and compares against baselines.

```bash
python code/04_simulate_eval.py \
 --baseline_path data/processed/vla_proxy_baseline.parquet \
 --inference_results data/results/inference_trajectory.json \
 --output_csv data/results/simulation_logs.csv \
 --tasks grasp,navigate,place \
 --seed 42
```

**Flags:**
- `--baseline_path`: Path to VLA Proxy baseline artifact
- `--inference_results`: Path to non-neural inference results
- `--output_csv`: Output CSV for simulation logs
- `--tasks`: Comma-separated list of task types to evaluate
- `--seed`: Random seed for reproducibility

**Outputs:**
- `data/results/simulation_logs.csv`: Simulation outcomes
- `data/results/fidelity_metrics.json`: Trajectory fidelity scores
- `data/results/evaluation_report.md`: Final statistical report

## Verification

To verify the pipeline execution:

```bash
python code/validate_quickstart.py
```

This script checks for the presence of all expected artifacts and validates data integrity.

## Troubleshooting

- **Memory Errors**: Ensure `--streaming` is used in Step 1. Reduce `--k_initial` if necessary.
- **GPU Detected**: The pipeline enforces CPU-only. If you see a GPU error, ensure `torch.cuda.is_available()` returns False or remove GPU drivers.
- **Data Fetch Failures**: Ensure network connectivity to HuggingFace. The pipeline will fail loudly if data cannot be fetched.

## Research Notes

For detailed methodology, see `research.md`.
