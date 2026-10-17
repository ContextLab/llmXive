# Quickstart: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Prerequisites

- Python 3.11+, `git`, internet access (HuggingFace `datasets` fetch of OQMD)
- ~7 GB RAM, ~14 GB disk, CPU‑only

## Installation

```bash
git clone <repository-url>
cd PROJ-355-predicting-the-impact-of-impurity-cluste
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` pins: `datasets`, `pymatgen`, `ase`, `scikit-learn`, `statsmodels`, `numpy`, `pandas`, `matplotlib`, `pyyaml`, `pytest`.

## Run the Full Pipeline

```bash
python -m code.main --mode full
```

This sequentially:
1. Loads real OQMD records via `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")` (verified recipe; ≤3 retries, `[DATA_UNAVAILABLE]` on permanent failure) and checksums them into `data/raw/`.
2. **Reconstructs bulk structures** from formula + `volume_per_atom` using pymatgen prototypes (the OQMD records do not contain atomic coordinates; this synthetic reconstruction is documented in `data/metadata.yaml`).  
   *Note*: The spec originally called for downloading full bulk configuration files from the Materials Project **and** OQMD. The Materials Project requires authentication and is not reachable on the free CI runner; therefore the pipeline uses **only** the OQMD dataset, a justified deviation recorded in the implementation plan.
3. Builds GB supercells, inserting impurities at the interface; zero‑impurity cases filtered and counted.
4. Computes RDF peaks, pair‑correlation statistics, and Voronoi neighbor counts **after** EAM relaxation, only in the interface region; runs VIF diagnostics (threshold 10) before any dimensionality reduction and writes the collinearity JSON report.
5. Simulates ≥200 leave‑one‑out segregation energies with validated EAM potentials for three alloy systems (Fe‑Cr, Ni‑Al, Cu‑Zn); excludes missing‑energy entries with counts (>5 % warning).
6. Runs the FR‑011 EAM‑vs‑DFT validation harness (≥30 samples, MAE ≤ 0.1 eV) — reports `[DATA_UNAVAILABLE]` with a structured limitation if no verified DFT benchmark is present.
7. Assembles `data/processed/training_set.csv` (schema‑validated; ≥200 samples, ≥3 alloy systems, ≥50 test samples).
8. Performs the FR‑010 linearity assessment (scatter plots + residuals).
9. Trains Linear Regression (with robust‑SE coefficient p‑values) **and** RandomForest under 5‑fold CV (LOOCV if N < 5); reports R², RMSE, 95 % prediction CIs, per‑system R², and permutation‑test p‑values.
10. Runs the FR‑008 power analysis (f² = 0.15, α = 0.05, 7 predictors, power ≥ 0.80) and compares required vs. achieved N.
11. Applies Bonferroni/FDR correction; writes `results/hypothesis_report.json` (raw/adjusted p‑values, significance‑change count, textual summary).
12. Generates `results/cluster_size_vs_segregation.png` (per‑alloy‑system, 95 % CIs).
13. Writes schema‑validated `results/metrics.json`.

## Inspect Results

```bash
cat results/metrics.json
cat results/hypothesis_report.json
ls results/cluster_size_vs_segregation.png
```

## Run Tests

```bash
pytest tests/
```

The integration test verifies the CONTENT of `.gitignore` (must contain `data/`, `results/`, `*.pyc`, `__pycache__/`) and of `README.md` (project title, execution instructions, data‑provenance section citing the verified OQMD loader), and runs the pipeline end‑to‑end plus the validation harness.

## CI Execution

The platform runner executes `python -m code.main --mode ci` with a reduced sample size, staying within the 6‑hour CPU budget; all artifacts are validated against the contracts.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `[DATA_UNAVAILABLE]` after 3 retries | Check network/HuggingFace access; the verified loader is `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")` |
| VIF ≥ 10 warnings | Expected for definitionally related descriptors; consult the collinearity JSON report — relationships are framed descriptively, predictors are not removed |
| Validation reports `DATA_UNAVAILABLE` | No verified open DFT benchmark exists; this is a recorded limitation, not an error to work around |
| Power shortfall (achieved N < required N) | Logged honestly in `metrics.json`; increase the OQMD sample size if budget allows |
| Results seem overly optimistic | Remember that all relationships are **associational within the EAM‑potential internal physics** (see Scope Limitation). |