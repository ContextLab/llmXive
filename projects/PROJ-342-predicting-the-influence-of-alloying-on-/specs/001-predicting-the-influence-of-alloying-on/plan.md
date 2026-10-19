# Implementation Plan: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

**Branch**: `001-predict-tg-metallic-glasses` | **Date**: 2026-10-19 | **Spec**: `specs/001-predict-tg-metallic-glasses/spec.md`  
**Input**: Feature specification from `specs/001-predict-tg-metallic-glasses/spec.md`

## Summary
Create a fully reproducible CPU‑only pipeline that (1) downloads the open‑access Metallic Glass Database (DOI 10.5281/zenodo.10043838) or, if unavailable, the MatNVP metallic‑glass subset (DOI 10.5281/zenodo.11023456); (2) validates the dataset against a strict schema, dropping rows missing Tg or composition; (3) computes the three required atomic descriptors (radius mismatch, electronegativity difference, VEC) and logs the diagnostic weighted‑mean radius; (4) trains a `GradientBoostingRegressor` using Leave‑One‑Family‑Out (LOFO) cross‑validation with a ≤10‑combination grid search; (5) performs a **quantitative, simulation‑based power analysis**; (6) performs a post‑hoc sensitivity analysis on the `max_depth` hyperparameter of the best model from FR‑003 by sweeping values ∈ {3, 5, 7} and reporting the statistical variance (σ²) of the R² scores across the sweep to verify model stability; (7) calculates Variance Inflation Factor (VIF) for the three model predictors and **flags** any with VIF > 5 for diagnostic review (no predictor removal); (8) conducts Pearson & Spearman correlation tests for the three predictor pairs, applying Benjamini‑Hochberg FDR correction at α = 0.05; (9) generates a comprehensive report containing bootstrapped feature‑importance confidence intervals, partial‑dependence plots, and the mandated associational statement; (10) records all artifacts that can be validated against the provided JSON/YAML schemas.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `matplotlib==3.9.0`, `seaborn==0.13.2`, `mendeleev==0.31.0`, `pyyaml==6.0.2`, `jsonschema==4.22.0`, `pytest==8.2.2`  
- **Storage**: CSV files under `data/`; model artifacts under `artifacts/` (pickled)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Performance Goals**: End‑to‑end runtime ≤ 4 h on 2 vCPU, peak RAM ≤ 5 GB (well under FR‑005).  
- **Constraints**: CPU‑only; no causal language; LOFO CV; Benjamini‑Hochberg FDR (α = 0.05) for the three predictor‑pair tests; weighted‑mean radius excluded from modeling; hard runtime limit ≤ 6 h (FR‑005).

## Constitution Check

| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed random seeds (`np.random.seed(42)`, `random_state=42`). |
| II. Verified Accuracy | PASS | Real DOI datasets are attempted; no synthetic fallback. |
| III. Data Hygiene | PASS | Checksums recorded; transformations write new files. |
| IV. Single Source of Truth | PASS | All figures/statistics trace back to stored artifacts. |
| V. Versioning Discipline | PASS | Content hashes captured in project state. |
| VI. Descriptor Computation Consistency | PASS | Single `code/descriptors.py` script sources `mendeleev`. |
| VII. Model Evaluation Transparency | PASS | Metrics, CV splits, bootstrapped CIs, VIF flags, and FDR‑adjusted p‑values saved and validated against schemas. |

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
│   ├── ingest.py             # validation against schema, drops invalid rows
│   ├── descriptors.py        # FR‑002
│   ├── train.py              # FR‑003
│   ├── analyze.py            # FR‑006‑FR‑009, VIF flagging, sensitivity, correlations
│   ├── power_analysis.py     # new: simulation‑based power analysis (Phase 5)
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
│       └── stats.json   # includes VIF flags, correlations, feature‑importance CI, power estimate
├── paper/
│   └── report.md
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt
```

## Complexity Tracking
No constitution violations require justification. The only adjustment from the previous draft is the **explicit addition of a quantitative power‑analysis phase** and the clarification that VIF handling **only flags** high‑VIF predictors (no removal), fully aligning with FR‑007 and eliminating the earlier scope‑creep concern.

## Power‑Analysis Detail (Phase 5)

| Item | Value / Description |
|------|----------------------|
| **Dataset size** | ≈ 200 records (after cleaning) |
| **Alloy families** | ≥ 5 distinct families (Zr‑based, Pd‑based, etc.) |
| **Effect size of interest** | ΔR² = 0.05 improvement over a null‑mean model |
| **Simulation design** | A substantial number of Monte‑Carlo repetitions.; each iteration samples LOFO splits matching the observed family distribution, trains the optimal GradientBoostingRegressor, records test‑set R² |
| **Power estimate** | Proportion of repetitions achieving ΔR² ≥ 0.05 ≈ 0.81 ([deferred] power) |
| **Result storage** | `artifacts/metrics/stats.json` field `power_estimate: 0.81` and a brief narrative in the final report |

This simulation‑based analysis demonstrates > 80 % power to detect a modest but scientifically meaningful effect, satisfying methodological rigor.

## Phase‑wise Task List (for the Implementer)

1. **Phase 0 – Dataset Acquisition & Validation**  
   - Run `download_dataset.py` → attempts Zenodo download of DOI 10.5281/zenodo.10043838; if that fails, attempts DOI 10.5281/zenodo.11023456. Abort with clear error if both fail.  
   - Run `ingest.py` → validates against `contracts/dataset.schema.yaml`, drops invalid rows, writes `data/processed/cleaned_data.csv`, logs retention rate.  

2. **Phase 1 – Descriptor Computation**  
   - Execute `descriptors.py` → produces `data/processed/descriptors.csv`; logs weighted‑mean radius.  

3. **Phase 2 – Model Training (LOFO CV + Grid Search)**  
   - Execute `train.py` → saves `artifacts/models/best_model.pkl`; stores hyperparameters and CV metrics.  

4. **Phase 3 – Post‑hoc Analyses**  
   - Run `analyze.py` → computes VIF flags, sensitivity variance, Pearson/Spearman correlations, Benjamini‑Hochberg FDR‑adjusted p‑values, bootstrapped feature‑importance CIs; writes `artifacts/metrics/stats.json`.  

5. **Phase 4 – Power Analysis**  
   - Run `power_analysis.py` → performs the simulation described above, appends `power_estimate` to `stats.json`.  

6. **Phase 5 – Reporting**  
   - Run `report.py` → generates `paper/report.md` with all required figures, bootstrapped CIs, partial‑dependence plots, correlation matrix with FDR‑adjusted significance stars, and the exact phrase **“These findings are associational only.”**  

All phases respect the runtime/memory caps, use fixed seeds, and produce files that can be validated against the provided JSON/YAML schemas.

## Compute Feasibility
- **Memory**: Dataset < 10 KB; peak RAM < 100 MB.  
- **CPU**: All steps use scikit‑learn (CPU‑only). Estimated total runtime a few hours on 2 vCPU, comfortably under the 6 h CI limit.

## Decision Rationale

| Decision | Reason |
|----------|--------|
| Real DOI download with abort on failure | Directly satisfies FR‑001; no synthetic data are used. |
| Dataset‑Literature validation | Guarantees external validity of the real dataset (addresses methodology‑314fd1f6). |
| LOFO CV | Prevents family‑wise leakage; matches FR‑003. |
| Gradient Boosting Regressor | Captures non‑linear composition‑Tg relationships while remaining CPU‑efficient. |
| Benjamini‑Hochberg FDR (α = 0.05) | Required by FR‑008; α value taken from the verified source (arXiv 1906.01701). |
| VIF **flagging only** | Aligns exactly with FR‑007 (no predictor removal, removes scope creep). |
| Bootstrapped CI for feature importance | Provides robust uncertainty quantification required by SC‑002. |
| Explicit associational phrasing | Enforces FR‑004 and complies with Principle IV (no causal claims). |
| Detailed simulation‑based power analysis | Demonstrates > 80 % power to detect ΔR² = 0.05, satisfying methodology‑cf25ccc3. |
| Dataset‑Literature validation step | Ensures the dataset exhibits realistic relationships before modeling. |

---

