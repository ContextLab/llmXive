# Implementation Plan: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

**Branch**: `001-predict-glass-forming-region` | **Date**: 2026-10-08 | **Spec**: [spec.md](../specs/001-predict-glass-forming-region/spec.md)

## Summary
The project must (1) obtain a **curated experimental dataset** of ternary alloys with reported `critical_cooling_rate` (≥ 500 valid entries) from an **open** source, (2) enrich each entry with thermodynamic descriptors (mixing enthalpy, atomic size mismatch, electronegativity variance) using elemental properties **strictly** from the Open Quantum Materials Database (OQMD), (3) train a Random Forest regressor with a strict 80/20 train‑test split and 5‑fold cross‑validation, (4) conduct permutation importance and a sensitivity analysis over the physically‑grounded thresholds **[50, 100, 150] K/s**, and (5) deliver reproducible, schema‑validated artifacts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas==2.2.*` – data manipulation  
  - `numpy==1.26.*` – numerical utilities  
  - `scikit-learn==1.5.*` – Random Forest, CV, permutation importance  
  - `datasets==2.19.*` – programmatic access to OQMD and experimental CCR datasets  
  - `pyyaml==6.0.*` – schema handling  
  - `click==8.1.*` – CLI wrappers  
- **Storage**: CSV/JSON under `data/` and Pickle for the model.  
- **Testing**: `pytest==8.2.*` with unit tests for feature engineering, data filtering, and schema validation.  
- **Target Platform**: Linux (GitHub Actions free tier) – CPU‑only, ≤2 cores, ≤7 GB RAM, ≤14 GB disk.  
- **Compute Budget**: Entire pipeline ≤ 6 h on the free runner. No GPU is required.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| **I. Reproducibility** | All scripts are deterministic (`random_state=42`), seeds pinned, data fetched from canonical URLs, and SHA‑256 checksums recorded in `data/checksums.txt`. |
| **II. Verified Accuracy** | **Verified Datasets** block (see below) lists the exact HuggingFace URLs for OQMD and the open CCR dataset. No unverified sources are used. |
| **III. Data Hygiene** | Raw OQMD files are stored unchanged; every transformation writes a new CSV (`processed_alloys.csv`). Checksums are recorded; no in‑place edits. |
| **IV. Single Source of Truth** | Every figure/metric in the final report is generated directly from the validated CSV/JSON artifacts; no manual transcription. |
| **V. Versioning Discipline** | After each artifact is created, its SHA‑256 hash is appended to `data/checksums.txt`; the CI records these hashes in the project state YAML. |
| **VI. Thermodynamic Feature Engineering Integrity** | Descriptors are computed solely from elemental properties supplied by OQMD (atomic radius, electronegativity, formation enthalpy). |
| **VII. Cross‑Validation and Permutation Importance Rigor** | The pipeline enforces an 80/20 train‑test split, 5‑fold CV on the training set, and permutation importance with `n_permutations=1000`. No alternative metrics are reported without explicit justification. |

### Verified Datasets
| Dataset | URL | Access Method | Notes |
|---------|-----|---------------|-------|
| OQMD elemental properties | https://huggingface.co/datasets/materials-toolkits/oqmd | `datasets.load_dataset("materials-toolkits/oqmd", revision="v1.0.0", streaming=True)` | Provides atomic radius, electronegativity, formation enthalpy per element. |
| Experimental CCR dataset (open) | https://huggingface.co/datasets/materials-project/glass_formability | `datasets.load_dataset("materials-project/glass_formability")` | Curated ternary alloy entries with measured `critical_cooling_rate`. Must contain ≥ 500 valid rows after filtering. |

## Phase Mapping (covers every FR & SC)

| Phase | Tasks | FR/SC addressed |
|-------|-------|-----------------|
| **Phase 0 – Contract Execution & Data‑Source Validation** | *Run `validate_schemas.py --dry-run` to ensure all contract files are syntactically valid.* Attempt to download the open experimental CCR dataset (see Verified Datasets). If the download fails, write details to `data/logs/fetch_error.log`. If the filtered dataset contains < 500 rows, abort with a clear `RuntimeError("Insufficient experimental CCR data (≥ 500 rows required).")`. No synthetic data is generated or used. | FR‑001, FR‑007, SC‑001, SC‑006 |
| **Phase 0‑0 – Contract Dry‑Run** | Execute `validate_schemas.py --dry-run` against **all** contracts to catch schema errors before any data processing. | SC‑006 |
| **Phase 0‑1 – Hash Generation** | Compute SHA‑256 of `data/processed/processed_alloys.csv` and write to `data/logs/ingestion_hash.txt`; also record the hash in `data/checksums.txt`. | Principle V |
| **Phase 1 – Data Ingestion & Feature Engineering** | `code/ingestion.py` → (a) download OQMD elemental tables, (b) download the experimental CCR dataset, (c) filter out rows with missing labels or elemental data, (d) compute mixing enthalpy, atomic size mismatch, electronegativity variance (VI), (e) **stratified sampling by element family** (no family > 30 % of training set) to mitigate composition‑distribution bias (FR‑008), (f) compute Pearson correlation matrix; if any |r| > 0.8, **pre‑registered rule** drops electronegativity variance (the descriptor with lower a priori theoretical relevance) before any model fitting (addresses CE39A1E8), (g) write `data/processed/processed_alloys.csv`, `data/logs/exclusion_log.txt`, `data/logs/empty_dataset_error.log` (if < 500 rows), and update `data/checksums.txt`. | FR‑001, FR‑002, FR‑008, FR‑010, FR‑011, FR‑012 |
| **Phase 2 – Train‑Test Split & Model Training** | `code/training.py` → stratified 80/20 split (`random_state=42`, `test_size=0.2`) stratified by binned CCR, fit `RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=2)`, perform 5‑fold CV on the training set, compute mean RMSE, test RMSE, and dummy baseline RMSE, save `data/models/random_forest_model.pkl` and `data/models/cv_metrics.json`. Validate the JSON against `contracts/metrics.schema.yaml`. | FR‑003, FR‑009, SC‑002, SC‑005, contracts/metrics.schema.yaml |
| **Phase 3 – Permutation Importance** | `code/analysis.py` → `sklearn.inspection.permutation_importance` with `n_permutations=1000`, `random_state=42`; output ranked CSV `data/reports/feature_importance.csv`. Validate against `contracts/feature_importance.schema.yaml`. | FR‑004, SC‑004, contracts/feature_importance.schema.yaml |
| **Phase 4 – Sensitivity Analysis** | `code/analysis.py` → sweep CCR thresholds across **[50, 100, 150] K/s**; for each threshold compute **RMSE** (primary hypothesis). Apply **Bonferroni correction** for the three RMSE tests (α ≈ 0.0167). Optionally compute binary F1‑score (exploratory, no correction). Output `data/reports/sensitivity_report.json` and validate against `contracts/sensitivity.schema.yaml`. | FR‑005, SC‑003, contracts/sensitivity.schema.yaml |
| **Phase 5 – Validation & Contract Enforcement** | Run `validate_schemas.py` against **all** contracts: `features.schema.yaml`, `processed_alloys.schema.yaml`, `metrics.schema.yaml`, `feature_importance.schema.yaml`, `sensitivity.schema.yaml`, `model_output.schema.yaml`. Abort if any validation fails. Also compute SHA‑256 for the model (`model_sha256.txt`) and append to `data/checksums.txt`. | FR‑010, FR‑011, SC‑006 |
| **Phase 6 – Documentation & Quickstart** | (6‑1) Write a “Limitations” section into the final report documenting that only three thermodynamic descriptors were used (FR‑007) and discuss potential bias. (6‑2) Generate `quickstart.md` (see artifact). (6‑3) Archive all artifacts and ensure their hashes are recorded in `data/checksums.txt`. | FR‑012, SC‑006 |

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open experimental CCR dataset available | Violates FR‑001 | Phase 0 aborts with a clear error; synthetic fallback is *not* used. |
| Large OQMD files exceed RAM | OOM on CI | Stream OQMD files (`datasets.load_dataset(..., streaming=True)`) and compute descriptors row‑by‑row; keep memory < 2 GB. |
| Random Forest training exceeds time budget | CI timeout | `n_estimators` capped at 500, `n_jobs=2`; if runtime > 4 h, automatically reduce to 200 trees (fallback). |
| Collinearity handling introduces bias | Inflated importance | Pre‑registered rule (drop electronegativity variance if |r| > 0.8) applied **before** any model fitting. |
| Multiple‑comparison inflation in sensitivity | Type I error | Primary inference limited to RMSE; Bonferroni correction applied across three thresholds. F1 is labeled exploratory. |
| Composition‑distribution bias | Confound | Stratified sampling by element family (max [deferred] per family) enforced in Phase 1. |
| Dataset version drift | Divergent results | Pin OQMD revision (`revision="v1.0.0"`); checksum files enforce immutability. |
| Relationship between thermodynamic parameters and glass‑forming ability is non‑linear | Justifies Random Forest | No mitigation needed; methodological choice justified in the spec. |

## Timeline (CI‑friendly)
| Week | Deliverable |
|------|-------------|
| 1 | Contract dry‑run, download OQMD & experimental CCR dataset, ingestion, checksum generation (Phase 0‑1). |
| 2 | Train‑test split, Random Forest fit, CV, model serialization, checksum update (Phase 2). |
| 3 | Permutation importance, sensitivity sweep, schema validation for all contracts (Phase 3‑5). |
| 4 | Limitations discussion (FR‑007), quickstart authoring, final artifact archiving, hash finalisation (Phase 6). |
