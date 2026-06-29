# Quickstart: Brain Network Dynamics ↔ Tactile Discrimination

This guide shows how to run the full pipeline on the GitHub Actions CI or locally on a Linux machine.

## Prerequisites
- Python 3.11 (or newer) installed.
- Git 2.40+
- Sufficient disk space (on the order of several gigabytes) for dataset download.
- Internet access to the verified HuggingFace URL for the HCP dataset.

## 1. Clone the Repository
```bash
git clone
cd brainnet-tactile
```

## 2. Create a Virtual Environment & Install Dependencies
```bash
python -m venv.venv
source.venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt # pins exact versions (CPU‑only wheels)
```

## 3. Run the End‑to‑End Pipeline
```bash
# The CLI supports sub‑commands; the default runs all phases.
# In CI we limit the number of subjects to a level that stays within the RAM/time budget.
python -m brainnet.run_all \
 --max-subjects 100 \ # CI subset for validation
 --seed <chosen seed> # reproducibility
```
The command performs:
1. **Dataset validation** (HCP only; aborts if tactile scores are missing).
2. **Preprocessing** of fMRI.
3. **Static & dynamic metric computation** (including flexibility).
4. **Statistical analysis** (power, VIF, partial correlations, FDR, sensitivity).
5. **Result packaging** into `results/` and contract validation.

### Full‑Scale Local Run
For a definitive analysis that meets the a‑priori power target (N ≈ adequate sample size to achieve the planned statistical power), run the pipeline without the `--max-subjects` limit on a machine with sufficient RAM (≥ 8 GB) and allow the full HCP cohort (a large number of subjects) to be processed:

```bash
python -m brainnet.run_all --seed 42
```

## 4. Inspect the Outputs
- `results/report.md` – full markdown report ready for inclusion in the manuscript.
- `results/figures/` – PNG/SVG files for plots.
- `data/processed/` – Parquet files for static metrics, `.npz` for dynamic series.
- `metadata/` – JSON provenance files.
- `contracts/` – schema files; CI runs `jsonschema` checks automatically.

## 5. Run the Test Suite (optional)
```bash
pytest -vv
```
All unit tests must pass; contract tests are located under `tests/contract/`.

## 6. CI Execution
The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:
- Sets up the Python environment using `requirements.txt`.
- Executes `python -m brainnet.run_all --max-subjects 100`.
- Checks that total wall‑clock time ≤ 6 h and peak RAM ≤ 6.5 GB (via `psutil`).
- Validates all output files against the schemas in `contracts/`.

If any check fails, the CI job aborts, protecting reproducibility (Principle I).

---

