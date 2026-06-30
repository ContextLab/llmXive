# Quickstart: Assessing Reproducibility of Machine‑Learned Reaction Yield Models

## 1. Prerequisites
- **Python**: 3.11+
- **Docker**: Installed and running (required for reproducible environment).
- **Git**: Installed.
- **Hardware**: 2 CPU cores, 7GB RAM (minimum for CI runner).

## 2. Installation

### Step 1: Clone and Setup
```bash
git clone
cd PROJ-761-assessing-reproducibility
```

### Step 2: Build the Docker Environment
The project requires a specific CPU-only environment to ensure reproducibility.
```bash
docker build -t repro-yield-audit:latest.
```
*Note: This Dockerfile pins Python 3.11, PyTorch 2.2 (CPU), scikit-learn 1.5, and RDKit.*

### Step 3: Install Dependencies (Local Development)
If running locally without Docker:
```bash
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

## 3. Running the Pipeline

### Option A: Run in Docker (Recommended)
Execute the full pipeline inside the container:
```bash
docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/artifacts:/app/artifacts repro-yield-audit:latest python code/main.py
```

### Option B: Run Locally
```bash
python code/main.py
```

## 4. Input Configuration
Edit `data/manifest.yaml` to add target papers. Example:
```yaml
- doi: ""
 repo_url: ""
 dataset_name: "USPTO-Extract"
 dataset_version: "v1.0"
 reported_metrics:
 mae: 0.15
 r2: 0.85
 spearman_rho: 0.75
 hyperparameters:
 n_estimators: 100
 max_depth: 10
 seed: 42
```

## 5. Output
After completion, check `artifacts/reports/`:
- `repro_results.json`: Per-paper metrics and scores.
- `stat_summary.json`: Meta-analysis results.
- `checklist.md`: Community guidelines.
- `plots/`: Bland-Altman PNGs.

## 6. Troubleshooting
- **Dataset Missing**: If a dataset URL is not found, the system logs "Data Unavailable" and skips the paper.
- **GPU Error**: Ensure `torch` is installed as the CPU wheel (`pip install torch --index-url).
- **Memory Error**: Reduce dataset size or model complexity in the manifest.
