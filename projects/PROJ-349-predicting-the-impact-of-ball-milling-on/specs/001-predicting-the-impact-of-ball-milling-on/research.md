# Research: Predicting the Impact of Ball Milling on Particle Size Distribution

## Overview
This document details the scientific decisions, dataset strategy, modeling choices, and validation procedures that will be implemented in the pipeline described in `plan.md`. All choices respect the project's constitution and the free‑tier CI constraints.

**Associational Nature**: Due to the observational nature of the data (no random assignment of milling parameters), all findings, interpretations, and the term "impact" in the title are strictly **associational**. The model predicts PSD outcomes based on milling parameters but does not claim causal effects. Confounding by material properties or unmeasured milling conditions is acknowledged.

## Dataset Strategy

| Source | Access Method | Expected Variables | Verified URL (if any) |
|--------|---------------|--------------------|-----------------------|
| Materials Project API | `requests` + MP REST endpoint | milling_speed_rpm, milling_time_hours, ball_to_powder_ratio, material_type, youngs_modulus_gpa, density_gcm3, process_duration_hours, D10/D50/D90 (if reported) | *Named Source: Specific MP IDs extracted during ingestion* |
| NIST Materials Data Repository | Direct download of CSV/JSON files (public URLs) | Same as above | *Named Source: Specific DOIs extracted during ingestion* |
| arXiv literature extraction | `pdfminer.six` + regex table parsing on selected arXiv IDs | Same as above (where reported) | *Named Source: Specific arXiv IDs extracted during ingestion* |
| Synthetic Prototyping Data | Generated via `numpy` to match `contracts/dataset.schema.yaml` | All required predictors and targets | *N/A (Synthetic)* |

> **Note**: The three primary sources (Materials Project, NIST, arXiv) are referenced as "Named Sources" because the specific ball-milling subset structure is not guaranteed. The ingestion scripts will search/filter for relevant records and extract specific accession IDs (MP IDs, DOIs, arXiv IDs) to populate `source_id`, satisfying Principle VII. The synthetic dataset is used solely for methodological prototyping and schema validation, as no verified ball-milling benchmark exists in the provided list.

### Expected Dataset Size & Coverage
- Target: ≥ 500 unique experiments with complete predictor & PSD fields (SC‑004).  
- Minimum viable: ≥ 150 experiments (US‑1).  
- If after full ingestion the count < 150, the pipeline will abort with a critical error (FR‑001, FR‑009).

## Preprocessing Decisions
- **Missing Data**: IterativeImputer (multiple imputation) with a sufficient number of iterations. **Crucially, target variables (D10, D50, D90) are EXCLUDED from the imputation feature set** to prevent data leakage. Imputation uses only predictors: milling speed, time, ratio, material properties.  
- **Normalization**: `StandardScaler` applied to all numeric predictors after imputation.  
- **Unstructured PSD**: Images or raw curves will be detected via file‑extension or MIME type; such rows are logged to `flagged_psd.log` and excluded from modeling (FR‑008).  

## Modeling Choices
| Model | Rationale | Hyper‑parameters (CPU‑friendly) |
|-------|-----------|---------------------------------|
| Gaussian Process Regression (GPR) | Captures smooth nonlinear relationships; provides uncertainty estimates. | Kernel = RBF + WhiteNoise with ARD; `n_restarts_optimizer=2`; max_iter=500 |
| Random Forest (RF) | Robust to collinearity; fast training on modest data sizes. | `n_estimators=500`; `max_depth=None`; `min_samples_leaf=1` |
| Linear Regression (Baseline) | Provides a simple reference for statistical testing. | Ordinary Least Squares (no regularization) |

- **Cross‑validation**: **Nested Cross-Validation (5x2)** for all models.  
  - **Outer Loop (5 folds)**: Provides unbiased performance estimates.  
  - **Inner Loop (2 folds)**: Used for hyperparameter tuning.  
  - **Stratification Strategy**: Folds are stratified by **binned D50** (target variable) rather than `material_type`.  
    - *Rationale*: Stratifying by material type risks bias if certain materials consistently produce finer/coarser particles, leading to folds with different target distributions. Stratifying by binned target ensures the distribution of the outcome (PSD) is preserved across folds, providing a more robust estimate of generalization error for the regression task.  
- **Fallback**: If GPR runtime > 30 min **or** peak memory > 5 GB, the pipeline aborts GPR training, logs a fallback event, and proceeds with RF only (FR‑009).  

## Evaluation & Statistical Rigor
- **Metrics**: R², RMSE, MAE computed on the **outer folds** of the Nested CV.  
- **Success Thresholds**: Primary R² > 0.6; Secondary R² > 0.3 (SC‑001).  
- **Statistical Testing**: **Nadeau & Bengio corrected resampled t-test** comparing the outer-fold R² scores of each ML model against the baseline (α = 0.05). This corrects for the dependence between training and testing sets in cross-validation, addressing the invalidity of standard paired t-tests on CV scores.  
- **Multiple Comparisons**: Bonferroni correction applied (α_adj = 0.025) for two ML models tested against the baseline.  
- **Power Analysis**: **A priori** sensitivity analysis using `statsmodels.stats.power.FTestPower`. We hypothesize a small-to-medium effect size (Cohen's f² = 0.15) based on literature expectations. The report will state the **minimum detectable effect size** given the actual sample size (N), avoiding circular post-hoc power calculations.  
- **Assumptions Disclosure**: Observational data → results are **associational, not causal**. Collinearity among speed, time, and ratio will be examined; if VIF > 5, we will report the issue but still present model scores (no claim of independent effects).  

## Computational Feasibility
- **Runtime Budgets**:  
  - Ingestion & preprocessing ≤ 1 h.  
  - Nested CV training (GPR/RF) ≤ 3 h (with fallback to RF only if GPR exceeds limits).  
  - Evaluation & plotting ≤ 30 min.  
- **Memory**: All pandas dataframes kept under ~3 GB; scikit-learn models use ≤ 1 GB.  
- **CI Integration**: The GitHub Actions workflow enforces a **6-hour** timeout; any step exceeding its sub-budget will trigger the fallback logic.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient ball‑milling experiments (< 150) | Blocked modeling (SC‑004) | Early abort with clear log; fallback to literature review only. |
| GPR exceeds resource limits | CI job failure | Automatic switch to RF only (FR‑009). |
| Missing Young’s modulus for novel materials | Imputation may reduce validity | Flag such rows; optionally request manual lookup. |
| Duplicate experiments with conflicting PSD | Data quality issue | Deduplicate by `experiment_id`; average conflicting PSD values, log rule. |
| **Material Bias in Stratification** | **Overfitting to material-specific trends** | **Use binned target (D50) stratification instead of material_type to ensure target distribution similarity across folds.** |