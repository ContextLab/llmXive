# Quickstart Guide: Quantization Robustness of Multi-Effect LoRA Adapters

This guide provides instructions for running the `llmXive` Quantization Robustness pipeline on **CPU-only runners**. The pipeline is designed to be robust against memory constraints and can handle quantization tasks on standard hardware.

## Prerequisites

- **Python 3.11+** installed.
- **Git** for cloning the repository.
- **CPU-only environment** (no NVIDIA GPU required).
- **Internet connection** to download models and datasets initially.

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-892-llmxive-follow-up-extending-collectionlo
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: This will install `torch` with CPU support if no CUDA is detected, along with `diffusers`, `transformers`, `pymc`, and other required libraries.*

## Configuration

The pipeline relies on a configuration file located at `code/config.yaml`. This file contains:
- A list of effect prompts (e.g., "oil painting", "watercolor").
- Seed values for deterministic generation.
- Model paths and quantization settings.

Ensure `code/config.yaml` is populated before running.

## Running the Pipeline

The main entry point is `code/main.py`. It orchestrates the entire workflow:
1. **Data Loading**: Downloads the `CollectionLoRA` adapter and base model.
2. **Validation**: Verifies the adapter contains the required distinct effects.
3. **Baseline Generation**: Generates FP16 reference images.
4. **Quantization**: Applies INT8 and INT4 quantization.
5. **Analysis**: Computes metrics (CLIP, LPIPS, CESR) and runs Bayesian analysis.

### Full Pipeline Execution

Run the following command from the project root:

```bash
python code/main.py
```

**CPU-Specific Behavior**:
- The script automatically detects CPU-only environments.
- It sets `torch.set_num_threads` to optimize CPU usage.
- It handles `MemoryError` and SIGKILL (Exit Code 137) gracefully, logging "Quantization Failure" and skipping the affected quantization level to prevent the entire job from crashing (FR-008).

### Output Artifacts

Upon successful completion, the following artifacts will be generated:

- **Data**:
 - `data/models/adapter_fp16.safetensors`: Downloaded LoRA adapter.
 - `data/quantized/adapter_int8.safetensors`, `adapter_int4.safetensors`: Quantized adapters.
 - `data/references/fp16_refs/`: Reference images for all effects.
 - `data/results.csv`: Comprehensive metrics (Cosine Similarity, LPIPS, CESR).
 - `data/analysis_results.json`: Bayesian statistical analysis results.
- **State**:
 - `state/artifacts.yaml`: SHA-256 hashes of all generated artifacts.
- **Logs**:
 - Console logs and `logs/pipeline.log` (if configured).

## Troubleshooting

### Memory Errors (OOM)
If the runner encounters a memory limit:
- The pipeline is designed to catch `MemoryError` and subprocess exits (SIGKILL).
- It will log "Quantization Failure" and skip the specific quantization level (e.g., INT4) while continuing with others.
- Check `state/artifacts.yaml` to see which artifacts were successfully saved.

### Missing Models
The pipeline requires an initial download of the `CollectionLoRA` adapter from HuggingFace.
- Ensure you have a stable internet connection.
- If the download fails, the script will raise a `FileNotFoundError` (no synthetic fallback).

### Backend Unavailable
If `torch.ao.quantization` backend is unavailable on your specific CPU build:
- The script will log "Backend Unavailable" and skip that quantization level rather than crashing.

## Verification

To verify the integrity of the downloaded models and generated artifacts:

```bash
python code/verify_artifacts.py
```

This script compares the SHA-256 hashes in `state/artifacts.yaml` against the actual files on disk.

## CI/CD Integration

For CI/CD environments (e.g., GitHub Actions), use the `code/run_pipeline_timing.py` script which generates a `data/ci_report.json` containing job duration and status, ensuring the total job duration remains under the 6-hour limit (SC-005).

```bash
python code/run_pipeline_timing.py
```