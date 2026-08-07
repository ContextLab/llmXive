# Implementation Plan: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

**Branch**: `001-llmxive-entanglement-analysis` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-entanglement-analysis/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-entanglement-analysis/spec.md`

## Summary

This feature implements a statistical analysis pipeline to test the hypothesis that "structural entanglement" in teacher model score distributions (variance, entropy) predicts "dimensional fidelity loss" when distilling to scalar rewards. The approach ingests Z-Reward evaluation data (prompts, teacher distributions, student scalars, human annotations), computes per-sample statistical features, and trains a Random Forest regressor to predict the MAE between student outputs and human ground truth. 

**Data Availability**: The pipeline requires the Z-Reward dataset to be present in `data/raw/z_reward.parquet`. If the dataset is missing or not verified in the `research.md` "Verified datasets" block, the pipeline will **FAIL** with a clear error message. Simulation mode is explicitly disabled to prevent data fabrication.

The analysis runs on CPU-first logic. No GPU is required.

## Technical Context

**Language/Version**: Python 3.x  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `datasets` (Hugging Face), `pyyaml`, `pytest`, `ruff`, `scipy`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results`, `state`)  
**Testing**: `pytest` (unit tests for feature engineering, integration tests for pipeline)  
**Target Platform**: GitHub Actions Free Tier (2 CPU, ~7GB RAM)  
**Project Type**: Research Data Pipeline / Statistical Analysis  
**Performance Goals**: Complete ingestion, feature engineering, and model training within 6 hours on CI runner.  
**Constraints**: Must handle missing data gracefully; must not impute missing human annotations; must fit in ~7GB RAM (streaming or sampling required if dataset > 1GB).  
**Scale/Scope**: Single dataset analysis; variable count fixed at a predetermined number of rubric dimensions.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file:*

- **Principle I (Reproducibility)**: Plan mandates pinned seeds in `code/` and deterministic data loading. All transformations output new files; raw data is immutable. Random seeds are pinned in `code/`.
- **Principle II (Verified Accuracy)**: Citations for the Z-Reward dataset are validated against the "Verified datasets" block in `research.md`. If the dataset is not in that block, the pipeline fails.
- **Principle III (Data Hygiene)**: Plan requires **SHA-256** checksums for all files in `data/raw`, recorded in `data/raw/checksums.txt`. Derived features in `data/processed` will be versioned.
- **Principle IV (Single Source of Truth)**: The `results/results.json` file will serve as the single source for all reported metrics (R², MAE, p-values), ensuring figures in the paper trace back to this file. The `results/lineage_report.csv` provides per-sample target source verification.
- **Principle V (Versioning)**: Every artifact under this project carries a content hash. The `state/projects/PROJ-967-llmxive-follow-up-extending-beyond-scala.yaml` file will be updated with `artifact_hashes` for `results/` and `data/processed/` after each run.
- **Principle VI (Distributional Entanglement Quantification)**: The plan explicitly includes a module to compute the 4x4 covariance matrix of the **ENTIRE dataset** (or the full available batch) to derive a quantifiable "entanglement score" (dominant eigenvalue) as a dataset-level descriptor. *Interpretation*: As a single 4-dim vector cannot have a covariance matrix, Principle VI is interpreted as "per-batch" covariance for the dataset window. This is the only mathematically valid interpretation for a single vector sample; the plan does not compute per-sample covariance matrices.
- **Principle VII (Independent Ground-Truth Fidelity Validation)**: The fidelity loss metric is calculated exclusively against human-annotated scores, never against the teacher model's own outputs. The target variable source is logged in `results/lineage_report.csv` and `results/exclusion_log.csv`.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-beyond-scala/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── feature.schema.yaml
│   └── result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/
├── data/
│   ├── raw/             # Downloaded parquet files (immutable), checksums.txt
│   └── processed/       # Derived features, cleaned datasets
├── code/
│   ├── __init__.py
│   ├── ingest.py        # FR-001: Data ingestion and alignment, exclusion logging
│   ├── features.py      # FR-002: Entanglement score calculation
│   ├── train.py         # FR-003, FR-004, FR-005: Model training and validation
│   └── utils.py         # Permutation tests, logging, synthetic data generation
├── tests/
│   ├── unit/
│   │   ├── test_features.py
│   │   └── test_ingest.py
│   └── integration/
│       └── test_pipeline.py
├── results/
│   ├── model.pkl        # Trained model artifact
│   ├── results.json     # Final metrics
│   ├── covariance_matrix.json # Global covariance matrix (FR-007)
│   ├── exclusion_log.csv      # Exclusion trace (FR-006, SC-004)
│   └── lineage_report.csv     # Per-sample target source verification (SC-004)
├── state/
│   └── projects/
│       └── PROJ-967-llmxive-follow-up-extending-beyond-scala.yaml  # Versioning state
├── pyproject.toml       # Dependencies (exact pins)
├── .ruff.toml           # Linting config
└── requirements.txt     # Pinned requirements for CI
```

**Structure Decision**: Single project structure selected to maintain tight coupling between ingestion, feature engineering, and analysis. This minimizes data movement overhead in the CI environment.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is limited to statistical analysis of a fixed 4-dim dataset. | N/A |

## FR/SC Mapping

- **FR-001**: Implemented in `code/ingest.py` (Data ingestion, alignment, exclusion logging).
- **FR-002**: Implemented in `code/features.py` (Variance, entropy, skewness, kurtosis, global covariance matrix).
- **FR-003**: Implemented in `code/features.py` (Fidelity loss calculation using metadata-defined primary dimension).
- **FR-004**: Implemented in `code/train.py` (Random Forest with k-fold cross-validation

The research question, method, and references remain unchanged.).
- **FR-005**: Implemented in `code/train.py` (R², MAE, permutation p-value).
- **FR-006**: Implemented in `code/ingest.py` (Exclusion logic + `results/exclusion_log.csv`).
- **FR-007**: Implemented in `code/features.py` (Output `results/covariance_matrix.json`).
- **SC-001**: Measured in `results/results.json` (R², p-value).
- **SC-002**: Measured in `results/results.json` (MAE vs null baseline).
- **SC-003**: Measured by CI runner timing logs.
- **SC-004**: Verified via `results/lineage_report.csv` (per-sample target source).
- **SC-005**: Verified by `ingest.py` outputting sample count > 0.
