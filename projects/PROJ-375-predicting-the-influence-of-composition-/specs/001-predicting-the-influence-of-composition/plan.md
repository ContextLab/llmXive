# Implementation Plan: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

**Branch**: `001-gene-regulation` | **Date**: 2026-10-24 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The pipeline must (1) ingest the user‑provided curated CSV of metallic‑glass compositions and CTE values, optionally augment it with any “glass” entries returned by the Materials Project (MP) and AFLOWlib APIs (composition only), (2) compute four elemental descriptors (weighted mean atomic radius, electronegativity variance, valence‑electron concentration, atomic‑size coefficient of variation), (3) mitigate multicollinearity via VIF filtering with a PCA‑Ridge fallback, (4) split the data by alloy family using GroupKFold (fallback to random split), (5) train linear‑regression and random‑forest models with 5‑fold CV, (6) compare against a baseline weighted‑average **experimental** elemental‑CTE model (with a documented DFT‑vs‑experimental confound flag), (7) assess statistical significance with ≥ 1 000 permutation iterations, (8) generate feature‑importance rankings and correlation diagnostics, and (9) log runtime & memory to verify the free‑tier GitHub Actions limits. All steps run on CPU only; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `pymatgen==2024.*` (Materials Project API), `requests`, `tqdm`, `statsmodels==0.14.*` (VIF), `joblib`, `pyyaml`, `ruff==0.6.*`, `mendeleev==0.12.*` (elemental properties)  
- **Storage**: CSV/Parquet under `data/` (raw, processed, splits); model pickles under `models/`  
- **Testing**: `pytest==8.*` with JSON‑Schema validation (`jsonschema`)  
- **Target Platform**: Linux (GitHub Actions free‑tier)  
- **Constraints**: ≤ 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h wall‑clock time, CPU‑first (no GPU)  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts set `np.random.seed(42)` and `random.seed(42)` at import; data fetched from the same MP/AFLOW endpoints each run. |
| II. Verified Accuracy | MP and AFLOW are open, programmatically accessible; elemental properties come from the verified `mendeleev` package. |
| III. Data Hygiene | Raw API responses saved with SHA‑256 checksums (`data/checksums.txt`); **each processed row now also stores a per‑row `checksum` column** (see Phase 0). |
| IV. Single Source of Truth | Every figure, statistic, and model output references a single row in `data/processed/clean_alloy_data.parquet`. |
| V. Versioning Discipline | All artifacts are content‑hashed; CI updates the `state/projects/...yaml` artifact‑hash map automatically. |
| VI. Compositional Feature Engineering Integrity | Only the four elemental descriptors are used as inputs; no structural or thermal‑history variables enter the models. |
| VII. Numerical Stability and Resource Constrained Validation | Models trained with scikit‑learn on ≤2 cores; 5‑fold GroupKFold, 1 000‑iteration permutation test, VIF filtering, and runtime/memory checks stay within free‑tier limits. |
| Random‑Seed Policy | Every stochastic component (`GroupKFold`, `train_test_split`, RandomForest `random_state`, permutation shuffling, `joblib` parallelism) uses seed 42. |

## Mapping of Functional & Success Requirements to Plan Phases
| FR / SC | Covered Phase(s) |
|---------|-------------------|
| FR‑001 (metallic‑glass retrieval) | **Phase 0 – Data Ingestion & Coverage Check** |
| FR‑002 (descriptor extraction) | **Phase 1 – Feature Extraction** |
| FR‑003 (stratified split) | **Phase 2 – Train/Test Split** |
| FR‑004 (model training & CV) | **Phase 3 – Model Training** |
| FR‑005 (permutation test) | **Phase 5 – Significance Testing** |
| FR‑006 (feature importance) | **Phase 5 – Feature‑Importance Ranking** |
| FR‑007 (resource limits) | **All Phases** |
| FR‑008 (VIF & PCA fallback) | **Phase 1 – Multicollinearity Mitigation** |
| FR‑009 (metadata & sensitivity) | **Phase 0 – Metadata Capture & Sensitivity Analysis** |
| FR‑010 (fixed seeds) | **All Phases** |
| FR‑011 (power analysis) | **Phase 0 – Power Analysis** |
| FR‑012 (metadata flagging & ΔR²) | **Phase 0 – Sensitivity Analysis (duplicate of FR‑009)** |
| SC‑001 (baseline ΔR² > 0.05) | **Phase 4 – Baseline Comparison & ΔR² Check** |
| SC‑002 (permutation p‑value) | **Phase 5 – Permutation Test** |
| SC‑003 (Spearman & Kendall‑τ) | **Phase 5 – Correlation Diagnostics** |
| SC‑004 (efficiency limits) | **Phase 6 – Resource Logging** |
| SC‑005 (ingestion completeness) | **Phase 0 – Coverage Verification** |

## Scope Limitation & Revised Objective
- **Data Availability**: The curated literature CSV is assumed to be present in the repository at `data/raw/curated_metallic_glass.csv`. Neither MP nor AFLOW reliably expose a `material_type` flag for amorphous phases nor measured CTE values for glasses. Consequently, the pipeline **only uses these APIs to supplement composition entries**; CTE values are taken exclusively from the curated CSV.  
- **Baseline Data Source**: Elemental CTE values for the baseline model are sourced from the **experimental NIST Thermophysical Properties database** where available. If an element lacks an experimental entry, the DFT‑derived value from Materials Project is used, and a **confound flag** (`baseline_source_mismatch: true`) is recorded in `results/baseline_comparison.json`.  
- **Termination Condition**: After merging and filtering, if the combined dataset (CSV + API) contains **< 95 %** of the rows of the original CSV **or** fewer than **500** usable samples, the pipeline records `results/ingestion_coverage.json` with a `"Specification Amendment Required"` flag and **stops** before any modeling. This preserves scientific validity while transparently reporting the limitation.  
- **Future Substitution**: The data schema (`contracts/mg_dataset.schema.yaml`) permits any future open metallic‑glass dataset that matches the schema to replace the current source without code changes.

## Phased Execution Plan

### Phase 0 – Data Ingestion, Metadata Capture & Power / Coverage Analysis
1. Load `data/raw/curated_metallic_glass.csv` (must contain at least `material_id`, `composition`, `cte`).  
2. Query MP via `pymatgen.ext.matproj.MPRester` (free API key `MP_API_KEY`) for records where `description` contains “glass”. Retrieve **only composition strings**, `material_id`, and any available `source_method`/`thermal_history` metadata.  
3. Optionally query AFLOWlib REST endpoint for the same keyword; if the endpoint is unreachable, log a warning and continue with MP data only.  
4. Concatenate CSV and API results, de‑duplicate on `material_id`.  
5. Filter to keep only entries where the description contains “glass” **or** a user‑provided “amorphous” flag is present in the CSV. Exclude rows with missing `cte` (these are only present in the CSV) or malformed formulas; log counts.  
6. Extract `source_method` (`DFT`/`Experimental`) and any `thermal_history` fields when present.  
7. **Missing‑Metadata Check**:  
   - Compute proportion missing `source_method` or `thermal_history`.  
   - If > 20 % missing, run a sensitivity analysis on the subset with complete metadata (train/evaluate models on that subset, compute ΔR² vs. full set) and store `results/metadata_sensitivity.json`.  
   - If ≤ 20 % missing, flag incomplete entries in `results/metadata_flags.csv`.  
8. **Checksum Generation**:  
   - For each row in the merged DataFrame, create a JSON‑serialised representation of the row (sorted keys) and compute its SHA‑256 hash.  
   - Store the hash in a new column `checksum`.  
   - Save the per‑row checksums alongside the data (fulfills Constitution III).  
9. **Coverage Verification**:  
   - `coverage = retrieved_entries / csv_entries`.  
   - If `coverage ≥ 0.95` **and** `total_entries ≥ 500`, proceed.  
   - Otherwise, write `results/ingestion_coverage.json` with `{coverage, total_entries, status:"Specification Amendment Required"}` and **terminate**.  
10. **Power Analysis**: Using the final usable `N`, compute required sample size for detecting `f² = 0.15` at α = 0.05, power = 0.8 (≈ 500). Save `results/power_analysis.txt`; if power < 0.8, note the limitation.

### Phase 1 – Feature Extraction & Multicollinearity Mitigation
1. Parse each `composition` with `pymatgen.Composition` to obtain element fractions.  
2. Load elemental properties from `mendeleev` (atomic radius, Pauling electronegativity, valence electron count).  
3. Compute the four descriptors:  
   - Weighted mean atomic radius (Σ fraction × radius).  
   - Electronegativity variance (weighted variance).  
   - Valence electron concentration (Σ fraction × valence).  
   - Atomic size coefficient of variation = σ(radius)/μ(radius).  
4. Assemble a DataFrame with original columns + descriptors + `alloy_family` (sorted tuple of element symbols, e.g., `"Al,Cu,Zr"`).  
5. Compute VIF for each descriptor (using `statsmodels`).  
   - Drop any descriptor with VIF > 5.0 **unless** it is `weighted_mean_atomic_radius` (retain preferentially).  
   - If **all** descriptors exceed VIF > 5.0, retain the one with the lowest VIF, apply **PCA** to the four‑dimensional space, retain the first two components (≥ 95 % variance), and plan to train a **Ridge Regression** model on these components (fallback satisfies FR‑008).  
6. Save cleaned dataset to `data/processed/clean_alloy_data.parquet`. Store VIF report at `results/vif_report.csv`.

### Phase 2 – Train/Test Split
1. Define `alloy_family` as the sorted, comma‑separated list of constituent elements.  
2. Attempt a 5‑fold **GroupKFold** split using `alloy_family` as the grouping key.  
3. **Fallback**: if any family has < 5 samples, perform a stratified random 80/20 split (`train_test_split(random_state=42)`).  
4. Persist `train.parquet` and `test.parquet` under `data/processed/`.

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
1. Retrieve **experimental** elemental CTE values from the NIST Thermophysical Properties database (public CSV available at – verified open source).  
2. If an element lacks an experimental entry, fall back to the DFT‑derived value from Materials Project **and set** `baseline_source_mismatch: true` in the results file.  
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
A conservative power analysis (α = 0.05, power = 0.80) for detecting `f² = 0.15` requires ≈ 500 samples. The curated CSV is expected to contain ≥ 500 entries; the augmentation step aims to increase coverage. If the final usable sample size falls below 500, the analysis writes a warning in `results/power_analysis.txt` and all downstream statistical interpretations are qualified accordingly.

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


## projects/PROJ-375-predicting-the-influence-of-composition-/specs/001-predicting-the-influence-of-composition/research.md

# Research: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Objective
Assess whether compositional descriptors derived solely from elemental properties can predict the coefficient of thermal expansion (CTE) of metallic glasses, identify the most influential descriptors, and rigorously test statistical significance, computational efficiency, and baseline physical approximations.

## Dataset Strategy
| Source | Access Method | Notes |
|--------|---------------|-------|
| **Curated literature CSV** (user‑provided) | Local file `data/raw/curated_metallic_glass.csv` | Primary ground‑truth dataset (FR‑001). Must contain `material_id`, `composition`, `cte`. |
| **Materials Project API** | `pymatgen.ext.matproj.MPRester` with free API key (`MP_API_KEY`) | Retrieves **additional composition entries** where the description contains “glass”. No CTE values are taken from MP/AFLOW because they lack amorphous‑phase data. |
| **AFLOWlib API** | Public REST endpoint (no verified URL) | Optional supplemental source for composition only; if unreachable, pipeline proceeds with MP data only. |
| **Experimental elemental CTE values** | NIST Thermophysical Properties of Substances database (open CSV at) | Used for the baseline weighted‑average elemental‑CTE model (SC‑001). If an element is missing, the DFT‑derived MP value is used and a **source‑mismatch flag** is recorded. |

> **Dataset Availability Verdict**: The curated CSV is part of the repository; the Materials Project API provides open, programmatic access to additional metallic‑glass compositions. No gated datasets are required, satisfying the compute‑feasibility constraints.

## Methodological Decisions & Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑only modeling (scikit‑learn)** | Guarantees execution on free GitHub Actions runner. | All steps on default runner. |
| **5‑fold GroupKFold by alloy family** | Prevents leakage of identical composition families between train and test (Constitution VII). | `sklearn.model_selection.GroupKFold`. |
| **Permutation test (≥ 1 000 iterations) with target shuffling** | Provides a robust p‑value for SC‑002; shuffling destroys any true X‑Y relationship while preserving feature structure. | Parallelised across 2 cores (`joblib`). |
| **VIF threshold = 5.0 with PCA‑Ridge fallback** | Enforces FR‑008; ensures multicollinearity does not invalidate coefficient interpretations. | One‑time computation after descriptor generation. |
| **Baseline weighted‑average elemental CTE model using **experimental** NIST data** | Supplies an appropriate physical baseline for SC‑001; avoids bias from mixing DFT‑derived elemental CTEs with experimental alloy CTEs. When experimental data are missing, DFT values are used with an explicit confound flag. | Simple linear regression on a single predictor. |
| **Runtime & memory logging** | Implements SC‑004; logs stored in `results/computational_efficiency.json`. | Minimal overhead. |
| **Power analysis** | Confirms dataset size is sufficient to detect modest effect sizes; if not, limitation is reported. | Performed after ingestion; results saved to `results/power_analysis.txt`. |
| **Fixed random seeds** | Guarantees reproducibility (Constitution I). | `np.random.seed(42)` and `random.seed(42)` at script start; `random_state=42` for all estimators and `joblib`. |

### Statistical Rigor Checklist
- **Multiple‑Comparison Correction**: Not required (single primary hypothesis per model).  
- **Power / Sample‑Size**: Reported in Phase 0; contingency plan for N < 500.  
- **Causal Claims**: All statements are **associational**; data are observational (DFT or experimental).  
- **Measurement Validity**: CTE values sourced directly from the curated CSV (experimental) or the Materials Project (DFT) for elemental references; baseline uses experimentally measured elemental CTEs from NIST.  
- **Collinearity**: Addressed via VIF analysis and PCA‑Ridge fallback (FR‑008).  

## Expected Deliverables
- `data/processed/clean_alloy_data.parquet` – cleaned dataset with all required columns and per‑row `checksum`.  
- Trained model files: `models/linear_regression.pkl`, `models/random_forest.pkl`, `models/baseline_linear.pkl`.  
- Performance metrics JSON: `results/model_performance.json` and `results/baseline_metrics.json`.  
- Permutation test outputs: `results/permutation_null_distribution.npy` and p‑value.  
- Feature‑importance CSV and correlation diagnostics (`results/feature_importance.csv`, `results/correlation_diagnostics.json`).  
- Computational‑efficiency JSON (`results/computational_efficiency.json`).  
- JSON‑Schema contracts (`contracts/*.schema.yaml`).  
- Unit tests validating schema compliance (`tests/unit/`).  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient metallic‑glass CTE entries | May reduce statistical power (SC‑004). | Power analysis; explicit coverage warning; Specification Amendment flag. |
| High VIF across all descriptors | Forces fallback to PCA, reducing interpretability. | Document fallback; still satisfies FR‑008. |
| AFLOWlib endpoint downtime | Loss of supplemental data. | Log warning; continue with MP data only. |
| Runtime or memory overrun on CI | Job failure. | Phase 6 monitors limits; aborts early with clear error. |
| Mis‑identification of alloy families for stratification | Potential leakage. | Use full elemental set as grouping key; fallback to random split. |
| Permutation test randomness | Unstable p‑values. | Fixed random seed (`np.random.seed(42)`). |

---

