# Implementation Plan: Predicting the Impact of Ball Milling on Particle Size Distribution

**Branch**: `001-predict-balling-milling-psd` | **Date**: 2026-07-06 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-predict-balling-milling-psd/spec.md`

## Summary
Create a reproducible pipeline that aggregates ball‑milling experiments from Materials Project, NIST, and arXiv, (2) preprocesses the data (imputation excluding targets, normalization, encoding), (3) trains Gaussian Process Regression (GPR) and Random Forest (RF) models using **Nested Cross-Validation** (5x2), (4) evaluates performance against a linear‑regression baseline using the **Nadeau & Bengio corrected resampled t-test**, (5) conducts **a priori** power analysis, and (6) generates interpretability artefacts (partial dependence plots, feature‑importance JSON). All steps respect the GitHub Actions free‑tier constraints (≤7 GB RAM, **6-hour** job limit) and the project constitution. All findings are explicitly framed as **associational** due to the observational nature of the data.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**:
  - `pandas==2.2.*`
  - `numpy==1.26.*`
  - `scikit-learn==1.5.*`
  - `statsmodels==0.14.*`
  - `matplotlib==3.9.*`
  - `seaborn==0.13.*`
  - `requests==2.32.*`
  - `tqdm==4.66.*`
  - `pyarrow==16.*` (for parquet I/O)
  - `pdfminer.six==20231228` (for arXiv extraction)
- **Storage**: CSV/Parquet files under `data/` (raw, cleaned, splits)
- **Testing**: `pytest==8.*` with contract validation via `jsonschema`
- **Target Platform**: Linux runner (GitHub Actions)
- **Project Type**: Library + CLI tools
- **Performance Goals**: Entire pipeline ≤ 5 h wall‑clock on free‑tier runner; peak RAM ≤ 5 GB.
- **Constraints**: CPU‑only; no GPU; model hyper‑parameters limited to ≤ 1000 RF trees and GPR kernel with ARD (dimensionality = number of predictors).

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | All random seeds are pinned; data fetching scripts are deterministic; `requirements.txt` pins all deps. |
| II. Verified Accuracy | References the "Verified Datasets" block; Materials Project/NIST/arXiv treated as "Named Sources" pending specific ID extraction; Reference-Validator Agent mechanism acknowledged. |
| III. Data Hygiene | Checksums recorded; raw files never overwritten; all transformations write new files. |
| IV. Single Source of Truth | Every figure/table references a specific row in `data/processed/ball_milling_dataset.parquet`. |
| V. Versioning Discipline | All artefacts are content‑hashed; `state/projects/...yaml` will be updated automatically. |
| VI. Computational‑Stability | Model complexity limits (≤ 1000 trees, GPR kernel ARD) and fallback logic guarantee ≤ 6 h runtime, ≤ 5 GB RAM. |
| VII. Experimental‑Data‑Traceability | Each record stores `source_name` and `source_id` (specific accession IDs) per the dataset schema. |

## Project Structure
```text
specs/001-predict-balling-milling-psd/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── dataset.schema.yaml

src/
├── ingest/
│   ├── materials_project.py
│   ├── nist_repo.py
│   └── arxiv_extractor.py
├── preprocess/
│   └── pipeline.py
├── model/
│   ├── train_gpr.py
│   ├── train_rf.py
│   └── baseline_lr.py
├── evaluate/
│   ├── metrics.py
│   └── statistical_tests.py
├── interpret/
│   ├── partial_dependence.py
│   └── feature_importance.py
└── utils/
    ├── logger.py
    ├── seed.py
    └── generate_report.py

tests/
├── contract/
│   └── test_dataset_schema.py
├── unit/
│   ├── test_ingest.py
│   ├── test_preprocess.py
│   └── test_model.py
└── integration/
    └── test_full_pipeline.py
```

## Complexity Tracking
No constitution violations remain after fixing the dataset schema and statistical methodology.

## Phase‑wise Plan (mapping FR/SC → steps)

| Phase | Steps | FR / SC addressed |
|-------|-------|--------------------|
| **0 – Data Acquisition** | 1. Run `src/ingest/materials_project.py` to pull all ball‑milling entries via Materials Project API.<br>2. Run `src/ingest/nist_repo.py` to download NIST CSV/JSON files.<br>3. Run `src/ingest/arxiv_extractor.py` to scrape tables from arXiv PDFs (using `pdfminer.six`).<br>4. Merge into a unified raw table, deduplicate by `experiment_id` (FR‑001, SC‑004). | FR‑001, SC‑004 |
| **1 – Preprocessing** | 5. Apply `src/preprocess/pipeline.py`:<br> a. Multiple imputation (IterativeImputer) for missing Young’s modulus, density, etc. **EXCLUDING target variables (D10/D50/D90)** to prevent leakage (FR‑002).<br> b. One‑hot encode `material_type` (FR‑002).<br> c. Standard‑scale numeric features.<br> d. Flag unstructured PSD entries (images, curves) → `flagged_psd.log` (FR‑008). | FR‑002, FR‑008 |
| **2 – Dataset Validation** | 6. Validate the cleaned dataset against `contracts/dataset.schema.yaml` using `jsonschema`. Halt if < 150 rows (critical error) with message: "Dataset size < 150 experiments (minimum viable) per spec SC-004" (FR‑001, FR‑009). | FR‑001, FR‑009, SC‑004 |
| **3 – Model Training** | 7. Implement **Nested Cross-Validation (k-fold)

The specific value to remove/generalize: 'k'

Rewritten passage:
Nested Cross-Validation (k-fold)

The research question is to determine the optimal hyperparameters for the proposed model while minimizing overfitting and providing an unbiased estimate of generalization performance. The method involves implementing a nested cross-validation procedure, where an inner loop is used for hyperparameter tuning and an outer loop is used for performance evaluation, utilizing a k-fold stratified splitting strategy. References: [Insert DOI/arXiv/author-year here].**:<br> - Outer loop: multiple folds for unbiased performance estimation.<br> - Inner loop: a small number of folds for hyperparameter tuning.<br> - **Stratify outer folds by binned D50** (target) to ensure outcome distribution similarity across folds, avoiding material-specific bias (FR‑003).<br>8. Train GPR with `src/model/train_gpr.py` using inner CV for tuning.<br>9. Monitor runtime & RAM; if > 30 min or > 5 GB, abort GPR and log fallback (FR‑009).<br>10. Train Random Forest (`src/model/train_rf.py`) with ≤ 1000 trees, using same Nested CV scheme. (FR‑003) | FR‑003, FR‑009 |
| **4 – Baseline & Evaluation** | 11. Fit linear regression baseline (`src/model/baseline_lr.py`) using same Nested CV scheme.<br>12. Compute R², RMSE, MAE on **outer folds** for each model (FR‑004).<br>13. Perform **Nadeau & Bengio corrected resampled t-test** comparing each ML model vs. baseline on the outer fold predictions (α = 0.05) (FR‑006).<br>14. Report **a priori** statistical power (minimum detectable effect size given N) based on hypothesized effect size (Cohen's f² = 0.15) (FR‑007). | FR‑004, FR‑006, FR‑007, SC‑001, SC‑002, SC‑003 |
| **5 – Interpretability** | 15. Generate partial dependence plots for each numeric predictor (`src/interpret/partial_dependence.py`).<br>16. Export RF feature‑importance JSON (`src/interpret/feature_importance.py`). (FR‑005) | FR‑005 |
| **6 – Reporting & Artefacts** | 17. Assemble `results/` folder containing:<br> - `metrics.csv` (R², RMSE, MAE)<br> - `t_test_summary.txt` (p‑value, Bonferroni-adjusted α, minimum detectable effect size)<br> - `partial_dependence_*.png` (size ≤ 10 MB total) (SC‑005)<br> - `feature_importance.json` (SC‑005)<br> - `associational_disclaimer.txt` (explicit statement that findings are associational) | SC‑001, SC‑002, SC‑003, SC‑005 |
| **7 – CI Integration** | 18. Add GitHub Actions workflow (`.github/workflows/ci.yml`) that runs the full pipeline, validates schema, and enforces the **6-hour** limit (addressing SC‑005, noting spec typo "-hour" → "6-hour"). | VI (Computational‑Stability) |

---
**Note on SC-005**: The spec text contains a typo ("-hour"). This plan explicitly enforces the standard **6-hour** GitHub Actions free-tier limit as per Constitution Principle VI.