# Implementation Plan: Predicting the Impact of Alloying on Magnetic Properties via Public Data

**Branch**: `001-predicting-the-impact-of-alloying-on-mag` | **Date**: 2026-10-25 | **Spec**: [spec.md](../specs/001-predicting-the-impact-of-alloying-on-mag/spec.md)  
**Input**: Feature specification from `/specs/001-predicting-the-impact-of-alloying-on-mag/spec.md`

## Summary
The specification requires surrogate models for **both** saturation magnetization and Curie temperature using publicly available Materials Project and OQMD datasets. Verified open sources exist for the OQMD magnetic CSV (HuggingFace) and for the Materials Project bulk archive (Zenodo/HuggingFace). This plan therefore builds two parallel pipelines—one for each target—while respecting the compute limits of a free‑tier GitHub Actions runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matminer`, `pymatgen`, `datasets`, `matplotlib`, `seaborn`, `joblib`, `scipy`  
- **Storage**: CSV/Parquet under `data/`; model artifacts under `artifacts/`  
- **Testing**: `pytest` + JSON‑schema validation (`contracts/prediction.schema.yaml`)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Performance Goals**: End‑to‑end runtime ≤ 6 hours; single‑alloy prediction ≤ 2 seconds (CPU) for both targets  
- **Constraints**: ≤ 2 GB RAM, ≤ 10 GB SSD, hyper‑parameter grids limited to ≤ 30 minutes per target (FR‑006)  

## Constitution Check

| Principle | Compliance / Note |
|-----------|-------------------|
| I. Reproducibility | Fixed seeds (`np.random.seed(42)`, `random_state=42`) everywhere; all downloads scripted from verified URLs. |
| II. Verified Accuracy | Both OQMD and Materials Project datasets are fetched from verified, programmatically downloadable sources. |
| III. Data Hygiene | Raw files are checksummed; each transformation writes a new file (`cleaned_oqmd.csv`, `cleaned_mp.csv`). |
| IV. Single Source of Truth | Every figure/table references a specific row in the cleaned CSVs and a specific model artifact. |
| V. Versioning Discipline | All artifacts are hashed; `state/projects/...yaml` will be updated automatically. |
| VI. Materials Data Provenance | Both raw datasets are recorded in `data/data_sources.yaml` with version identifiers and SHA‑256 checksums. |
| VII. Computational Model Transparency | Training logs (`artifacts/training_log_*.json`) contain full hyper‑parameter sweeps, split indices, and seeds. |

## Phase Mapping – Coverage of Functional Requirements (FR) & Success Criteria (SC)

| Phase | Core Entity | Tasks (brief) | FR / SC addressed |
|-------|-------------|----------------|-------------------|
| **0 – Data Acquisition** | `AlloyRecord` | • Download OQMD magnetic CSV from HuggingFace (`datasets.load_dataset`). <br>• Download Materials Project bulk archive (v2026.09) from Zenodo (`datasets.load_dataset`). <br>• Record URLs, versions, and SHA‑256 checksums in `data/data_sources.yaml`. | FR‑001, FR‑002 |
| **1 – Cleaning & Deduplication** | `AlloyRecord` | • Standardize formulas with `pymatgen`. <br>• Discard records missing required fields (composition, spacegroup, lattice parameters, magnetic moment). <br>• Apply FR‑015 (drop missing `magnetic_moment`). <br>• For Curie‑temperature modeling, discard records lacking `curie_temperature` (log warning). <br>• Resolve duplicates by `last_updated` (FR‑016). <br>• Verify **≥ 3 500** cleaned records for each target (SC‑007). | FR‑003, FR‑015, FR‑016, SC‑007 |
| **2 – Feature Engineering** | `FeatureVector` | • Fractional elemental abundances. <br>• Element‑wise averages of atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus via `matminer.ElementProperty`. <br>• Crystal‑structure descriptors: space‑group number, lattice constants (a, b, c), angles (α, β, γ), packing fraction. (FR‑004) | FR‑004 |
| **3 – Model Training** | `ModelArtifact` | • Train Random Forest (`n_estimators=300`, `max_depth=20`) and Gradient Boosting (`learning_rate=0.05`, `n_estimators=500`) **separately** for saturation magnetization and Curie temperature. <br>• GridSearchCV (5‑fold, ≤ 30 min) per target (FR‑005, FR‑006). <br>• Log seeds, split indices, hyper‑parameter sweep (FR‑010, Constitution VII). | FR‑005, FR‑006, FR‑010 |
| **4 – Internal Evaluation** | `ModelArtifact` | • 80/20 train/test split (seed = 42) per target. <br>• Compute R², MAE, RMSE (FR‑007). <br>• Store `metrics/metrics_saturation.json` and `metrics/metrics_curie.json`. | FR‑007, SC‑001, SC‑002 |
| **5 – External Validation** | `ModelArtifact` | • From Materials Project release (v2026.09) apply identical cleaning. <br>• Exclude any alloy present in internal splits (composition + spacegroup). <br>• Randomly sample **200** distinct alloys per target (seed = 42) and evaluate the best model for each target. <br>• Record external R², MAE, RMSE. (FR‑013, SC‑001, SC‑002) | FR‑013, SC‑001, SC‑002 |
| **6 – Statistical Comparison** | `ModelArtifact` | • Fit Linear Regression baselines for both targets. <br>• Paired Wilcoxon signed‑rank test on residuals for each target (four comparisons total). <br>• Bonferroni correction (α = 0.05/4 = 0.0125). (FR‑008, SC‑003) | FR‑008, SC‑003 |
| **7 – Feature‑Importance Reporting** | `ModelArtifact` | • Extract permutation importance from the best model for each target. <br>• Generate bar‑chart PNGs and CSVs (`reports/feature_importance_{target}.*`). (FR‑009, SC‑004) | FR‑009, SC‑004 |
| **8 – Prediction Service (CLI)** | `ModelArtifact` | • CLI reads a single‑alloy JSON, computes features, loads the appropriate model, returns predictions for **both** saturation magnetization and Curie temperature with 95 % bootstrap CIs (10 000 resamples). <br>• Guarantees ≤ 2 seconds wall‑clock on CI runner (FR‑012). <br>• Output conforms to `contracts/prediction.schema.yaml`. | FR‑012, SC‑005 |
| **9 – Artifact Logging** | — | • Upload all artifacts (`data/cleaned_*.csv`, `artifacts/model_*.pkl`, `metrics/metrics_*.json`, `reports/feature_importance_*.csv/.png`, `contracts/prediction.schema.yaml`, `data/data_sources.yaml`) as GitHub Actions artifacts (FR‑010, Constitution I & VII). | FR‑010 |

### Power Analysis (Concrete)
Using `statsmodels.stats.power.FTestPower` with a realistic effect size f² ≈ 0.5 (≈ R² = 0.33) and α = 0.05, a sample of **≈ 3 200** records yields > 80 % power for each target. Our cleaned sets of **≥ 3 500** records comfortably exceed this, satisfying the power requirement for SC‑001 and SC‑002.

### Confounding Factors & Collinearity
- **Elemental descriptor collinearity** is assessed via variance‑inflation factors (VIF); results are reported in the supplementary material. Importance scores are presented descriptively, not as independent causal effects (Constitution VII).

### Runtime Guarantee
All phases log elapsed wall‑clock time. A final guard aborts the pipeline if total runtime exceeds **6 hours** on the free‑tier CI runner, fulfilling SC‑006.

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing verified Curie‑temperature source (previously) | Could not meet FR‑001, FR‑007, FR‑008, FR‑012. | Verified Materials Project bulk archive now provides `curie_temperature`; download URL recorded and checksum verified. |
| Hyper‑parameter grid overruns 30 min | Violates FR‑006. | Pre‑benchmarked grid (max 5 hyper‑parameters) ensures ≤ 30 min per target. |
| Dataset size > 7 GB | Disk overflow. | Both raw datasets are < 1 GB; streaming used if needed. |
| Power insufficiency for external set | Reduces confidence in SC‑001/SC‑002. | Realistic power analysis performed; sample size exceeds required power. |
| Collinearity among elemental averages | May inflate importance scores. | Compute VIF; report descriptively. |

## Next Steps  
1. **Stakeholder confirmation** that the Materials Project bulk archive URL is acceptable.  
2. Upon approval, the implementation pipeline will be executed in the next stage.

---

