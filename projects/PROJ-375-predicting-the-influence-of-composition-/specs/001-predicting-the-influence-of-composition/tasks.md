# Tasks: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

**Inputs**: spec.md (US-1/US-2/US-3, FR-001–FR-009, SC-001–SC-005), plan.md (Phases 0–7), data-model.md, contracts/*.schema.yaml.  
**Revised**: This revision aligns all tasks with the specification, fixes verification artifacts, and adds missing steps to satisfy panel concerns.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [US1] Establish the runnable pipeline and input provenance: create `docs/quickstart.md` documenting (a) `MP_API_KEY` environment‑variable setup, (b) the exact run commands `python code/ingestion/fetch_data.py && python code/modeling/train.py && python code/modeling/evaluate.py`, and (c) the verified data sources: Materials Project via `pymatgen.ext.matproj.MPRester` (thermal‑properties endpoint) and the AFLOWlib public REST API at `[UNRESOLVED-CLAIM: https://aflowlib.org` — ConnectionError: HTTPSConnectionPool(host='aflowlib.org%60', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPSConnection(host='aflowlib.org%60', port=443): Failed to resolve 'aflowlib.org%60' ([Errno -2] Name or service not known)"))]. The project layout (`code/ingestion`, `code/features`, `code/modeling`, `code/utils`, `tests/unit`, `tests/integration`, `data/raw`, `data/processed`, `data/results`, `models`, `figures`, `docs`) is created on demand by the toolkit's `paths` helper. Reuse the existing `code/utils/io.py` fail‑loud loader and `compute_sha256`; a failed real fetch MUST raise — no synthetic fallback is permitted. Verification: the documented command sequence runs end‑to‑end and `logs/pipeline.log` records the source URLs and queries issued. <!-- FAILED-IN-EXECUTION: code/ingestion/fetch_data.py exit=1; code/modeling/train.py exit=1; code/modeling/evaluate.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingestion/fetch_data.py exit=1; code/modeling/train.py exit=1; code/modeling/evaluate.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingestion/fetch_data.py exit=1; code/modeling/train.py exit=1; code/modeling/evaluate.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingestion/fetch_data.py exit=1; code/modeling/train.py exit=1; code/modeling/evaluate.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingestion/fetch_data.py exit=1; code/modeling/train.py exit=1; code/modeling/evaluate.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingestion/fetch_data.py exit=1; code/modeling/train.py exit=1; code/modeling/evaluate.py exit=1 -->

- [ ] T002 [US1] Implement data ingestion, amorphous filtering, and feature extraction:   <!-- FAILED-IN-EXECUTION: code/ingestion/fetch_data.py exit=1 -->
  1. In `code/ingestion/fetch_data.py`, query MP for entries containing `thermal_expansion_coefficient`.  
  2. **Amorphous detection (FR‑001)** – first check the entry’s `material_type` metadata field for value `"amorphous"` or `"glass"`; if absent, search the entry description for the keyword `"glass"`. Only entries passing this check are kept. The previous heuristics (`entry.data['tags']`, `structure_type` substring, missing space‑group) are retained **only as documented fallback** if the primary fields are missing.  
  3. Query AFLOWlib (`property=thermal_expansion_coefficient&keywords=glass`) as supplemental source; warnings are logged on failure but the pipeline continues with MP data.  
  4. Save raw JSON responses under `data/raw/` and record SHA‑256 checksums in `data/checksums.txt`.  
  5. Extract `material_id, composition, cte, source_method, thermal_history, amorphous_flag`. Exclude entries with missing CTE or `amorphous_flag=False`.  
  6. Compute ingestion completeness ratio (collected / filtered‑returned) into `data/results/ingestion_stats.json`.  
  7. Emit `data/results/data_availability_report.json` detailing, per source, the raw hit count, post‑filter count, and valid‑CTE count.  
  8. **Graceful degradation (US‑1 scenario 1)** – if the final metallic‑glass subset contains **fewer than 500 entries**, log a warning and continue; abort only when the subset is empty.  
  9. In `code/features/descriptors.py`, parse compositions with `pymatgen.core.Composition`, load elemental properties from `mendeleev`, and compute the four descriptors (weighted mean atomic radius, electronegativity variance, VEC, atomic size coefficient of variation = σ/μ). Merge the source checksum into each row.  
  Verification: `data/processed/clean_mg_data.parquet` validates against `specs/001-predicting-the-influence-of-composition/contracts/mg_dataset.schema.yaml` (the well‑formed schema); `data/results/ingestion_stats.json` and `data/results/data_availability_report.json` exist and contain the required ratios.

- [ ] T003 [US1] Implement VIF multicollinearity handling, PCA fallback, and train/test split:  
  1. Compute VIF over the four descriptors using `statsmodels`. Drop any descriptor with VIF > 5.0, **prioritising retention of `weighted_mean_atomic_radius`**; drop `atomic_size_coefficient_of_variation` only if its VIF remains > 5.0 after the mean radius is kept.  
  2. **PCA fallback (FR‑008)** – if **all** descriptors exceed VIF > 5.0, apply PCA **retaining exactly the first two principal components** and use those two components as predictors for downstream modeling (no Ridge regression is added). Document the decision in `data/results/vif_report.txt`.  
  3. Define **alloy family** as the **set of all constituent elements** (e.g., `{Zr, Cu, Al}`) extracted from the composition string.  
  4. Perform a **GroupKFold** split grouped by the full composition string to guarantee no identical formula appears in both folds, and stratify by the alloy‑family set. If any family lacks enough samples for the grouped split, fall back to a random 80/20 split (`random_state=42`).  
  5. Persist splits as `data/processed/train.parquet` and `data/processed/test.parquet`.  
  Verification: split files exist, composition strings do not overlap, VIF/PCA decisions are logged, and the fallback behavior (if triggered) is recorded.

- [ ] T004 [US2] Run the first end‑to‑end model training and evaluation on the real dataset:  
  1. In `code/modeling/train.py`, train a `LinearRegression` model and a `RandomForestRegressor` with a **concrete grid**: `n_estimators=[100,200,500]`, `max_depth=[None,10,20]`, `min_samples_leaf=[1,2]`. Use 5‑fold CV on the training split (`n_jobs=2`) and select the hyper‑parameter set with the highest mean CV R².  
  2. If the PCA fallback from T003 was triggered, train a **LinearRegression** on the two principal components (no Ridge).  
  3. Serialize final models to `models/linear_regression.pkl` and `models/random_forest.pkl` and write metadata JSON conforming to `contracts/model_output.schema.yaml`.  
  4. In `code/modeling/evaluate.py`, compute R², MAE, RMSE on the held‑out test set and write `data/results/model_performance.json` conforming to `contracts/model_metrics.schema.yaml`.  
  Verification: CV and test metrics are finite, non‑null; the command sequence from T001 produces these artifacts from real MP/AFLOW data.

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [US2] Implement the SC‑001 baseline comparison using NIST data:  
  1. Retrieve elemental CTE values from the **NIST Thermophysical Properties of Substances** database (public CSV endpoint).  
  2. Compute each alloy’s weighted‑average elemental CTE from stoichiometric fractions.  
  3. Train a baseline `LinearRegression` using this single predictor and evaluate R², MAE, RMSE on the same test set.  
  4. Write `data/results/baseline_metrics.json` (schema‑conformant, `model_type: "baseline_linear"`).  
  5. Generate a **baseline comparison report** `data/results/baseline_comparison.json` that records the baseline R² and the ΔR² improvement of the primary models.  
  Verification: baseline metrics file exists, and the comparison report is present and shows improvement.

- [ ] T006 [US3] Implement the permutation significance test (FR‑005, SC‑002): in `code/modeling/evaluate.py`, run **≥ 1000 iterations** shuffling the target CTE vector relative to the fixed feature matrix, re‑fit the selected best model on the training split, compute null R² on the test split, and report the two‑sided p‑value as the proportion of null R² ≥ observed R². If observed R² < 0.3, set `p_value=null` and flag `"Null Result"` with `null_result_flag=true`. Verification: `data/results/model_performance.json` contains a p‑value (or null‑result flag) for every model.

- [ ] T007 [US3] Implement feature‑importance and correlation‑diagnostic analysis (FR‑006, SC‑003):  
  1. For **Random Forest**, compute permutation importance (`sklearn.inspection.permutation_importance`).  
  2. For **Linear Regression**, compute SHAP values (`shap.LinearExplainer`) and use the mean absolute SHAP value per feature as its importance.  
  3. Compute Pearson correlation between each descriptor and CTE on the training data, rank descriptors by absolute correlation, and compute **both** Spearman ρ **and** Kendall‑τ between the importance ranking and the absolute‑correlation ranking.  
  4. Write `data/results/feature_importance.csv` (columns: `model_type, feature_name, importance_score, rank, pearson_corr, abs_corr_rank, spearman_rho, kendall_tau`) and `data/results/spearman_correlation.txt` containing both ρ and τ values.  
  Verification: both files exist with finite values for every retained descriptor and both models; CSV columns match the `FeatureImportance` entity.

- [ ] T008 [US1] Implement the FR‑009 sensitivity analysis and SC‑004 resource reporting: flag entries whose `thermal_history` does not match the standard `<temp>K for <time>h` pattern or whose `source_method` is inconsistent across duplicate families; retrain the best model with and without flagged entries and report ΔR² in `data/results/sensitivity_analysis.json`. Extend runtime/memory profiling to emit `data/results/computational_efficiency.json` with `{"runtime_seconds","memory_peak_mb","cpu_cores_used":2,"limits":{"runtime_seconds":21600,"memory_mb":7000},"pass":true/false}`. Verification: both JSON files exist and the `pass` flag reflects measured runtime and memory.

- [ ] T009 [US2] Complete the full‑scale run and validation checks: execute the entire documented pipeline on the full retrieved dataset (all MP + AFLOW entries), applying the ≤ 10 000‑row random‑sample cap if the raw set exceeds memory limits, and re‑emit `data/results/computational_efficiency.json` for the complete pipeline. Record the power analysis (α = 0.05, power = 0.80, detecting R² ≥ 0.10, N ≈ 500) in `data/results/power_analysis.txt`, including a caveat if the final N < 200. Add unit tests for edge cases (empty API responses, malformed formulas, VIF/PCA fallback). Verify that the run finishes within ≤ 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h, and that `data/results/power_analysis.txt` is present.  
  Verification: full run completes within limits, all tests pass, dataset size and any sampling reduction are logged, and `power_analysis.txt` exists.

- [ ] T010 [P] [US3] Generate the result tables and figures directly from the validated outputs: a parity plot (predicted vs. measured CTE for both models and the baseline on the test set), a null‑distribution histogram with the observed R² marked, and a feature‑importance bar chart with correlation‑rank overlay, saved under `figures/`, plus a summary table of all model metrics in `data/results/metrics_summary.csv`. Verification: every figure and table row traces to `data/processed/clean_mg_data.parquet` rows and the serialized models; no values are hand‑entered.

## Phase 3: Reproducible results and paper handoff

- [ ] T011 Write the methods/results account in `docs/research.md`: data sources and retrieval counts (MP, AFLOWlib with URL, and the measured availability numbers from `data/results/data_availability_report.json`), descriptor definitions, VIF decisions, split strategy, model configurations and CV scores, baseline comparison (SC‑001), permutation p‑values, feature‑importance and ρ/τ diagnostics, sensitivity ΔR², resource measurements, and an honest statement of any null result (R² < 0.3), reduced power (N < 200), or source‑availability limitation. Link each claim to the specific artifact file under `data/results/` or `figures/`.

- [ ] T012 Re‑run the documented workflow from its declared inputs (`python code/ingestion/fetch_data.py && python code/modeling/train.py && python code/modeling/evaluate.py`), confirm all unit/integration tests pass, verify every contract‑conformant artifact in `data/results/` regenerates deterministically (seed 42), and document the paper‑stage handoff in `docs/quickstart.md`: the paper stage receives `data/results/metrics_summary.csv`, `data/results/model_performance.json`, `data/results/baseline_comparison.json`, `data/results/feature_importance.csv`, `figures/*`, and `docs/research.md`; paper layout, PDF compilation, and publication are not research‑stage tasks.

## Dependencies and requirement coverage

- **FR‑001, FR‑009, SC‑005** → T001, T002 (amorphous filtering now uses `material_type`/description keyword, warning‑only for < 500, availability report).  
- **FR‑002, FR‑008** → T002, T003 (descriptors include atomic size coefficient of variation; VIF handling and exact two‑component PCA fallback).  
- **FR‑003** → T003 (alloy family defined as full element set).  
- **FR‑004, FR‑007** → T004, T009 (LR + RF grid search, 5‑fold CV, ≤ 2 cores / ≤ 7 GB RAM).  
- **FR‑005, SC‑002** → T006 (≥ 1000‑iteration permutation test, null‑result flag).  
- **FR‑006, SC‑003** → T007 (SHAP for LR, permutation importance for RF, Spearman ρ + Kendall‑τ).  
- **SC‑001** → T005 (baseline from NIST database, baseline comparison report).  
- **SC‑004** → T008, T009 (runtime/memory pass/fail JSON, power analysis).  

Execution order: T001 → T002 → T003 → T004 → (T005, T006, T007, T008 may follow T004) → T009 → T010 → T011 → T012. T010 is [P] relative to T008 once T009 finishes.

All tasks now satisfy the specification without weakening any functional or success criteria.  
