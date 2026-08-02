# Quick Start Guide: Non-Neural Approximation of VLA Priors

This guide provides instructions for setting up the environment, running the pipeline, and generating results for the **llmXive** project (PROJ-962).

## Prerequisites

- Python 3.9+
- pip
- Sufficient disk space (~10GB for datasets and models)
- CPU-only environment (no GPU required)

## 1. Installation

Clone the repository and install dependencies:

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

The `requirements.txt` includes:
- `datasets`: For streaming HuggingFace datasets
- `scikit-learn`, `sklearn-mixture`: For clustering and GMM
- `transformers`: For BERT embeddings
- `pandas`, `numpy`, `scipy`: Data processing
- `pybullet`: Simulation engine
- `pyyaml`: Configuration management

## 2. Directory Structure

The project uses the following structure (created automatically by `T001a`):

```
.
├── code/
│ ├── 01_ingest.py
│ ├── 02_cluster.py
│ ├── 03_train.py
│ ├── 04_inference.py
│ ├── 05_simulate.py
│ ├── 06_evaluate.py
│ ├── utils/
│ └── tests/
├── data/
│ ├── raw/ # Downloaded raw datasets
│ ├── processed/ # Intermediate artifacts (embeddings, clusters)
│ └── results/ # Final simulation logs and reports
├── artifacts/
│ └── models/ # Trained CGMM and BERT models
├── specs/ # Design documents
└── docs/ # Documentation
```

## 3. Configuration

Edit `code/utils/config.py` or provide a `config.yaml` to adjust:
- Dataset paths
- Clustering parameters (silhouette threshold, k-decrement)
- Simulation parameters (joint limits, task types)

## 4. Running the Pipeline

Execute the pipeline in sequential order. Each script reads from the previous step's outputs.

### Step 1: Data Ingestion (User Story 1)
Downloads the Qwen-VLA/Hy-Embodied dataset and extracts text-action pairs.
```bash
python code/01_ingest.py
```
*Output*: `data/processed/ingested_data.parquet`

### Step 2: Clustering (User Story 1)
Extracts kinematic features and clusters actions into behavioral groups.
```bash
python code/02_cluster.py
```
*Output*: `data/processed/clusters.json`, `data/processed/assignments.parquet`

### Step 3: Model Training (User Story 2)
Generates BERT embeddings and trains Conditional Gaussian Mixture Models (CGMM).
```bash
python code/03_train.py
```
*Output*: `artifacts/models/` (CGMMs and BERT encoder)

### Step 4: Inference (User Story 2)
Generates trajectories for new prompts using the trained models.
```bash
python code/04_inference.py
```
*Output*: `data/processed/inferred_trajectories.parquet`

### Step 5: Simulation (User Story 3)
Executes trajectories in PyBullet and compares against baselines.
```bash
python code/05_simulate.py
```
*Output*: `data/results/simulation_logs.csv`

### Step 6: Evaluation (User Story 3)
Performs McNemar's Test and calculates fidelity metrics.
```bash
python code/06_evaluate.py
```
*Output*: `data/results/evaluation_report.md`

## 5. Verification

To verify the pipeline end-to-end:
```bash
# Run all tests
python -m pytest code/tests/ -v

# Check clustering coverage (T018)
python code/07_verify_coverage.py
```

## 6. Troubleshooting

- **Dataset Download Fails**: Ensure network access to HuggingFace. The script will fail loudly if data is missing (no synthetic fallback).
- **Memory Errors**: The ingestion script uses `streaming=True` to handle large datasets. Ensure at least 7GB RAM is available.
- **Clustering Quality**: If silhouette scores are low, check `config.yaml` for clustering parameters (T016).

## 7. Methodology Notes

See `docs/research.md` for detailed methodology on:
- **Conditional Gaussian Mixture Models (CGMM)**: The primary non-neural model.
- **McNemar's Test**: The statistical method for binary success rate comparison.
- **Kinematic Feature Extraction**: Velocity, acceleration, and joint angle normalization.
