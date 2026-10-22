# Implementation Plan: Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases

**Branch**: `001-predicting-corrosion-rates-of-common-met` | **Date**: 2026-10-22 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `/specs/001-predicting-corrosion-rates-of-common-met/spec.md`

## Summary
The project will ingest a publicly‑available tabular corrosion dataset (provided as a CSV in `data/raw/` by the verifier), validate that all required columns exist, harmonize units, impute missing values, and one‑hot encode material descriptors. Interaction features between environmental variables and material one‑hots will be engineered, then constrained Random Forest and Gradient Boosting regressors will be trained under a Group‑aware 5‑fold CV scheme. A **paired sign‑flip permutation test** will compare the Full model (with interactions) to a Null model (without interactions). Permutation‑importance p‑values for each interaction column will be obtained and corrected with Benjamini‑Hochberg. SHAP interaction values will be computed for the top interactions, and a hyper‑parameter stability analysis will be performed. All phases run on the CPU‑only GitHub Actions free tier (2 vCPUs, ≈7 GB RAM, ≤6 h wall‑time).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `pandas==2.2.*`, `numpy==2.0.*`, `scikit-learn==1.5.*`, `shap==0.45.*`, `statsmodels==0.14.*`, `datasets==2.19.*`, `psutil==5.9.*`, `pyyaml==6.0.*`, `openml==0.14.*`  
- **Storage**: File‑system (`data/`, `outputs/`)  
- **Testing**: `pytest==8.*` (contract and unit tests)  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: End‑to‑end wall‑time ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: CPU‑only, `max_depth ≤ 5`, `n_estimators ≤ 200`, k‑fold GroupKFold CV, BH correction, Jaccard stability ≥ 0.8  

## Constitution Check
| Principle | How Plan Satisfies |
|-----------|-------------------|
| I. Reproducibility | Fixed random seeds (`np.random.seed(42)`, `random_state=42`). All external data fetched via deterministic URLs (or supplied locally) and checksummed. |
| II. Verified Accuracy | No external citations beyond the dataset URL (provided by verifier). |
| III. Data Hygiene | Raw CSV never overwritten; each transformation writes a new file with provenance recorded under `metadata/`. |
| IV. Single Source of Truth | Every figure/table is generated from `cleaned_dataset.csv` and `model_artifact.yaml`. |
| V. Versioning Discipline | All artifacts hashed (SHA‑256) and referenced in `metadata/`. |
| VI. Interaction‑Effect Quantification | Interaction columns are explicitly engineered; SHAP interaction values and permutation‑importance p‑values quantify their contribution. |
| VII. Tabular Data Integrity & Environmental Normalization | Required environmental columns are validated, standardized, and GroupKFold splits enforce no batch leakage. Composition categories are balanced across folds. |

## Entity Mapping
The pipeline creates the core entities defined in **data-model.md**:

* **CorrosionRecord** → persisted as `data/processed/cleaned_dataset.csv` (the collection of validated, imputed, and standardized records).  
* **InteractionFeature** → derived and stored in `data/processed/features.parquet` (each row corresponds to a named interaction with its values).  
* **DatasetMetadata** → provenance information written to `metadata/dataset.yaml` (DOI, URL, SHA‑256, column list).  
* **ModelArtifact** → best model and its training metadata saved as `data/results/model_artifact.yaml` (conforms to `contracts/model_artifact.schema.yaml`).  

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
│   ├── ingest.py          # FR‑001, FR‑008, FR‑011, FR‑006 (collinearity diagnostics)
│   ├── features.py        # FR‑002, FR‑007
│   ├── split.py           # FR‑009, FR‑010 (GroupKFold)
│   ├── train.py           # FR‑003, FR‑010
│   ├── evaluate.py        # FR‑002, FR‑005, FR‑012, SC‑002 (paired permutation test, perm‑importance)
│   ├── interpret.py       # FR‑004
│   ├── sensitivity.py     # FR‑006, FR‑007, SC‑005
│   ├── vif.py             # FR‑006 (VIF computation)
│   └── utils.py
└── run_all.py             # orchestrates all phases and runs verification tests
```

## Phase‑wise Implementation Tasks
| Phase | FR/SC addressed | Description | Expected Runtime |
|-------|----------------|-------------|------------------|
| **0 – Data Ingestion & Hygiene** | FR‑001, FR‑008, FR‑011, FR‑006 | Download (or read local) CSV, verify required columns, harmonize corrosion‑rate units to mm/yr, impute missing non‑target values (median/mode), one‑hot encode `composition`, standardize numeric predictors, compute VIF for base predictors (exclude interactions). Write `data/processed/cleaned_dataset.csv`, `metadata/dataset.yaml`, and `data/results/vif_report.json`. | ≤ 20 min |
| **1 – Interaction Feature Engineering** | FR‑002, FR‑007 | Create pairwise products among numeric env variables (pH, salinity, temperature) **and** between each numeric env variable and each one‑hot composition column. Add degree‑2 polynomial terms for numeric env variables. Residualize each interaction against its constituent main effects (linear regression) to reduce circular inflation. Store as `data/processed/features.parquet`. | ≤ 10 min |
| **2 – Group‑aware Splitting** | FR‑009, FR‑010 | Perform 5‑fold GroupKFold on `source_id`. Additionally enforce stratified balance of composition one‑hots across folds (custom `StratifiedGroupKFold`). Cache train/validation indices as `data/processed/splits.pkl`. | ≤ 5 min |
| **3 – Model Training (Full & Null)** | FR‑003, FR‑010 | For each CV fold, train (a) Full RandomForest/GradientBoosting **with** interaction columns and (b) Null models **without** interaction columns, respecting `max_depth ≤ 5`, `n_estimators ≤ 200`. Persist each fold’s models; select the best (highest mean CV R²) as `data/results/model_artifact.yaml`. | ≤ 2 h |
| **4 – Interaction‑Gain Significance (Paired Permutation Test)** | FR‑002, FR‑005, FR‑012, SC‑002 | Compute RMSE on the held‑out test set for Full and Null models per fold. Observed statistic = mean ΔRMSE (Null − Full). Generate a null distribution by **sign‑flipping** the Full/Null labels within each fold 1 000 times, recompute mean ΔRMSE each iteration. Two‑sided p‑value = proportion of permuted ΔRMSE ≥ observed. Report adjusted p‑value after BH correction (though only one test). | ≤ 30 min |
| **5 – Permutation‑Importance per Interaction** | FR‑012, FR‑005, SC‑004 | For each engineered interaction column, shuffle its values across the full dataset (multiple permutations), re‑evaluate the Full model, record ΔRMSE. Empirical p‑value = proportion of shuffled ΔRMSE ≤ observed (since larger ΔRMSE indicates worse performance). Apply Benjamini‑Hochberg correction across all interaction columns. | ≤ 45 min |
| **6 – Interpretability (SHAP)** | FR‑004 | Compute SHAP interaction values for the top‑ranked interaction features (by absolute mean SHAP). Generate (i) summary plot, (ii) dependence plots for the top‑interactions, (iii) partial‑dependence curves. Save PNGs under `outputs/figures/`. | ≤ 45 min |
| **7 – Sensitivity & Diagnostics** | FR‑006, FR‑007, SC‑005 | Re‑compute VIF including interaction terms (diagnostic only). Sweep `max_depth` ∈ {3,4,5} (keeping other hyperparameters fixed) and record top‑5 feature lists; compute pairwise Jaccard similarity, require ≥ 0.8 stability. Save results in `data/results/sensitivity.json`. | ≤ 20 min |
| **8 – Reporting & Provenance** | SC‑001, SC‑003, SC‑006, SC‑007 | Assemble `report.md` with (a) performance metrics (R², RMSE) vs. baseline, (b) paired permutation‑test result, (c) BH‑adjusted interaction importance, (d) SHAP visualisations, (e) hyper‑parameter stability, (f) explicit associational disclaimer, (g) runtime & memory usage summary. Ensure total wall‑time ≤ 6 h. | ≤ 10 min |
| **9 – Verification** | – | Run the full pytest suite (`pytest src/tests/`) to validate contract compliance and that all pipeline modules execute without error. Failure aborts the CI run. | ≤ 5 min |

All phases are ordered so that data is available before downstream steps, and models are trained before interpretation.

---

