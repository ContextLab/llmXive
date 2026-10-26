# Implementation Plan: Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases

**Branch**: `001-predicting-corrosion-rates-of-common-met` | **Date**: 2026-10-25 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `/specs/001-predicting-corrosion-rates-of-common-met/spec.md`

## Summary
The project will (1) ingest a version‑controlled, publicly‑available corrosion dataset, (2) validate required columns, (3) harmonize corrosion‑rate units to mm / year, (4) impute missing values, (5) one‑hot encode material composition and standardize numeric predictors, (6) engineer explicit pairwise interaction features, (7) perform a group‑aware 5‑fold CV split, (8) train constrained Random‑Forest (and optionally Gradient‑Boosting) models for a **Full** (with interactions) and a **Null** (without interactions) version, (9) assess the incremental value of interactions with a **target‑permutation test** (shuffling the response variable), (10) compute **conditional permutation‑importance** p‑values for each interaction column and adjust them with Benjamini‑Hochberg, (11) generate SHAP interaction values and partial‑dependence plots for the top interactions, (12) run a hyper‑parameter stability analysis, (13) evaluate a baseline mean‑only predictor and compare it to the Full model to satisfy SC‑001, (14) assemble a reproducible report. All steps run on the CPU‑only GitHub Actions free tier (2 vCPUs, ≈7 GB RAM, ≤ 6 h wall‑time).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (exact pins, mirrored in `code/requirements.txt`):  

```text
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

- **Storage**: Files under `data/`, `metadata/`, `outputs/`.  
- **Testing**: `pytest==8.2.2` (contract and unit tests).  
- **Constraints** (per FR‑003): `max_depth ≤ 5`, `n_estimators ≤ 200`; no GPU libraries.  
- **Compute**: CPU‑first; if RSS > 7 GB a stratified sample (seed 42) is drawn automatically (FR‑003).  

## Constitution Check
| Principle | How Plan Satisfies |
|-----------|-------------------|
| I. Reproducibility | Fixed seeds (`np.random.seed(42)`, `random_state=42`). All external files fetched from deterministic URLs (or are version‑controlled). SHA‑256 checksums recorded in `metadata/dataset.yaml`. |
| II. Verified Accuracy | No external citations beyond the verified dataset URL (the CSV is stored in the repo). |
| III. Data Hygiene | Raw CSV never overwritten; each transformation writes a new file with provenance recorded (`metadata/`). |
| IV. Single Source of Truth | Every figure/table is generated from `cleaned_dataset.csv`, `features.parquet`, and `model_artifact.yaml`. |
| V. Versioning Discipline | All artifacts hashed (SHA‑256) and referenced in `metadata/`. `src/requirements.txt` and `code/requirements.txt` are byte‑identical. |
| VI. Interaction‑Effect Quantification | Interaction columns are engineered explicitly; SHAP interaction values and conditional permutation‑importance quantify their contribution (FR‑004, FR‑012). |
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
│   ├── clean.py           # FR‑008 (imputation, scaling, encoding)
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
| Phase | FR/SC addressed | Description | Expected Output(s) | Approx. Runtime |
|-------|----------------|-------------|--------------------|-----------------|
| **0 – Requirements Sync** | – | Copy `src/requirements.txt` to `code/requirements.txt` ensuring byte‑identical content. | `src/requirements.txt`, `code/requirements.txt` | < 1 min |
| **1 – Data Ingestion & Hygiene** | FR‑001, FR‑008, FR‑011, FR‑006 | Load `data/raw/sample_corrosion.csv`, validate required columns, harmonize corrosion‑rate units to mm/yr, median/mode imputation, one‑hot encode `composition`, standardize numerics, compute VIF for base predictors (exclude interactions). | `data/processed/cleaned_dataset.csv`, `metadata/dataset.yaml`, `data/results/vif_diagnostics.json` | ≤ 20 min |
| **2 – Interaction Feature Engineering** | FR‑002, FR‑007 | Create pairwise products among (pH, salinity, temperature) and each one‑hot composition column; add degree‑2 polynomials for env variables; write feature matrix and plain‑text list. | `data/processed/features.parquet`, `data/processed/feature_names.txt` | ≤ 10 min |
| **3 – Group‑aware Splitting** | FR‑009, FR‑010 | Perform 5‑fold GroupKFold on `source_id`; serialize split indices. | `data/processed/splits.pkl` | ≤ 5 min |
| **4 – Model Training (Full & Null)** | FR‑003, FR‑010 | For each CV fold, train (a) Full model **with** interaction columns and (b) Null model **without** them, respecting `max_depth ≤ 5`, `n_estimators ≤ 200`. Select best model by mean CV R². **Optional exploratory sweep** with relaxed limits (`max_depth ≤ 6`, `n_estimators ≤ 250`) is run only for diagnostic power analysis and does **not** affect primary claims. | `data/results/best_full_model.joblib`, `data/results/best_null_model.joblib`, `data/results/model_artifact.yaml` | ≤ 2 h |
| **5 – Baseline Mean‑Only Model** | SC‑001 | Compute predictions using the training‑set mean corrosion rate; evaluate R² and RMSE on each test fold; store results for comparison with Full model. | `data/results/baseline_performance.json` | ≤ 5 min |
| **6 – Interaction‑Gain Target‑Permutation Test** | FR‑002, FR‑005, FR‑012, SC‑002 | For each CV fold compute RMSE_Full and RMSE_Null. Shuffle the **target variable y** 1 000 times, refit Full and Null on each permuted set, record ΔRMSE = RMSE_Null − RMSE_Full per permutation; two‑sided p‑value = proportion of |ΔRMSE| ≥ observed. | `data/results/interaction_gain_test.json` (ΔRMSE, p‑value) | ≤ 30 min |
| **7 – Conditional Permutation‑Importance per Interaction** | FR‑012, FR‑005, SC‑004 | For each engineered interaction column, orthogonalize it against its constituent base features (regress out base features, keep residuals). Shuffle the residuals **1 000 times**, re‑evaluate the Full model, compute ΔRMSE. Empirical p‑value = proportion of shuffled ΔRMSE ≥ observed (upper‑tail). Apply Benjamini‑Hochberg across all interactions. | `data/results/interaction_permutation_importance.json` (raw & BH‑adjusted p‑values) | ≤ 45 min |
| **8 – Interpretability (SHAP)** | FR‑004 | Compute SHAP interaction values for the top‑5 interaction features (by absolute mean SHAP). Generate (i) summary plot, (ii) dependence plots for each top interaction, (iii) partial‑dependence curves. Save PNGs. | `outputs/figures/shap_summary.png`, `outputs/figures/shap_dep_<interaction>.png`, `outputs/figures/pdp_<interaction>.png` | ≤ 45 min |
| **9 – Sensitivity & Diagnostics** | FR‑006, FR‑007, SC‑005 | Re‑compute VIF including interactions (diagnostic only). Sweep `max_depth` ∈ {3, 4, 5} (keep other hyper‑parameters fixed). For each depth record top‑5 feature list; compute pairwise Jaccard similarity, require ≥ 0.8. **Optional exploratory sweep** with relaxed limits (`max_depth ≤ 6`, `n_estimators ≤ 250`) is performed only for power diagnostics. | `data/results/sensitivity.json` (Jaccard scores, VIF report, optional exploratory results) | ≤ 20 min |
| **10 – Reporting & Provenance** | SC‑001, SC‑003, SC‑006, SC‑007 | Assemble `report.md` with (a) baseline vs. Full performance (R², RMSE), (b) target‑permutation test result, (c) BH‑adjusted interaction importance, (d) SHAP visualisations, (e) hyper‑parameter stability, (f) explicit associational disclaimer, (g) runtime & memory summary. | `report.md` | ≤ 10 min |
| **11 – Verification** | – | Run `pytest src/tests/` to validate contracts (`cleaned_dataset.schema.yaml`, `model_artifact.schema.yaml`) and that each pipeline module executes without error. CI aborts on failure. | Test report (stdout) | ≤ 5 min |

All phases are ordered so that data is produced before downstream steps, models before interpretation, and figures before reporting.
