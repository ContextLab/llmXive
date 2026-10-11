# Quickstart: llmXive follow‑up: extending "Qwen-Image-VAE-2.0 Technical Report"

## Prerequisites
- Python 3.11+  
- 2 vCPU, ~7 GB RAM (or Kaggle GPU access for the optional escape hatch)  
- Internet connection (for streaming the HF dataset)  

## Installation

```bash
# 1️⃣ Clone the repository
git clone https://github.com/your-org/llmxive-vae-geometric-analysis.git
cd llmxive-vae-geometric-analysis

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate

# 3️⃣ Install pinned dependencies
pip install -r projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/requirements.txt
```

## Running the Pipeline

All phases are orchestrated via `main.py`. Use the `--phase` flag to run a specific stage or `--full` for end‑to‑end execution.

| Phase | Command | What it does |
|-------|---------|--------------|
| **Data Load** | `python projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/src/main.py --phase data_load` | Streams Omni‑Doc‑1, validates fields, applies purity filter. |
| **Disentanglement** | `python ... --phase disentanglement` | Encodes crops, trains Linear SVM, runs permutation test, outputs `metrics.json`. |
| **Editing** | `python ... --phase editing` | Performs vector arithmetic, decodes edited images, runs OCR & layout metrics. |
| **Full Run** | `python ... --full` | Executes all phases in order and writes the final `experiment_output.json`. |

## Output Verification
- `data/results/metrics.json` – per‑metric values, p‑values, significance flags.  
- `data/results/plots/` – PCA scatter plot, example edited images.  
- `data/results/experiment_output.json` – conforms to `contracts/output.schema.yaml`.  

## Troubleshooting
- **OOM on CPU** – The script will automatically switch to the Kaggle GPU escape hatch and set `cpu_feasibility: rejected` in the final JSON.  
- **Dataset download failed** – Ensure outbound internet is allowed; the script will abort with a clear “Data Unavailable” error if the HF URL is unreachable.  
- **PaddleOCR import error** – Verify `paddlepaddle‑cpu` and `paddleocr` are installed from the pinned `requirements.txt`.  

---
