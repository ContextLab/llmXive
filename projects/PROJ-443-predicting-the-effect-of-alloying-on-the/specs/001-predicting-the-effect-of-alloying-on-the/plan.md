# Implementation Plan: Predicting the Effect of Alloying on the Elastic Modulus of High‑Entropy Alloys

**Branch**: `001-predict-elastic-modulus` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-elastic-modulus/spec.md`

## Summary

This project implements a computational pipeline to predict the Bulk Modulus of High‑Entropy Alloys (HEAs) by analyzing the effect of alloying. The approach retrieves raw composition and elastic constant data from Materials Project and OQMD, engineers compositional descriptors (mixing enthalpy, atomic radius variance, entropy of mixing, VEC) **excluding** mixing enthalpy from the predictor matrix, applies an Isometric Log‑Ratio (ILR) transformation to break compositional closure, and trains ensemble and linear regression models (Random Forest, Gradient Boosting, ElasticNet) on the **residual bulk modulus** (`B_obs - B_Miedema`). 

**Critical Methodological Safeguards**:
1. **Orthogonality Check**: Explicitly verifies that predictors are not deterministic functions of the Miedema baseline inputs (Task T016, T017).
2. **Residual Variance Pre-Check**: Validates signal-to-noise ratio before power analysis (Task T018).
3. **Robust CI Estimation**: Uses Bayesian Hierarchical Bootstrap for low-group scenarios (<30) to ensure valid 95% CIs (Task T011).
4. **CPU-Only**: All steps run on CPU-only GitHub Actions runners.

## Technical Context

- **Language/Version**: Python 3.10  
- **Primary Dependencies** (pinned in `code/requirements.txt`):
  - `scikit-learn==1.3.2`
  - `pandas==2.1.3`
  - `numpy==1.26.2`
  - `scipy==1.11.4`
  - `scikit-bio==0.5.9` (provides `ilr` implementation)
  - `matplotlib==3.8.2`
  - `seaborn==0.13.2`
  - `shap==0.44.0`
  - `pyyaml==6.0.1`
  - `requests==2.31.0`
  - `pymc==5.8.0` (for Bayesian Hierarchical Bootstrap in low-group scenarios)
- **Storage**: `data/` (raw, processed), `results/` (metrics, models, reports).  
- **Testing**: `pytest` suite under `tests/`.  
- **Compute Constraints**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM). All steps run CPU‑only (`n_jobs=1`).  
- **Performance Goal**: Full pipeline ≤ 6 h, memory < 6 GB.

## Constitution Check

| Principle | Requirement | Plan Compliance Strategy |
|-----------|-------------|--------------------------|
| **I. Reproducibility** | Random seeds pinned; external datasets fetched from canonical sources. | `random_state=42` everywhere; API queries logged with timestamps/parameters in `data/source_metadata.yaml`. |
| **II. Verified Accuracy** | All citations verified against primary sources. | All dataset URLs are taken from the verified block; `Reference‑Validator Agent` invoked via Task T001. |
| **III. Data Hygiene** | Datasets checksummed; no in‑place modifications. | Raw API dumps saved under `data/raw/`; processed files written to new filenames; checksums stored in `state/...yaml`. |
| **IV. Single Source of Truth** | Figures/statistics trace back to one data row and code block. | Metrics generated directly from evaluation scripts; no manual transcription. |
| **V. Versioning Discipline** | Content hashes trigger state updates. | `data/source_metadata.yaml` includes API version & query params; any change updates `state/...yaml`. |
| **VI. Materials Database Provenance** | Provenance metadata required. | Task T005 writes `data/source_metadata.yaml` with API version, query parameters, and SHA‑256 checksums (explicitly cites Principle VI). |
| **VII. Model Evaluation Transparency** | Full metric reporting, bootstrap CI, t‑test, FDR. | Task T007 computes metrics, 1000‑iteration grouped bootstrap CIs (or Bayesian Hierarchical fallback), t‑test vs. R² = 0, and Benjamini‑Hochberg FDR correction. |

## Project Structure

```
specs/001-predict-elastic-modulus/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── compositional_descriptor.schema.yaml
│   ├── hea_sample.schema.yaml
│   ├── model_performance.schema.yaml
│   └── model_performance_record.schema.yaml
└── tasks.md   # generated from the task list below
```

```
code/
├── __init__.py
├── config.py            # paths, thresholds, seeds
├── data/
│   ├── __init__.py
│   ├── fetch.py         # Materials Project & OQMD API clients
│   ├── clean.py         # Normalization, sum‑to‑1.0 checks
│   └── features.py      # Miedema baseline, descriptors, ILR, Orthogonality checks
├── models/
│   ├── __init__.py
│   ├── train.py         # RF, GB, EN training on residual target
│   └── eval.py          # Bootstrap CI, FDR, sensitivity, VIF, correlation checks, Bayesian CI
├── reports/
│   ├── __init__.py
│   └── generate.py      # SHAP, parity plots, partial dependence, disclaimer
├── validate_references.py  # invokes Reference‑Validator Agent
├── main.py              # orchestration script
└── requirements.txt
```

## Complexity Tracking & Methodological Safeguards

| Complexity | Reason | Mitigation |
|------------|--------|------------|
| **ILR Transformation** | Compositional closure creates singular matrices. | Apply `scikit‑bio.ilr` to composition before any regression. |
| **Residual Target** | Predicting absolute bulk modulus risks physics leakage. | Model **residual bulk modulus** (`B_obs - B_Miedema`) as target; **mixing enthalpy excluded** from predictors. |
| **Baseline-Descriptor Circularity** | Miedema inputs (radius, electronegativity) overlap with descriptors. | **Task T016**: Verify orthogonality. **Task T017**: Residualize predictors against Miedema inputs if correlation > 0.3. |
| **Grouped Bootstrap** | Potential leakage across chemically similar alloys. | Sample by **unique element set** (unordered) – defined in Task T010. |
| **Low Group Count (<30)** | Bootstrap variance unstable. | **Task T011**: Switch to **Bayesian Hierarchical Bootstrap** (weakly informative prior) to compute valid 95% CIs. |
| **Sample Size / Signal Strength** | Power may be limited if residual variance is low. | **Task T018**: Pre-check residual variance. **Task T013**: Adjust power analysis based on observed signal-to-noise ratio. |
| **Descriptor‑Baseline Correlation** | Miedema baseline shares elemental inputs with descriptors. | Verify orthogonality via VIF and Pearson correlation (Task T016); residualize if needed (Task T017). |
| **GPU / Heavy Models** | CI runners have no GPU. | All models trained with `n_jobs=1` on CPU; no GPU flags allowed. |

## Task List

| ID | Description | FR / SC Addressed |
|----|-------------|-------------------|
| **T001** | Run `python code/validate_references.py` to invoke the Reference‑Validator Agent. **Exit codes**: 0 = all citations verified, 1 = mismatch, 2 = unreachable. | – |
| **T002** | Retrieve HEA compositions and elastic constants from Materials Project and OQMD APIs (filter: ≥5 principal elements, elastic constants present). Save raw JSON/CSV to `data/raw/`. Record total count; if `<500`, log `"Retrieved X samples; threshold 500 not met"` and halt. | **FR‑001** |
| **T003** | Compute compositional descriptors: mixing enthalpy (Miedema, **used only for baseline**), atomic radius variance, entropy of mixing, VEC, electronegativity variance. Store in `data/processed/descriptors.csv` **excluding** mixing enthalpy from the predictor matrix. | **FR‑002** |
| **T004** | Apply ILR transformation to the normalized composition using `scikit‑bio.ilr`. Append `ilr_features` to `data/processed/features.csv`. | **FR‑003** |
| **T005** | Write `data/source_metadata.yaml` containing API version, query parameters, and SHA‑256 checksum of each raw source. **Explicitly cite Constitution Principle VI**. | – |
| **T006** | Train Random Forest, Gradient Boosting, ElasticNet on **residual bulk modulus** (`B_obs - B_Miedema`) with `random_state=42`, `n_jobs=1`. Save models under `results/models/`. | **FR‑004** |
| **T007** | Evaluate models: compute R², RMSE, MAE on held‑out test set; perform 1000‑iteration **grouped bootstrap** (group = unique element set) for 95 % CI of R²; run t‑test vs. R² = 0; apply Benjamini‑Hochberg FDR. Also perform VIF screening (VIF < 5) and Pearson correlation checks between residuals and each ILR component (warn if |r| > 0.3). Log power‑analysis results (ΔR² = 0.05). | **FR‑005**, **FR‑006**, scientific soundness‑e4a32cb0 |
| **T008** | Generate interpretability report: SHAP (global) and permutation importance, parity plots, partial dependence plots. Insert mandatory disclaimer: **\"Associational Disclaimer: All reported relationships are observational; no causal inference is claimed.\"** Save to `reports/summary.md`. | **FR‑007** |
| **T009** | Perform **sensitivity analysis** sweeping R² thresholds {0.25, 0.30, 0.35}. For each threshold compute false‑positive rate; write `results/sensitivity.json` with fields `thresholds_tested` and `fpr_variance` (variance across thresholds). | **FR‑006** |
| **T010** | Define grouping key for bootstrap as the **unordered set of constituent elements** (e.g., `{'Cr','Fe','Co','Ni','Mn'}`). Use this key in Task T007. | methodological‑9f9b7ae8 |
| **T011** | **Low‑Group Fallback**: If number of unique groups < 30, log warning and switch to **Bayesian Hierarchical Bootstrap** (weakly informative prior on group variance) to compute 95% CIs. **Do not omit CIs or use heuristics.** | methodological‑9f9b7ae8, spec_coverage‑497e5c7b, spec_coverage‑6bf522c7 |
| **T012** | **Orthogonality Validation**: Compute Pearson correlation between the residual target and each predictor (including ILR components). If any |r| > 0.3, log a warning and flag the residual target as potentially confounded. | methodological‑b49c576e, scientific_soundness‑e4a32cb0 |
| **T013** | **Power Analysis**: Using `statsmodels.stats.power.FTestPower`, calculate required sample size for detecting ΔR² = 0.05 with α = 0.05, power = 0.8. **Condition this on the residual variance estimate from T018.** Log the result and compare to actual sample count. | methodological‑6627bfc5 |
| **T014** | **CPU‑Only Guard**: Enforce `device='cpu'` and `n_jobs=1` in all sklearn calls; abort if any GPU flag detected. | **FR‑004**, compute‑constraint |
| **T015** | **Descriptor‑Baseline Decoupling**: Ensure mixing enthalpy is *only* used to compute `miedema_baseline` and never appears in the predictor matrix passed to training scripts. | scientific_soundness‑b4dbf1ec |
| **T016** | **Baseline-Descriptor Orthogonality Check**: Compute Pearson correlation between each predictor (radius variance, VEC, etc.) and the **inputs** of the Miedema Bulk Modulus model (electron density, electronegativity). If any |r| > 0.3, flag for residualization. | scientific_soundness‑e4a32cb0, methodology‑6f01c211 |
| **T017** | **Predictor Residualization**: If T016 flags high correlation, regress each predictor against the Miedema inputs and use the **residuals** as the new predictors to ensure independence from the baseline model's functional form. | scientific_soundness‑e4a32cb0, methodology‑6f01c211 |
| **T018** | **Residual Variance Pre-Check**: Calculate the variance of the residual target (`B_obs - B_Miedema`). If variance is < 5% of total bulk modulus variance, flag the study as potentially underpowered for the assumed effect size and adjust ΔR² in T013 accordingly. | methodology‑6627bfc5 |

*All tasks are ordered so that data download (T002) precedes cleaning/feature engineering (T003‑T004), provenance recording (T005), orthogonality/power checks (T012‑T018), model training (T006/T014), evaluation (T007/T011), interpretability/reporting (T008), and sensitivity analysis (T009/T010). The fallback tasks (T011) are invoked conditionally after group‑count assessment.*

## Deliverables

- `data/raw/` – raw API dumps with checksums.  
- `data/processed/` – cleaned CSV, descriptors, ILR features, residual target, and (if T017 runs) residualized predictors.  
- `results/models/` – serialized sklearn models.  
- `results/metrics.yaml` – R², RMSE, MAE, 95 % CI (standard or Bayesian), p‑values, FDR flags.  
- `results/sensitivity.json` – threshold sweep variance.  
- `reports/summary.md` – visualizations + associational disclaimer.  
- `data/source_metadata.yaml` – provenance per Constitution Principle VI.  