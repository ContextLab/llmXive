# Research: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

## Overview
This research plan details how we will answer the core question: *How do surface‑treatment parameters **associate** with polymer adhesion strength?* The plan explicitly acknowledges that **no verified open dataset** containing the required variables is currently available (see Verified datasets block). Consequently, the pipeline cannot produce empirical evidence for SC‑001 or SC‑002 with real data at this time. The plan therefore serves as a **methodological demonstration** that will become fully empirical once an appropriate dataset is obtained.

## Dataset Strategy
| Source | Variable Coverage* | Access Method | Verified URL |
|--------|-------------------|---------------|--------------|
| **Open dataset (to be identified)** | Must contain all required predictors (`plasma_power_w`, `exposure_time_s`, `chemical_concentration_pct`, `polymer_surface_energy`, `substrate_roughness_nm`) **and** target `adhesion_strength_mj_m2`, plus `treatment_type` and `pair_id`. | Programmatic download via `wget`/`curl` or `datasets.load_dataset`. | **None currently meet the requirement** – see “Data Availability & Mitigation” in the plan. |
| **Synthetic generator (illustrative only)** | Full coverage of all required fields (generated deterministically). | `python code/generate_synthetic.py` → `data/raw/synthetic_adhesion.csv` (used only for pipeline verification). | N/A (synthetic) |

\*Coverage is [deferred] by construction for the synthetic generator; real datasets must be verified to meet this coverage.

### Decision & Rationale
- **Primary choice:** Await acquisition of a verified open dataset that satisfies FR‑001. The pipeline is ready to ingest such a dataset once it becomes available.
- **Illustrative fallback:** A deterministic synthetic generator (seed = 42) is provided to exercise the full analysis workflow and to validate that all scripts, schemas, and contract tests function correctly. Results derived from this synthetic data are **clearly labeled as illustrative** and **do not count toward SC‑001 or SC‑002**.
- **Power‑analysis guardrail:** When a real dataset is supplied, the pipeline will first verify that it contains **≥ 200 usable records** (the a‑priori power target for detecting a medium effect with α = 0.05, power = 0.8). The synthetic dataset exceeds this threshold, ensuring that the pipeline can demonstrate statistical machinery, but the scientific claims remain illustrative.

## Methodology
1. **Data Ingestion & Validation** – Download the identified open dataset; parse CSV/JSON files into a unified pandas DataFrame; validate each record against `contracts/treatment_record.schema.yaml`. If no dataset is present, the step aborts with a clear error message.  
2. **Pre‑processing** – Convert any non‑SI units using a generated `adhesion_units.json`; canonicalise `treatment_type` via a taxonomy dict; median‑impute missing numeric values per substrate class; add missing‑indicator columns; log all transformations.  
3. **Grouped Split** – 70/15/15 split **grouped by `pair_id`**; exclude groups with < 5 records (FR‑011).  
4. **Model Training** – Grid search ≤ 50 combos across Random Forest, Gradient Boosting, Linear Regression; compute **block‑bootstrap confidence interval for validation R²** (10 000 resamples, resampling whole `pair_id` groups).  
5. **Model Selection & Threshold Justification** – Choose the model whose **validation R² lower‑CI ≥ 0.5** **and** permutation p‑value < 0.05. **If no model meets both**, produce a documented “null” result per FR‑012 and clearly flag the failure of SC‑001/SC‑002.  
6. **Permutation Significance Test** *(conditional)* – If a real dataset is available, run a permutation test with a substantial number of shuffles on the held‑out test set to obtain an empirical p‑value for the observed R². This step is **skipped for synthetic‑only runs** because exchangeability is violated.  
7. **Confounder & Random‑Effects Modeling** *(optional)* – Fit a mixed‑effects model (`statsmodels.MixedLM`) with `pair_id` random intercept; compare performance to primary models; report differences.  
8. **SHAP Interpretability** – Use `shap.TreeExplainer` for tree models; fallback to `shap.LinearExplainer` or `shap.KernelExplainer` for linear models (FR‑015). Produce PNG summary and JSON ranking.  
9. **Report Generation** – Compile JSON and Markdown reports containing: validation & test R² (with CI), RMSE, MAE, permutation p‑value (if computed), top‑3 SHAP features, per‑predictor p‑values (where applicable), mixed‑effects summary (if run), and the four required visualizations (FR‑014). The report explicitly states whether the analysis is **illustrative** (due to lack of real data) or **empirical** (if real data are supplied).

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No verified real dataset | Cannot answer the scientific question; only illustrative results possible. | Flag the limitation early; request dataset acquisition or adjust the research scope; keep the pipeline ready for when data become available. |
| Synthetic target may be deterministic | Artificially high R² and trivial permutation p‑values would be misleading. | Use synthetic data **only for pipeline validation**; never claim scientific success criteria based on it; clearly label all synthetic results as illustrative. |
| Sparse polymer‑substrate groups (even in synthetic data) | Reduced effective sample size. | Generator ensures ≥ 5 records per `pair_id`; any group failing this is excluded per FR‑011 and logged. |
| Runtime > 6 h | CI job failure. | Limit hyper‑parameter grid to ≤ 50 combos; use `n_jobs=1`; block‑bootstrap and permutation steps are vectorized; total estimated time ≈ 4 h. |

## Expected Deliverables
- `data/raw/<dataset>.csv` – the verified raw dataset (once identified).  
- `data/raw/adhesion_units.json` – unit‑metadata JSON (generated from source metadata).  
- `data/cleaned/cleaned.csv` – fully standardized dataset.  
- `data/cleaned/train.csv`, `val.csv`, `test.csv` – grouped splits.  
- `models/<model_type>.pkl` – serialized best model artifact.  
- `results/report.json` & `results/report.md` – complete analysis output (illustrative if synthetic, empirical if real).  
- `figures/` – PNGs: predicted‑vs‑actual scatter, residual histogram, SHAP summary, parameter‑response curves.  
- `contracts/` – schema files for `TreatmentRecord`, `ModelArtifact`, and `AnalysisResult`.  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed random seeds; deterministic synthetic generator (if used); immutable URLs; checksums guarantee identical inputs. |
| II. Verified Accuracy | No unverified external citations; only URLs from the verified block are referenced (for documentation only). |
| III. Data Hygiene | Raw files are read‑only; each transformation writes a new file; SHA‑256 checksums recorded for every artifact. |
| IV. Single Source of Truth | All figures/tables are generated directly from the JSON report; no manual transcription. |
| V. Versioning Discipline | Artifact hashes are computed; any change updates the project state file. |
| VI. Computational Model Stability and Parsimony | Hyper‑parameter grid ≤ 50 combos; model acceptance requires **validation R² lower‑CI ≥ 0.5** **and** permutation p < 0.05 (or a labeled null result). |
| VII. Material‑Specific Feature Engineering Integrity | Unit conversion, median imputation per substrate class, missingness indicators, canonical treatment taxonomy, and `pair_id` covariate are enforced in Phase 2. |
| **Associational Framing** | Methodology explicitly states that the analysis is associational; no causal claims are made. |
| **Data‑Source Limitation** | The lack of a verified real dataset is acknowledged; synthetic data are used solely for pipeline validation and are clearly labeled as illustrative. |

---

