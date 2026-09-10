# Implementation Plan: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

**Branch**: `001-gene-regulation` | **Date**: 2026-09-10 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project must (1) ingest metallic‑glass composition and coefficient of thermal expansion (CTE) data from **both** the Materials Project (MP) and AFLOWlib open APIs, (2) compute compositional descriptors derived from elemental properties, (3) clean the data (remove missing CTEs, filter amorphous entries, compute VIF and apply a robust fallback when all descriptors are collinear), (4) split the dataset (stratified by alloy family, fallback to random), (5) train linear‑regression and random‑forest models with 5‑fold cross‑validation, (6) train a **baseline** linear model that uses the weighted‑average elemental CTE as its sole predictor, (7) run a sufficiently large‑scale permutation test that shuffles the target while keeping features fixed to obtain a null R² distribution, (8) generate feature‑importance rankings and compute the **Spearman ρ** between the importance rank and the absolute Pearson‑correlation rank as a diagnostic, (9) record runtime and memory usage and report a pass/fail flag against the GitHub Actions free‑tier limits, and (10) produce all artifacts with full reproducibility. All steps respect the CPU‑only resource limits (≤2 cores, ≤7 GB RAM) and the constitution’s principles.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `pymatgen==2024.*` (Materials Project API), `requests`, `tqdm`, `statsmodels==0.14.*` (VIF), `joblib`, `pyyaml`, `ruff==0.6.*` (linting), `mendeleev==0.12.*` (elemental property tables – verified at https://pypi.org/project/mendeleev/)  
- **Storage**: CSV/Parquet files under `data/` (raw, processed, splits) and model pickles under `models/`  
- **Testing**: `pytest==8.*` with contract validation via `jsonschema`  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Project Type**: Library/CLI pipeline (no web service)  
- **Performance Goals**: Full pipeline ≤ 6 h on free‑tier GitHub Actions; memory ≤ 7 GB  
- **Constraints**: CPU‑only; no GPU; open datasets only.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts are deterministic, seeds are pinned, and external data are fetched from the same canonical API endpoints on each run. |
| II. Verified Accuracy | The `mendeleev` package source is cited with a verified PyPI URL; no other external citation is introduced without verification. |
| III. Data Hygiene | Raw API responses are saved with SHA‑256 checksums; every transformation writes a new file with a provenance header. |
| IV. Single Source of Truth | Every figure or statistic in the eventual paper will trace back to exactly one row in `data/processed/clean_mg_data.parquet` and a single model file in `models/`. |
| V. Versioning Discipline | All artifacts are content‑hashed; the `state/projects/...yaml` will be updated automatically by the CI pipeline. |
| VI. Compositional Feature Engineering Integrity | Only elemental properties (atomic radius, electronegativity, VEC, size mismatch) are used; no structural or thermal‑history descriptors are included as model inputs. |
| VII. Numerical Stability and Resource Constrained Validation | Models are trained with scikit‑learn on ≤2 CPU cores; 5‑fold stratified CV, 1 000 permutation iterations, VIF filtering, and runtime/memory checks are all bounded to stay within the RAM limit. |

## Mapping of Functional & Success Requirements to Plan Phases
| FR / SC | Plan Phase(s) |
|---------|----------------|
| FR‑001 | **Phase 0 – Data Ingestion & Metadata Capture** |
| FR‑002 | **Phase 1 – Feature Extraction & VIF** |
| FR‑003 | **Phase 2 – Train‑Test Split** |
| FR‑004 | **Phase 3 – Model Training & CV** |
| FR‑005 | **Phase 5 – Permutation Significance Test** |
| FR‑006 | **Phase 5 – Feature‑Importance Ranking** |
| FR‑007 | **All Phases** – resource limits enforced |
| FR‑008 | **Phase 1 – Multicollinearity Check (VIF) & fallback** |
| FR‑009 | **Phase 0 – Metadata Capture & Thermal‑History Flagging** |
| SC‑001 | **Phase 4 – Baseline Comparison** |
| SC‑002 | **Phase 5 – Permutation Test (1 000 iterations)** |
| SC‑003 | **Phase 5 – Spearman ρ between importance & absolute correlation** |
| SC‑004 | **Phase 6 – Runtime & Memory Logging + Pass/Fail Reporting** |

## Phased Execution Plan

### Phase 0 – Data Ingestion & Metadata Capture
1. **Materials Project (MP) API**: query the **Thermal Properties** endpoint via `pymatgen.ext.matproj.MPRester` for entries that contain `thermal_expansion_coefficient`.  
2. **Amorphous detection**:  
   - Prefer entries that have the MP metadata tag `"glass"` (available via `entry.data['tags']`).  
   - If the tag is absent, treat an entry as amorphous when `structure.get_space_group_info()` returns `None` **or** when the optional `structure_type` field contains the substring “amorphous”.  
   - Record the boolean `amorphous_flag`.  
3. **AFLOWlib**: query the public REST endpoint `https://aflowlib.org/AFLOWDATA/AFLOWLIB_LIBRARY/v1.2.0/` with parameters `property=thermal_expansion_coefficient` and `keywords=glass`. Parse JSON responses; apply the same amorphous detection logic (AFLOW records lack a space‑group; treat them as amorphous). If the request fails (network error, rate limit, or returns no glass entries), log a warning and continue with MP data only (still satisfies FR‑001).  
4. Store raw JSON responses under `data/raw/` and compute SHA‑256 checksums (`data/checksums.txt`).  
5. Extract fields: `material_id`, `composition` (string), `thermal_expansion_coefficient` → `cte` (float), `source_method` (`DFT`/`Experimental`), `thermal_history` (optional free‑text), `amorphous_flag`.  
6. Discard entries where `cte` is missing or `amorphous_flag=False`. Log total counts; if < 500 entries, emit a warning but continue (per US‑1).  

### Phase 1 – Feature Extraction & Multicollinearity Mitigation
1. Parse each composition into element fractions using `pymatgen.core.Composition`.  
2. Load elemental property tables (atomic radius, Pauling electronegativity, valence electron count) from the open `mendeleev` package (verified PyPI source).  
3. Compute:  
   - **Weighted mean atomic radius** = Σ fraction × radius  
   - **Electronegativity variance** = Σ fraction × (χ − μ)²  
   - **Valence Electron Concentration (VEC)** = Σ fraction × valence electrons  
   - **Atomic size mismatch** = √[ Σ fraction × (radius − mean)² ] (standard deviation).  
   *Note*: `atomic_size_mismatch` is deterministically derived from the radii; when VIF indicates high collinearity, **drop `atomic_size_mismatch`** and retain `weighted_mean_atomic_radius`.  
4. Assemble a DataFrame with the original columns plus the four descriptors.  
5. Compute **Variance Inflation Factor (VIF)** for the descriptor set (using `statsmodels.stats.outliers_influence.variance_inflation_factor`).  
   - Drop any descriptor with VIF > 5.0.  
   - **Fallback**: if *all* descriptors exceed VIF > 5.0, retain the descriptor with the lowest VIF, apply **PCA** to the original four descriptors (retain components that explain ≥95 % variance), and train a **Ridge Regression** model on the principal components. Document the choice in `data/processed/vif_report.txt`.  
6. Write the cleaned table to `data/processed/clean_mg_data.parquet`.  

### Phase 2 – Train‑Test Split
1. Determine the **alloy family** for each entry as the ordered tuple of the two most abundant elements (by atomic fraction).  
2. Perform a **5‑fold stratified split** using `StratifiedKFold` on this family identifier.  
3. If any family has fewer than 5 samples, fall back to a **random 80/20 split** (`train_test_split(random_state=42)`).  
4. Persist splits as Parquet files: `data/processed/train.parquet`, `data/processed/test.parquet`.  

### Phase 3 – Model Training & Cross‑Validation
1. **Linear Regression**: `sklearn.linear_model.LinearRegression` (no hyperparameters).  
2. **Random Forest**: grid‑search over `n_estimators=[[deferred]]`, `max_depth=[None,10,20]`, `min_samples_leaf=[1,2]`.  
3. Use **5‑fold cross‑validation** (`cross_val_score`) on the training set; record mean R², MAE, RMSE for each hyper‑parameter combo.  
4. Select the best hyper‑parameter set (highest mean R²).  
5. Fit final models on the full training data and serialize with `joblib.dump` to `models/linear_regression.pkl` and `models/random_forest.pkl`.  

### Phase 4 – Baseline Comparison
1. Retrieve **elemental CTE** values from the MP pure‑element entries (e.g., `mp-112` for Zr) via the same `/thermal` endpoint.  
2. For each alloy, compute a **weighted‑average elemental CTE** using the stoichiometric fractions.  
3. Train a **baseline linear regression** model that uses the weighted‑average elemental CTE as the sole predictor.  
4. Evaluate baseline R², MAE, RMSE on the held‑out test set; store metrics in `results/baseline_metrics.json`.  

### Phase 5 – Statistical Significance & Feature Importance
1. **Permutation Test** (1 000 iterations):  
   - Shuffle the **target CTE vector** (`y`) **relative to the fixed feature matrix** (`X`).  
   - Re‑fit the **selected best model** (from Phase 3) on the training split with the shuffled `y`.  
   - Compute R² on the original test split.  
   - Collect the 1 000 null R² values; compute a two‑sided p‑value as the proportion of null R² ≥ observed R².  
2. **Feature Importance**:  
   - For Random Forest, extract `feature_importances_`.  
   - For Linear Regression, use absolute coefficient magnitude.  
   - Rank descriptors; save `results/feature_importance.csv`.  
3. **Correlation Diagnostic**: compute Pearson correlation between each descriptor and CTE on the training data; rank descriptors by absolute correlation. Compute **Spearman ρ** **between the two rank vectors** (importance rank vs. absolute‑correlation rank). Store the ρ value in `results/spearman_correlation.txt`. This metric is a *consistency check*, not a claim of scientific novelty.  
4. If observed R² < 0.3, flag a **“Null Result”** in `results/model_performance.json` and set `p_value=null`.  

### Phase 6 – Resource & Runtime Logging & Pass/Fail Reporting
1. Wrap each major script with a timer (`time.perf_counter`) and memory profiler (`psutil`).  
2. Append a summary line to `results/runtime_log.txt` (wall‑clock seconds, max RSS).  
3. After the full pipeline, generate `results/computational_efficiency.json` containing:  
   ```json
   {
     "runtime_seconds": <total>,
     "memory_peak_mb": <peak>,
     "cpu_cores_used": 2,
     "limits": {"runtime_seconds": 21600, "memory_mb": 7000},
     "pass": <true/false>
   }
   ```  
   The `pass` flag is true only if both runtime ≤ 6 h and memory ≤ 7 GB, satisfying SC‑004.  

### Phase 7 – Documentation & Contracts
1. Generate `contracts/mg_dataset.schema.yaml`, `contracts/model_metrics.schema.yaml`, and `contracts/model_output.schema.yaml` (valid YAML, see the updated contract files).  
2. Provide unit tests in `tests/unit/` that validate the schema against a small example DataFrame.  
3. Lint all code with `ruff` (line length < 88, no unused imports).  

## Compute Feasibility
All steps are CPU‑first and compatible with the free GitHub Actions runner. The largest memory consumer is the full processed DataFrame; we enforce a hard cap of **10 000 rows** (≈ 2 MB) if the raw query returns > 10 k entries. This satisfies the “≤ 7 GB RAM” constraint while preserving statistical power (the dataset will still exceed the 500‑entry target in typical MP queries). No GPU is required.

## Project Structure
```text
specs/001-predicting-the-influence-of-composition/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── mg_dataset.schema.yaml
    ├── model_metrics.schema.yaml
    └── model_output.schema.yaml

code/
├── ingestion/
│   └── fetch_materials_project.py
├── features/
│   └── descriptors.py
├── modeling/
│   ├── train.py
│   ├── evaluate.py
│   ├── baseline.py
│   ├── permutation_test.py
│   └── feature_importance.py
├── utils/
│   └── io.py
├── .ruff.toml
└── __init__.py

data/
├── raw/
│   ├── materials_project_raw.json
│   └── aflowlib_raw.json
├── processed/
│   ├── clean_mg_data.parquet
│   ├── train.parquet
│   ├── test.parquet
│   ├── vif_report.txt
│   └── thermal_history_flags.csv
└── checksums.txt

models/
├── linear_regression.pkl
├── random_forest.pkl
└── baseline_linear.pkl

results/
├── baseline_metrics.json
├── model_performance.json
├── feature_importance.csv
├── spearman_correlation.txt
├── runtime_log.txt
└── computational_efficiency.json

tests/
├── unit/
│   ├── test_schema_validation.py
│   └── test_descriptors.py
└── integration/
    └── test_full_pipeline.py

docs/
├── quickstart.md
└── research.md
```

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts are deterministic, seeds are fixed, and external data are fetched from the same canonical API endpoints on each run. |
| II. Verified Accuracy | The `mendeleev` package source is cited with a verified PyPI URL; no other external citation is introduced without verification. |
| III. Data Hygiene | Raw API responses are saved with SHA‑256 checksums; every transformation writes a new file with a provenance header. |
| IV. Single Source of Truth | Every figure or statistic in the eventual paper will trace back to exactly one row in `data/processed/clean_mg_data.parquet` and a single model file in `models/`. |
| V. Versioning Discipline | All artifacts are content‑hashed; the `state/projects/...yaml` will be updated automatically by the CI pipeline. |
| VI. Compositional Feature Engineering Integrity | Only elemental properties (atomic radius, electronegativity, VEC, size mismatch) are used; no structural or thermal‑history descriptors are included as model inputs. |
| VII. Numerical Stability and Resource Constrained Validation | Models are trained with scikit‑learn on ≤2 CPU cores; 5‑fold stratified CV, 1 000 permutation iterations, VIF filtering, and runtime/memory checks are all bounded to stay within the RAM limit. |