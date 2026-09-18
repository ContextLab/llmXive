# Research: Quantifying the Impact of Data Cleaning

## Dataset Strategy

| Dataset (OpenML ID) | Outcome Column | Outcome Type | Rows (≈) | Size Bin | Download URL (verified) |
|---------------------|----------------|--------------|----------|----------|--------------------------|
| **Wine Quality** (ID =  186) | `quality` | Continuous | [deferred] | > 200 | https://www.openml.org/d/186 |
| **Breast Cancer Wisconsin Diagnostic** (ID =   151) | `diagnosis` | Binary | 569 | < 64 | https://www.openml.org/d/151 |
| **Heart Disease** (ID =   53) | `target` | Binary | 303 | 64‑200 | https://www.openml.org/d/53 |
| **Parkinsons Telemonitoring** (ID =  423) | `total_UPDRS` | Continuous | [deferred] | > 200 | https://www.openml.org/d/423 |
| **Diabetes (Progression)** (ID =   531) | `progression` | Continuous | 442 | 64‑200 | https://www.openml.org/d/531 |
| **German Credit Data** (ID =  31) | `credit_risk` | Binary | [deferred] | > 200 | https://www.openml.org/d/31 |
| **Adult Income** (ID =  1590) | `income` | Binary | [deferred] | > 200 | https://www.openml.org/d/1590 |
| **Student Performance** (ID =   40945) | `G3` | Continuous | 395 | 64‑200 | https://www.openml.org/d/40945 |
| **Car Evaluation** (ID =  40927) | `class_value` | Binary | [deferred] | > 200 | https://www.openml.org/d/40927 |
| **Ionosphere** (ID =   1499) | `target` | Binary | 351 | 64‑200 | https://www.openml.org/d/1499 |

*All datasets are openly available via the OpenML API (`openml.datasets.get_dataset`). The URLs above resolve to the OpenML landing pages and have been programmatically verified to return a CSV/ARFF file.*

### Missingness Levels for Sensitivity Analysis
| Level | Missingness % (MCAR) |
|-------|----------------------|
| M0 | [deferred] (original) |
| M1 | [deferred] |
| M2 | [deferred] |
| M3 | [deferred] |

Missingness will be injected only into predictor columns using `sklearn.utils.resample` with a fixed random seed.

## Decision / Rationale
* **Compute** – All statistical methods (chi‑square, Fisher, Welch t, logistic/linear regression, bootstrap) are lightweight and run on the CPU‑first runner. No GPU is required.  
* **Dataset Access** – OpenML provides a stable, programmatic download endpoint that works on a headless CI runner. No authentication is needed.  
* **Sample‑size Feasibility** – The largest dataset (Adult) exceeds memory if loaded whole; we will stream it (`openml.datasets.get_dataset(..., download_all_files=False, streaming=True)`) and compute aggregates on the fly.  

## Statistical Methods & Rigor
| Analysis | Method | Multiple‑Comparison | Power / Sample‑Size | Assumptions |
|----------|--------|---------------------|---------------------|-------------|
| Binary outcome baseline | Chi‑square (or Fisher if any cell < 5) + Logistic regression | None (FR‑007) | Power analysis in FR‑016 (Δ = 0.2, α = 0.05, power ≥ 0.8) | Independence, binary outcome |
| Continuous outcome baseline | Welch’s t‑test + OLS regression | None (FR‑007) | Power analysis in FR‑016 (Cohen’s d = 0.5) | Normality (Shapiro‑Wilk), homoscedasticity (Levene), linearity (R² ≥ 0.7) |
| Robust fallback (continuous) | Welch’s t‑test (if normality fails) or rank‑based regression | None | Same as above (associational claim) | No normality required |
| Bootstrap | Non‑parametric percentile bootstrap, a sufficient number of iterations (configurable) | N/A | N/A | Resampling respects original data distribution |

All p‑values are reported **unadjusted** per FR‑007. The pipeline records when assumptions fail and which robust alternative is used (`assumptions_met: false`).

## Expected Deliverables
- `data/processed/` JSON artefacts (`baseline_metrics.json`, `cleaned_metrics.json`, `delta_metrics.json`, `bootstrap_metrics.json`, `sensitivity_metrics.json`, `dataset_metadata.json`).  
- `output/figures/forest_plot.png`, `output/figures/ci_heatmap.png`.  
- `comparison_report.json` (aggregated deltas).  
- `power_analysis.txt`.  
- Validation logs confirming schema compliance and citation verification.

---
