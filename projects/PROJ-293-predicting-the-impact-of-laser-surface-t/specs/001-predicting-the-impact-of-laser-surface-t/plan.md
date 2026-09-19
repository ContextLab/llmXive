# Implementation Plan: Predicting the Impact of Laser Surface Texturing on Wear Resistance

**Branch**: `001-predict-lst-wear` | **Date**: 2026-08-21 | **Spec**: `specs/001-predict-lst-wear/spec.md`

## Summary

This feature implements a reproducible, CPU-first machine learning pipeline to aggregate open tribological datasets, normalize wear rates using Archard's law, and train regression models (Linear, RF, GB) to predict wear resistance from Laser Surface Texturing (LST) parameters. The plan strictly adheres to the project constitution's constraints on data hygiene, numerical stability, and cross-material generalizability validation, while operating within the GitHub Actions free-tier compute limits (2 CPU, 7GB RAM, 6h).

The plan explicitly acknowledges the high risk of data insufficiency given the single verified source. It defines a strict "Data Sufficiency Gate" that halts or degrades scope if the dataset lacks the required schema or volume.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn==1.6.0`, `shap`, `numpy`, `requests`, `pyyaml`, `statsmodels`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/intermediate`, `models`, `reports`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Complete full pipeline (ingestion → SHAP) within 6 hours on 2 CPU cores.  
**Constraints**: No GPU usage for training (FR-003); strict handling of missing predictors (FR-002); Archard normalization fallback for missing load/speed (FR-009).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **I. Reproducibility**: Plan mandates pinned `requirements.txt`, fixed random seeds in all scripts, and deterministic data fetching from verified HuggingFace URLs.
- **II. Verified Accuracy**: All dataset citations in `research.md` are restricted to the verified URL block provided in the prompt. The `reference_validator` agent is integrated into the pipeline to verify these citations before ingestion.
- **III. Data Hygiene**: Plan includes checksumming raw data upon download; transformations write to new files (`data/processed/`) without modifying raw inputs. Checksums are recorded in `state/projects/PROJ-293-predicting-the-impact-of-laser-surface-t.yaml`.
- **IV. Single Source of Truth**: All metrics (R², MAE) are logged to `model_report.json` and derived programmatically; no hand-typed numbers in `paper/`.
- **V. Versioning Discipline**: Content hashes will be recorded in `state/` upon artifact creation.
- **VI. Numerical Stability**: Plan explicitly schedules feature scaling and interaction term construction *inside* the cross-validation loop using `scikit-learn Pipelines` to prevent leakage.
- **VII. Cross-Material Generalizability**: The plan prioritizes Leave-One-Material-Class-Out (LOMO) CV; fallback to 5-fold K-Fold is scripted if <3 material classes are detected, with explicit scope re-framing.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-lst-wear/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── feature_importance.schema.yaml
    ├── model_output.schema.yaml
    ├── model_report.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-293-predicting-the-impact-of-laser-surface-t/
├── code/
│   ├── __init__.py
│   ├── ingest.py           # Data ingestion, schema mapping, checksumming, state update
│   ├── preprocess.py       # Cleaning, Archard normalization, VIF, Pipeline construction
│   ├── train.py            # Model training, GridSearchCV, LOMO-CV, Power Analysis
│   ├── interpret.py        # SHAP computation & significance testing
│   └── validate.py         # Power analysis, data sufficiency checks, causal language filter
├── data/
│   ├── raw/                # Downloaded parquet/csv files (checksummed)
│   ├── intermediate/       # Merged, raw-cleaned datasets (merged.csv)
│   └── processed/          # Cleaned, normalized, encoded datasets (cleaned.csv)
├── models/                 # Saved .pkl models and artifacts
├── reports/                # SHAP plots, model metrics JSON
├── tests/
│   ├── unit/
│   └── integration/
└── state/
    └── projects/PROJ-293-predicting-the-impact-of-laser-surface-t.yaml
```

**Structure Decision**: Single-project structure (`code/`) selected to maintain a monolithic research pipeline suitable for sequential execution on a CI runner. This minimizes overhead and simplifies dependency management for a data-centric workflow.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dual-track normalization (Raw vs. Normalized) | Required by FR-002/FR-009 to handle missing `contact_load`/`sliding_speed` without data loss. | Imputing missing load/speed would violate Archard's law physics and introduce bias; dropping records would violate FR-002. |
| LOMO-CV + Fallback Logic | Required by FR-006 to assess cross-material generalizability. | Standard K-Fold alone cannot validate the "virtual prototyping" hypothesis across material classes. |
| Permutation Significance Testing | Required by FR-008 to validate SHAP importance against null distribution. | Relying solely on mean absolute SHAP values does not provide statistical p-values or detect unstable features. |
| Pipeline Architecture | Required by Constitution Principle VI to prevent data leakage in scaling/interaction terms. | Applying scaling before CV split leaks information from test to train. |
| State Management | Required by Constitution Principle III to record checksums in `state/`. | Manual checksumming is error-prone and not reproducible. |

## Phase Sequence & Gates

1.  **Phase 0: Data Validation & Ingestion**
    -   Verify dataset schema (FR-001).
    -   Check record count (SC-004).
    -   Calculate checksums and update `state/` (Constitution III).
    -   *Gate*: If schema mismatch or N < 100, halt. If 100 <= N < 300, warn and proceed as "pilot".
2.  **Phase 1: Preprocessing & Power Analysis**
    -   Drop missing predictors (FR-002).
    -   Apply Archard normalization (FR-009, FR-018).
    -   Run Shapiro-Wilk/Levene's on raw subset (FR-017).
    -   Run Power Analysis on normalized subset (FR-014).
    -   *Gate*: If normalized_count < 100, halt primary analysis.
3.  **Phase 2: Model Training**
    -   Build `Pipeline` (Scaling + Model) to prevent leakage (Constitution VI).
    -   Run GridSearchCV (10+ combos) (FR-004).
    -   Run LOMO-CV or Fallback (FR-006).
4.  **Phase 3: Interpretation & Reporting**
    -   Compute SHAP (FR-005).
    -   Run Permutation Test (FR-008).
    -   Apply Causal Language Filter (FR-007).
    -   Generate Reports.