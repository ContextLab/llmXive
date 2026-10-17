# Quickstart: Running the LLM Fidelity Evaluation Pipeline

## Prerequisites
- Python (a recent version) installed (GitHub Actions provides this automatically).
- Internet access (required for cloning repositories and downloading model weights).
- Optional: Kaggle account (only needed if a model exceeds the CPU time budget; the CI workflow will handle the off‑load automatically).

## Setup
```bash
# 1. Clone the project (already done in CI)
git clone 
cd PROJ-104-evaluating-the-use-of-llms-for-automated

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions

# 3. Pin random seeds (handled inside the pipeline)
```

## Running the Full Pipeline
```bash
python -m src.cli.run_pipeline \
    --repos pandas requests scikit-learn flask django \
    --years 2 \
    --min-pairs 500 \
    --gold-samples 50 \
    --models phi3-mini gemma2-2b llama3.2-3b \
    --timeout-per-commit 60 \
    --max-commits 200 \   # default CI sample size; increase to 500 for a full run (requires manual workflow)
    --seed 42
```
**What happens:**
1. Repositories are cloned (cached on subsequent runs).
2. Commits from the last two years that touch `.md`/`.rst` are extracted → `data/raw/commit_pairs.csv`.
3. A random subset is sampled for gold‑standard annotation (manual step – see `README.md` for instructions).
4. Each LLM generates a documentation update per commit; generation time is logged. If any model exceeds the 60 s CPU timeout, **all** models are re‑executed on a Kaggle free GPU with identical prompts (uniform fallback).
5. Entities are extracted, verified (expanded regex + AST), and fidelity metrics are computed.
6. Statistical tests (power analysis, Friedman/ANOVA with Holm‑Bonferroni correction) and visualizations are saved under `results/`.

## Inspecting Results
- **Dataset**: `data/raw/commit_pairs.csv` (validated against `contracts/commitpair.schema.yaml`).  
- **Generated outputs**: `data/generated/<model_id>/`.  
- **Metrics**: `results/fidelity_metrics.csv` (validated against `contracts/fidelity.schema.yaml`).  
- **Figures**: `results/figures/intent_precision_bar.png`, `results/figures/hallucination_rate.png`.  
- **Summary report**: `results/summary.md`.

## Re‑Running a Sub‑step
To debug or re‑run only the generation step for a specific model:
```bash
python -m src.pipeline.generation \
    --model phi3-mini \
    --input data/raw/commit_pairs.csv \
    --output data/generated/phi3-mini/
```

## CI Execution
The repository includes a GitHub Actions workflow (`.github/workflows/research.yml`) that automatically runs the full pipeline on every push to the designated evaluation branch, caches model weights, and uploads artifacts. No manual intervention is required.

---


