# Implementation Plan: Can Publicly Available Microbiome Data Predict Host Plant Defense Responses?

**Branch**: `001-predict-plant-defense` | **Date**: 2026-10-18 | **Spec**: [spec.md](../specs/001-predict-plant-defense/spec.md)  
**Input**: Feature specification from `specs/001-predict-plant-defense/spec.md`

## Summary
The project must (1) download paired 16S rRNA amplicon data (SRA) and metabolomics profiles (MetaboLights) for *Arabidopsis thaliana* and *Solanum lycopersicum* under herbivore stress, (2) integrate them into a sample‑wise table, (3) reduce microbiome dimensionality with PCA, (4) train a multi‑output Random Forest regressor using leave‑one‑study‑out 5‑fold CV, (5) assess significance with permutation tests, (6) evaluate sensitivity to the PCA variance‑retention threshold (80 %, 90 %, 95 %), and (7) perform a power‑analysis sanity check.  

Because the verified dataset list **does not contain a MetaboLights source**, the required metabolomics data cannot be fetched automatically on the CI runner. The plan therefore includes an explicit *data‑availability checkpoint* that aborts the pipeline with a clear, reproducible error if metabolomics data are missing. This satisfies FR‑008 and SC‑005 while preserving reproducibility (Constitution Principle I).

If a future open metabolomics dataset becomes available (with a verified URL), the “Data Acquisition” phase can be re‑enabled without changing downstream analysis code.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas>=2.2`, `numpy>=1.26`, `scikit-learn>=1.5`, `rpy2` (for optional DADA2), `pyarrow`, `datasets>=2.18` (HuggingFace), `matplotlib>=3.9`, `seaborn>=0.13`, `pytest>=8.2`  
- **Storage**: Files under `data/` (raw parquet, intermediate TSV/CSV, final merged dataset)  
- **Testing**: `pytest` + contract validation (`jsonschema`/`yamale`)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, ≤6 h)  
- **Constraints**: Must stay within 7 GB RAM, 6 h wall‑clock, and avoid any GPU‑only libraries. All statistical methods are CPU‑tractable.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All external data are fetched from immutable URLs; random seeds are pinned; pipeline is pure functions; no manual steps. |
| II. Verified Accuracy | Only URLs from the **Verified datasets** block are referenced; MetaboLights is explicitly marked unavailable. |
| III. Data Hygiene | Raw parquet files are checksum‑verified; each transformation writes a new file with a derivation log. |
| IV. Single Source of Truth | Every figure/table is generated directly from the merged CSV produced in Phase 1; no hand‑typed numbers. |
| V. Versioning Discipline | Artifacts are stored under `state/projects/PROJ-327-...yaml` with content hashes (handled by the platform). |
| VI. Cross‑Dataset Integration Integrity | Integration step validates that sample IDs, species, and condition tags match exactly before merging. |
| VII. Computational Resource & Statistical Rigor | PCA retains ≤90 % variance, Random Forest runs on ≤500 samples, 5‑fold CV, 200 permutations; all fit within RAM/CPU limits. |
| VIII. Power & Sample‑Size Awareness | Post‑hoc power analysis is performed after modeling; a minimum of 30 usable samples is enforced (FR‑008) and reported with effect‑size‑based power. |

## Project Structure
```text
specs/001-predict-plant-defense/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── merged-dataset.schema.yaml

code/
├── acquire.py          # data download & checksum
├── curate.py           # preprocessing, optional DADA2, metadata normalization
├── integrate.py        # merge ASV & metabolite tables, missing‑data assessment
├── pca.py              # PCA fitting within CV folds
├── model.py            # Random Forest training, CV, permutation test
├── sensitivity.py      # variance‑threshold + RF hyper‑parameter sweep
└── utils.py            # logging, seed handling

tests/
├── contract/
│   └── test_merged_schema.py
└── unit/
    ├── test_acquire.py
    ├── test_curate.py
    └── test_model.py
```

## Phase Overview & FR/SC Mapping
| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|----------------|-----------------|
| **0️⃣ Data‑Availability Check** | Verify presence of both 16S (SRA) and metabolomics (MetaboLights) sources. Abort with error if metabolomics missing. | FR‑001, FR‑002, FR‑008 | SC‑005 |
| **1️⃣ Acquisition** | Download SRA parquet files (verified URLs). Compute checksums. **Note**: placeholder URL replaced with a descriptive guard until a verified 16S dataset is supplied. | FR‑001 | SC‑003 |
| **2️⃣ Pre‑processing** | Optional DADA2 via `rpy2` (executed only if raw reads are available). When using open ASV tables, simply load them. Normalize metabolite intensities (median scaling) once metabolomics data become available. | FR‑001, FR‑002 | SC‑004 |
| **3️⃣ Integration** | Align samples by `sample_id`, `species`, `condition`; canonicalize metadata labels (FR‑007). **Missing‑Data Assessment**: characterise missingness, report bias, optionally impute (median for metabolites, zero for ASVs) before dropping rows with irrecoverable gaps; log exclusions. | FR‑002, FR‑007, FR‑008, **new** assessment | SC‑005 |
| **4️⃣ Modeling – Core** | *Leave‑one‑study‑out* 5‑fold CV; within each training fold fit PCA (retain [deferred] variance) → `pca_scores`; **add species one‑hot encoding** to predictor matrix; train multi‑output Random Forest (n_estimators=500, max_features='sqrt', random_state=42). Record per‑metabolite R², mean R², and species‑stratified performance. | FR‑003, FR‑004, FR‑009, FR‑012, FR‑013, **new** species covariate | SC‑001, SC‑006 |
| **5️⃣ Permutation Test** | Reduced to **200** permutations (each permutes metabolite labels **within** each CV fold, refits PCA & RF). Parallelise across available cores. Build null distribution, compute one‑sided p‑value. | FR‑005, FR‑011 | SC‑001, SC‑007 |
| **6️⃣ Sensitivity Sweep** | Repeat Phase 4 for variance thresholds 0.80, 0.90, 0.95 **and** sweep Random Forest `n_estimators` ∈ {200, 500} and `max_features` ∈ {'sqrt', 0.5}. Summarise R² per configuration in a comparison table. | FR‑006, **new** hyper‑parameter robustness | SC‑002 |
| **7️⃣ Reporting** | Generate regression plots (observed vs. predicted per metabolite), feature‑importance bar plot (top 10 PC scores), species‑stratified performance tables, and a markdown summary of all metrics. | FR‑010 | SC‑008 |
| **8️⃣ Guardrails & Tests** | Unit test for FR‑008 abort condition; contract validation for merged CSV against `merged-dataset.schema.yaml`; post‑hoc power analysis (effect‑size based) reported in summary. | FR‑008, SC‑005 | SC‑005 |

All phases are ordered so that data download precedes any processing, and modeling precedes reporting, satisfying the “Computational Task Ordering” rule.

---
