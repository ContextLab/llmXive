# Implementation Plan: Comparing Born Model Predictions with Experimental Solvation Energies of Small Ions

**Branch**: `001-born-model-solvation-comparison` | **Date**: 2026-06-26 | **Spec**: specs/001-born-model-solvation-comparison/spec.md
**Input**: Feature specification from `/specs/001-born-model-solvation-comparison/spec.md`

## Summary

This feature implements a Python-based computational chemistry pipeline that compares Born model predictions of ion solvation free energies against experimental measurements. The approach compiles experimental data from public chemistry databases, implements the Born equation, performs regression analysis with multiple-comparison correction, and generates diagnostic visualizations identifying breakdown regimes where continuum dielectric assumptions fail.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scipy, matplotlib, scikit-learn, pyyaml  
**Storage**: CSV/parquet files under `data/`  
**Testing**: pytest  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: computational chemistry analysis library  
**Performance Goals**: Complete analysis on 30+ ion-solvent pairs in <10 minutes on 2 CPU cores, no GPU  
**Constraints**: CPU-only execution, ≤7 GB RAM, ≤14 GB disk, no CUDA/PyTorch GPU dependencies  
**Scale/Scope**: Various ion-solvent pairs, Multiple diagnostic plots, regression with multiple-comparison correction

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Notes |
|------------------------|-------------------|-------|
| I. Reproducibility | PASS | Random seeds pinned in `code/born_calculator.py` and `code/regression_analysis.py`; external datasets fetched from canonical NIST/CRC/Shannon sources on every run; `requirements.txt` at `code/` pins all dependencies |
| II. Verified Accuracy | PASS | All citations validated against primary sources before contributing review points; title-token-overlap ≥0.7 enforced by Reference-Validator Agent; specific tables/papers documented in `research.md` Dataset Strategy |
| III. Data Hygiene | PASS | All data files checksummed in `state/*.yaml` artifact_hashes; raw data preserved unchanged under `data/raw/`; derivations written to new filenames with documented lineage |
| IV. Single Source of Truth | PASS | All figures/statistics trace to exactly one row in `data/` and one code block in `code/`; no hand-typed numbers in paper; `data-model.md` defines entity-to-file mapping |
| V. Versioning Discipline | PASS | Every artifact carries content hash; Advancement-Evaluator invalidates stale review records on artifact change; `updated_at` timestamp updated in state YAML |
| VI. Thermodynamic Parameter Consistency | PASS | Physical parameters (elementary charge, vacuum permittivity, ionic radii, dielectric constants) sourced from NIST/CRC/Shannon; values recorded with source citation and temperature in `data/parameters.csv` |
| VII. Statistical Significance Thresholds | PASS | All regression analyses report p-values; failure to meet p<0.05 explicitly flagged in paper as limitation; multiple-comparison correction applied per FR-006 |

## Project Structure

### Documentation (this feature)

```text
specs/001-born-model-solvation-comparison/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command) - schema definitions
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-675-comparing-born-model-predictions-with-ex/
├── data/
│   ├── raw/                    # Downloaded source data (checksummed) - stores IonSolventPair raw records
│   ├── parameters.csv          # Thermodynamic parameters with citations
│   ├── experimental_solvation.csv  # Compiled experimental dataset - IonSolventPair entity
│   ├── born_predictions.csv    # Born model calculations - BornPrediction entity
│   ├── residual_analysis.csv   # Regression output - ResidualAnalysis entity
│   └── metadata.json           # Retrieval timestamps, version identifiers
├── code/
│   ├── requirements.txt        # Pinned Python dependencies
│   ├── born_calculator.py      # Born equation implementation with uncertainty propagation
│   ├── data_compiler.py        # Experimental data compilation
│   ├── regression_analysis.py  # Statistical analysis pipeline
│   └── diagnostics.py          # Plot generation
├── tests/
│   ├── unit/
│   │   ├── test_born_calculator.py
│   │   └── test_data_compiler.py
│   └── contract/
│       └── test_schemas.py     # Validates against contracts/ schemas
└── state/
    └── projects/PROJ-675-comparing-born-model-predictions-with-ex.yaml
```

**Structure Decision**: Single project structure selected. This is a computational chemistry analysis library without web frontend or mobile components. The `data/` directory separates raw source data from derived datasets per Constitution Principle III (Data Hygiene). The `code/` directory contains modular Python scripts for each pipeline stage. Tests are organized into unit and contract categories to support both functional validation and schema conformance checking. **The project structure adheres to the schemas defined in the `contracts/` directory**, ensuring all data files conform to validated entity definitions before downstream processing.

## Complexity Tracking

> **No violations in Constitution Check; complexity tracking table omitted.**