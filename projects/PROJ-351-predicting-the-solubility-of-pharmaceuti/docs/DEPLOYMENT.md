# Deployment Guide

## Environment Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows (WSL2).
- **Python**: 3.8 or higher.
- **RAM**: Minimum 8GB (16GB recommended for full dataset processing).
- **CPU**: Multi-core CPU required. GPU is optional but not supported in this implementation (CPU-optimized).

## Deployment Steps

### 1. Environment Setup

Ensure all system dependencies are installed:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv build-essential cmake
```

### 2. Installation

```bash
# Clone repository
git clone <repo-url>
cd <project-dir>

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configuration

Verify `code/config/seeds.py` is configured with the desired random seed for reproducibility.

### 4. Execution

Run the full pipeline:
```bash
# 1. Setup
python code/setup_project_structure.py
python code/setup_logging.py

# 2. Data
python code/data/download_esol.py
python code/data/preprocess.py
python code/data/split.py

# 3. Training
python code/training/train_baseline.py
python code/training/train_gnn.py

# 4. Evaluation
python code/evaluation/statistical_test.py
python code/evaluation/report_generator.py
```

### 5. Verification

Check `results/final_report.json` to ensure all metrics are generated and the pipeline completed successfully.

## Troubleshooting

- **RDKit Import Error**: Ensure `rdkit` is installed via conda or pip with the correct version.
- **Out of Memory**: The pipeline is designed to stream data, but if OOM occurs, reduce the batch size in `code/training/train_gnn.py`.
- **Download Failure**: If the ESOL dataset fails to download, check network connectivity and verify the MoleculeNet URL.

## Maintenance

- **Logs**: Review `data/logs/` for errors after each run.
- **Updates**: Update `requirements.txt` if new dependencies are added.
- **Backups**: Back up `models/` and `results/` directories regularly.
