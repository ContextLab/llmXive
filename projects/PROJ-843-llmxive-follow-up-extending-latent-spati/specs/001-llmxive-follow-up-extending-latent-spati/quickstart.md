# Quickstart: llmXive follow-up: extending "Latent Spatial Memory for Video World Models"

## Prerequisites

- **OS**: Linux (Ubuntu 22.04 recommended) or macOS (Intel/Apple Silicon with Rosetta for CPU-only consistency).
- **Python**: 3.11+
- **Memory**: Minimum 8 GB RAM (pipeline optimized for 7 GB).
- **Disk**: 20 GB free space.

## Installation

1. **Clone and Setup**:
   ```bash
   cd projects/PROJ-843-llmxive-follow-up-extending-latent-spati
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Verify Environment**:
   ```bash
   python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
   # Expected: CUDA available: False (CPU-only mode)
   ```

## Running the Pipeline

### 1. Data Preparation (Phase 0)
Downloads and stratifies RealEstate10K.
```bash
python code/main.py --phase data_prepare
```
*Output*: `data/stratified/` containing 4 subfolders.

### 2. Feature Extraction (Phase 1)
Extracts SIFT/ORB descriptors.
```bash
python code/main.py --phase extract_features
```
*Output*: `data/features/` with `.npy` files.

### 3. Geometry & Warping (Phase 2)
Runs RANSAC and RBF interpolation.
```bash
python code/main.py --phase compute_geometry
```
*Output*: `data/results/warping/` with reconstructed frames.

### 4. Evaluation & Statistics (Phase 3)
Computes metrics and runs ANOVA.
```bash
python code/main.py --phase evaluate
```
*Output*: `data/results/metrics.json`, `data/results/anova_summary.csv`.

## Validation

Run the test suite to ensure integrity:
```bash
pytest tests/ -v
```

## Troubleshooting

- **OOM Error**: If the job fails with "Out of Memory", reduce the `batch_size` in `code/config.py` or enable `--sequential-mode` in `main.py`.
- **RANSAC Failure**: Check `data/results/warping/unsolvable_log.csv` for sequences with low texture.
- **Slow Execution**: Ensure no background GPU processes are running (even if CUDA is disabled, some libraries check for GPU presence).
