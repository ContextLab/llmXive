# Quickstart: Running the LLM Fidelity Evaluation Pipeline

## Prerequisites
- **Python** 3.11 (exact version required for reproducibility).  
- Internet access (to clone repositories and download model weights).  
- A GitHub personal access token (optional but recommended to increase API rate limits).  
- CPU‑only environment (2 CPU cores, ~7 GB RAM; no GPU needed).

## Required Packages
```text
requests==2.32.3
gitpython==3.1.43
datasets==2.20.0
transformers==4.44.2
bitsandbytes==0.44.1
torch==2.4.0
scikit-learn==1.5.2
scipy==1.14.1
statsmodels==0.15.0
matplotlib==3.9.2
seaborn==0.13.2
pandas==2.2.3
pyyaml==6.0.2
tqdm==4.66.5
regex==2024.9.11
astor==0.8.1
```
Save the above list to `requirements.txt` (already present) and install with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Seed Policy (Constitution I)
All stochastic operations use the single global seed defined in `src/utils.py`:

```python
SEED = 42
```

This seed controls:
- Random sampling of commits,
- Monte‑Carlo power analysis,
- Bootstrap resampling for confidence intervals,
- Zero‑shot classifier deterministic inference (`do_sample=False`).

Re‑running any stage with the same seed yields identical results.

## Step‑by‑Step Execution

### 1. Smoke Test (Phase 0)
Runs a minimal end‑to‑end pass on a small set of synthetic commit pairs to verify the pipeline wiring.

```bash
python -m src.run_pipeline --sample 5
```

Expected outcome:
- `data/raw/commit_pairs.csv` with a modest number of rows,
- `data/processed/fidelity_metrics.csv` with several rows,
- All contract tests pass (`pytest tests/contract/`).

### 2. Power Analysis (Phase 0)
```bash
python -m src.analysis.power_analysis
```
Creates `results/power_report.md` with the estimated power for a representative sample size. The report is automatically included in the final summary.

### 3. Full Pipeline (CPU‑only)
```bash
python -m src.run_pipeline --full
```
What happens:

1. **Power analysis** (writes `results/power_report.md`).  
2. **Data extraction** – clones the five repos (cached) and pulls commit/diff pairs via the GitHub API; writes `data/raw/commit_pairs.csv`.  
3. **Gold annotation** – samples a representative set of commits, expects two CSV files `data/gold/annotator_A.csv` and `data/gold/annotator_B.csv`; computes κ and writes `data/gold/annotations.csv`.  
4. **Model inference** – loads each model in 4‑bit CPU mode, generates docs for a **default stratified subset of 100 samples per model** (adjustable via `--samples N`). Generation respects the 60 s timeout, retries up to 2×, and logs outcomes in `data/generated/<model_id>/generation_log.txt`. Each generated file is validated against the `GeneratedOutput` schema.  
5. **Entity extraction** – writes JSON files under `data/intermediate/surface_entities/` and `data/intermediate/intent_entities/`. All JSON conforms to the `EntitySet` definition in `project.schema.yaml`.  
6. **Scoring** – aggregates metrics into `data/processed/fidelity_metrics.csv` (validated against `FidelityMetric` schema).  
7. **Statistical analysis** – writes `results/statistics.json` and a human‑readable `results/statistics.md`.  
8. **Visualization** – creates PNGs `results/figures/intent_precision_bar.png` and `results/figures/surface_confusion_matrix.png`.  
9. **Summary** – assembles `results/summary.md` linking to figures and tables.  
10. **Verification** – runs `pytest` (unit + contract tests); computes SHA‑256 checksums for all files under `data/` and records them in `data/metadata.yaml`.

### 4. Running the Test Suite
```bash
pytest tests/contract/
pytest tests/unit/
```
All tests must pass before committing. The contract tests ensure every output file conforms to the JSON/YAML schemas in `contracts/`.

### 5. Inspecting Results
- **Power analysis**: `results/power_report.md`  
- **Dataset**: `data/raw/commit_pairs.csv` (validated against `CommitPair`)  
- **Generated docs**: `data/generated/<model_id>/`  
- **Metrics**: `data/processed/fidelity_metrics.csv` (validated against `FidelityMetric`)  
- **Figures**: `results/figures/intent_precision_bar.png`, `results/figures/surface_confusion_matrix.png`  
- **Summary**: `results/summary.md`

## Model Compatibility Table
| Model | CPU‑only Compatibility | Approx. Parameter Count |
|-------|------------------------|--------------------------|
| Phi‑3‑mini | ✅ (4‑bit quantized) | ~3 B |
| Gemma‑2‑2b | ✅ (4‑bit quantized) | ~2 B |
| Llama‑3.2‑3B | ✅ (4‑bit quantized) | ~3 B |

## Scale‑Limitation Note
The default run processes a **representative subset of 100 samples per model**, which is **comparable** to the full‑scale analysis and ensures the pipeline finishes within the CI time limit. For a **similar** full‑scale analysis (≥500 samples), invoke `python -m src.run_pipeline --full --samples 500`; this will require additional wall‑clock time and may approach the CI limit.

## Optional: Full‑Scale Run
If you have more compute time, process the entire sample set:

```bash
python -m src.run_pipeline --full --samples 500
```

The pipeline will automatically adjust the CI timeout handling; the same artifacts will be produced but may require more wall‑clock time.

## Quickstart Test Verification
A dedicated pytest file `tests/test_quickstart.py` runs the above commands in a temporary environment and asserts successful exit codes and the existence of all expected output files. The CI logs the test run; a passing test confirms the quickstart guide is functional.

---

