# Implementation Plan: Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses

**Branch**: `001-gene-regulation` | **Date**: 2026-06-28 | **Spec**: `specs/001-quantifying-the-effect-of-alloying-eleme/spec.md`
**Input**: Feature specification from `/specs/001-quantifying-the-effect-of-alloying-eleme/spec.md`

## Summary

This project implements a computational pipeline to quantify the relationship between alloy composition and Glass-Forming Ability (GFA) in metallic glasses. The system ingests experimental data from the GFA-D2 pilot dataset, engineers physics-based descriptors (including pairwise and triplet interactions) using Pymatgen, trains ensemble regression models (Random Forest, Gradient Boosting) to predict the logarithm of the critical cooling rate ($log_{10}(R_c)$), and screens novel ternary combinations. The pipeline strictly adheres to CPU-only constraints, ensuring reproducibility on free-tier GitHub Actions runners. It addresses statistical rigor through Leave-One-Cluster-Out (LOCO) validation, heteroscedasticity correction via multivariate residual binning, and Conformal Prediction (calibrated on LOCO validation folds) for uncertainty quantification. Novelty is assessed against the training set and the Materials Project database.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `pymatgen`, `statsmodels`, `shap`, `pyyaml`, `requests`, `scikit-learn-extra`  
**Storage**: Local CSV/Parquet files within `data/` and `output/` directories; no external database.  
**Testing**: `pytest` with contract tests validating schema compliance and deterministic outputs.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM, no GPU).  
**Project Type**: Scientific data pipeline / CLI  
**Performance Goals**: Complete end-to-end pipeline (ingestion, training, screening, SHAP analysis) within ≤6 hours; memory usage <7GB.  
**Constraints**: No GPU/CUDA; no large language models; strict adherence to verified dataset URLs; deterministic random seeds.  
**Scale/Scope**: ~500 experimental data points (estimated); [deferred] unique ternary combinations to screen.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | All random seeds pinned in `code/`; dataset fetched from canonical HuggingFace URL; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | ✅ Pass | Dataset URL verified in `# Verified datasets` block; no external citations in plan without source verification. |
| **III. Data Hygiene** | ✅ Pass | Raw data preserved in `data/raw/`; checksums recorded; transformations write to new files in `data/processed/`. |
| **IV. Single Source of Truth** | ✅ Pass | All metrics (R², MAE) derived from `code/` execution logs; no hand-typed numbers in documentation. |
| **V. Versioning Discipline** | ✅ Pass | Artifact hashes tracked in `state/`; plan updates timestamp on change. |
| **VI. Physical Descriptor Consistency** | ✅ Pass | `pymatgen` version pinned; descriptor calculation logic isolated to ensure consistency across runs. |
| **VII. Prediction Uncertainty** | ✅ Pass | **Phase 3 (Screening)** implements Conformal Prediction (via `code/03_screen_candidates.py`) with explicit steps: (1) LOCO calibration, (2) Mahalanobis DoA check, (3) Interval generation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantifying-the-effect-of-alloying-eleme/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── model_output.schema.yaml
    ├── candidate.schema.yaml
    └── prediction.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_ingest_and_engineer.py   # FR-001, FR-002
│   ├── 02_train_and_validate.py    # FR-003, FR-004, FR-010
│   ├── 03_screen_candidates.py     # FR-005, FR-006, FR-007, FR-009
│   ├── 04_analyze_feature_importance.py # SC-002 (SHAP)
│   └── utils/
│       ├── descriptors.py          # Pymatgen wrappers (incl. pairwise/triplet)
│       ├── conformal.py            # DoA logic
│       └── logging.py
├── data/
│   ├── raw/                        # Downloaded CSVs (checksummed)
│   └── processed/                  # Feature-engineered CSVs
├── output/
│   ├── best_model.pkl
│   ├── best_model_weighted.pkl     # If heteroscedasticity detected
│   ├── top_candidates.csv
│   ├── verification_requests.json  # FR-008
│   └── shap_summary.png            # SC-002
└── tests/
    ├── contract/
    │   └── test_schemas.py
    └── unit/
        └── test_descriptors.py
```

**Structure Decision**: Single project structure chosen to minimize overhead for a data-science pipeline. Scripts are ordered by data flow (Ingest → Train → Screen → Analyze) to ensure dependencies are met before execution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Conformal Prediction (FR-009)** | Required for rigorous Domain of Applicability (DoA) and extrapolation risk flagging. | Simple variance-only intervals do not guarantee coverage probability or distinguish between interpolation and extrapolation risk. |
| **Weighted Loss Retraining (FR-010)** | Required to address heteroscedasticity if Breusch-Pagan test fails (p < 0.05). | Ignoring heteroscedasticity leads to biased confidence intervals and unreliable predictions for high-variance regions. |
| **LOCO Cross-Validation (FR-004)** | Required to test generalizability across chemical families, not just random splits. | Random K-Fold splits would leak chemical family information, inflating performance metrics and failing to detect model bias toward specific element clusters. |
| **SHAP Analysis (SC-002)** | Required to measure feature importance rankings against global SHAP values. | Standard feature importance (Gini/impurity) is biased towards high-cardinality features and does not provide additive explanations. |
| **Pairwise/Triplet Descriptors** | Required to capture local atomic environments beyond global means. | Global scalar features (mean/variance) fail to distinguish between chemically distinct but globally similar alloys. |