# Quickstart: llmXive follow-up

## Prerequisites

- **Python**: 3.10+
- **GPU**: Access to a GPU with $\ge 16$ GB VRAM (e.g., T4, V100, A10). *Note: CPU-only execution is not supported for this feature due to model size.*
- **HuggingFace Token**: Required to download `meta-llama/CodeLlama-7b-Instruct-hf`. Set `HF_TOKEN` environment variable.
- **Kaggle Account**: Required for GPU offload (optional if running locally on GPU).

## Installation

1. **Clone and Setup**:
   ```bash
   git checkout 001-gene-regulation
   cd projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   ```bash
   export HF_TOKEN="your_huggingface_token"
   export SEED=42
   ```

## Running the Pipeline

### Option A: Local GPU Execution
Run the full pipeline on your local machine (requires GPU):
```bash
python -m src.run_pipeline --mode full
```
This will:
1. Download datasets.
2. Compute entropy.
3. Run inference loops.
4. Perform statistical analysis.
5. Save results to `data/processed/`.

### Option B: Kaggle GPU Offload
If local GPU is unavailable, use the Kaggle script:
```bash
./run_gpu.sh
```
This script:
1. Detects CUDA requirements.
2. Uploads code/data to a Kaggle kernel.
3. Executes the pipeline.
4. Downloads results to `data/processed/`.

## Verification

After completion, verify artifacts:
```bash
python -m src.verify_artifacts
```
Expected outputs:
- `data/processed/convergence_results_core.csv`
- `data/processed/correlation_results_final.json`
- `data/processed/router_model.pkl`

## Troubleshooting

- **OOM Errors**: Reduce `batch_size` in `config.py`.
- **Model Download Failures**: Ensure `HF_TOKEN` is set and network is accessible.
- **CUDA Mismatch**: Ensure `torch` version matches the system CUDA driver.
