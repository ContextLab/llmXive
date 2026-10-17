# Quickstart: Running the LLM Fidelity Evaluation Pipeline

## Prerequisites
- Python 3.11 installed.  
- Internet access (required for cloning repositories and downloading model weights).  
- CPU‑only runner (2 CPU cores, ~7 GB RAM is sufficient; no GPU is required for the default run).  

## Setup
```bash
# 1. Clone the project
git clone <repository-url>
cd PROJ-104-evaluating-the-use-of-llms-for-automated

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Install model‑inference extras (CPU‑only, 4‑bit quantization)
pip install transformers bitsandbytes
```

## Seed Policy (Constitution I)
All stochastic components use the single pinned seed `SEED = 42` defined in `src/utils.py`. This seed governs:
- Monte‑Carlo power analysis,
- Random sampling of commits,
- LLM generation (`do_sample=False` for deterministic output),
- Zero‑shot classifier (deterministic inference),
- Bootstrap resampling for confidence intervals.

Re‑running any stage reproduces identical results.

## Smoke Test (Phase 0)
```bash
python -m src.run_pipeline --sample 5
```
Runs a minimal end‑to‑end pass on five synthetic commit pairs (hard‑coded in `src/utils.py`). Verifies that:
- Data extraction produces a CSV adhering to `commitpair.schema.yaml`,
- Generation produces JSON adhering to `generatedoutput.schema.yaml`,
- Entity extraction produces `entityset.schema.yaml`‑compliant output.

## Power Analysis (Phase 1)
```bash
python -m src.analysis.power_analysis
```
Outputs `results/power_report.md` with the estimated power for `n = 500` and an `exploratory` flag (true if power < 0.8).

## Full Pipeline (CPU‑first)
```bash
python -m src.run_pipeline --full
```
What happens:
1. Power analysis runs and writes `results/power_report.md`.  
2. Repositories are cloned (cached on subsequent runs).  
3. Commits from the last two years that touch `.md`/`.rst` are extracted → `data/raw/commit_pairs.csv`.  
4. A 50‑sample gold‑standard is created (annotators fill `data/gold/annotation_template.csv`).  
5. Each LLM generates a documentation update per commit on CPU (4‑bit, 60 s timeout, up to 2 retries).  
6. Entities are extracted, verified (regex + AST + `git grep`), and fidelity metrics are computed → `data/processed/fidelity_metrics.csv`.  
7. Statistical tests (Friedman/ANOVA with Holm‑Bonferroni) and visualizations are saved under `results/figures/`.  
8. Contract validation runs; artifacts are checksummed and uploaded as CI artifacts.

## GPU Escape Hatch (if needed)
If any model exceeds the 60 s timeout, the pipeline automatically re‑runs **all** models on a Kaggle free GPU (`torch.cuda.is_available()` triggers the fallback). No code changes are required; the same script handles both environments.

## Inspecting Results
- **Power analysis**: `results/power_report.md`.  
- **Dataset**: `data/raw/commit_pairs.csv` (validated against `contracts/commitpair.schema.yaml`).  
- **Generated outputs**: `data/generated/<model_id>/`.  
- **Metrics**: `data/processed/fidelity_metrics.csv` (validated against `contracts/fidelitymetric.schema.yaml`).  
- **Figures**: `results/figures/intent_precision_bar.png`, `results/figures/surface_confusion_matrix.png`.  
- **Summary report**: `results/summary.md`.

## Running Tests
```bash
pytest tests/contract/
pytest tests/unit/
```

## CI Execution
The repository includes a GitHub Actions workflow (`.github/workflows/research.yml`) that automatically:
- Runs the full CPU‑only pipeline on every push,
- Caches model weights between runs,
- Uploads `data/`, `results/`, and checksum manifests as artifacts,
- Fails the job if any contract validation error occurs.

No manual intervention is required.

---
