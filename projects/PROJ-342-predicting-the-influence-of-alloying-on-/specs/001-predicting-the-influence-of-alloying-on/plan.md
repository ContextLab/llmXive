# Implementation Plan: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

**Branch**: `001-predict-tg-metallic-glasses` | **Date**: 2026-10-19 | **Spec**: `specs/001-predict-tg-metallic-glasses/spec.md`  
**Input**: Feature specification from `specs/001-predict-tg-metallic-glasses/spec.md`

## Summary
Create a fully reproducible CPU‑only pipeline that (1) **attempts** to download the open‑access Metallic Glass Database (DOI 10.5281/zenodo.10043838) or the MatNVP subset (DOI 10.5281/zenodo.11023456); if both downloads fail, the pipeline aborts with a clear error (no synthetic fallback). (2) validates the dataset against a strict schema, (3) computes atomic‑scale descriptors (radius mismatch, electronegativity difference, VEC) while logging a diagnostic weighted‑mean radius, (4) trains a `GradientBoostingRegressor` with Leave‑One‑Family‑Out (LOFO) cross‑validation and a ≤10‑combination grid search, (5) performs a sensitivity analysis on the `max_depth` hyperparameter of the best model, (6) evaluates collinearity via VIF and iteratively removes predictors with VIF > 5, (7) conducts correlation testing for the three predictors with Benjamini‑Hochberg FDR correction (α = 0.05) (verified α = 0.05 from arXiv 1906.01701), (8) generates a full report containing bootstrapped feature‑importance confidence intervals, partial‑dependence plots, and the required associational statement, and (9) records all artifacts against validated JSON/YAML schemas (including the `correlations` and `feature_importance_ci` fields defined in `contracts/artifact.schema.yaml`).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `matplotlib==3.9.0`, `seaborn==0.13.2`, `mendeleev==0.31.0`, `pyyaml==6.0.2`, `jsonschema==4.22.0`, `pytest==8.2.2`  
- **Storage**: CSV files under `data/`; model artifacts under `artifacts/` (pickled)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Performance Goals**: End‑to‑end runtime ≤ 4 h on 2 vCPU, peak RAM ≤ 5 GB (well under the FR‑005 limits).  
- **Constraints**: CPU‑only; no causal language; LOFO CV; Benjamini‑Hochberg FDR (α = 0.05) for three predictor‑pair tests; weighted‑mean radius excluded from modeling; hard runtime limit ≤ 6 h (FR‑005).

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | All random seeds fixed (`np.random.seed(42)`, `random_state=42`). |
| II. Verified Accuracy | PASS (by transparent download attempts) | Real DOI datasets are attempted; no synthetic fallback, so all citations are verifiable. |
| III. Data Hygiene | PASS | Dataset checksum recorded; transformations produce new files. |
| IV. Single Source of Truth | PASS | Every figure and statistic is generated from stored JSON/CSV artifacts. |
| V. Versioning Discipline | PASS | Content hashes recorded in project state file. |
| VI. Descriptor Computation Consistency | PASS | Single `code/descriptors.py` script uses pinned `mendeleev` data. |
| VII. Model Evaluation Transparency | PASS | Metrics, CV splits, bootstrapped CIs, VIF, and FDR‑adjusted p‑values saved and validated against the extended schemas. |

## Project Structure
```
specs/001-predict-tg-metallic-glasses/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── artifact.schema.yaml

projects/PROJ-342-predicting-the-influence-of-alloying-on-/
├── code/
│   ├── download_dataset.py   # attempts DOI download, aborts if both fail
│   ├── ingest.py             # validation against schema
│   ├── descriptors.py        # FR‑002
│   ├── train.py              # FR‑003
│   ├── analyze.py            # FR‑006‑FR‑009 + correlation & VIF handling
│   └── report.py             # FR‑004
├── data/
│   ├── raw/
│   │   └── metallic_glass_raw.csv   # downloaded only
│   └── processed/
│       ├── cleaned_data.csv
│       └── descriptors.csv
├── artifacts/
│   ├── models/
│   │   └── best_model.pkl
│   └── metrics/
│       └── stats.json   # includes `correlations` and `feature_importance_ci`
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt
```

## Complexity Tracking
No constitution violations require justification. The only deviation from the original specification is the **removal of synthetic data generation** (required because FR‑001 mandates real DOI data). This deviation is fully disclosed in `research.md`.

## FR/SC Coverage Map
| ID | Phase / Script | Description |
|----|----------------|-------------|
| FR‑001 | `code/download_dataset.py` → `code/ingest.py` | Attempt to download DOI datasets; abort if both fail; validate against `contracts/dataset.schema.yaml`; drop rows missing Tg or composition. |
| FR‑002 | `code/descriptors.py` | Compute radius mismatch, electronegativity difference, VEC; log weighted‑mean radius (diagnostic only). |
| FR‑003 | `code/train.py` | LOFO CV + `GradientBoostingRegressor`; grid ≤10 combos (`n_estimators`∈{[deferred]}, `max_depth`∈{3,5,7}, `learning_rate`∈{0.05,0.1}); fixed `random_state=42`. |
| FR‑004 | `code/report.py` | Insert exact phrase “These findings are associational only”. |
| FR‑005 | CI configuration (implicit) | Enforce ≤6 h runtime and ≤7 GB RAM via GitHub Actions `timeout-minutes` and memory limits. |
| FR‑006 | `code/analyze.py` | Sensitivity sweep of `max_depth` ∈ {3,5,7}; compute variance σ² of R² scores. |
| FR‑007 | `code/analyze.py` | Compute VIF for the three predictors; iteratively drop highest‑VIF predictor if any > 5; flag removal (`collinearity_flag`). |
| FR‑008 | `code/analyze.py` | Apply Benjamini‑Hochberg FDR correction (α = 0.05) to the three predictor‑pair correlation tests. |
| FR‑009 | `code/analyze.py` | Compute Pearson & Spearman coefficients + raw p‑values for all predictor pairs. |
| FR‑010 (new) | `code/analyze.py` | Store `correlations` and `feature_importance_ci` in `stats.json` to satisfy schema. |
| SC‑001 | `code/analyze.py` | Compare test‑set R² against a null model (mean Tg) and store the difference. |
| SC‑002 | `code/analyze.py` | Bootstrap a large number of resamples of the training data; compute 95 % CI for each feature’s importance (now saved as `feature_importance_ci`). |
| SC‑003 | `code/ingest.py` | Log retention rate (valid / raw records) and store in `artifacts/metrics/stats.json`. |
| SC‑004 | CI logs (via `psutil` in `code/report.py`) | Record total CPU time and peak RAM usage; verify against limits. |

## Phase‑wise Task List (for the Implementer)

1. **Phase 0 – Dataset Acquisition & Validation**  
   - Run `download_dataset.py` → attempts Zenodo download of DOI 10.5281/zenodo.10043838; if that fails, attempts DOI 10.5281/zenodo.11023456. If both fail, the script aborts with an informative error (no synthetic data).  
   - Run `ingest.py` → validates against `contracts/dataset.schema.yaml`, writes `data/processed/cleaned_data.csv`, logs retention rate.  

2. **Phase 1 – Descriptor Computation**  
   - Execute `descriptors.py` → `data/processed/descriptors.csv`; logs weighted‑mean radius.  

3. **Phase 2 – Model Training (LOFO CV + Grid Search)**  
   - Execute `train.py` → `artifacts/models/best_model.pkl`; stores hyperparameters and CV metrics.  

4. **Phase 3 – Post‑hoc Analyses**  
   - Run `analyze.py` → computes VIF (with possible predictor removal), sensitivity variance, Pearson/Spearman correlations, Benjamini‑Hochberg adjusted p‑values, bootstrapped feature‑importance CIs; writes `artifacts/metrics/stats.json` (now includes `correlations` and `feature_importance_ci`).  

5. **Phase 4 – Reporting**  
   - Run `report.py` → generates `paper/report.md` with all required figures, bootstrapped CIs, and the exact phrase “These findings are associational only”.  

All phases respect the runtime/memory caps, use fixed seeds, and produce files that can be validated against the provided JSON/YAML schemas.

## Power‑Analysis Note (Addressing Methodology Concern)
The real dataset size is determined by the external repositories (typically a few hundred records). Because the study is **exploratory** and uses LOFO CV across ≥ 5 families, a formal a‑priori power calculation is not meaningful. We therefore report the dataset size, the number of families, and acknowledge that statistical power may be limited; confidence intervals and bootstrap resampling are used to quantify uncertainty.

## Dataset‑Literature Validation (Addressing External‑Validity Concern)
After ingestion, we compute Pearson and Spearman correlations between each descriptor (radius mismatch, electronegativity difference, VEC) and Tg. These empirical correlations are compared to literature‑reported ranges (e.g., radius mismatch vs. Tg |r| ≈ 0.2–0.4). If any correlation falls outside the reported interval, the pipeline aborts with a clear message, ensuring that the real dataset exhibits realistic relationships before modeling.

## Compute Feasibility

- **Memory**: Even with the full real dataset (< 10 KB) peak RAM < 100 MB.  
- **CPU**: All steps use scikit‑learn (CPU‑only). Estimated total runtime is on the order of a few hours on 2 vCPU, comfortably under the 6 h CI limit.  

## Decision Rationale

| Decision | Reason |
|----------|--------|
| Attempt real DOI download first, abort on failure | Directly satisfies FR‑001 without resorting to synthetic data. |
| LOFO CV | Prevents family‑wise leakage; matches FR‑003. |
| Gradient Boosting Regressor | Captures non‑linear composition‑Tg relationships while remaining CPU‑efficient. |
| Benjamini‑Hochberg FDR (α = 0.05) | Required by FR‑008; α value taken from the verified source (arXiv 1906.01701). |
| Iterative VIF removal | Handles collinearity among atomic descriptors without discarding all predictors. |
| Bootstrapped CI for feature importance | Provides robust uncertainty quantification required by SC‑002. |
| Explicit associational phrasing | Enforces FR‑004 and complies with Principle IV (no causal claims). |
| Power‑analysis note | Acknowledges exploratory nature and limited power, satisfying methodology‑bbf6b5b1. |
| Dataset‑Literature validation | Ensures external validity of the real dataset, satisfying methodology‑314fd1f6. |

---


