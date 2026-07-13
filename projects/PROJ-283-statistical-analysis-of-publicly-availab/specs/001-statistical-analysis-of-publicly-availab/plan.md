# Implementation Plan: Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

**Branch**: `001-statistical-chess-elo-analysis` | **Date**: 2026-07-13 | **Spec**: `spec.md`

## Summary

This plan implements a statistical analysis pipeline to predict Elo rating deviations using publicly available chess game data. The approach involves ingesting PGN (Portable Game Notation) data, extracting features (opening codes, move times, material imbalance at move 5), calculating expected win probabilities via the Elo formula, and fitting regression models (Gaussian GLM and Ridge) to identify systematic model misspecifications. The pipeline includes rigorous statistical validation (cross-validation, FDR correction, sensitivity analysis) and is constrained to run on CPU-only GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `chess` (python-chess), `matplotlib`, `seaborn`, `requests`, `datasets`  
**Storage**: Local CSV/Parquet files under `data/` (raw and processed)  
**Testing**: `pytest` (contract tests against schemas, unit tests for parsers)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data Science / Statistical Analysis Pipeline  
**Performance Goals**: Runtime ≤ 6 hours, RAM ≤ 7 GB, No GPU usage  
**Constraints**: No GPU/CUDA, no heavy deep learning training, strict memory limits (sample data if needed), deterministic parsing (Constitution Principle VI).  
**Scale/Scope**: Process a subset of [deferred] games (targeting a feasible scale for CPU implementation), ensuring the inclusion rate meets **SC-001** (≥ 95% of valid PGNs) as defined in **US-1**.

> **Dataset Verification**: The primary data source is the **Lichess Games Database** on HuggingFace (`https://huggingface.co/datasets/lichess/big-chess-dataset` or verified mirror), which explicitly contains move-time metadata. If the verified URL is unreachable or the dataset lacks move-time metadata for >5% of the sample, the pipeline **HALTS** immediately (Constitution Principle II) and reports the verification failure.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Check | Status |
|-----------|------------------|--------|
| **I. Reproducibility** | Plan mandates pinned `requirements.txt`, random seeds, and deterministic parsing. | ✅ Pass |
| **II. Verified Accuracy** | Plan requires citations only from verified sources. **Action**: Pipeline HALTS immediately if the verified dataset URL is unreachable or metadata is missing. No "graceful" fallback to unverified sources. | ✅ Pass |
| **III. Data Hygiene** | Plan mandates checksumming of raw data and immutable derivations. | ✅ Pass |
| **IV. Single Source of Truth** | Plan ensures all figures/stats trace back to `data/` and `code/`. | ✅ Pass |
| **V. Versioning Discipline** | Plan includes content hashing for artifacts. | ✅ Pass |
| **VI. PGN Parsing Consistency** | Plan defines a single, deterministic parsing pipeline for all features. | ✅ Pass |
| **VII. Outcome Deviation Integrity** | Plan strictly separates historical ratings (for expectation) from current game features. | ✅ Pass |

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-chess-elo-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── game_record.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Handles Lichess API/PGN download with retry logic
│   ├── parse.py             # PGN parsing and feature extraction (Move 5 material)
│   └── process.py           # Data cleaning and deviation calculation
├── models/
│   ├── fit.py               # Gaussian GLM and Ridge regression fitting
│   ├── validate.py          # Cross-validation and diagnostics
│   └── metrics.py           # Significance testing (Wald Z/LRT) and FDR correction
├── reports/
│   ├── generate_plots.py    # Diagnostic visualizations
│   └── sensitivity.py       # Threshold sweep analysis
├── validation/
│   └── validate_contracts.py # Validates data against YAML schemas before modeling
├── main.py                  # Orchestration script
└── config.py                # Configuration (seeds, thresholds, paths)

tests/
├── contract/
│   ├── test_game_record.py  # Validates against game_record.schema.yaml
│   └── test_model_output.py # Validates against model_output.schema.yaml
├── unit/
│   ├── test_parsers.py      # Unit tests for PGN parsing logic
│   └── test_calculations.py # Unit tests for Elo/Deviation math
└── integration/
    └── test_pipeline.py     # End-to-end smoke test on small sample
```

**Structure Decision**: Single project structure (`src/`) chosen for simplicity and direct data flow. No frontend/backend split required as this is a batch analysis pipeline. Contract validation (`validate_contracts.py`) is a mandatory step before modeling to ensure data integrity.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Two Model Types (Gaussian GLM & Ridge)** | Required by FR-005 to compare distribution assumptions. Gaussian GLM handles the discrete spikes in `outcome_deviation` better than Beta regression (which requires continuous data bounded within the unit interval). Ridge provides a linear baseline. | A single model type would fail to capture the specific distributional nuances of `outcome_deviation` and reduce statistical rigor. Beta regression was rejected due to its invalidity for discrete, zero-inflated outcomes. |
| **FDR Correction + Sensitivity Analysis** | Required by FR-009 and FR-010 to control false discoveries in multiple testing and ensure robustness. | Skipping these would violate the "Methodological Rigor" assumption and risk false positives in correlational claims. |
| **ECO Collapsing** | Required by FR-011 to reduce multicollinearity. | One-hot encoding all ECO codes would lead to perfect multicollinearity and unstable coefficients in a small sample. |
| **Material Imbalance at Move 5** | Required to avoid endogeneity (circularity where the feature correlates with the outcome). Move selection was found to be too close to the final result. | Using Move would introduce severe endogeneity, making the model simply learn "who won" rather than "why the rating was wrong". |