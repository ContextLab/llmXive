# Implementation Plan: Physical Activity Levels and Mood Variability in Daily Life

**Branch**: `001-physical-activity-mood-variability` | **Date**: 2026-06-17 | **Spec**: `specs/001-physical-activity-mood-variability/spec.md`
**Input**: Feature specification from `/specs/001-physical-activity-mood-variability/spec.md`

## Summary

This project implements a statistical analysis pipeline to investigate the associational relationship between daily step counts and intra-day mood variability using the StudentLife dataset. The system will ingest raw sensor and EMA data, compute daily aggregates (including derived sleep and affect metrics), and fit linear mixed-effects models (LMM) controlling for sleep, day-of-week, and measurement frequency. The pipeline includes rigorous validation via leave-one-participant-out cross-validation (reporting coefficient distributions) and sensitivity analyses (weekdays-only, alternative metrics, and imputation for single-rating days) to ensure robustness. All results will be framed as associational, adhering to the observational nature of the data.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `statsmodels`, `scikit-learn`, `pyyaml`, `requests`, `numpy`
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/interim`)
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for aggregation logic)
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7GB RAM)
**Project Type**: Computational Research Pipeline (CLI/Data Processing)
**Performance Goals**: Complete full pipeline (ingestion to report) within 6 hours on CPU-only runner.
**Constraints**: No GPU usage; memory usage < 6GB; strict handling of missing data; explicit "associational" framing.
**Scale/Scope**: Single dataset (StudentLife), ~100 participants, ~30-60 days per participant.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

**Status**: PASSED (with implementation notes)

| Principle | Requirement | Implementation Plan Alignment |
| :--- | :--- | :--- |
| **I. Reproducibility** | Random seeds pinned; external datasets from canonical source. | `code/` scripts will set `np.random.seed(42)` and `random.seed(42)`. Data fetched via verified HuggingFace mirror of OSF DOI. |
| **II. Verified Accuracy** | Citations verified against primary sources. | `research.md` cites only verified dataset URLs. The `Reference-Validator` agent will check title-token overlap (threshold) before awarding review points. |
| **III. Data Hygiene** | Checksums recorded; raw data immutable; derivations new files. | `ingest.py` computes SHA256 checksum of downloaded files and records it in `state/projects/PROJ-715...yaml`. `data/raw` stores the immutable parquet. |
| **IV. Single Source of Truth** | Figures/stats trace to one row in `data/` and one block in `code/`. | Report generation will read exclusively from `data/processed/daily_aggregates.csv` and `data/processed/model_results.json`. |
| **V. Versioning Discipline** | Content hashes update state. | `state/projects/PROJ-715...yaml` will be updated by the execution agent with content hashes of all artifacts upon every run. |
| **VI. EMA Data Temporal Integrity** | Variability metrics only after timestamp alignment; missing ratings excluded. | `preprocess.py` explicitly filters data (`drop where n_mood_ratings < 2`) *before* writing to output. The `daily_aggregates.schema.yaml` contract validates the final output adheres to this constraint. |
| **VII. Model Diagnostics** | Residual normality/homoscedasticity checks; LOOCV for generalization. | `code/analysis.py` will include `statsmodels` diagnostic plots (Shapiro-Wilk, Breusch-Pagan) and a LOPO loop reporting coefficient distributions. |
| **VIII. Derived Metrics** | Sleep and Affect must be derived if missing. | `preprocess.py` implements algorithmic derivation for `sleep_duration` (accelerometer inactivity) and `baseline_affect` (survey aggregate) if raw columns are absent. |

**Reproducibility Requirements**:
- `code/requirements.txt` will pin `pandas`, `statsmodels`, `scikit-learn`, `pyyaml`, `requests`, `numpy`.
- Scripts will run in an isolated virtualenv.

**Data Hygiene**:
- `data/raw/bronze.parquet` checksum recorded in state file by `ingest.py`.
- PII scan passed (dataset is anonymized; no PII committed).

## Project Structure

### Documentation (this feature)

```text
specs/001-physical-activity-mood-variability/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── daily_aggregates.schema.yaml
    └── model_results.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants
├── ingest.py            # Download, verify checksum, convert to parquet
├── preprocess.py        # Aggregation, alignment, cleaning, feature engineering (incl. derived metrics)
├── analysis.py          # LMM/GLMM fitting, diagnostics, LOPO, sensitivity
├── report.py            # Generate PDF/HTML report
└── requirements.txt

data/
├── raw/                 # Downloaded parquet (immutable)
└── processed/           # daily_aggregates.csv, model_results.json

tests/
├── contract/            # Schema validation tests
├── integration/         # Full pipeline test
└── unit/                # Aggregation logic tests
```

**Structure Decision**: Single project structure selected to minimize overhead for a data analysis pipeline. `code/` contains all logic; `data/` separates raw vs. processed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The project scope fits within a single script pipeline. | N/A |