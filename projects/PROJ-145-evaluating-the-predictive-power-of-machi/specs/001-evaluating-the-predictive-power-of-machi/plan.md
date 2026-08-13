# Implementation Plan: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

**Branch**: `001-eva-predictive-power-hea` | **Date**: 2026-08-01 | **Spec**: `specs/001-evaluating-the-predictive-power-of-machi/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-predictive-power-of-machi/spec.md`

## Summary

This project evaluates the extrapolative capability of descriptor-based Machine Learning (Random Forest, Gradient Boosting) for High-Entropy Alloys (HEAs). The technical approach involves ingesting thermodynamic data from verified Hugging Face sources (AFLOW, API-derived datasets), engineering compositional descriptors (atomic radius, electronegativity, VEC, melting point) using `pymatgen`, and training models under strict CPU constraints. The core innovation is the separation of test sets into "Hold-out Known" (for error measurement) and "True Novel" (for uncertainty calibration), addressing the research question of whether standard descriptors can reliably identify novel compositions in unexplored chemical spaces. **Crucially, the "True Novel" set is filtered for thermodynamic stability to ensure physical plausibility.**

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymatgen` (v2024+), `scikit-learn` (v1.5+), `pandas`, `numpy`, `datasets` (Hugging Face), `scipy`, `statsmodels`  
**Storage**: Local CSV/Parquet files under `data/processed/` and `data/models/`  
**Testing**: `pytest` with `pytest-cov`  
**Target Platform**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Complete end-to-end pipeline (ingestion to report) within 6 hours; RAM usage < 7 GB.  
**Constraints**: No GPU access for training; must use streaming or sampling for large datasets; strict reproducibility (random seeds).  
**Scale/Scope**: Ingest a substantial corpus of known HEA entries, ranging from thousands to tens of thousands. (estimated from source); generate ~1k Hold-out and ~1k True Novel candidates. **Streaming chunk size: A moderate batch size is selected to balance latency and throughput.; Max row limit: a large, scalable threshold sufficient for comprehensive dataset analysis..**

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/config.py`; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs sourced from the "# Verified datasets" block; no external URLs invented. |
| **III. Data Hygiene** | **PASS** | Checksums recorded in `state/...yaml`; raw data preserved in `data/raw/`. |
| **IV. Single Source of Truth** | **PASS** | All metrics in `paper/` derived from `data/processed/metrics_summary.csv`. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked for all artifacts in `data/` and `code/`. |
| **VI. Extrapolation Integrity** | **PASS** | Plan explicitly separates "Hold-out Known" (error) and "True Novel" (uncertainty) sets. **Uncertainty metrics (variance + Mahalanobis distance + Conformal Prediction intervals) are explicitly mapped to this principle.** |
| **VII. Descriptor-Traceability** | **PASS** | All descriptors (radius, electronegativity, VEC, melting point) calculated via `pymatgen` with versioned constants. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-predictive-power-of-machi/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── hea_dataset.schema.yaml
│   ├── heas_train.schema.yaml
│   ├── output_schema.schema.yaml
│   ├── prediction_output.schema.yaml
│   └── split_metadata.schema.yaml  # NEW: Schema for split validation
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Seeds, paths, hyperparameters
├── data_ingestion.py    # FR-001, FR-002: Download and filter HEA data
├── descriptor_calc.py   # FR-003: Calculate pymatgen descriptors
├── train_model.py       # FR-004: Train RF/GB models with 5-fold CV
├── evaluate.py          # FR-005, FR-006, FR-007: Extrapolation & Uncertainty
├── report_gen.py        # FR-008: Generate final CSV and stats
├── validate_splits.py   # FR-002: Verify no overlap between sets
└── utils.py             # Helpers (clamping, hashing)

data/
├── raw/                 # Downloaded parquet/jsonl (immutable)
│   ├── aflow_thermalcond.parquet
│   └── api_thermal.parquet
├── processed/           # Cleaned, feature-engineered data
│   ├── heas_train.csv
│   ├── holdout_known.csv
│   ├── true_novel.csv
│   └── metrics_summary.csv
└── models/              # Pickle artifacts
    ├── rf_model.pkl
    └── gb_model.pkl

tests/
├── __init__.py
├── unit/
│   ├── test_descriptors.py
│   └── test_data_split.py
└── integration/
    └── test_pipeline.py

specs/001-evaluating-the-predictive-power-of-machi/
└── contracts/
    ├── hea_dataset.schema.yaml
    └── output_schema.schema.yaml
```

**Structure Decision**: Single project structure selected. The pipeline is linear (Ingest -> Feature Eng -> Train -> Evaluate -> Report), making a monolithic `code/` directory with modular scripts the most maintainable approach for a research pipeline. `tests/` is separated to ensure unit tests for descriptor calculation and data splitting logic can run without downloading data.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Separation of Hold-out vs. True Novel** | Required to distinguish between "unseen in training" (interpolation error) and "unmeasured in nature" (extrapolation/uncertainty). | A single test set would conflate these distinct research questions, failing to address the specific hypothesis about novel composition identification. |
| **Streaming Data Load** | Source datasets (AFLOW) may exceed 7GB RAM if fully loaded. | Loading full datasets into memory risks OOM on GitHub Actions; streaming ensures CPU-first feasibility. **Chunk size: 1000 rows.** |
| **Convex Hull Distance Calculation** | Required for "True Novel" uncertainty calibration (FR-007). | Simple variance is insufficient for chemical space extrapolation; distance from training hull provides a geometric proxy for reliability. **Now uses Mahalanobis distance with StandardScaler normalization.** |
| **Thermodynamic Stability Filter** | Required to ensure "True Novel" set contains physically plausible, stable phases. | A set of random compositions may be thermodynamically unstable, rendering uncertainty calibration meaningless for the goal of identifying *stable* novel HEAs. |
| **Live API Verification** | Required to satisfy FR-001 and FR-002 (verify absence from source API). | Checking only against local dumps is insufficient; a live API check is needed to confirm true novelty. |
