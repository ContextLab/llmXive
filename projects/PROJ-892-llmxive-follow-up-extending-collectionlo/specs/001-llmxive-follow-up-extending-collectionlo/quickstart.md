# Quickstart: Quantization Robustness of Multi-Effect LoRA Adapters

## Prerequisites

- Python 3.11+
- Git
- 16GB+ RAM (Recommended for CPU loading, though GB is the minimum target)
- GitHub Actions Runner (Free Tier)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-892-llmxive-follow-up-extending-collectionlo
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: Ensure `torch` is installed for CPU only (no CUDA).*

## Configuration

1. **Edit `code/config.yaml`**:
   - Set `base_model`: e.g., `runwayml/stable-diffusion-v1-5`
   - Set `adapter_model`: e.g., `user/collection-lora-multi-effect`
   - Set `prompts`: List of distinct effect prompts.

The research question remains: [Research Question].
The method remains: [Method].
The references remain: [References].
   - Set `seeds`: Fixed list of integers for reproducibility.

2. **Verify Model Availability**:
   Ensure the specified adapter and base model are accessible on HuggingFace.

## Running the Pipeline

### 1. Data Generation & Metric Computation
Run the main script to generate images and compute metrics:
```bash
python code/main.py --mode generate
```
- This will download models (if missing), quantize, generate images, and compute CosSim, LPIPS, and CESR.
- Output: `data/results.csv`, `data/generated/`.

### 2. Statistical Analysis
Run the Bayesian analysis:
```bash
python code/main.py --mode analyze
```
- This reads `data/results.csv` and runs the hierarchical model.
- Output: `data/analysis_results.json`, plots in `data/plots/`.

### 3. Verification
Check the state manifest:
```bash
cat state/artifacts.yaml
```
Verify that all generated files have SHA-256 hashes.

## Troubleshooting

- **OOM Error**: If `MemoryError` occurs, the script will log "Quantization Failure" and skip the level. Ensure no other heavy processes are running.
- **Backend Unavailable**: If `torch.ao.quantization` fails, check `torch` version. Fallback to standard `torch` quantization or manual rounding for INT4.
- **Slow Runtime**: Reduce `num_inference_steps` in `config.yaml` from 50 to 20.
- **Underpowered Analysis**: If the correlation analysis is flagged as "Underpowered" or "PredictorInsufficientVariance", the results are exploratory and should be interpreted with caution.

## Expected Output

- `data/results.csv`: Contains multiple rows (prompts × levels) with metrics.
- `data/analysis_results.json`: Contains posterior distributions and correlation coefficients.
- `state/artifacts.yaml`: Checksums for all artifacts.