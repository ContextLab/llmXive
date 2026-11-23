# Implementation Plan: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

**Branch**: `001-gene-regulation` | **Date**: 2026-10-25 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The pipeline must (1) ingest a curated literature CSV of metallic‑glass compositions and measured CTE values, optionally augment it with composition‑only entries from the Materials Project (MP) and AFLOWlib APIs; (2) compute four elemental descriptors (weighted mean atomic radius, electronegativity variance, valence‑electron concentration, atomic‑size coefficient of variation); (3) mitigate multicollinearity via VIF filtering with a PCA‑Ridge fallback; (4) split data by alloy family using GroupKFold (fallback to random split); (5) train linear‑regression and random‑forest models with 5‑fold CV; (6) compare against a baseline weighted‑average elemental‑CTE model; (7) assess statistical significance with ≥ 1 000 permutation iterations; (8) generate feature‑importance rankings and rank‑correlation diagnostics; (9) log runtime and memory to verify free‑tier limits. All steps run on CPU only; any step that would exceed the 7 GB RAM / 2‑core limit aborts with a clear error.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `pymatgen==2024.*` (Materials Project API), `mendeleev==0.12.*` (elemental properties), `statsmodels==0.14.*` (VIF), `joblib`, `psutil`, `jsonschema`, `ruff==0.6.*`  
- **Storage**: CSV/Parquet under `data/` (raw, processed, splits); model pickles under `models/`  
- **Testing**: `pytest==8.*` with JSON‑Schema validation (`jsonschema`)  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Constraints**: ≤ 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h wall‑clock; CPU‑first (no GPU).  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts set `np.random.seed(42)` and `random.seed(42)` at import; deterministic file paths; no manual intervention required. |
| II. Verified Accuracy | All external data sources are either the user‑provided CSV (part of the repository) or open APIs (Materials Project, AFLOWlib) that are publicly documented; elemental properties come from the verified `mendeleev` package. |
| III. Data Hygiene | Raw API responses and the original CSV are saved with SHA‑256 checksums (`data/checksums.txt`). Processed rows receive a per‑row `checksum` column. |
| IV. Single Source of Truth | Every figure, statistic, and model output references a single row in `data/processed/clean_alloy_data.parquet`. |
| V. Versioning Discipline | All artifacts are content‑hashed; CI updates the `state/projects/...yaml` artifact‑hash map automatically. |
| VI. Compositional Feature Engineering Integrity | Only the four elemental descriptors are used as predictors; no structural or thermal‑history variables enter the models. |
| VII. Numerical Stability and Resource Constrained Validation | Models trained with scikit‑learn on ≤2 cores; 5‑fold GroupKFold; 1 000‑iteration permutation test; VIF filtering; runtime & memory logged against free‑tier limits. |
| Fixed‑Seed Policy | Every stochastic component (`train_test_split`, `GroupKFold`, model `random_state`, permutation shuffling, `joblib`) uses seed 42. |

## Mapping of Functional & Success Requirements to Plan Phases
| FR / SC | Covered Phase(s) |
|---------|-------------------|
| FR‑001 (data retrieval) | **Phase 0 – Ingestion & Coverage Check** |
| FR‑002 (descriptor extraction) | **Phase 1 – Feature Extraction** |
| FR‑003 (stratified split) | **Phase 2 – Train/Test Split** |
| FR‑004 (model training & CV) | **Phase 3 – Model Training** |
| FR‑005 (permutation test) | **Phase 5 – Significance Testing** |
| FR‑006 (feature importance) | **Phase 5 – Feature‑Importance Ranking** |
| FR‑007 (resource limits) | **All Phases** |
| FR‑008 (VIF & PCA fallback) | **Phase 1 – Multicollinearity Mitigation** |
| FR‑009 (metadata & sensitivity) | **Phase 0 – Metadata Capture & Sensitivity** |
| FR‑010 (fixed seeds) | **All Phases** |
| FR‑011 (power analysis) | **Phase 0 – Power / Sample‑Size Check** |
| FR‑012 (metadata flagging) | **Phase 0 – Duplicate of FR‑009** |
| SC‑001 (ΔR² > 0.05 over baseline) | **Phase 4 – Baseline Comparison** |
| SC‑002 (permutation p‑value) | **Phase 5 – Permutation Test** |
| SC‑003 (Spearman & Kendall‑τ) | **Phase 5 – Correlation Diagnostics** |
| SC‑004 (efficiency limits) | **Phase 6 – Resource Logging** |
| SC‑005 (≥ 95 % coverage, ≥ 500 entries) | **Phase 0 – Coverage Verification** |

## Scope Limitation & Revised Objective
- **Data Availability**: The curated CSV is expected to be present in the repository (`data/raw/curated_metallic_glass.csv`). No open‑source API provides amorphous‑phase flags or measured CTE values; MP and AFLOW can only supply composition strings. Consequently, CTE values are taken **exclusively** from the curated CSV.  
- **Baseline Data Source**: Elemental CTE values for the baseline model are sourced from the **experimental NIST Thermophysical Properties database** (open CSV). If an element lacks an experimental entry, the DFT‑derived value from Materials Project is used and a `baseline_source_mismatch: true` flag is recorded.  
- **Termination Condition**: After merging and filtering, if the final dataset contains **< 95 %** of the rows from the original CSV **or** fewer than **500** usable samples, the pipeline writes `results/ingestion_coverage.json` with a `"Specification Amendment Required"` flag and **stops** before any modeling.  

## Phased Execution Plan

### Phase 0 – Data Ingestion, Metadata Capture, Coverage & Power Analysis
1. Load `data/raw/curated_metallic_glass.csv` (must contain `material_id`, `composition`, `cte`).  
2. Query the Materials Project via `pymatgen.ext.matproj.MPRester` (free API key `MP_API_KEY`) for records whose `description` contains the keyword “glass”. Retrieve only `material_id` and `composition`.  
3. (Optional) Query AFLOWlib REST endpoint for the same keyword; if the endpoint fails, log a warning and continue with MP data only.  
4. Concatenate CSV and API results, de‑duplicate on `material_id`.  
5. Filter to keep entries flagged as amorphous in the CSV **or** whose description contains “glass”. Exclude rows with missing `cte` or malformed formulas; log counts.  
6. Extract any available `source_method` (`DFT`/`Experimental`) and `thermal_history` metadata from the CSV; if > 20 % of rows lack these fields, run a sensitivity analysis on the subset with complete metadata (train/evaluate models on that subset, compute ΔR² vs. full set) and store `results/metadata_sensitivity.json`. Otherwise, flag incomplete entries in `results/metadata_flags.csv`.  
7. Compute a SHA‑256 checksum for each row (JSON‑serialised, sorted keys) and store in a new column `checksum`.  
8. **Coverage Verification**:  
   - `coverage = retrieved_entries / csv_entries`.  
   - If `coverage ≥ 0.95` **and** `total_entries ≥ 500`, proceed.  
   - Else, write `results/ingestion_coverage.json` with `{coverage, total_entries, status:"Specification Amendment Required"}` and **terminate**.  
9. **Power Analysis**: Using the final usable `N`, compute required sample size for detecting `f² = 0.15` at α = 0.05, power = 0.8 (≈ 500). Save `results/power_analysis.txt`; if power < 0.8, note the limitation.  

### Phase 1 – Feature Extraction & Multicollinearity Mitigation
1. Parse each `composition` with `pymatgen.Composition` to obtain element fractions.  
2. Load elemental properties from `mendeleev` (atomic radius, Pauling electronegativity, valence electron count).  
3. Compute the four descriptors:  
   - **Weighted mean atomic radius** Σ fraction × radius.  
   - **Electronegativity variance** (weighted variance).  
   - **Valence electron concentration (VEC)** Σ fraction × valence.  
   - **Atomic size coefficient of variation** = σ(radius) / μ(radius).  
4. Add a column `alloy_family` = sorted, comma‑separated list of element symbols (e.g., `"Al,Cu,Zr"`).  
5. Compute VIF for each descriptor using `statsmodels`.  
   - Drop any descriptor with VIF > 5.0, **unless** it is `weighted_mean_atomic_radius` (retain preferentially).  
   - If **all** descriptors exceed VIF > 5.0, retain the descriptor with the lowest VIF, apply **PCA** to the four‑dimensional space, retain the first two components (≥ 95 % variance), and plan to train a **Ridge Regression** model on these components (fallback satisfies FR‑008).  
6. Save the cleaned DataFrame to `data/processed/clean_alloy_data.parquet`. Store the VIF report at `results/vif_report.csv`.  

### Phase 2 – Train/Test Split
1. Attempt a 5‑fold **GroupKFold** split using `alloy_family` as the grouping key.  
2. If any family has < 5 samples, fall back to a stratified random 80/20 split (`train_test_split(random_state=42)`).  
3. Persist `train.parquet` and `test.parquet` under `data/processed/`.  

### Phase 3 – Model Training & Cross‑Validation
1. **Linear Regression**: `sklearn.linear_model.LinearRegression` (no hyper‑parameters).  
2. **Random Forest**: grid‑search over  
   - `n_estimators = [100, 200]`  
   - `max_depth = [None, 10, 20]`  
   - `min_samples_leaf = [1, 2]`  
   using `random_state=42`.  
3. Perform **5‑fold CV** on the training set (same folds as Phase 2). Record mean **R²**, **MAE**, **RMSE** for each hyper‑parameter combo.  
4. Select the best hyper‑parameters (highest mean R²) and fit final models on the full training data.  
5. Serialize models to `models/linear_regression.pkl`, `models/random_forest.pkl`.  

### Phase 4 – Baseline Comparison & ΔR² Check
1. Retrieve **experimental** elemental CTE values from the **NIST Thermophysical Properties** database (open CSV).  
2. For any element lacking an experimental entry, fall back to the DFT‑derived value from Materials Project and set `baseline_source_mismatch: true` in the results file.  
3. Compute a weighted‑average elemental CTE for each alloy using stoichiometric fractions.  
4. Train a baseline linear regression on this single predictor (no regularization).  
5. Evaluate baseline on the test set; store metrics in `results/baseline_metrics.json`.  
6. Compute `ΔR² = R²_best_model – R²_baseline`.  
   - If `ΔR² > 0.05` (SC‑001), flag success.  
   - Otherwise, record a warning in `results/baseline_comparison.json` and include the `baseline_source_mismatch` flag when applicable.  

### Phase 5 – Statistical Significance & Feature Importance
1. **Permutation Test** (≥ 1 000 iterations, `np.random.seed(42)`):  
   - Shuffle `y_train` while keeping `X_train` fixed.  
   - Re‑fit the selected best model (linear or random forest) on shuffled data.  
   - Compute R² on the original test set.  
   - Build the null distribution; compute a two‑sided p‑value as `prop(null_R² ≥ observed_R²)`.  
   - If observed `R² < 0.3`, set `null_result_flag=True` and store `p_value=null`.  
2. **Feature Importance**:  
   - Random Forest: `feature_importances_`.  
   - Linear Regression: absolute standardized coefficients.  
   - Rank descriptors; save `results/feature_importance.csv`.  
3. **Correlation Diagnostics**:  
   - Compute Pearson correlation between each descriptor and CTE on the training data; rank by absolute value.  
   - Compute **Spearman ρ** and **Kendall‑τ** between the importance ranking and the absolute‑correlation ranking; store both in `results/correlation_diagnostics.json`.  

### Phase 6 – Resource & Efficiency Reporting
1. Wrap each script with timing (`time.perf_counter`) and memory profiling (`psutil`).  
2. Append a summary line to `results/runtime_log.txt`.  
3. Consolidate into `results/computational_efficiency.json` containing: `runtime_seconds`, `memory_peak_mb`, `cores_used`, `limits_passed` (boolean).  

### Phase 7 – Contracts & Validation
1. Provide JSON‑Schema files under `contracts/` (`mg_dataset.schema.yaml`, `model_metrics.schema.yaml`, `model_output.schema.yaml`).  
2. Add unit tests in `tests/unit/` that load a tiny example row and validate against the schemas using `jsonschema`.  
3. Lint all code with `ruff` (line length < 88, no unused imports).  

## Compute Feasibility
All operations are CPU‑first. The largest in‑memory object is the processed DataFrame (< 10 k rows, ≈ 200 KB). Parallelism in the permutation test is limited to `n_jobs=2`. No GPU is required; the plan runs comfortably within the free‑tier limits.

## Power Analysis & Sample‑Size Justification
A conservative power analysis (α = 0.05, power = 0.80) for detecting `f² = 0.15` requires ≈ 500 samples. If the final usable sample size falls below 500, the analysis writes a warning in `results/power_analysis.txt` and all downstream statistical interpretations are qualified accordingly.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient metallic‑glass CTE entries | Low statistical power (SC‑004). | Power analysis; explicit coverage warning; Specification Amendment flag. |
| High VIF across all descriptors | Forces PCA fallback, reducing interpretability. | Document fallback; still satisfies FR‑008. |
| AFLOWlib endpoint downtime | Loss of supplemental data. | Log warning; continue with MP data only. |
| Runtime or memory overrun on CI | Job failure. | Phase 6 monitors limits; aborts early with clear error. |
| Mis‑identification of alloy families for stratification | Potential leakage. | Use full elemental set as grouping key; fallback to random split. |
| Permutation test randomness | Unstable p‑values. | Fixed random seed (`np.random.seed(42)`). |

---
