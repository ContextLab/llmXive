# llmXive Quickstart Guide

This guide provides the exact steps to set up the environment and run the full noise-injection pipeline on CPU-only hardware.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- 7GB+ available RAM (enforced by `memory_monitor.py`)
- 20GB+ free disk space for datasets and outputs

## 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## 2. Data Preparation

The pipeline automatically downloads the `bigbench_lite` dataset from HuggingFace on first run. No manual download is required.

Ensure the `data/` directory structure exists:

```bash
mkdir -p data/raw data/processed logs
```

## 3. Execution

The pipeline is orchestrated via `code/main.py`. It performs the following steps sequentially:

1. **Baseline Extraction**: Loads the model and dataset, extracts hidden states, and saves `data/processed/baseline_vectors.csv`.
2. **Perturbation Sweep**: Injects Gaussian noise, projects to valid tokens, checks validity, and saves `data/processed/perturbed_vectors.csv` and `data/processed/validity_log.csv`.
3. **Statistical Analysis**: Computes separability metrics, applies corrections, and saves `data/processed/statistical_results.json`.

### Run the Full Pipeline

Execute the following command from the project root:

```bash
python code/main.py
```

**Note**: The script enforces a hard memory limit of 7GB RSS. If this limit is exceeded, the process will terminate with a `MemoryLimitExceeded` error.

### Configuration

Default parameters (noise sweep range, model paths, memory limits) are defined in `code/config.py`. To modify the noise sweep parameters:

```python
# Edit code/config.py
config = NoiseSweepConfig(
 sigma_min=0.1,
 sigma_max=2.0,
 step=0.1,
 #... other settings
)
```

## 4. Output Artifacts

Upon successful completion, the following files will be generated in `data/processed/`:

- `baseline_vectors.csv`: L2-normalized hidden state vectors for the control group.
- `filtered_pairs_input_drift.csv`: Pairs that passed the semantic drift check (cosine similarity ≥ 0.95).
- `perturbed_vectors.csv`: Latent vectors for noise-augmented inputs.
- `validity_log.csv`: Pass rates and collapse points for each noise level ($\sigma$).
- `trade_off_curve.csv`: Per-task trade-off curves between perturbation magnitude and validity.
- `global_trade_off_curve.csv`: Aggregated global distribution.
- `statistical_results.json`: Final hypothesis test results with corrected p-values.
- `sensitivity_report.json`: Global sensitivity analysis.
- `memory_profile.json`: Peak RSS memory usage statistics.

## 5. Verification

To verify the pipeline ran correctly:

1. Check that `data/processed/statistical_results.json` exists and contains a `p_value` key.
2. Review `logs/sweep.log` for JSON lines confirming the sweep steps.
3. Inspect `data/processed/memory_profile.json` to ensure peak RSS was recorded.

## Troubleshooting

- **Memory Limit Exceeded**: The dataset or model is too large for the available RAM. Try reducing the batch size in `code/config.py` or use a machine with more RAM.
- **Dataset Fetch Failed**: Ensure you have an active internet connection. The pipeline fetches `bigbench_lite` from HuggingFace.
- **CUDA Errors**: This pipeline is CPU-only. If you see CUDA errors, ensure `torch` was installed without CUDA support or set `CUDA_VISIBLE_DEVICES=""`.