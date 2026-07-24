# Quickstart Guide: CPU-Only Execution

This guide provides instructions for running the **Quantization Robustness of Multi-Effect LoRA Adapters** pipeline on CPU-only runners (e.g., GitHub Actions `ubuntu-latest`, local machines without GPUs).

## Prerequisites

- Python 3.11+
- Git
- At least 32GB RAM (recommended) and 50GB disk space
- Internet access for initial model download

## 1. Clone and Setup

```bash
git clone <repository-url>
cd <project-directory>

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Configuration

Ensure `code/config.yaml` contains your desired effect prompts and seed values:

```yaml
# code/config.yaml
seeds:
 - 42
 - 123
 - 456
effects:
 - "oil painting style"
 - "watercolor style"
 - "pencil sketch"
 - "cyberpunk neon"
 - "vintage photograph"
```

## 3. Running the Pipeline on CPU

The main entry point `code/main.py` automatically detects CPU execution and manages memory constraints.

```bash
# Run the full pipeline (FP16 Baseline -> Quantization -> Analysis)
python code/main.py
```

### Key CPU-Specific Behaviors

1. **Automatic Device Detection**: The pipeline automatically uses `cpu` for all model loading and inference.
2. **Memory Management**:
 - OOM handling is built-in (see Task T008). If a quantization level triggers `MemoryError` or Exit Code 137, the pipeline logs "Quantization Failure" and skips that level gracefully.
 - Models are loaded sequentially to minimize peak memory usage.
3. **Download Logic**:
 - The base model (Stable Diffusion 1.5/2.1) and CollectionLoRA adapter are downloaded automatically on first run via `code/data_loader.py` (Task T007).
 - The adapter is saved as `data/models/adapter_fp16.safetensors` and hashed (Task T007b).

## 4. Expected Output

Upon successful completion, the following artifacts will be generated:

- `data/results.csv`: Metrics (CLIP similarity, LPIPS, CESR) for all runs.
- `data/generated/`: Generated images for FP16, INT8, and INT4 adapters.
- `data/references/`: Baseline reference images.
- `data/subspace_ranks.json`: SVD-based effective rank analysis.
- `data/analysis_results.json`: Bayesian Hierarchical Model results.
- `state/artifacts.yaml`: SHA-256 hashes of all artifacts.

## 5. Troubleshooting CPU Runs

### Out of Memory (OOM) Errors
If the runner crashes with Exit Code 137 (SIGKILL), the pipeline has a built-in handler (Task T008) to skip the failing quantization level. Ensure your runner has sufficient RAM (32GB+ recommended for full batch).

### Slow Execution
CPU execution is significantly slower than GPU. The full pipeline may take 4-6 hours on a standard 4-core runner. [UNRESOLVED-CLAIM: c_f32843c7 — status=not_enough_info]
- To speed up, reduce the number of prompts in `code/config.yaml`.
- Ensure `torch` is installed with CPU support (not CUDA).

### Model Download Failures
If HuggingFace downloads fail, ensure your network allows access to `huggingface.co`. The models are cached in `~/.cache/huggingface`.

## 6. Verification

Run the end-to-end validation script to verify the pipeline integrity:

```bash
python code/run_e2e_validation.py
```

This checks for:
- Presence of all required data files.
- Correct SHA-256 hashes in `state/artifacts.yaml`.
- Validity of `data/results.csv` and `data/analysis_results.json`.

## 7. Bayesian Analysis Note

The pipeline uses a Bayesian Hierarchical Model (BHM) instead of ANOVA (Constitution Amendment pending, see Task T034) to better handle small sample sizes and hierarchical data structures (images nested within prompts). Results are reported with 95% credible intervals. [UNRESOLVED-CLAIM: c_56ea320b — status=not_enough_info]