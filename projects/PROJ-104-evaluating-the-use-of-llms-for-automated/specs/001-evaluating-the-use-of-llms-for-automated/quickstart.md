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
- Data extraction produces a CSV adhering to the `CommitPair` definition,
- Generation produces JSON adhering to `GeneratedOutput`,
- Entity extraction produces `EntitySet`‑compliant output.

## Power Analysis (Phase 1)
```bash
python -m src.analysis.power_analysis
```
Outputs `results/power_report.md` with the estimated power for `n = 500` given α = 0.05, effect size f = 0.25, and the variance estimated from pilot data. Flags the run as exploratory if power < 0.8.

## Full Pipeline (CPU‑only)
```bash
python -m src.run_pipeline --full
```
What happens:
1. Power analysis runs and writes `results/power_report.md`.  
2. Repositories are cloned (cached on subsequent runs).  
3. Commits from the last two years that touch `.md`/`.rst` are extracted via the GitHub API → `data/raw/commit_pairs.csv` using **stratified sampling** across the five repos.  
4. A **human‑annotated gold‑standard** of 50 samples is created (`data/gold/annotations.csv`) by two independent annotators; κ ≥ 0.6 is required.  
5. Each LLM generates a documentation update per commit on CPU (4‑bit, 60 s timeout, up to 2 retries). If a model exceeds the timeout, the pipeline **reduces the per‑model sample size** to stay within the 6 h CI limit.  
6. Entities are extracted, verified (regex + AST + `git grep`) and fidelity metrics are computed → `data/processed/fidelity_metrics.csv`.  
7. Statistical tests (normality, Friedman/ANOVA, Holm‑Bonferroni) and visualizations are saved under `results/figures/`.  
8. Contract validation runs automatically via the test suite; artifacts are checksummed and uploaded as CI artifacts.

## Inspecting Results
- **Power analysis**: `results/power_report.md`.  
- **Dataset**: `data/raw/commit_pairs.csv` (validated against `CommitPair` definition).  
- **Generated outputs**: `data/generated/<model_id>/`.  
- **Metrics**: `data/processed/fidelity_metrics.csv` (validated against `FidelityMetric` definition).  
- **Figures**: `results/figures/intent_precision_bar.png`, `results/figures/surface_confusion_matrix.png`.  
- **Summary report**: `results/summary.md`.

## Running Tests
```bash
pytest tests/contract/
pytest tests/unit/
```

---

