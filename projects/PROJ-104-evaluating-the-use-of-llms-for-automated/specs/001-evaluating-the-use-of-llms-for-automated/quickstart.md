# Quickstart: Running the LLM Fidelity Evaluation Pipeline

## Prerequisites
- Python 3.11 installed.
- Internet access (required for cloning repositories and downloading model weights).
- CPU-only runner (2 CPU cores, ~7 GB RAM is sufficient; no GPU is used anywhere — NFR-001).

## Setup
```bash
# 1. Clone the project
git clone <repository-url>
cd PROJ-104-evaluating-the-use-of-llms-for-automated

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Model-inference dependencies (CPU-only, 4-bit quantization)
pip install transformers bitsandbytes
```
`transformers` and `bitsandbytes` are needed only for the model-inference
stage (T005); the Phase-0 smoke test runs without them.

## Seed policy (Constitution I)
All stochastic components use the single pinned seed `SEED = 42` defined in
`code/seeds.py`: the Monte-Carlo power analysis (T002), dataset sampling
(T004), LLM generation (T005, `do_sample=False`), the zero-shot classifier
(T007), and any bootstrap resampling (T009). Re-running any stage
reproduces identical results.

## Quick smoke test (Phase 0)
```bash
python -m code.run_pipeline --sample 5
```
This loads one tiny hard-coded synthetic commit pair (a plumbing smoke
test only — never analysis data), invokes the CPU-only generation module,
and writes `data/generated/phi3-mini/sample_test.txt`. It completes in
[deferred] and requires no model downloads.

## Running the Full Pipeline
```bash
python -m code.run_pipeline --full
```
**What happens:**
1. Repositories (`pandas`, `requests`, `scikit-learn`, `flask`, `django`) are cloned (cached on subsequent runs).
2. Commits from the last two years that touch `.md`/`.rst` are extracted → `data/raw/commit_pairs.csv`.
3. A random subset is sampled for gold-standard annotation.
4. Each LLM (Phi-3-mini, Gemma-2-2b, Llama-3.2-3B) generates a documentation update per commit on CPU, with a 60 s timeout and up to 2 retries.
5. Entities are extracted, verified (regex + AST + `git grep`), and fidelity metrics are computed.
6. Statistical tests (power analysis, Friedman/ANOVA with Holm-Bonferroni correction) and visualizations are saved under `results/`.

## Inspecting Results
- **Dataset**: `data/raw/commit_pairs.csv` (validated against `contracts/commitpair.schema.yaml`).
- **Generated outputs**: `data/generated/<model_id>/`.
- **Metrics**: `data/processed/fidelity_metrics.csv` (validated against `contracts/fidelity.schema.yaml`).
- **Figures**: `results/figures/intent_precision_bar.png`, `results/figures/surface_confusion_matrix.png`.
- **Summary report**: `results/summary.md`.

## Running the tests
```bash
pytest tests/quickstart_test.py
```

## CI Execution
The repository includes a GitHub Actions workflow (`.github/workflows/research.yml`) that automatically runs the full CPU-only pipeline on every push, caches model weights, and uploads artifacts. No manual intervention is required.