# Implementation Plan: Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases

**Branch**: `001-predicting-corrosion-rates-of-common-met` | **Date**: 2026-10-13 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `/specs/001-predicting-corrosion-rates-of-common-met/spec.md`

## Summary
The project must ingest a publicly‑available tabular corrosion dataset, validate that the required columns (pH, salinity, temperature, material composition, corrosion rate) exist, harmonize units, impute missing values, engineer interaction features (restricted to numeric environmental variables and one‑hot encoded material composition columns), train constrained Random Forest and Gradient Boosting regressors, evaluate the added value of interactions via a hierarchical permutation test, compute SHAP interaction values, apply Benjamini‑Hochberg correction to feature‑importance p‑values, assess collinearity (including interaction terms as diagnostics), perform hyper‑parameter sensitivity, and generate a reproducible report. All steps run on the CPU‑only GitHub Actions free tier (2 vCPUs, ≈7 GB RAM, ≤6 h wall‑time).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==2.0.*`, `scikit-learn==1.5.*`, `shap==0.45.*`, `statsmodels==0.14.*`, `datasets==2.19.*`, `psutil==5.9.*`, `pyyaml==6.0.*`  
- **Storage**: File‑system (`data/`, `outputs/`)  
- **Testing**: `pytest==8.*` (contract tests)  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: Whole pipeline ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: CPU‑only, `max_depth ≤ 5`, `n_estimators ≤ 200`, 5‑fold GroupKFold CV, BH correction, Jaccard stability ≥ 0.8  

## Constitution Check
| Principle | How Plan Satisfies |
|-----------|-------------------|
| I. Reproducibility | All random seeds are pinned (`np.random.seed(42)`, `random_state=42`). External datasets are fetched via deterministic URLs (if available) and checksummed. |
| II. Verified Accuracy | No external citations are introduced beyond the dataset source (see Dataset Strategy). |
| III. Data Hygiene | Raw files are never overwritten; each transformation writes a new file with provenance metadata stored under `metadata/`. |
| IV. Single Source of Truth | Every figure/table is generated from the canonical cleaned dataset (`cleaned_dataset.csv`) and model artifact (`model_artifact.yaml`). |
| V. Versioning Discipline | All artifacts are hashed (SHA‑256) and referenced in `metadata/`. |
| VI. Interaction‑Effect Quantification | Interaction columns are explicitly engineered; SHAP interaction values and hierarchical permutation‑importance p‑values quantify their contribution. |
| VII. Tabular Data Integrity & Environmental Normalization | Environmental features are validated for physical ranges, standardized, and group‑aware splits enforce no batch leakage. Composition categories are balanced across folds to mitigate residual confounding. |

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
│   ├── ingest.py          # FR‑001, FR‑008, FR‑011, FR‑006 (collinearity)
│   ├── features.py        # FR‑002, FR‑007
│   ├── train.py           # FR‑003, FR‑009, FR‑010
│   ├── evaluate.py        # FR‑002, FR‑005, FR‑012, SC‑002
│   ├── interpret.py       # FR‑004
│   └── utils.py
tests/
├── contract/
│   └── test_contracts.py
└── unit/
    └── test_pipeline_*.py
```

## Phase‑wise Implementation Tasks
| Phase | FR/SC addressed | Description | Expected Runtime |
|-------|----------------|-------------|------------------|
| **0 – Data Ingestion, Validation, & Collinearity** | FR‑001, FR‑008, FR‑011, **FR‑006** | Download dataset(s), verify required columns, harmonize corrosion‑rate units to mm/yr, impute missing values, one‑hot encode metals, scale numerics, compute **VIF** for all base predictors **and** for each engineered interaction term (diagnostic only). Flag VIF > 5; interaction VIFs are reported but not interpreted as independent effects. Record provenance. | ≤ 30 min |
| **1 – Interaction Feature Engineering** | FR‑002, FR‑007 | Create pairwise products among numeric environmental variables (pH, salinity, temperature) **and** between each numeric env variable and each one‑hot encoded composition column. Also generate degree‑2 polynomial terms for numeric env variables. Prior to importance testing, each interaction column is orthogonalized (residualized) against its constituent main‑effect columns to avoid circular inflation. Store in `features.parquet`. | ≤ 15 min |
| **2 – Group‑aware Splitting & CV** | FR‑009, FR‑010 | Perform 5‑fold GroupKFold based on `source_id`. Additionally enforce that the distribution of composition one‑hot categories is balanced across folds (stratified‑GroupKFold) to reduce residual confounding between material type and experimental batch. Cache train/validation indices. | ≤ 10 min |
| **3 – Model Training (Full & Null)** | FR‑003, FR‑010 | For each CV fold, train RandomForest & GradientBoosting under depth/estimator caps; also train Null models **without** interaction columns. Persist the best model (by CV R²) as `model_artifact.yaml`. | ≤ 2 h |
| **4 – Interaction Significance Testing** | FR‑002, **FR‑005**, **FR‑012**, SC‑002 | *Hierarchical* permutation test (200 target permutations) comparing Full vs Null RMSE (statistic = ΔR²). Compute permutation‑importance for each engineered interaction column (200 shuffles per column) to obtain empirical p‑values; apply Benjamini‑Hochberg correction (FR‑005). Report adjusted p‑values and ΔR². | ≤ 1 h |
| **5 – Interpretability (SHAP)** | FR‑004 | Compute SHAP interaction values **for the top‑10 interaction features (by absolute SHAP magnitude)** to stay within the CPU budget, generate summary plot, top‑3 interaction dependence plots, partial‑dependence curves; save figures under `outputs/figures/`. | ≤ 1 h |
| **6 – Sensitivity & Additional Diagnostics** | FR‑006, FR‑007, SC‑004, SC‑005 | Re‑compute VIF including interaction terms (diagnostic only). Sweep `max_depth` ∈ {3,4,5}, record top‑5 feature Jaccard similarity; ensure ≥ 0.8 stability. | ≤ 30 min |
| **7 – Reporting & Provenance** | SC‑001, SC‑003, SC‑006, SC‑007 | Assemble `report.md` with performance metrics, hierarchical permutation‑test results, BH‑corrected p‑values, stability analysis, and explicit associational disclaimer. Ensure total wall‑time ≤ 6 h. | ≤ 15 min |

All phases are ordered so that data is available before any downstream step, and models are trained before interpretation.

---



