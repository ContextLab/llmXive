# Implementation Plan: Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases  

**Branch**: `001-predicting-corrosion-rates-of-common-met` | **Date**: 2026-10-22 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `/specs/001-predicting-corrosion-rates-of-common-met/spec.md`

## Summary
The project will (1) ingest a publicly‑available tabular corrosion dataset, (2) validate required columns, (3) harmonize corrosion‑rate units to mm / year, (4) impute missing values, (5) one‑hot encode material composition and standardize numeric predictors, (6) engineer pairwise interaction features between environmental variables and composition one‑hots (plus low‑order polynomials), (7) train constrained Random‑Forest and Gradient‑Boosting regressors under a group‑aware 5‑fold CV scheme, (8) compare a **Full** model (with interactions) to a **Null** model (without interactions) using a **paired sign‑flip permutation test**, (9) compute permutation‑importance p‑values for each interaction column and adjust with Benjamini‑Hochberg, (10) generate SHAP interaction values and partial‑dependence plots for the top interactions, (11) perform hyper‑parameter stability analysis, and (12) assemble a reproducible report. All steps run on the CPU‑only GitHub Actions free tier (2 vCPUs, ≈7 GB RAM, ≤ 6 h wall‑time).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (exact pins, mirrored in `code/requirements.txt`):  
  ```
  pandas==2.2.2
  numpy==2.0.0
  scikit-learn==1.5.0
  shap==0.45.0
  statsmodels==0.14.2
  datasets==2.19.1
  psutil==5.9.8
  pyyaml==6.0.1
  openml==0.14.2
  tqdm==4.66.2
  joblib==1.4.2
  ```
- **Storage**: File‑system under `data/`, `metadata/`, `outputs/`.  
- **Testing**: `pytest==8.2.2` (contract and unit tests).  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Constraints**: CPU‑only, `max_depth ≤ 5`, `n_estimators ≤ 200`, GroupKFold CV, Benjamini‑Hochberg correction, Jaccard stability ≥ 0.8, wall‑time ≤ 6 h, RAM ≤ 7 GB.  

## Constitution Check
| Principle | How Plan Satisfies |
|-----------|-------------------|
| I. Reproducibility | Fixed seeds (`np.random.seed(42)`, `random_state=42`). All external files fetched via deterministic URLs (or are version‑controlled). SHA‑256 checksums recorded in `metadata/`. |
| II. Verified Accuracy | No external citations beyond the verified dataset URL (provided by the verifier). |
| III. Data Hygiene | Raw CSV never overwritten; each transformation writes a new file with provenance recorded (`metadata/`). |
| IV. Single Source of Truth | Every figure/table is generated from `cleaned_dataset.csv`, `features.parquet`, and `model_artifact.yaml`. |
| V. Versioning Discipline | All artifacts hashed (SHA‑256) and referenced in `metadata/`. |
| VI. Interaction‑Effect Quantification | Interaction columns are engineered explicitly; SHAP interaction values and permutation‑importance p‑values quantify their contribution (FR‑004, FR‑012). |
| VII. Tabular Data Integrity & Environmental Normalization | Required environmental columns are validated, standardized, and GroupKFold splits prevent batch leakage (FR‑001, FR‑009). |

## Entity Mapping (to `data-model.md`)
* **CorrosionRecord** → `data/processed/cleaned_dataset.csv` (FR‑001, FR‑008, FR‑011).  
* **InteractionFeature** → `data/processed/features.parquet` + `data/processed/feature_names.txt` (FR‑002, FR‑007).  
* **DatasetMetadata** → `metadata/dataset.yaml` (FR‑011).  
* **ModelArtifact** → `data/results/model_artifact.yaml` (FR‑003, FR‑010).  

## Project Structure
```text
specs/001-predicting-corrosion-rates-of-common-met/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── cleaned_dataset.schema.yaml
    └── model_artifact.schema.yaml

src/
├── pipeline/
│   ├── __init__.py
│   ├── ingest.py          # FR‑001, FR‑008, FR‑011, FR‑006 (VIF)
│   ├── features.py        # FR‑002, FR‑007
│   ├── split.py           # FR‑009, FR‑010
│   ├── train.py           # FR‑003, FR‑010
│   ├── evaluate.py        # FR‑002, FR‑005, FR‑012, SC‑002
│   ├── interpret.py       # FR‑004
│   ├── sensitivity.py     # FR‑006, FR‑007, SC‑005
│   ├── vif.py             # FR‑006 (VIF computation)
│   └── utils.py
├── requirements.txt       # exact pins, mirrored to code/requirements.txt
└── run_all.py             # orchestrates all phases
```

## Phase‑wise Implementation Tasks
| Phase | FR/SC addressed | Description | Expected Output(s) | Runtime |
|-------|----------------|-------------|--------------------|---------|
| **0 – Requirements Sync** | – | Copy `src/requirements.txt` to `code/requirements.txt` ensuring byte‑identical content. | `src/requirements.txt`, `code/requirements.txt` | < 1 min |
| **1 – Data Ingestion & Hygiene** | FR‑001, FR‑008, FR‑011, FR‑006 | Load CSV, verify required columns, harmonize corrosion‑rate units, median/mode imputation, one‑hot encode `composition`, standardize numerics, compute VIF for base predictors (exclude interactions). | `data/processed/cleaned_dataset.csv`, `metadata/dataset.yaml`, `data/results/vif_diagnostics.json` | ≤ 20 min |
| **2 – Interaction Feature Engineering** | FR‑002, FR‑007 | Create pairwise products among (pH, salinity, temperature) and each one‑hot composition column; add degree‑2 polynomials for env variables; residualize interactions against main effects; write feature matrix and plain‑text list. | `data/processed/features.parquet`, `data/processed/feature_names.txt` | ≤ 10 min |
| **3 – Group‑aware Splitting** | FR‑009, FR‑010 | Perform 5‑fold GroupKFold on `source_id` with stratified balance of composition one‑hots; serialize indices. | `data/processed/splits.pkl` | ≤ 5 min |
| **4 – Model Training (Full & Null)** | FR‑003, FR‑010 | For each CV fold, train (a) Full model **with** interaction columns and (b) Null model **without** them, respecting `max_depth ≤ 5`, `n_estimators ≤ 200`. Select best model by mean CV R². | `data/results/best_full_model.joblib`, `data/results/best_null_model.joblib`, `data/results/model_artifact.yaml` | ≤ 2 h |
| **5 – Interaction‑Gain Significance (Paired Sign‑Flip Test)** | FR‑002, FR‑005, FR‑012, SC‑002 | Compute RMSE on held‑out test set for Full and Null per fold. Observed statistic = mean ΔRMSE (Null − Full). Generate null distribution by **sign‑flipping** the Full/Null labels within each fold 1 000 times. Two‑sided p‑value reported; BH correction trivial (single test). | `data/results/interaction_gain_test.json` (contains observed ΔRMSE, p‑value) | ≤ 30 min |
| **6 – Permutation‑Importance per Interaction** | FR‑012, FR‑005, SC‑004 | For each engineered interaction column, shuffle its values 200 times, re‑evaluate the Full model, record ΔRMSE; empirical p‑value = proportion of shuffled ΔRMSE ≤ observed. Apply Benjamini‑Hochberg across all interactions. | `data/results/interaction_permutation_importance.json` (raw p‑values & BH‑adjusted) | ≤ 45 min |
| **7 – Interpretability (SHAP)** | FR‑004 | Compute SHAP interaction values for the top‑5 interaction features (by absolute mean SHAP). Generate (i) summary plot, (ii) dependence plots for each top interaction, (iii) partial‑dependence curves. Save PNGs. | `outputs/figures/shap_summary.png`, `outputs/figures/shap_dep_<interaction>.png`, `outputs/figures/pdp_<interaction>.png` | ≤ 45 min |
| **8 – Sensitivity & Diagnostics** | FR‑006, FR‑007, SC‑005 | Re‑compute VIF including interactions (diagnostic only). Sweep `max_depth` ∈ {3,4,5} (keep other hyperparameters fixed); for each depth record top‑5 feature list; compute pairwise Jaccard similarity, require ≥ 0.8. | `data/results/sensitivity.json` (Jaccard scores, VIF report) | ≤ 20 min |
| **9 – Reporting & Provenance** | SC‑001, SC‑003, SC‑006, SC‑007 | Assemble `report.md` with (a) baseline vs. Full performance (R², RMSE), (b) paired sign‑flip test result, (c) BH‑adjusted interaction importance, (d) SHAP visualisations, (e) hyper‑parameter stability, (f) explicit associational disclaimer, (g) runtime & memory summary. | `report.md` | ≤ 10 min |
| **10 – Verification** | – | Run `pytest src/tests/` to validate contracts (`cleaned_dataset.schema.yaml`, `model_artifact.schema.yaml`) and that each pipeline module executes without error. CI aborts on failure. | Test report (stdout) | ≤ 5 min |

All phases are ordered so that data is produced before downstream steps, models before interpretation, and figures before reporting.

---
