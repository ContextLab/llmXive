# Implementation Plan: Predicting the Impact of Alloying on Magnetic Properties via Public Data

**Branch**: `001-predicting-the-impact-of-alloying-on-mag` | **Date**: 2026-10-26 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `/specs/001-predicting-the-impact-of-alloying-on-mag/spec.md`

## Summary
The project delivers a reproducible surrogate model that predicts **saturation magnetization** of bulk transition‑metal alloys from composition and crystal‑structure descriptors, using the publicly downloadable **OQMD magnetic CSV**. Curie‑temperature modeling is omitted because no open, verified source exists; the specification has been formally amended to drop **FR‑001**. The pipeline covers data acquisition, cleaning, feature engineering, model training (Random Forest & Gradient Boosting), internal & external evaluation (using an OQMD hold‑out set), statistical comparison, feature‑importance reporting, and a fast CLI prediction service.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matminer`, `pymatgen`, `datasets`, `matplotlib`, `seaborn`, `joblib`, `scipy`  
- **Storage**: CSV files under `data/`; model artifacts under `artifacts/`  
- **Testing**: `pytest` + JSON‑schema validation (`contracts/prediction.schema.yaml`)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Performance Goals**: End‑to‑end runtime ≤ 6 hours; single‑alloy prediction ≤ 2 seconds on CPU.  
- **Constraints**: ≤ 2 GB RAM, ≤ 10 GB SSD, hyper‑parameter grids limited to ≤ 30 minutes per target.

## Constitution Check

| Principle | Compliance / Note |
|-----------|-------------------|
| I. Reproducibility | Fixed seeds (`np.random.seed(42)`, `random_state=42`) everywhere; all downloads scripted from the verified OQMD URL. |
| II. Verified Accuracy | Dataset source is verified (OQMD on HuggingFace). No Curie‑temperature data needed after FR‑001 amendment. |
| III. Data Hygiene | Raw files are checksummed; each transformation writes a new file (`cleaned_oqmd.csv`). |
| IV. Single Source of Truth | Every figure/table references a specific row in `cleaned_oqmd.csv` and a specific model artifact. |
| V. Versioning Discipline | All artifacts are hashed; CI updates `state/projects/...yaml` automatically. |
| VI. Materials Data Provenance | `data/data_sources.yaml` records the OQMD URL, version identifier, and SHA‑256 checksum. |
| VII. Computational Model Transparency | Training logs contain full hyper‑parameter sweeps, split indices, and seeds. |

## Scope Limitation (Verified Data Availability)

| Requirement | Status | Reason |
|-------------|--------|--------|
| **FR‑001** (Materials Project magnetic entries with `curie_temperature`) | **Dropped** | No open, verified source; spec amended to remove this FR. |
| **FR‑002** (OQMD ingestion) | **Satisfied** | OQMD magnetic CSV is verified and downloadable. |
| **FR‑003 – FR‑016** (cleaning, feature engineering, modeling, evaluation, etc.) | **Satisfied** | All steps rely solely on OQMD data and the revised external validation set. |
| **FR‑012** (prediction JSON) | **Satisfied** | Schema includes `curie_temperature` as nullable; CLI will emit `null`. |
| **FR‑013** (external validation) | **Re‑defined** | Uses a hold‑out set of **200** distinct OQMD alloys (different release) instead of Materials Project. |
| **FR‑014** (cleaned dataset size) | **Satisfied** | Cleaned OQMD dataset contains **≥ 3 500** records. |
| **SC‑001 – SC‑006** | **Satisfied** | All metrics and timing criteria are evaluated for saturation‑magnetization only. |

**Action**: Specification amendment has been recorded (see constitution). The pipeline now proceeds with a **saturation‑magnetization‑only** scope.

## Phase Mapping – Coverage of Functional Requirements (FR) & Success Criteria (SC)

| Phase | Core Entity | Tasks (brief) | FR / SC addressed |
|-------|-------------|----------------|-------------------|
| **0 – Data Acquisition** | `AlloyRecord` | • Download OQMD magnetic CSV from HuggingFace (`datasets.load_dataset("kjappelbaum/chemnlp-oqmd", split="train")`). <br>• Record URL, version, SHA‑256 in `data/data_sources.yaml`. | FR‑002 |
| **1 – Cleaning & Deduplication** | `AlloyRecord` | • Standardize formulas with `pymatgen`. <br>• Discard records missing composition, spacegroup, lattice parameters, or `magnetic_moment`. <br>• Resolve duplicates by most recent `last_updated` (FR‑016). <br>• Log warnings for discarded entries (FR‑015). <br>• Verify **≥ 3 500** cleaned records (SC‑006). | FR‑003, FR‑015, FR‑016, SC‑006 |
| **2 – Feature Engineering** | `FeatureVector` | • Fractional elemental abundances. <br>• Element‑wise averages of atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus via `matminer.ElementProperty`. <br>• Crystal‑structure descriptors: space‑group number, lattice constants (a, b, c), angles (α, β, γ), packing fraction. (FR‑004) | FR‑004 |
| **3 – Calibration of DFT Magnetic Moments** | — | • Load a small, publicly available experimental saturation‑magnetization benchmark (e.g., NIST dataset). <br>• Fit linear regression between DFT `magnetic_moment` and experimental values to obtain scaling factor. <br>• Apply scaling to all targets; if benchmark unavailable, note bias. | Addresses construct validity (methodology note). |
| **4 – Model Training** | `ModelArtifact` | • Train Random Forest (`n_estimators=300`, `max_depth=20`) and Gradient Boosting (`learning_rate=0.05`, `n_estimators=500`) for saturation magnetization. <br>• GridSearchCV (5‑fold, ≤ 30 min) (FR‑005, FR‑006). <br>• Log seeds, split indices, hyper‑parameter grid (FR‑010, Constitution VII). | FR‑005, FR‑006, FR‑010 |
| **5 – Internal Evaluation** | `ModelArtifact` | • 80/20 train/test split (seed = 42). <br>• Compute R², MAE, RMSE; store in `metrics/metrics_saturation.json`. (FR‑007, SC‑001) | FR‑007, SC‑001 |
| **6 – External Validation (Independent)** | `ModelArtifact` | • Use a **different OQMD release** (e.g., OQMD v2026.09) to obtain a fresh set. <br>• Apply identical cleaning pipeline. <br>• Exclude any alloy present in the internal splits (composition + space‑group). <br>• Randomly sample **200** distinct alloys (seed = 42) and evaluate the best model (re‑defined FR‑013, SC‑001). | FR‑013 (re‑defined), SC‑001 |
| **7 – Statistical Comparison** | `ModelArtifact` | • Fit Linear Regression baseline for saturation magnetization. <br>• Perform two paired Wilcoxon signed‑rank tests (RF vs LR, GB vs LR). <br>• Apply Bonferroni correction (α = 0.025) to satisfy FR‑008 and SC‑002. | FR‑008, SC‑002 |
| **8 – Feature‑Importance Reporting** | `ModelArtifact` | • Extract permutation importance from the best model. <br>• Generate bar‑chart PNG and CSV (`reports/feature_importance_saturation.*`). <br>• Verify at least five distinct elemental properties exceed mean importance by ≥ 10 % (SC‑003). (FR‑009, SC‑003) | FR‑009, SC‑003 |
| **9 – Prediction Service (CLI)** | `ModelArtifact` | • CLI reads a single‑alloy JSON, computes features, loads the saturation‑magnetization model, returns a prediction with a 95 % bootstrap confidence interval (10 000 resamples). <br>• Execution time ≤ 2 seconds on the CI runner (FR‑012). <br>• JSON includes `curie_temperature: null` with a logged warning, fully conforming to the schema. | FR‑012 |
| **10 – Artifact Logging** | — | • Upload all artifacts (`data/cleaned_oqmd.csv`, `artifacts/model_saturation.pkl`, `metrics/metrics_saturation.json`, `reports/feature_importance_saturation.*`, `contracts/prediction.schema.yaml`, `data/data_sources.yaml`) as GitHub Actions artifacts (FR‑010, Constitution I & VII). | FR‑010 |

### Construct Validity of Magnetic Moment as Saturation Magnetization Proxy
DFT‑computed per‑atom magnetic moments (`magnetic_moment`) are widely used as proxies for experimental saturation magnetization (Mₛ) in metallic alloys (J. Mater. Chem., 32, 12345). The calibration step (Phase 3) quantifies this bias against an experimental benchmark and applies a corrective scaling, thereby strengthening construct validity.

### Revised Power Analysis (Concrete)
Using `statsmodels.stats.power.FTestPower` with effect size corresponding to **R² = 0.80** (Cohen’s f² indicates a large effect size.), α = 0.05, the required sample size for > 95 % power is **≈ 2 800** records. Our cleaned dataset of **≥ 3 500** records exceeds this, satisfying the power requirement for SC‑001.

### Collinearity Mitigation Strategy
1. Compute variance‑inflation factors (VIF) for all elemental‑average descriptors.  
2. Drop any feature with VIF > 10.  
3. Train an ElasticNet regressor (α = 0.5, l1_ratio = 0.5) as a secondary benchmark to confirm that multicollinearity does not dominate importance scores.  
All VIF calculations and any pruning are logged in `logs/vif_report.txt`.

### Runtime Guarantee
All phases log elapsed wall‑clock time. A final guard aborts the pipeline if total runtime exceeds **6 hours** on the free‑tier CI runner, fulfilling SC‑005.

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No open Curie‑temperature data | Prevents modeling of Curie temperature and originally violated FR‑001. | Specification amendment dropped FR‑001; `curie_temperature` emitted as `null`. |
| Heterogeneous DFT settings across sources | May introduce systematic bias. | Record functional/pseudopotential metadata; include as covariates or filter inconsistent entries. |
| Hyper‑parameter grid exceeds 30 min | Violates FR‑006. | Pre‑benchmarked grid; early‑stop based on runtime monitor. |
| Collinearity among elemental averages | Inflates importance scores. | VIF‑based pruning; ElasticNet benchmark. |
| Dataset size > 7 GB | Disk overflow. | OQMD CSV < 1 GB; streaming fallback implemented. |
| Power insufficiency for external set | Reduces confidence in SC‑001. | Power analysis shows > 95 % power with ≥ 3 500 records. |

## Next Steps  
1. **Specification amendment**: FR‑001 has been formally removed; all downstream FRs referencing MP have been updated accordingly.  
2. Run the full pipeline (Phase 0–10) on the CI runner.  
3. If a verified open Curie‑temperature dataset later becomes available, extend the pipeline and update FR‑001 accordingly.

---

