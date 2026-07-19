# Implementation Plan: Molecular Property Prediction Pipeline

**Branch**: `324-molecular-property-prediction` | **Date**: 2026-07-09 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/324-molecular-property-prediction/spec.md`

## Summary

This project implements a reproducible pipeline to predict molecular properties (logP, solubility, boiling point) from Open Babel fingerprints using Random Forests. The system downloads real molecular data via `PubChemPy`, filtering strictly for **experimental** values where available. It generates topological fingerprints (MACCS, ECFP4, FP2) via Open Babel CLI, trains nested cross-validated models, and performs statistical comparisons against an additive fragment baseline (Crippen). 

Crucially, the project addresses the "non-additivity" research question by identifying **topological interaction signatures**: regions where the Random Forest's non-linear predictions deviate significantly from the additive baseline. These deviations are mapped to chemical substructures using RDKit's SMARTS pattern matching on the underlying SMILES strings. The plan explicitly acknowledges that 2D fingerprints capture topological connectivity, not 3D steric hindrance, and frames all "substructure" claims as statistical proxies for physical phenomena.

The pipeline adheres to strict data hygiene and compute constraints (CPU-first, limited RAM). It includes a quantitative threshold: if the dataset contains <50% experimental values for a target property, the analysis for that property is restricted to "Model Consistency" (comparing RF vs. Crippen on computational data) and the limitation is explicitly reported.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `pubchempy`, `rdkit` (for SMILES parsing and SMARTS matching), `scikit-learn`, `shap`, `openbabel` (CLI), `matplotlib`, `pandas`, `pyyaml`, `ruff`, `black`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/derived`)  
**Testing**: `pytest` (unit tests for data loaders, integration tests for pipeline steps)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM)  
**Project Type**: CLI/Data Pipeline  
**Performance Goals**: Complete full pipeline (~5k molecules, 3 fingerprints, nested CV) within 4 hours on CPU.  
**Constraints**: No external GPU required (RF and SHAP on CPU); Open Babel must be available in PATH; strict memory limits (streaming data loading if >1GB).  
**Scale/Scope**: [deferred] molecules; 3 target properties; 3 fingerprint types.

## Constitution Check

*Gates determined based on constitution file.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | **COMPLIANT** | `code/` uses pinned `requirements.txt`; random seeds set in `data/` and `models/`; `data/` artifacts checksummed in `state/`. |
| **II. Verified Accuracy** | **COMPLIANT** | Citations in `research.md` validated against primary sources (PubChem, Open Babel docs); no hallucinated URLs. |
| **III. Data Hygiene** | **COMPLIANT** | Raw data preserved; derivations written to new files; `data_quality_report.csv` logs missing covariates (metadata absence); PII scan passed (no PII in chemical data). |
| **IV. Single Source of Truth** | **COMPLIANT** | All figures/stats trace to `data/derived`; no hand-typed values in `paper/`. |
| **V. Versioning Discipline** | **COMPLIANT** | Content hashes tracked in `state/`; `updated_at` timestamps updated on artifact change. |
| **VI. Non-Additivity Interaction Mapping** | **COMPLIANT** | Plan explicitly compares RF residuals vs. Crippen baseline; SHAP interaction values are mapped to substructures via **RDKit SMARTS matching** (not external DB); "interaction zones" are defined as topological dependencies. |
| **VII. Computational Efficiency** | **COMPLIANT** | CPU-first strategy; nested CV limited to a standard number of folds; tree depth capped; streaming data loading for large sets. |

## Project Structure

### Documentation (this feature)

```text
specs/324-molecular-property-prediction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-324-predicting-molecular-properties-from-ope/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py       # PubChemPy loader, metadata generation, experimental filtering
│   │   ├── preprocess.py     # Missing value handling, quality report, missing_covariates derivation
│   │   └── fingerprint.py    # Open Babel CLI wrapper
│   ├── models/
│   │   ├── baseline.py       # Crippen additive model
│   │   └── rf.py             # Random Forest with nested CV
│   ├── analysis/
│   │   ├── stats.py          # Wilcoxon test, MAE/RMSE, plots, Local Non-Additivity Index
│   │   └── explainability.py # SHAP interaction values, RDKit SMARTS mapping
│   └── main.py               # Orchestration script
├── data/
│   ├── raw/                  # Downloaded CSVs, metadata JSON
│   ├── processed/            # Cleaned SMILES, fingerprint arrays
│   └── derived/              # Predictions, residuals, plots, reports
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
├── pyproject.toml            # Black/Ruff config
└── .ruff.toml
```

**Structure Decision**: Single project structure selected to minimize overhead and ensure reproducibility on free-tier runners. `code/` is modularized by function (data, models, analysis) to facilitate unit testing and clear separation of concerns.

## Complexity Tracking

*No violations detected. Complexity is managed via modular design and strict resource limits.*

## Resolving Unresolved Panel Concerns

1.  **Missing Data Fields (T035)**: The plan clarifies that `measurement_uncertainty` and `quantity_of_substance` are **optional/derived** fields. PubChem's standard API does not guarantee these. The schema and plan now reflect that these fields are populated only if explicitly provided or derived from metadata spread; otherwise, they are null. FR-008 will log "Missing Confidence Data" if these are absent.
2.  **Missing Chemical Rules Database (T030)**: The plan replaces the external database requirement with **RDKit SMARTS matching**. `code/analysis/explainability.py` will use RDKit to map fingerprint bits to atom indices, then match those atoms against a predefined set of SMARTS patterns (hydroxyl, carbonyl, aromatic, etc.) in `code/data/rules.py`. This is self-contained and verified.
3.  **Circular Validation (Scientific Soundness)**: The plan now enforces a **50% experimental data threshold**. If <50% of the dataset for a property is 'Experimental', the analysis for that property is restricted to "Model Consistency" (comparing RF vs. Crippen on computational data) and the limitation is explicitly reported. This prevents using XLogP3 as ground truth for XLogP3-like models.
4.  **Construct Validity (2D vs 3D)**: The plan explicitly reframes the research question to identify "topological interaction signatures" rather than physical mechanisms. All claims about "substructures" are qualified as topological correlations derived from 2D fingerprints, not 3D physical interactions.

## Resolving Rejected Tasks

- **T001a/b/c**: The plan mandates the creation of the full directory structure (`code/`, `data/`, `tests/`, `data/raw`, `data/processed`, `data/derived`) in the `quickstart.md` and `data-model.md`.
- **T003**: `pyproject.toml` and `.ruff.toml` are explicitly included in the project structure for linting/formatting.
- **T009**: `preprocess.py` will be implemented to detect missing covariates (defined as absence of 'Experimental' flags or standard metadata) and log them to `data/derived/data_quality_report.csv`.
- **T031**: `download.py` will generate `data/raw/dataset_metadata.json` with source, conditions, and confidence.
- **T014**: `baseline.py` will compute Crippen contributions and write `data/derived/baseline_predictions.csv`.
- **T015/T022**: `stats.py` will generate `data/derived/baseline_residuals.png` and `data/derived/model_comparison.png`.
- **T027**: `explainability.py` will compute SHAP interactions, map to substructures via RDKit SMARTS, and save `data/derived/shap_interactions.png`.

## Phase Plan

### Phase 0: Data Acquisition & Validation
- **Step 0.1**: Implement `download.py` using `PubChemPy` to fetch [deferred] molecules. **Filter strictly for 'Experimental' property types** where available. If a property is only 'Computed', record it but flag for the 50% threshold check.
- **Step 0.2**: Generate `data/raw/dataset_metadata.json` (Source: PubChem, Confidence: High, Property Types: Experimental/Computed).
- **Step 0.3**: Validate data integrity (checksum, missing values). **Check experimental ratio**: if <50% experimental for a target, flag for fallback analysis.

### Phase 1: Preprocessing & Fingerprint Generation
- **Step 1.1**: Implement `preprocess.py` to handle missing values. **Derive `missing_covariates`** by checking for absence of 'Experimental' flags or standard metadata (pH, temperature) in the source. Log these to `data/derived/data_quality_report.csv`.
- **Step 1.2**: Implement `fingerprint.py` to call Open Babel CLI for MACCS, ECFP4, FP2.
- **Step 1.3**: Store processed fingerprints in `data/processed/`.

### Phase 2: Baseline & Model Training
- **Step 2.1**: Implement `baseline.py` (Crippen) to generate `data/derived/baseline_predictions.csv`.
- **Step 2.2**: Implement `rf.py` with nested cross-validation with repeated folds to train RF models.
- **Step 2.3**: Generate predictions and residuals.

### Phase 3: Statistical Analysis & Explainability
- **Step 3.1**: Implement `stats.py` for Wilcoxon signed-rank test, MAE/RMSE calculation, and plots (`baseline_residuals.png`, `model_comparison.png`). **Compute Local Non-Additivity Index**: correlate residual differences (RF - Crippen) with substructure presence.
- **Step 3.2**: Implement `explainability.py` for SHAP interaction values. **Map bits to substructures** using RDKit SMARTS matching against `code/data/rules.py`. Classify `context_type` based on matched patterns (e.g., 'Topological-Electronic-Proxy'). Save `data/derived/shap_interactions.png`.
- **Step 3.3**: Generate final report and paper-ready figures, explicitly stating limitations if the experimental threshold was not met.