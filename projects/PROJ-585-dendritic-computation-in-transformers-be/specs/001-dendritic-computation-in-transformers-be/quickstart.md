# Quickstart: Dendritic Computation in Transformers

## Prerequisites

- Python 3.11+
- Git
- GB RAM (minimum)
- CPU cores (minimum)

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-585-dendritic-computation-in-transformers-be
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Environment**:
    Ensure PyTorch is running on CPU:
    ```bash
    python -c "import torch; print(torch.__version__); print('CUDA available:', torch.cuda.is_available())"
    # Expected: CUDA available: False
    ```

## Running the Experiments

### 1. Architecture Validation (FLOP/Param Check)
Verify that the baseline and dendritic models are matched before training.
```bash
python code/experiments/validate_arch.py --config code/config/config.yaml
```
*Expected Output*: Parameter diff < 0.1%, FLOP diff < 1%.

### 2. Training (with h Timeout)
Run the training loop for both models. The script will automatically stop after a predefined duration.
```bash
python code/experiments/train.py --config code/config/config.yaml --seeds 42 123 456
```
*Output*: Logs in `artifacts/logs/`, checkpoints in `artifacts/checkpoints/`.

### 3. Probing Analysis
Train linear probes on the saved checkpoints.
```bash
python code/experiments/probe.py --checkpoints-dir artifacts/checkpoints/
```
*Output*: `artifacts/results/probe_*.csv`.

### 4. Statistical Analysis
Compute paired tests and apply corrections.
```bash
python code/experiments/analyze.py --probe-results-dir artifacts/results/
```
*Output*: `artifacts/results/stat_test.json`.

## Troubleshooting

- **Out of Memory (OOM)**: Reduce `batch_size` in `config.yaml` or use a smaller subset of the dataset.
- **Training Too Slow**: The 6-hour timeout is a hard limit. If the model hasn't converged, the results are marked "incomplete" but still valid for comparison.
- **Gradient Explosion**: If `clipped_gradients` is high in logs, check the `nonlinearity_threshold` in the dendritic config.
