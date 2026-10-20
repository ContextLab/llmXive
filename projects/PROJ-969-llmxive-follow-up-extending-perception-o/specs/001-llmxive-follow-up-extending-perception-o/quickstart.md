# Quickstart: Running the Prejudice‑Gap Study

## Prerequisites
- GitHub Actions runner (or local Linux environment) with Python 3.11.
- Internet access to download the open substitute dataset (`huggingface: mmbench/ocean`) and the multiple open‑source MLLMs.
- Clone the repository and navigate to the project root.

## Installation
```bash
# 1. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Execution

| Step | Command | Description |
|------|---------|-------------|
| **0. Verify environment** | `python -c "import torch; print(torch.__version__)"` | Ensure CPU‑only PyTorch is installed. |
| **0.5. Pre‑configured fallback** | *(no command needed – configuration is baked into the pipeline; see `src/pipeline/config.py`)* | The pipeline will automatically apply the pre‑specified top‑15 model & 10‑frame‑per‑video fallback if resource limits are projected to be exceeded. |
| **1. Acquire data** | `python -m src.pipeline.acquire` | Downloads the open substitute dataset, computes checksums, stores under `data/raw/`. If the official MM‑OCEAN becomes publicly available, the script will automatically prefer it. |
| **2. Build knowledge base** | `python -m src.pipeline.knowledge` | Parses metadata and creates `data/knowledge_base.json`. |
| **3. Run baseline inference** | `python -m src.pipeline.inference --condition baseline` | Processes the selected models on the full validation set (batch size 20). Outputs `data/derived/baseline_outputs.jsonl`. |
| **4. Run context‑grounded inference** | `python -m src.pipeline.inference --condition context` | Retrieves the appropriate context profile per video and injects it into the prompt. Outputs `data/derived/context_outputs.jsonl`. |
| **5. Run noise control** | `python -m src.pipeline.inference --condition noise` | Uses random noise as context. Outputs `data/derived/noise_outputs.jsonl`. |
| **6. Compute metrics** | `python -m src.pipeline.metrics` | Generates three CSV files (`baseline_metrics.csv`, `context_metrics.csv`, `noise_metrics.csv`) and validates them against `contracts/metric_record.schema.yaml`. |
| **7. Statistical analysis** | `python -m src.pipeline.analysis` | Produces `results.md` and figures under `outputs/`. Includes paired tests, mixed‑effects model, sensitivity analysis, **formal power analysis**, **multiple‑comparison correction**, and **quantization‑impact assessment**. |
| **8. Resource report** | `cat data/derived/runtime_log.json` | Shows total wall‑clock time and peak RAM; if limits were exceeded, a fallback note appears. |
| **9. Contract validation** | `pytest -m contract` | Ensures all output artifacts conform to their schemas and that every figure/table traces back to a single row in the metric CSVs. |
| **10. Randomization check** | `python -m src.pipeline.utils --verify-randomization` | Confirms that condition order was randomly permuted per model‑video pair (seeded for reproducibility). |

## Optional: GPU Escape Hatch
If a model fails to load on CPU, the inference script automatically re‑runs that model on a free Kaggle GPU (handled by the platform). No manual action is required.

## Reproducibility Checklist
- Random seeds are fixed in `src/pipeline/utils.py` (`np.random.seed(42); torch.manual_seed(42)`).  
- All external URLs are hard‑coded in `src/pipeline/acquire.py`; they are version‑pinned.  
- Output files are content‑hashed; the platform records hashes in `state/projects/...yaml`.  

Running the full pipeline on the open substitute completes in **≈ 3.5 h** on a standard GitHub Actions runner and stays under **6 GB** peak RAM.

---



