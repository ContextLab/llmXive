# Quickstart: Running the LLM Fidelity Evaluation Pipeline

## Prerequisites
- Python 3.11 installed.
- Internet access (required for cloning repositories and downloading model weights).
- CPU‑only runner (2 CPU cores, ~7 GB RAM is sufficient, no GPU is used anywhere — NFR-001).

## Setup
```bash
# 1. Clone the project
git clone <repository-url>
cd PROJ-104-evaluating-the-use-of-llms-for-automated

# 2. Create a virtual environment and install dependencies
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## Model-inference dependencies (CPU-only, 4-bit quantization)
```bash
pip install transformers bitsandbytes
```
`transformers` and `bitsandbytes` are needed for the model-inference stage (T006); the Phase-0 smoke test and the power analysis run without them.

## Seed Policy & Reproducibility (Constitution I)
To ensure scientific reproducibility, all stochastic components of the pipeline are pinned to a single global seed defined in `code/seeds.py`:
- **Seed Value**: `SEED = 42`
- **Scope**: This seed governs Monte-Carlo power analysis (T002), dataset sampling (T004), LLM generation (T006, `do_sample=False`), the zero-shot classifier (T008), and bootstrap resampling (T009).
- **Verification**: Re-running any stage will produce identical results. [UNRESOLVED-CLAIM: c_8eaf98c7 — status=not_enough_info]

## Data Hygiene
The pipeline maintains a manifest at `data/metadata.yaml` containing SHA-256 checksums and provenance notes for all artifacts.
- **Immutability**: Files in `data/raw/` are treated as immutable. Any modification to these files will cause the pipeline to fail loudly during the hygiene check to prevent silent data corruption.

## Quick smoke test (Phase 0)
```bash
python -m code.run_pipeline --sample 5
```
This loads one tiny hard-coded commit pair (a plumbing smoke test only), invokes the CPU-only generation module, and writes `data/generated/phi3-mini/sample_test.txt`. It completes in well under 30 seconds [UNRESOLVED-CLAIM: c_045c75b4 — status=not_enough_info] and requires no model downloads.

## Power analysis (Phase 1)
```bash
python -m code.power_analysis
```
Runs the Monte-Carlo power analysis for the Friedman test (T002) with the pinned seed and writes `results/power_report.md`. The report contains the estimated power for n = 500 and an `exploratory` flag that is `true` exactly when the estimated power is below 0.8.

## Running the Full Pipeline
```bash
python -m code.run_pipeline --full
```
**What happens:**
1. The Monte-Carlo power analysis runs → `results/power_report.md`.
2. Repositories (`pandas`, `requests`, `scikit-learn`, `flask`, `django`) are cloned.
3. Commits from the last two years that touch `.md`/`.rst` are extracted → `data/raw/commit_pairs.csv`.
4. A random subset is sampled for gold-standard annotation.
5. Each LLM (Phi-3-mini, Gemma-2-2b, Llama-3.2-3B) generates a documentation update per commit on CPU, with a 60 s timeout, up to 2 retries.
6. Entities are extracted, verified (regex + AST + `git grep`), and fidelity metrics are computed.
7. Statistical tests (Friedman/ANOVA, honoring the power report's `exploratory` flag) and visualizations are saved under `results/`.

## Inspecting Results
- **Power analysis**: `results/power_report.md`.
- **Dataset**: `data/raw/commit_pairs.csv`.
- **Generated outputs**: `data/generated/<model_id>/`.
- **Metrics**: `data/processed/fidelity_metrics.csv`.
- **Figures**: `results/figures/intent_precision_bar.png`, `results/figures/surface_confusion_matrix.png`.
- **Summary report**: `results/summary.md`.

## Running the tests
```bash
pytest tests/quickstart_test.py tests/test_power_analysis.py tests/test_hygiene_and_seeds.py
```