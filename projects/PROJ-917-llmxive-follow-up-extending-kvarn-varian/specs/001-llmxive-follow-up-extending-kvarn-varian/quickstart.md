# Quickstart: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

## Prerequisites

- Python 3.11 or higher.
- A POSIX-compliant environment (Linux, macOS, or WSL).
- At least 8 GB of available RAM (project requires ~6 GB peak).
- No GPU required (CPU-only execution).

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: Ensure `torch` is installed for CPU only. If using `pip`, use the CPU wheel: `pip install torch --index-url https://download.pytorch.org/whl/cpu`.*

## Running the Pipeline

The project is designed to run as a single pipeline, but individual stages can be executed separately.

### 1. Generate Synthetic Data (FR-001)
Generates a large set of synthetic attention matrices and computes ground-truth scaling factors.
```bash
python code/main.py --stage generate
```
- **Output**: `data/raw/synthetic_attention_dataset.csv`
- **Time**: ~10-30 minutes (depending on Sinkhorn solver speed).

### 2. Train the Static Prior Model (FR-002)
Trains a multi-layer perceptron with multiple hidden layers to predict scaling factors.
```bash
python code/main.py --stage train
```
- **Input**: `data/raw/synthetic_attention_dataset.csv`
- **Output**: `code/models/static_prior.pt`, `data/processed/model_predictions.json`
- **Time**: ~1-5 minutes.

### 3. Run Simulation (FR-003)
Simulates the autoregressive loop with KVarN, Static Prior, and Closed-form baselines.
```bash
python code/main.py --stage simulate --runs 30 --steps 1000
```
- **Input**: `code/models/static_prior.pt`
- **Output**: `data/processed/simulation_results.csv`
- **Time**: ~2-4 hours (depending on CPU speed and number of runs).

### 4. Analyze Results (FR-006, FR-007)
Performs statistical analysis (t-tests, sensitivity analysis) and generates summary reports.
```bash
python code/main.py --stage analyze
```
- **Input**: `data/processed/simulation_results.csv`
- **Output**: `data/final/statistical_summary.json`, `data/final/visualizations/`

## Verification

To verify the installation and data generation:
```bash
python code/main.py --stage verify
```
This runs a quick check on the generated dataset to ensure:
- Dimensions are correct (128x128).
- Sinkhorn solver converges.
- Scaling factors are within expected ranges.

## Troubleshooting

- **OOM (Out of Memory)**: If you encounter memory errors, reduce the number of simulation runs (`--runs`) or steps (`--steps`). The default is designed for standard RAM configurations.
- **Sinkhorn Timeout**: If the Sinkhorn solver takes too long, check the `MAX_ITERATIONS` parameter in `code/data_generation/synthetic_attention.py`.
- **CUDA Error**: Ensure you installed the CPU version of PyTorch. If you see CUDA errors, reinstall with `pip install torch --index-url https://download.pytorch.org/whl/cpu`.
