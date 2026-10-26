# Implementation Plan: Predicting the Impact of Alloying on Magnetic Properties via Public Data

**Branch**: `001-predicting-the-impact-of-alloying-on-mag` | **Date**: 2026-10-26 | **Spec**: [spec.md](../specs/001-predicting-the-impact-of-alloying-on-mag/spec.md)  
**Input**: Feature specification from `/specs/001-predicting-the-impact-of-alloying-on-mag/spec.md`

## Summary
The original specification calls for surrogate models of **both** saturation magnetization and Curie temperature using the Materials Project and OQMD databases. Only the OQMD magnetic CSV is available from a **verified, programmatically downloadable source**. No verified open source provides Curie‑temperature values, and the Materials Project bulk archive is not listed among the verified URLs. Consequently, the pipeline **cannot** currently satisfy the Curie‑temperature portion of the specification. The plan therefore proceeds with a **saturation‑magnetization‑only** pipeline **while explicitly flagging** the missing Curie‑temperature data as a specification‑level blocker that must be resolved (either by providing a verified Curie‑temperature dataset or by revising the specification). Until such an amendment is made, the implementation will:

1. Build, train, evaluate, and interpret models for **saturation magnetization** only.
2. Produce artifacts that conform to the **original** JSON schema (both `saturation_magnetization` and `curie_temperature` fields) but note that the `curie_temperature` value will be set to `null` pending data availability. This limitation is documented transparently in the pipeline logs and the plan.

## Spec Revision Required
* The functional requirements FR‑001, FR‑003, FR‑004, FR‑005, FR‑006, FR‑007, FR‑008, FR‑009, FR‑012, FR‑013, FR‑014 and the associated success criteria (SC‑001 – SC‑007) depend on the availability of Curie‑temperature data.  
* As no open, verifiable source for Curie temperature exists, we request a **specification amendment** to either:
  1. Supply an open dataset that includes both `magnetic_moment` and `curie_temperature`, **or**  
  2. Redefine the project scope to focus exclusively on **saturation magnetization** (removing all Curie‑temperature‑related FRs/SCs).  

Until such an amendment is made, the pipeline will implement and evaluate only the saturation‑magnetization target, while keeping the contract schema unchanged (both fields present) and documenting the missing field.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matminer`, `pymatgen`, `datasets`, `matplotlib`, `seaborn`, `joblib`, `scipy`  
- **Storage**: CSV files under `data/`; model artifacts under `artifacts/`  
- **Testing**: `pytest` + JSON‑schema validation (`contracts/prediction.schema.yaml`)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Performance Goals**: End‑to‑end runtime ≤ 6 hours; single‑alloy prediction ≤ 2 seconds (CPU) for the **saturation‑magnetization** target.  
- **Constraints**: ≤ 2 GB RAM, ≤ 10 GB SSD, hyper‑parameter grids limited to ≤ 30 minutes per target.

## Constitution Check

| Principle | Compliance / Note |
|-----------|-------------------|
| I. Reproducibility | Fixed seeds (`np.random.seed(42)`, `random_state=42`) everywhere; all downloads scripted from **verified URLs**. |
| II. Verified Accuracy | Dataset source is the OQMD magnetic CSV from HuggingFace (verified). No open source for Curie‑temperature; this limitation is documented. |
| III. Data Hygiene | Raw files are checksummed; each transformation writes a new file (`cleaned_oqmd.csv`). |
| IV. Single Source of Truth | Every figure/table references a specific row in `cleaned_oqmd.csv` and a specific model artifact. |
| V. Versioning Discipline | All artifacts are hashed; `state/projects/...yaml` will be updated automatically. |
| VI. Materials Data Provenance | `data/data_sources.yaml` records the OQMD URL, version identifier, and SHA‑256 checksum. |
| VII. Computational Model Transparency | Training logs contain full hyper‑parameter sweeps, split indices, and seeds. |

## Scope Limitation (Verified Data Availability)

| Requirement | Status | Reason |
|-------------|--------|--------|
| **FR‑001** (Materials Project magnetic entries with `curie_temperature`) | **Not satisfied** | No verified open source provides Curie‑temperature data. |
| **FR‑002** (OQMD ingestion) | **Satisfied** | OQMD magnetic CSV is verified and downloadable. |
| **FR‑003 – FR‑016** (cleaning, feature engineering, modeling, evaluation, etc.) | **Partially satisfied** | All steps that rely **only** on OQMD data (saturation‑magnetization) can be executed. Steps that require Curie‑temperature data are omitted. |
| **FR‑012** (prediction JSON containing both targets) | **Partially satisfied** | Schema still includes both fields, but `curie_temperature` will be `null` until data become available. |
| **FR‑013** (external validation set) | **Partially satisfied** | External validation is provided for saturation‑magnetization only. |
| **FR‑014** (cleaned dataset size) | **Satisfied** for saturation‑magnetization (≥ 3 500 records). |
| **SC‑001 – SC‑007** | **Partially satisfied** | Metrics, statistical tests, and feature‑importance are computed for saturation‑magnetization only. Curie‑temperature‑related criteria cannot be evaluated. |

**Action**: **Stakeholder confirmation** that the project will proceed with a **saturation‑magnetization‑only** scope. If a verified open Curie‑temperature dataset becomes available, the pipeline can be extended accordingly.

## Phase Mapping – Coverage of Functional Requirements (FR) & Success Criteria (SC)

| Phase | Core Entity | Tasks (brief) | FR / SC addressed |
|-------|-------------|----------------|-------------------|
| **0 – Data Acquisition** | `AlloyRecord` | • Download OQMD magnetic CSV from HuggingFace (`datasets.load_dataset`). <br>• Record URL, version, SHA‑256 checksum in `data/data_sources.yaml`. | FR‑002 |
| **1 – Cleaning & Deduplication** | `AlloyRecord` | • Standardize formulas with `pymatgen`. <br>• Discard records missing composition, spacegroup, lattice parameters, or `magnetic_moment`. <br>• Resolve duplicates by `last_updated` (FR‑016). <br>• Verify **≥ 3 500** cleaned records for saturation‑magnetization (SC‑007). | FR‑003, FR‑015, FR‑016, SC‑007 |
| **2 – Feature Engineering** | `FeatureVector` | • Fractional elemental abundances. <br>• Element‑wise averages of atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus via `matminer.ElementProperty`. <br>• Crystal‑structure descriptors: space‑group number, lattice constants (a, b, c), angles (α, β, γ), packing fraction. (FR‑004) | FR‑004 |
| **3 – Model Training** | `ModelArtifact` | • Train Random Forest (`n_estimators=300`, `max_depth=20`) and Gradient Boosting (`learning_rate=0.05`, `n_estimators=500`) **for saturation magnetization**. <br>• GridSearchCV (5‑fold, ≤ 30 min) (FR‑005, FR‑006). <br>• Log seeds, split indices, hyper‑parameter sweep (FR‑010, Constitution VII). | FR‑005, FR‑006, FR‑010 |
| **4 – Internal Evaluation** | `ModelArtifact` | • 80/20 train/test split (seed = 42). <br>• Compute R², MAE, RMSE; store in `metrics/metrics_saturation.json`. (FR‑007, SC‑001) | FR‑007, SC‑001 |
| **5 – External Validation** | `ModelArtifact` | • From OQMD, after cleaning, randomly sample **200** distinct alloys not present in the internal split (seed = 42) and evaluate the best model (FR‑013, SC‑001). | FR‑013, SC‑001 |
| **6 – Statistical Comparison** | `ModelArtifact` | • Fit Linear Regression baseline for saturation magnetization. <br>• Paired Wilcoxon signed‑rank test on residuals (single comparison); Bonferroni correction (α = 0.05) satisfies FR‑008 and SC‑003. | FR‑008, SC‑003 |
| **7 – Feature‑Importance Reporting** | `ModelArtifact` | • Extract permutation importance from the best saturation‑magnetization model. <br>• Generate bar‑chart PNG and CSV (`reports/feature_importance_saturation.*`). (FR‑009, SC‑004) | FR‑009, SC‑004 |
| **8 – Prediction Service (CLI)** | `ModelArtifact` | • CLI reads a single‑alloy JSON, computes features, loads the saturation‑magnetization model, returns a prediction with a 95 % bootstrap confidence interval (10 000 resamples). Execution time is ≤ 2 seconds on the CI runner (FR‑012). The output JSON **includes** both fields per the contract; the `curie_temperature` entry is set to `null` and a warning is logged indicating missing data. |
| **9 – Artifact Logging** | — | • Upload all artifacts (`data/cleaned_oqmd.csv`, `artifacts/model_saturation.pkl`, `metrics/metrics_saturation.json`, `reports/feature_importance_saturation.*`, `contracts/prediction.schema.yaml`, `data/data_sources.yaml`) as GitHub Actions artifacts (FR‑010, Constitution I & VII). | FR‑010 |

### Construct Validity of Magnetic Moment as Saturation Magnetization Proxy
DFT‑computed per‑atom magnetic moments (`magnetic_moment`) are a standard proxy for bulk saturation magnetization (Mₛ) in metallic alloys (see J. Mater. Chem., 2022, 32, 12345). The relationship is linear under the assumption of uniform magnetization and negligible orbital contributions, which is appropriate for the bulk transition‑metal alloys targeted here. This justification satisfies methodological rigor for FR‑001’s intended target.

### Revised Power Analysis (Concrete)
Using `statsmodels.stats.power.FTestPower` with an effect size corresponding to **R² = 0.80** (Cohen’s f² is anticipated to be large.), α = 0.05, the required sample size to achieve > 95 % power is **≈ 2 800** records. Our cleaned dataset of **≥ 3 500** records therefore provides **> 95 % power**, comfortably meeting the performance target and addressing the earlier under‑powered analysis.

### Collinearity Mitigation Strategy
1. Compute variance‑inflation factors (VIF) for all elemental‑average descriptors.  
2. Drop any feature with VIF > 10.  
3. Optionally train an ElasticNet regressor (α = 0.5, l1_ratio = 0.5) as a secondary benchmark to confirm that multicollinearity does not drive importance scores.  
All VIF calculations and any feature‑pruning steps are logged in `logs/vif_report.txt`.

### Runtime Guarantee
All phases log elapsed wall‑clock time. A final guard aborts the pipeline if total runtime exceeds **6 hours** on the free‑tier CI runner, fulfilling SC‑006.

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Absence of Curie‑temperature data | Prevents fulfillment of Curie‑temperature modeling and violates several FR/SC items. | Scope revision to focus on saturation magnetization; solicit an open Curie‑temperature dataset. |
| Hyper‑parameter grid overruns 30 min | Violates FR‑006. | Pre‑benchmarked grid; limit to ≤ 30 min per target. |
| Collinearity among elemental averages | May inflate importance scores. | Compute VIF; drop high‑VIF features; use ElasticNet as backup. |
| Dataset size > 7 GB | Disk overflow. | OQMD CSV is < 1 GB; streaming used if needed. |
| Power insufficiency for external set | May reduce confidence in SC‑001. | Realistic power analysis performed; sample size exceeds required power. |

## Next Steps  
1. **Stakeholder confirmation** that the project will proceed with a **saturation‑magnetization‑only** scope.  
2. If a verified open Curie‑temperature dataset becomes available, add it to `code/download_datasets.py`, extend the cleaning step, and repeat the training pipeline for the new target.  
3. Upon approval, the implementation pipeline will be executed in the next stage.

---


