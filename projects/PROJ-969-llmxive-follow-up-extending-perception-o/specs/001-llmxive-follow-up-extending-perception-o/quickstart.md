# Quickstart: Running the Prejudice-Gap Study

## Prerequisites
- GitHub Actions runner (or local Linux environment) with Python 3.11.
- Internet access to download the primary dataset (`huggingface: mmbench/ocean`) and the open-source MLLMs.
- Clone the repository and navigate to the project root.

## Installation
```bash
# 1. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r requirements.txt
```

## Step-by-Step Execution

| Step | Command | Description |
|------|---------|-------------|
| **0. Verify environment** | `python -c "import torch; print(torch.__version__)"` | Ensure CPU-only PyTorch is installed. |
| **0.5. Pre-inference projection & fallback** | `python -m src.pipeline.inference --pilot` | Runs a small-scale pilot to measure per-model throughput and RAM; projects total runtime for 27 × ~350–400 × 3 runs. If the projection exceeds 5.5 h / 6.5 GB, the pre-registered top-15 model + 10-frame fallback is applied uniformly to all conditions **before any inference data is produced**. |
| **1. Acquire data** | `python -m src.pipeline.acquire` | Downloads the primary dataset `mmbench/ocean` (validation split, comprising several hundred videos), computes checksums, stores under `data/raw/`, and validates each record against `contracts/video_metadata.schema.yaml`. |
| **2. Build knowledge base** | `python -m src.pipeline.knowledge` | Parses metadata and creates `data/knowledge_base.json`; every context profile is validated against `contracts/context_profile.schema.yaml`. |
| **3. Run baseline inference** | `python -m src.pipeline.inference --condition baseline` | Processes the selected models on the full validation set (batch size 20). Outputs `data/derived/baseline_outputs.jsonl`, validated against `contracts/model_output.schema.yaml`. |
| **4. Run context-grounded inference** | `python -m src.pipeline.inference --condition context` | Retrieves the appropriate context profile per video and injects it into the prompt. Outputs `data/derived/context_outputs.jsonl` (schema-validated). |
| **5. Run noise control** | `python -m src.pipeline.inference --condition noise` | Uses random noise as context. Outputs `data/derived/noise_outputs.jsonl` (schema-validated). |
| **6. Compute metrics** | `python -m src.pipeline.metrics` | Generates three CSV files (`baseline_metrics.csv`, `context_metrics.csv`, `noise_metrics.csv`) including primary PR (spec FR-018 denominator), supplementary `PR_all`, and rating accuracy; validated against `contracts/metric_record.schema.yaml`. |
| **7. Statistical analysis** | `python -m src.pipeline.analysis` | Produces `results.md` and figures under `outputs/`. Includes the **video-level mixed-effects primary test** (power ≥ 0.80 for d = 0.5 via the design-effect calculation in research.md), model-level paired secondary test, Bonferroni correction, sensitivity sweep, and quantisation-impact assessment. |
| **8. Resource report** | `cat data/derived/runtime_log.json` | Shows total wall-clock time and peak RAM; if the pre-registered fallback was applied, a note appears. |
| **9. Contract validation** | `pytest -m contract` | Ensures all output artifacts conform to their schemas (video_metadata, context_profile, model_output, metric_record) and that every figure/table traces back to a single row in the metric CSVs. |
| **10. Randomisation check** | `python -m src.pipeline.utils --verify-randomization` | Confirms that condition order was randomly permuted per model-video pair (seeded for reproducibility). |

## Optional: GPU Escape Hatch
If a model fails to load on CPU, the inference script automatically re-runs that model on a free Kaggle GPU (handled by the platform). No manual action is required.

## Reproducibility Checklist
- Random seeds are fixed in `src/pipeline/utils.py` (`np.random.seed(42); torch.manual_seed(42)`).
- All external URLs are hard-coded in `src/pipeline/acquire.py`; they are version-pinned.
- Output files are content-hashed; the platform records hashes in `state/projects/...yaml`.

Running the full pipeline (27 models × ~350–400 videos × 3 conditions) completes in **≈ 4 h** on a standard GitHub Actions runner and stays under **6 GB** peak RAM.