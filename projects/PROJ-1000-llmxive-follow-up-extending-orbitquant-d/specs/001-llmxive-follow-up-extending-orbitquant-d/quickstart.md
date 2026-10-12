# Quickstart: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

## Prerequisites
- Python 3.11 or newer  
- Git  
- (Optional) Kaggle API token for GPU off‑load (`kaggle.json` placed in `~/.kaggle/`)

## Setup

```bash
# 1. Clone the repo and checkout the feature branch
git clone <repo-url>
cd projects/PROJ-1000-llmxive-followup-extending-orbitquant-d
git checkout 001-llmxive-followup

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Initialize Data (writes only under `data/`)

```bash
# Download MS‑COCO parquet files and verify checksums
python code/data/download_coco.py
# Extract captions to a CSV of prompts
python code/data/preprocess.py
```

## Run the Full Research Pipeline

```bash
# Phase 0: Correlation study (CPU)
python code/main.py --phase correlation

# Phase 1: Generate rotation matrices (CPU)
python code/main.py --phase clustering

# Phase 2: Build router (CPU)
python code/main.py --phase router

# Phase 3: Evaluation (CPU for metrics, GPU escape for generation)
python code/main.py --phase evaluation
```

Each phase creates deterministic output files under `data/processed/` and plots under `figures/`. Logs are written to `data/processed/logs/`. The pipeline will automatically off‑load the generation steps to a Kaggle GPU if the selected DiT model cannot fit on the CI runner.

## Inspect Results

- Correlation plot: `figures/correlation_scatter.png`  
- Clustering report: `data/processed/clustering_report.json`  
- Rotation matrices: `data/processed/rotation_matrices/matrix_{i}.npy` and `metadata_{i}.json`  
- Evaluation table: `data/processed/results.csv`  

## Testing

```bash
# Unit tests (router logic, entropy calculation)
pytest tests/unit/

# Integration test (end‑to‑end on a tiny subset of prompts)
pytest tests/integration/
```

All test artifacts are written to `data/processed/` or `figures/`; no `state/` directory is touched.

---

