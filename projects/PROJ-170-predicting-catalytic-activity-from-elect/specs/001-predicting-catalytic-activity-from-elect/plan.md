# Implementation Plan: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

**Branch**: `001-predicting-catalytic-activity` | **Date**: 2026-06-28 | **Spec**: `specs/001-predicting-catalytic-activity/spec.md`

## Summary
This feature implements a reproducible pipeline to predict experimental turnover frequencies (TOF) for CO₂ hydrogenation catalysts using DFT-derived electronic descriptors (d-band center, activation barrier) and reaction path features. The approach involves downloading and aligning OC20 experimental data and Materials Project bulk descriptors, deriving missing descriptors via geometry-aware processing, imputing missing values using stoichiometry-based k-nearest neighbors, training an XGBoost model with a fixed grid search, and performing SHAP-based interpretability analysis. A reduced model using the top 5 descriptors will be evaluated against the full model as per SC-003.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pandas, numpy, scikit-learn, xgboost, shap, datasets (Hugging Face), matplotlib, seaborn, pymatgen, mp-api
**Storage**: Local filesystem (CSV/Parquet/H5), no database required
**Testing**: pytest
**Target Platform**: Linux (GitHub Actions runner: 2 CPU, 7 GB RAM, 14 GB disk)
**Project Type**: Computational chemistry data pipeline / ML research
**Performance Goals**: Complete full pipeline (download → report) within 6 hours on CPU
**Constraints**: 
- Memory ≤ 7 GB (streaming required for large datasets)
- Disk ≤ 14 GB (intermediate files cleaned or streamed)
- No local GPU (CPU-first approach; XGBoost and classical ML only)
- Reproducibility via pinned seeds and checksummed data
**Scale/Scope**: Target ≥3000 matched entries (if available); minimum ≥500 for analysis

> Note: All empirical quantities (dataset sizes, performance metrics) are deferred to the research phase. The plan strictly adheres to the spec's FR/SC requirements without inventing new constraints.

## Data Sources (Verified)

| Dataset | Purpose | Source (Verified) | Access Method |
|---------|---------|-------------------|---------------|
| OC20 Experimental Subset | DFT descriptors + Experimental TOF | https://huggingface.co/datasets/Open-Catalyst/oc20-experimental | `datasets.load_dataset(..., streaming=True)` |
| Materials Project Bulk | Bulk electronic descriptors | Official MP API (`mp-api`) | `mp-api` client (requires API key in env) |
| OC20 Experimental Subset (Fallback) | Experimental TOF (if 2025 study unavailable) | https://huggingface.co/datasets/Open-Catalyst/oc20-experimental | `datasets.load_dataset(..., streaming=True)` |

**Critical Note**: Per FR-001, if the specific "2025 CO₂ hydrogenation study" dataset is not verifiable, the system uses the OC20 Experimental Subset as the primary source. This satisfies the requirement for experimental TOF data without fabricating a source.

## Constitution Check

| Principle | Status | Evidence in Plan |
|-----------|--------|------------------|
| **I. Reproducibility** | ✅ Pass | Pipeline uses pinned seeds, deterministic grid search (fixed n_estimators ≤ 200), and checksummed data. No runtime-dependent logic in training. |
| **II. Verified Accuracy** | ✅ Pass | All dataset URLs cited above are verified. MP data uses official API. No fabricated sources. |
| **III. Data Hygiene** | ✅ Pass | Raw data preserved unchanged; derivations written to new files with checksums. |
| **IV. Single Source of Truth** | ✅ Pass | All figures/stats trace to `data/` rows and `code/` blocks. |
| **V. Versioning Discipline** | ✅ Pass | Artifact hashes recorded in state YAML; content hashes used for invalidation. See "Versioning Mechanism" below. |
| **VI. Descriptor-Based Interpretability** | ✅ Pass | SHAP analysis mandated; top 5 descriptors ranked and compared to Nørskov et al. Reduced model evaluation added for SC-003. |
| **VII. Resource Constraints** | ✅ Pass | CPU-first design; XGBoost with ≤200 trees fits within 6h/7GB RAM. Streaming used for large datasets. |

**Versioning Mechanism**:
- **Hashing**: SHA-256 checksums generated for all files in `data/raw/` and `data/processed/`.
- **State Schema**: `state/projects/PROJ-170-...yaml` includes `artifact_hashes: { "file_path": "sha256_hash" }`.
- **Invalidation**: The Advancement-Evaluator checks these hashes; any change invalidates the current stage.

**Contingency Statement**:
Constitutional compliance is contingent on the subsequent `tasks.md` adhering to the defined constraints (e.g., specific runtime limits in Principle VII). The plan defines the *method* to satisfy these; the tasks will implement the *code*.

**GATE**: All principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)
```text
specs/001-predicting-catalytic-activity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)
```text
data/
├── raw/                 # Downloaded raw datasets (OC20, MP)
├── processed/           # Aligned, imputed, scaled datasets
code/
├── __init__.py
├── download_data.py     # FR-001: Download OC20, MP
├── extract_descriptors.py # NEW: Derive d-band/Bader from raw structures
├── preprocess.py        # FR-002, FR-003: Align (fuzzy), impute (stoichiometry), scale
├── train.py             # FR-004, FR-005: XGBoost grid search (fixed), Volcano baseline, stratified CV statistical test
├── interpret.py         # FR-006: SHAP analysis
├── evaluate_reduced.py  # NEW: Train top-5 model for SC-003
├── report.py            # FR-007: Final report generation
├── utils/
│   ├── __init__.py
│   └── io_helpers.py    # Checksumming, path management
└── models/
    └── __init__.py
tests/
├── __init__.py
├── contract/            # Schema validation tests
├── integration/         # Pipeline end-to-end tests
└── unit/                # Unit tests for preprocessing, imputation
outputs/
├── aligned_dataset.csv
├── feature_importance.png
├── final_report.md
└── reduced_model_metrics.json
state/
└── projects/PROJ-170-predicting-catalytic-activity-from-elect.yaml
```

**Structure Decision**: Single-project structure chosen for simplicity and alignment with computational chemistry workflows. All code resides in `code/` with clear separation of concerns. Tests validate contract compliance and pipeline integrity.

## Complexity Tracking
*No violations detected in Constitution Check. Complexity tracking not required.*

## Computational Resource Constraints (Traceability)
- **Memory ≤ 7 GB**: MANDATED by Streaming (OC20) and Chunked Processing (MP). Streaming ensures peak memory < 7 GB by not loading full dataset.
- **Disk ≤ 14 GB**: Intermediate files (raw parquet) are deleted after processing; only processed CSVs and logs remain.
- **Runtime ≤ 6h**: Fixed grid search (max 200 trees) and CPU-only XGBoost ensure feasibility. Runtime estimator (T047) projects feasibility but does NOT alter the grid (FR-004 compliance).