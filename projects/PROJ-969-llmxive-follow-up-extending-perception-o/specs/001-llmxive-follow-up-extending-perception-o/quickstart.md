# Quickstart: Running the Prejudice‑Gap Study

## Prerequisites
- GitHub Actions runner (or local Linux environment) with Python 3.11.
- Internet access to download the primary dataset (`mmbench/ocean`) and the open‑source MLLMs.
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
| **0.5. Pre‑registered runtime projection** | `python -m src.pipeline.runtime_monitor --projected` | Computes worst‑case runtime (approximately several hours) and decides *a priori* whether to apply the top‑15‑model / 10‑frame fallback (logged, no data‑driven pilot). |
| **1. Acquire data** | `python -m src.pipeline.acquire` | Downloads `mmbench/ocean` (validation split, multiple videos), computes checksums, stores under `data/raw/`, validates each record against `contracts/video_metadata.schema.yaml`. |
| **2. Build knowledge base** | `python -m src.pipeline.knowledge` | Generates `data/knowledge_base.json`; each profile validated against `contracts/context_profile.schema.yaml`. |
| **3. Baseline inference** | `python -m src.pipeline.inference --condition baseline` | Processes selected models on the full validation set (batch ≤ 30, length‑equalised prompts). Outputs `data/derived/baseline_outputs.jsonl` (validated by `contracts/model_output.schema.yaml`). |
| **4. Context‑grounded inference** | `python -m src.pipeline.inference --condition context` | Retrieves the matching context profile per video, injects it into the prompt, runs inference. Outputs `data/derived/context_outputs.jsonl`. |
| **5. Neutral‑Noise control** | `python -m src.pipeline.inference --condition noise` | Uses a **semantically neutral but syntactically valid** filler sentence (`"The following statements are neutral and do not contain any relevant social information."`) to keep prompt length equalised without providing informative context. Outputs `data/derived/noise_outputs.jsonl`. |
| **6. Compute metrics** | `python -m src.pipeline.metrics` | Produces three CSV files (`baseline_metrics.csv`, `context_metrics.csv`, `noise_metrics.csv`) validated against `contracts/metric_record.schema.yaml`. |
| **7. Statistical analysis** | `python -m src.pipeline.analysis` | Generates `results.md` and figures under `outputs/`. Includes the video‑level mixed‑effects primary test (power ≥ 0.80 for d ≈ 0.5), secondary exploratory model‑level test, Bonferroni correction, sensitivity sweep, and quantisation‑impact assessment. |
| **8. Resource report** | `cat data/derived/runtime_log.json` | Shows total wall‑clock time and peak RAM; indicates whether the fallback was applied. |
| **9. Contract validation** | `pytest -m contract` | Ensures all output artifacts conform to their schemas and that every figure/table traces back to a single row in the metric CSVs. |
| **10. Randomisation check** | `python -m src.pipeline.utils --verify-randomization` | Confirms condition order was randomly permuted per model‑video pair (seed = 42). |

## Reproducibility Checklist
- Random seeds fixed in `src/pipeline/utils.py` (`np.random.seed(42); torch.manual_seed(42)`).
- All external URLs hard‑coded in `src/pipeline/acquire.py`; version‑pinned.
- Output files are content‑hashed; the platform records hashes in the project state file.
- No GPU escape‑hatch is used; all inference runs on CPU‑only quantised models.

Running the full pipeline (a modest collection of models × a sizable set of videos × 3 conditions) completes in on the order of hours on a standard GitHub Actions runner and stays within modest RAM usage.
