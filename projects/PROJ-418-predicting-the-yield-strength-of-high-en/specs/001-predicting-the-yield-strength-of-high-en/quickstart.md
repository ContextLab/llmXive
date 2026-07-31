# Quickstart: Predicting Yield Strength of High‑Entropy Alloys

Follow these steps to reproduce the full analysis on a fresh GitHub Actions runner (or locally on Linux/macOS).

## 1. Clone the Repository
```bash
git clone https://github.com/your-org/PROJ-418-predicting-the-yield-strength-of-high-en.git
cd PROJ-418-predicting-the-yield-strength-of-high-en
```

## 2. Set Up the Python Environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

## 3. Verify Dataset Availability
The pipeline will attempt to download the open HEA yield‑strength dataset (see `research.md`). **If a verified dataset cannot be fetched**, the script will abort with a clear error and the rest of the pipeline will not run. No manual download is required beyond this step.

## 4. Run the Full Pipeline
```bash
python code/run_pipeline.py
```
`run_pipeline.py` orchestrates the following stages (see `plan.md` for mapping):
1. `download_data.py` – downloads **and validates** the raw dataset against `contracts/dataset.schema.yaml`.  
2. `compute_descriptors.py` – computes descriptors, validates elemental properties (`contracts/elemental_properties.schema.yaml`), and validates the merged composition (`contracts/hea_composition.schema.yaml`).  
3. `train_model.py` – performs hyper‑parameter grid search and fits the final RandomForest.  
4. `validate_cv.py` – outer k‑fold cross‑validation.  
5. `bootstrap_ci.py` – bootstrap confidence intervals.  
6. `perm_importance.py` – permutation importance with exactly 1000 permutations and Benjamini‑Hochberg FDR correction.  
7. `shap_analysis.py` – Kernel SHAP on a representative set of samples (≤ 200).  
8. `generate_report.py` – assembles `reports/report.md` with all metrics, CI, importance plots, and the conditional “Data Limitation Warning”.

All intermediate artefacts are stored under `data/` and checksummed automatically.

## 5. Inspect the Results
- The final report is at `reports/report.md`.  
- Figures are in `data/figures/` (permutation importance, SHAP summary).  
- Checksums are listed in `state/projects/PROJ-418-predicting-the-yield-strength-of-high-en.yaml`.

## 6. Run the Test Suite
```bash
pytest -q
```
The suite validates:
- Schema compliance for all contracts (including the newly added elemental and HEA‑composition schemas).  
- Reproducibility (fixed seeds, deterministic outputs).  
- Success criteria (R² ≥ 0.6, CI width ≤ 0.1, etc.).

## 7. (Optional) Re‑run with a Subsample
If you wish to execute faster (e.g., for debugging), set `MAX_SAMPLES` in `code/config.yaml` to a lower number; the pipeline will respect this limit while still using 1000 permutations for importance.

## 8. Clean Up
```bash
deactivate
rm -rf .venv
```

All steps are fully automated; no manual intervention is required after cloning the repository.

---



