# Quickstart: Running the LLM Fidelity Evaluation Pipeline

## Prerequisites
- Python 3.11 installed.
- Internet access (required for cloning repositories and downloading model weights).
- CPU‑only runner (2 CPU cores, ~7 GB RAM is sufficient; no GPU is used anywhere — NFR‑001).
- A **GitHub personal access token** (optional but recommended) to increase API rate limits.

## Required Python 3.11 packages
Install the exact versions listed below to guarantee reproducibility.
Save the list to `requirements.txt` (already present) and run:

```text
torch>=2.0
bitsandbytes
transformers
datasets
pandas
scikit-learn
statsmodels
matplotlib
seaborn
tqdm
regex
pyyaml
gitpython
```

```bash
pip install -r requirements.txt
```

## Model‑inference dependencies (CPU‑only, 4‑bit quantization)
```bash
pip install transformers bitsandbytes
```
`transformers` and `bitsandbytes` are needed for the model‑inference stage (T006); the Phase‑0 smoke test and the power analysis run without them.

## Setting the GitHub token
The data‑extraction stage uses the GitHub REST API. Supplying a token avoids strict unauthenticated rate limits.

```bash
export GITHUB_TOKEN="ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```
If the variable is not set, the extraction script will abort with a clear error message.

## Seed policy (Constitution I)
All stochastic components use the single pinned seed `SEED = 42` defined in `code/seeds.py`:

- Monte‑Carlo power analysis (T002)
- Dataset sampling (T004)
- LLM generation (`do_sample=False`) (T006)
- Zero‑shot classifier calibration (T008)
- Any bootstrap resampling (T009)

Re‑running any stage reproduces identical results. [UNRESOLVED-CLAIM: c_3924e858 — status=not_enough_info]

## Quick smoke test (Phase 0)
```bash
python -m code.run_pipeline --sample 5
```
This loads a tiny hard‑coded commit pair (a plumbing smoke test only — never analysis data), invokes the CPU‑only generation module, and writes `data/generated/phi3-mini/sample_test.txt`. It completes in well under 30 seconds and requires no model downloads.

## Power analysis (Phase 1)
```bash
python -m code.power_analysis
```
Runs the Monte‑Carlo power analysis for the Friedman test (T002) with the pinned seed and writes `results/power_report.md`. The report contains the estimated power for *n* = 500 and an `exploratory` flag that is `true` exactly when the estimated power is below 0.8; downstream statistical reporting (T010) honors this flag.

## Running the Full Pipeline
```bash
python -m code.run_pipeline --full
```
**What happens:**
1. The Monte‑Carlo power analysis runs → `results/power_report.md`.
2. Repositories (`pandas`, `requests`, `scikit-learn`, `flask`, `django`) are cloned (cached on subsequent runs).
3. Commits from the last two years that touch `.md`/`.rst` are extracted → `data/raw/commit_pairs.csv`.
4. A random subset is sampled for gold‑standard annotation.
5. Each LLM (Phi‑3‑mini, Gemma‑2‑2b, Llama‑3.2‑3B) generates a documentation update per commit on CPU, with a 60 s timeout and up to 2 retries.
6. Entities are extracted, verified (regex + AST + `git grep`), and fidelity metrics are computed.
7. Statistical tests (Friedman/ANOVA with Holm‑Bonferroni correction, honoring the power‑report’s `exploratory` flag) and visualizations are saved under `results/`.

Until the remaining tasks land, `--full` runs every implemented stage (currently the Phase‑0 smoke test and Phase‑1 power analysis), reports the not‑yet‑implemented stages as pending, and exits successfully so the run‑book stays executable at every point in the project.

## Inspecting Results
- **Power analysis**: `results/power_report.md`.
- **Dataset**: `data/raw/commit_pairs.csv` (validated against `contracts/commitpair.schema.yaml`).
- **Generated outputs**: `data/generated/<model_id>/`.
- **Metrics**: `data/processed/fidelity_metrics.csv` (validated against `contracts/fidelity.schema.yaml`).
- **Figures**: `results/figures/intent_precision_bar.png`, `results/figures/surface_confusion_matrix.png`.
- **Summary report**: `results/summary.md`.

## Running the tests
```bash
pytest tests/test_quickstart.py
```
The test invokes the pipeline via `subprocess`, checks that the expected artefacts are created, and writes a short log file `logs/quickstart_run.log`.

## CI Execution
The repository includes a GitHub Actions workflow (`.github/workflows/research.yml`) that automatically runs the full CPU‑only pipeline on every push, caches model weights, and uploads artefacts. No manual intervention is required.
