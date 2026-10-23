# Implementation Plan: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

**Branch**: `001-predicting-adhesion-strength` | **Date**: 2026-10-23 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-predicting-adhesion-strength/spec.md`

## Summary
The pipeline must (1) acquire a **verified open dataset** that contains the required treatment‑parameter and adhesion‑strength variables, (2) standardize units and canonicalize categorical values, (3) split the data by polymer‑substrate pair while handling sparse groups, (4) train three regression models (Random Forest, Gradient Boosting, Linear Regression) with ≤ 50 hyper‑parameter combos, (5) select the best model based on **validation‑R² lower‑CI ≥ 0.5** *and* a **permutation‑test p‑value < 0.05** (or produce a documented “null” result per FR‑012), (6) generate SHAP explanations (with Linear/Kernel fallback), and (7) output reproducible JSON + Markdown reports with all required metrics and four visualizations. All steps respect FR‑001 – FR‑015 and SC‑001 – SC‑006.

### Data Availability & Mitigation
- **Verified dataset search**: The specification lists NIST, Zenodo, and Materials Project as sources. A systematic check of the “Verified datasets” block reveals that none of the publicly downloadable URLs contain **all** required variables (`plasma_power_w`, `exposure_time_s`, `chemical_concentration_pct`, `polymer_surface_energy`, `substrate_roughness_nm`, `adhesion_strength_mj_m2`). Consequently, **FR‑001 cannot be satisfied with currently available open data**.
- **Scope implication**: Without a suitable dataset, the core research question (associating surface‑treatment parameters with real adhesion strength) cannot be empirically answered. The plan therefore **flags this limitation** and recommends a **specification revision** to either (a) identify an appropriate open dataset, or (b) adjust the research goal to a methodological demonstration using a synthetic benchmark (which would be clearly labeled as illustrative and would not claim fulfillment of SC‑001/SC‑002).
- **Power‑analysis guardrail**: If a real dataset is supplied, the pipeline will first verify that it contains ≥ 200 usable records (the a‑priori power target for detecting a medium effect with α = 0.05, power = 0.8). The check aborts with a clear error if the threshold is not met.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas>=2.2`  
  - `numpy>=1.26`  
  - `scikit-learn>=1.5`  
  - `shap>=0.45`  
  - `statsmodels>=0.14` (mixed‑effects)  
  - `tqdm>=4.66`  
  - `pyyaml>=6.0` (schema validation)  
- **Storage**: CSV/Parquet files under `data/` (raw, cleaned, splits).  
- **Testing**: `pytest>=8.2` with contract‑validation tests.  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h wall‑clock).  
- **Constraints**: All methods are CPU‑compatible; no GPU is required.  

## Phase Overview & FR/SC Mapping
| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|-----------------|
| **0. Constitution & Feasibility Check** | Verify compliance with all constitution principles; run a power analysis (target R² = 0.5, α = 0.05, power = 0.8 → ≈ 200 records). Abort if the real dataset is insufficient. | – | SC‑001 (via power check) |
| **1. Data Ingestion & Validation** | Download verified open datasets (if any); parse CSV/JSON files into a unified pandas DataFrame; validate against `contracts/treatment_record.schema.yaml`. | FR‑001, FR‑008, FR‑009 | SC‑005 |
| **2. Pre‑processing** | Convert any non‑SI units using per‑source unit‑metadata JSON (`adhesion_units.json`); canonicalise `treatment_type` via a taxonomy dict; median‑impute missing numeric values per substrate class; add missing‑indicator columns; log all transformations. | FR‑002, FR‑008, FR‑009, FR‑011 | SC‑005 |
| **3. Grouped Train/Val/Test Split** | Perform a 70/15/15 split **grouped by `pair_id`**; exclude groups with < 5 records (FR‑011). | FR‑010, FR‑011 | SC‑005 |
| **4. Model Training & Hyper‑parameter Search** | Grid search ≤ 50 combos across Random Forest, Gradient Boosting, Linear Regression; compute **block‑bootstrap 95 % CI for validation R²** (10 000 resamples, resampling whole `pair_id` groups). | FR‑003, FR‑010, FR‑012 | SC‑001, SC‑003, SC‑005 |
| **5. Model Selection & Threshold Justification** | Select the model whose **validation R² lower‑CI ≥ 0.5** **and** permutation‑test p‑value < 0.05. If none meet both, produce a documented “null” result per FR‑012 and clearly flag failure of SC‑001/SC‑002. | FR‑003, FR‑012 | SC‑001, SC‑002, SC‑003 |
| **6. Permutation Significance Test** *(conditional)* | If a real dataset is present, run a permutation test with a sufficiently large number of shuffles on the held‑out test set to obtain an empirical p‑value for the observed R². This step is **omitted for synthetic-only runs** because exchangeability is violated. | FR‑005 | SC‑002 |
| **6b. Confounder & Random‑Effects Modeling** *(optional)* | Fit a mixed‑effects model (`statsmodels.MixedLM`) with `pair_id` random intercept; compare to primary models; report differences. | FR‑013 (via added covariates) | SC‑001, SC‑004 |
| **7. SHAP Interpretability** | Use `shap.TreeExplainer` for tree models; fallback to `shap.LinearExplainer` or `shap.KernelExplainer` for linear models (FR‑015). Produce PNG summary and JSON ranking. | FR‑006, FR‑015 | SC‑004 |
| **8. Report Generation** | Assemble JSON & Markdown report containing: validation & test R² (with CI), RMSE, MAE, permutation p‑value (if computed), top‑3 SHAP features, per‑predictor p‑values (where applicable), mixed‑effects summary (if run), and the four required visualizations (FR‑014). The report explicitly states whether the analysis is **illustrative** (due to lack of real data) or **empirical** (if real data are supplied). | FR‑007, FR‑014, FR‑012, FR‑013 | SC‑001, SC‑002, SC‑006 |
| **9. Constitution Check** | Verify that all steps respect the constitution (reproducibility, data hygiene, single source of truth, versioning, parsimony, feature‑engineering integrity, associational framing, and data‑source limitation). | – | – |

## Compute Feasibility
- Model training: `n_estimators ≤ 200`, `n_jobs=1` → ≤ 2 GB RAM.  
- Permutation test (if executed) on ≤ 5 000 records completes in ≈ 1 h.  
- Estimated total wall‑clock time: **≈ 4 h** (well under the 6 h CI limit).

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Random seeds (`np.random.seed(42)`, `random_state=42`) are fixed; dataset downloads are deterministic; checksums guarantee identical inputs. |
| II. Verified Accuracy | No unverified external citations are introduced; only URLs from the verified block are referenced (for documentation). |
| III. Data Hygiene | Raw files are read‑only; each transformation writes a new file; SHA‑256 checksums recorded for every artifact. |
| IV. Single Source of Truth | All figures/tables are generated directly from the JSON report; no manual transcription. |
| V. Versioning Discipline | Artifact hashes are computed; any change updates the project state file. |
| VI. Computational Model Stability and Parsimony | Hyper‑parameter grid ≤ 50 combos; model acceptance requires **validation R² lower‑CI ≥ 0.5** **and** permutation p < 0.05 (or a labeled null result). |
| VII. Material‑Specific Feature Engineering Integrity | Unit conversion, median imputation per substrate class, missingness indicators, canonical treatment taxonomy, and `pair_id` covariate are enforced in Phase 2. |
| **Associational Framing** | Methodology explicitly states that the analysis is associational; no causal claims are made. |
| **Data‑Source Limitation** | The absence of a verified real dataset is acknowledged; synthetic data (if ever used) are for pipeline validation only and are clearly labeled as illustrative. |

---

