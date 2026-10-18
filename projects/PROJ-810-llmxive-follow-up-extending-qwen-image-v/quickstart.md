# Quickstart: llmXive follow‑up: extending "Qwen-Image-VAE-2.0 Technical Report"

## Prerequisites
- Python 3.11+
- 2 vCPU, ~7 GB RAM (or Kaggle GPU access for the optional escape hatch)
- Internet connection (for streaming the verified benchmark dataset)

## Installation

```bash
# 1️⃣ Clone the repository
git clone
cd llmxive-vae-geometric-analysis

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate

# 3️⃣ Install pinned dependencies (the file lives under the code directory as required by the Constitution)
pip install -r projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/requirements.txt
```

## Running the Pipeline

All phases are orchestrated via `code/src/main.py`. Use the `--phase` flag to run a specific stage or `--full` for end‑to‑end execution.

| Phase | Command | Description |
|-------|---------|-------------|
| **0** | `python -m code.main --config config.yaml` | Verify external URLs for dataset and model (Phase 0). |
| **1** | `python -m code.main --phase data_load` | Streams the **verified CPU‑only benchmark parquet** dataset. |
| **2** | `python -m code.main --phase model_load` | Loads the **tiny-vae** model on CPU; if this fails, the GPU escape hatch will be triggered automatically. |
| **3** | `python -m code.main --phase preprocess` | Applies the purity filter, computes confounder metadata, and writes `RawImageCrop` records. |
| **4** | `python -m code.main --phase encode` | Encodes crops into `LatentVector` objects using tiny‑vae. |
| **5** | `python -m code.main --phase disentangle` | Clustering, DCI computation, triviality check, and permutation test with Bonferroni correction. |
| **6** | `python -m code.main --phase linearity` | Pilot linearity verification on 10 samples (R² ≥ 0.9). |
| **7** | `python -m code.main --phase centroids` | Computes modality centroids. |
| **8** | `python -m code.main --phase edit` | Performs vector arithmetic, decodes, runs OCR, and computes layout‑preservation metrics against the original image. |
| **9** | `python -m code.main --phase sensitivity` | Sweeps classification threshold and reports FP/FN variation. |
| **10** | `python -m code.main --phase power` | Runs power analysis and runtime feasibility check. |
| **11** | `python -m code.main --phase aggregate` | Writes the final `experiment_output.json` conforming to the output schema. |
| **12** | `python -m code.main --phase gpu_fallback` | (Optional) Runs Phases 4‑11 on a Kaggle free GPU with 8‑bit quantization if CPU loading fails. |

> **Important**: The pipeline now uses **verified** open resources (benchmark parquet dataset and tiny‑vae model). No unverified Omni‑Doc‑1 or Qwen‑Image‑VAE‑2.0 resources are required. If either resource cannot be fetched, the script logs an error and aborts; the optional GPU fallback is only for the *model* loading step.

## Output Verification
- `data/results/experiment_output.json` – conforms to `contracts/output.schema.yaml`.
- `data/results/metrics.json` – per‑metric values (populated only when resources are available).
- `data/results/plots/` – PCA scatter plot, example edited images (if generated).

## Troubleshooting
- **Missing verified dataset** – The script logs `DataUnavailableError` and aborts; no fallback to a non‑verified dataset is attempted.
- **Model cannot load on CPU** – The script logs `ModelUnavailableError` and automatically triggers the optional GPU escape hatch; `cpu_feasibility` will be set to `"rejected"` in the final JSON.
- **Out‑of‑memory on CPU** – Reduce the sample size via `--sample-size N`; the power analysis will be updated accordingly.
- **PaddleOCR import error** – Ensure `paddlepaddle‑cpu` and `paddleocr` are installed from the pinned `requirements.txt`.