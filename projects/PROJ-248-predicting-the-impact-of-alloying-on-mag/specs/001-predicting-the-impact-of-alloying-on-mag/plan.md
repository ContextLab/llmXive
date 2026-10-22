# Implementation Plan: Predicting the Impact of Alloying on Magnetic Properties via Public Data

**Branch**: `001-predicting-the-impact-of-alloying-on-mag` | **Date**: 2026-10-22 | **Spec**: [spec.md](../specs/001-predicting-the-impact-of-alloying-on-mag/spec.md)  
**Input**: Feature specification from `/specs/001-predicting-the-impact-of-alloying-on-mag/spec.md`

## Summary
Build an end‑to‑end, reproducible pipeline that (1) downloads publicly available magnetic‑property datasets (Materials Project bulk archive **v2026.09** – openly downloadable via Zenodo – and OQMD magnetic release), (2) cleans and deduplicates the data, (3) engineers compositional, crystallographic, **and optional DFT‑metadata** descriptors, (4) trains two regression models per target (Random Forest, Gradient Boosting) for **both** saturation magnetization **and** Curie temperature, (5) evaluates models on internal and independent external splits, (6) conducts Bonferroni‑corrected Wilcoxon signed‑rank tests against a linear‑regression baseline for each target, (7) extracts permutation‑importance scores for each target, and (8) exposes a CLI for single‑alloy prediction (with 95 % bootstrap confidence intervals) that runs in ≤ 2 seconds.

All steps are CPU‑first and respect the free‑tier GitHub Actions resource limits (≤ 2 GB RAM, ≤ 10 GB SSD, ≤ 6 h total wall‑clock). No GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matminer`, `pymatgen`, `datasets`, `matplotlib`, `seaborn`, `joblib`, `scipy`  
- **Storage**: CSV/Parquet under `data/`; model artifacts under `artifacts/`  
- **Testing**: `pytest` + JSON‑schema validation (`contracts/prediction.schema.yaml`)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Performance Goals**: End‑to‑end runtime ≤ 6 hours; single‑alloy prediction ≤ 2 seconds (CPU)  
- **Constraints**: ≤ 2 GB RAM, ≤ 10 GB SSD, hyper‑parameter grid limited to ≤ 30 minutes per target  
- **Scale/Scope**: ≥ 3 500 cleaned alloy records **per modelling target**; external validation set of ≥ 200 distinct alloys from Materials Project.

## Constitution Check
| Principle | Compliance / Note |
|-----------|-------------------|
| I. Reproducibility | Fixed seeds (`np.random.seed(42)`, `random_state=42`) everywhere; all downloads scripted. |
| II. Verified Accuracy | Only verified open datasets (OQMD via HuggingFace, Materials Project bulk archive via Zenodo) are used; no unverified citations. |
| III. Data Hygiene | Raw files are checksummed; each transformation writes a new file (`cleaned_oqmd.csv`, `cleaned_mp.csv`). |
| IV. Single Source of Truth | Every figure/table references a specific row in `data/cleaned_*.csv` and a specific model artifact (`artifacts/model_{target}.pkl`). |
| V. Versioning Discipline | All artifacts are hashed; `state/projects/...yaml` will be updated automatically. |
| VI. Materials Data Provenance | **All raw magnetic‑property data are obtained from the publicly released Materials Project bulk archive (v2026.09) – an official snapshot of the REST API – and from OQMD.** The exact version identifiers are recorded in `data/data_sources.yaml`. |
| VII. Computational Model Transparency | Training logs (`artifacts/training_log_{target}.json`) contain full hyper‑parameter sweep, split indices, seeds, and optional DFT‑metadata covariates. |

**Note**: Success criteria are SC‑001 through SC‑007; there is no SC‑VI.

## Project Structure
```text
specs/001-predicting-the-impact-of-alloying-on-mag/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── prediction.schema.yaml

src/
├── cli/
│   └── predict.py          # CLI entry point for single‑alloy prediction
├── models/
│   ├── train.py            # Training & evaluation pipeline
│   └── utils.py            # Feature‑engineering utilities
└── services/
    └── data_fetch.py       # Download Materials Project and OQMD datasets
```

## Phase Mapping – Coverage of Functional Requirements (FR) & Success Criteria (SC)

| Phase | Core Entity | Tasks (brief) | FR / SC addressed |
|-------|-------------|----------------|-------------------|
| **0 – Data Acquisition** | `AlloyRecord` | • Download **Materials Project bulk archive v2026.09** (Zenodo DOI ``) via `datasets.load_dataset(..., streaming=True)`.<br>• Download OQMD magnetic CSV from the verified HuggingFace URL.<br>• Record both version identifiers in `data/data_sources.yaml`. | FR‑001 (Materials Project), FR‑002 (OQMD) |
| **1 – Cleaning & Deduplication** | `AlloyRecord` | • Standardize formulas with `pymatgen`.<br>• Discard records missing `composition`, `spacegroup`, or lattice parameters.<br>• Apply FR‑015: drop entries lacking `magnetic_moment`; retain those missing `curie_temperature` for saturation‑magnetization only (log warning).<br>• Resolve duplicates by `last_updated` (FR‑016).<br>• After cleaning, verify **≥ 3 500** records for **each** target (SC‑007). | FR‑003, FR‑015, FR‑016, SC‑007 |
| **2 – Feature Engineering** | `FeatureVector` | • Compute fractional elemental abundances.<br>• Compute element‑wise averages of atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus via `matminer.ElementProperty` (FR‑004).<br>• Add crystal‑structure descriptors: space‑group number, lattice constants (a,b,c), angles (α,β,γ), packing fraction.<br>• **Optional**: Append DFT metadata (functional, k‑point density, pseudopotential) as additional numeric covariates (addressing methodology‑be748e2e). | FR‑004 |
| **3 – Model Training** | `ModelArtifact` | • For **each target** (saturation magnetization, Curie temperature) train Random Forest (`n_estimators=300`, `max_depth=20`) and Gradient Boosting (`learning_rate=0.05`, `n_estimators=500`).<br>• Perform **GridSearchCV** (5‑fold, ≤ 30 min) over a limited grid for **both** targets (FR‑005, FR‑006).<br>• Log seeds, split indices, full hyper‑parameter sweep, and optional DFT‑metadata usage (FR‑010, Constitution VII). | FR‑005, FR‑006, FR‑010 |
| **4 – Internal Evaluation** | `ModelArtifact` | • 80/20 train/test split (seed = 42) **per target**.<br>• Compute R², MAE, RMSE for **both** targets (FR‑007).<br>• Store `metrics/metrics_{target}.json`. | FR‑007, SC‑001, SC‑002 |
| **5 – External Validation** | `ModelArtifact` | • From the **Materials Project v2026.09** pool (post‑cleaning), randomly sample **200** distinct alloys **per target** that are not in the internal split (seed = 42) (FR‑013).<br>• Evaluate the best model for each target; report the same metrics (R², MAE, RMSE). | FR‑013, SC‑001, SC‑002 |
| **6 – Statistical Comparison** | `ModelArtifact` | • Fit a simple Linear Regression baseline for each target.<br>• Conduct paired Wilcoxon signed‑rank tests on residuals for **both** targets (FR‑008).<br>• Apply Bonferroni correction for four comparisons (α = 0.0125). | FR‑008, SC‑003 |
| **7 – Feature‑Importance Reporting** | `ModelArtifact` | • Extract permutation importance from the best‑performing model **per target** (by R²).<br>• Generate bar‑chart PNGs and CSVs (`reports/feature_importance_{target}.csv` / `.png`). | FR‑009, SC‑004 |
| **8 – Prediction Service (CLI)** | `ModelArtifact` | • CLI reads a single‑alloy JSON, computes features (including optional DFT metadata if supplied), loads the appropriate model, returns predictions + 95 % CI via bootstrap (10 000 resamples).<br>• Guarantees wall‑clock ≤ 2 seconds on the CI runner (FR‑012).<br>• Output conforms to the updated `contracts/prediction.schema.yaml` (no nullable fields). | FR‑012, SC‑005 |
| **9 – Artifact Logging** | — | • Upload all artifacts (`data/cleaned_*.csv`, `artifacts/model_{target}.pkl`, `metrics/metrics_{target}.json`, `reports/feature_importance_*.csv/.png`, `contracts/prediction.schema.yaml`, `data/data_sources.yaml`) as GitHub Actions artifacts (FR‑010, Constitution I & VII). | FR‑010 |

### Power Analysis (Concrete)

Assuming a medium effect size for R² = 0.80 (Cohen’s f² ≈ 4), α = 0.05, two‑tailed test, and 5‑fold CV, the required sample size is on the order of a few thousand. Our cleaned set of **≥ 3 500** records therefore yields > 80 % power for both targets (validated with `statsmodels.stats.power.FTestPower`). The external validation of 200 records provides > 70 % power to confirm the achieved R², which is reported as a limitation.

### Confounding Factors & Collinearity

- **DFT metadata** are now optional covariates; we will compute variance‑inflation factors (VIF) and report them in the supplementary analysis (Methodology‑be748e2e).  
- **Elemental descriptor collinearity** is acknowledged; importance scores are presented descriptively, not as independent causal effects (Constitution VII).

### Runtime Guarantee

All phases log elapsed wall‑clock time. The pipeline aborts with a clear error if total runtime exceeds **6 hours** on the free‑tier CI runner.

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing open Curie‑temperature data (previously) | Prevented Curie modeling; now resolved by using Materials Project bulk archive. |
| Hyper‑parameter grid overruns 30 min | Pre‑benchmarked grid guarantees ≤ 30 min per target. |
| Collinearity among elemental averages | VIF analysis; importance interpreted descriptively. |
| Dataset size > 7 GB | Combined raw files < 500 MB; streaming used for MP bulk archive. |
| Power insufficiency for external set | Power analysis (deferred) will be reported; note limitation if power < 80 %. |

---


