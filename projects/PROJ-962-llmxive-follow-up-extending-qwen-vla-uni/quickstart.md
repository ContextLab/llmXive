# Quickstart Guide: Non-Neural VLA Approximation Pipeline

This guide provides instructions for executing the full research pipeline, from dataset ingestion to simulation evaluation.

## Prerequisites

- Python 3.9+
- Dependencies listed in `requirements.txt`
- Access to HuggingFace Hub (for Qwen-VLA dataset)

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Pipeline Execution

The pipeline consists of four main stages. You can run them individually or execute the full pipeline using the main runner script.

### Option 1: Run Full Pipeline (Recommended)

The `code/09_run_final_validation.py` script orchestrates the entire flow:

```bash
python code/09_run_final_validation.py
```

This script performs:
- Ingestion & Clustering (US1)
- Model Training (US2)
- Inference (US2)
- Simulation & Evaluation (US3)
- Final Report Generation

### Option 2: Run Stages Individually

If you need to debug a specific stage, run the scripts directly:

#### Stage 1: Ingestion & Clustering (US1)

```bash
python code/01_ingest_cluster.py
```

**Arguments:**
- `--k-init`: Initial number of clusters (default: 50)
- `--silhouette-threshold`: Minimum silhouette score to stop reduction (default: 0.25)
- `--k-step`: Step size for k-reduction (default: 5)
- `--output-dir`: Output directory for artifacts (default: `data/processed`)

**Outputs:**
- `data/processed/clusters.json`
- `data/processed/assignments.parquet`
- `data/results/clustering_method_log.json`

#### Stage 2: Model Training (US2)

```bash
python code/02_train_models.py
```

**Arguments:**
- `--cluster-dir`: Directory containing clustering artifacts (default: `data/processed`)
- `--model-dir`: Output directory for trained models (default: `artifacts/models`)
- `--r2-threshold`: Minimum R² for model acceptance (default: 0.6)
- `--max-inference-time`: Max inference time in seconds (default: 2.0)

**Outputs:**
- `data/processed/train_embeddings.parquet`
- `artifacts/models/cluster_{id}_selected.pkl`
- `artifacts/models/cluster_{id}_selection.json`
- `data/results/model_selection_decision.md`

#### Stage 3: Inference (US2)

```bash
python code/03_inference.py
```

**Arguments:**
- `--prompt`: Text prompt to generate trajectory for
- `--model-dir`: Directory containing trained models (default: `artifacts/models`)
- `--cluster-dir`: Directory containing clustering artifacts (default: `data/processed`)
- `--output`: Output file for generated trajectory (default: `data/results/inference_trajectory.json`)

**Outputs:**
- `data/results/inference_trajectory.json`

#### Stage 4: Simulation & Evaluation (US3)

```bash
python code/04_simulate_eval.py
```

**Arguments:**
- `--baseline-dir`: Directory containing VLA proxy baseline (default: `data/processed`)
- `--model-dir`: Directory containing trained models (default: `artifacts/models`)
- `--output-dir`: Output directory for simulation results (default: `data/results`)
- `--num-prompts`: Number of prompts to evaluate (default: 100)

**Outputs:**
- `data/results/simulation_logs.csv`
- `data/results/fidelity_metrics.json`
- `data/results/evaluation_report.md`
- `data/results/memory_profile.json`

## Verification

To verify the pipeline execution and check for artifacts:

```bash
python code/validate_quickstart.py
```

This script checks:
- Existence of all required output files
- Validity of clustering assignments
- Presence of trained models
- Simulation log integrity

## Troubleshooting

### Data Fetch Errors
If the dataset download fails, the script will raise a `DataFetchError`. Ensure you have a stable internet connection and valid HuggingFace credentials.

### CPU-Only Enforcement
The pipeline enforces CPU-only execution. If a GPU is detected, the script will raise a `RuntimeError`. Set `CUDA_VISIBLE_DEVICES=""` to force CPU mode if necessary.

### Clustering Degeneracy
If the silhouette score remains below the threshold even at k=1, the pipeline will log a "degenerate clustering" warning and proceed with k=1. This is expected for certain dataset distributions.

## License

This project is part of the llmXive research initiative. See the repository LICENSE file for details.
