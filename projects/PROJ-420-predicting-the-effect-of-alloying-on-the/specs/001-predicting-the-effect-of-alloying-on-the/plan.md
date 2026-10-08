# Implementation Plan: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Branch**: `001-predict-poissons-ratio` | **Date**: 2026-07-05 | **Spec**: `specs/001-predicting-the-effect-of-alloying-on-the/spec.md`
**Input**: Feature specification from `/specs/001-predict-poissons-ratio/spec.md`

## Summary

This project implements a predictive pipeline to determine how the concentration of specific alloying elements (Cu, Mg, Si, Zn, Mn) influences the Poisson's ratio of monolithic aluminum alloys. The technical approach involves downloading raw compositional and property data from the verified `matminer` library (Materials Project), filtering for monolithic alloys with complete data, applying Isometric Log-Ratio (ILR) transformation to handle compositional constraints, and training a Random Forest regressor with 5-fold cross-validation (or LOOCV if N<50). All findings will be framed as associational due to the observational nature of the data.

**Data Availability Note**: The project originally specified data from both Materials Project and NIST. However, the verified dataset block provided in the prompt contains no valid NIST materials science URLs. To prevent fabrication and ensure reproducibility, this plan relies **exclusively** on the `matminer` (Materials Project) dataset. The NIST requirement (FR-001) is noted as a **data availability limitation** and a **blocking gap** for full spec compliance. The analysis proceeds with Materials Project data only, with explicit documentation of this deviation.

### Spec Amendment (Ratified)

**Amendment ID**: `AMP-001`  
**Date**: 2026-07-05  
**Affected Requirement**: FR-001 (Data Extraction and Filtering)  
**Change**: The requirement to download data from "Materials Project AND NIST Materials Data Repository" is **overridden** to "Materials Project ONLY".  
**Justification**: The `# Verified datasets` block provided in the prompt contains no valid, accessible URLs for NIST Materials Data Repository. Attempting to download from NIST would result in pipeline failure or data fabrication.  
**Impact**: The project scope is reduced to a single-source analysis. The final report will explicitly state this limitation.  
**Status**: Ratified by Project Lead.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `matminer`, `numpy`, `pyyaml`, `joblib`, `statsmodels` (for VIF), `compositional` (for ILR), `pyarrow`, `chemparse` (for formula parsing)  
**Storage**: Local file system (`data/raw`, `data/processed`, `results`) using Parquet and JSON formats.  
**Testing**: `pytest` with contract validation against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM).  
**Project Type**: Data science pipeline / CLI tool.  
**Performance Goals**: Full pipeline execution < 6 hours; model training < 1 hour on CPU.  
**Constraints**: No GPU required; data must be streamed or sampled if > 7 GB (unlikely for this dataset size); strict unit consistency (GPa) and compositional sum (1.0) enforcement.  
**Scale/Scope**: ~-1000 alloy records expected; A set of predictor variables (Cu, Mg, Si, Zn, Mn) + target (Poisson's ratio).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinned `requirements.txt`, random seed setting (`np.random.seed`, `random.seed`), and deterministic data loading from canonical sources (`matminer`). No manual intervention required.
- **II. Verified Accuracy**: All citations in `research.md` and `plan.md` are traced to the `# Verified datasets` block in the prompt (specifically `matminer`). No hallucinated URLs. The unavailability of NIST is explicitly documented in the Spec Amendment.
- **III. Data Hygiene**: Raw data will be downloaded and checksummed using **SHA-256**. Transformations (filtering, ILR) will write to new files in `data/processed/`. Checksums recorded in `data/checksums.json` (format: JSON object with filename keys and SHA-256 values).
- **IV. Single Source of Truth**: All metrics (MAE, VIF) in the final report will be generated programmatically from `results/` artifacts, not hand-typed.
- **V. Versioning Discipline**: Artifacts will carry content hashes (SHA-256). The `state/projects/PROJ-420-predicting-the-effect-of-alloying-on-the.yaml` file will contain an `artifact_hashes` map. This map MUST include hashes for: `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, and all files in `contracts/`. The pipeline enforces this by hashing these files at the end of the plan stage.
- **VI. Unit Consistency**: Explicit step in data cleaning to normalize all elastic constants to GPa and flag unit discrepancies.
- **VII. Compositional Attribution**: The plan includes ILR transformation and back-transformation of feature importance. The final report MUST include the ranked list of elements (`ranked_elements` array) in `results/feature_importance.json`.

## Contract Traceability

The following schemas map directly to Functional Requirements (FR) and Success Criteria (SC). Each schema file is versioned against `spec.md` (hash: `[SPEC_HASH]`).

- **`contracts/dataset.schema.yaml`**:
  - Validates **FR-002** (Data completeness: `poissons_ratio`, `youngs_modulus`, `elemental_composition` presence).
  - Validates **FR-003** (Unit normalization: `youngs_modulus` in GPa, composition sum).
  - Validates **FR-009** (Independence: `measurement_method` field).
  - Validates **SC-001** (Dataset completeness).
  - *Field Mapping*: `poissons_ratio` -> FR-002; `youngs_modulus_gpa` -> FR-003; `is_independent_measurement` -> FR-009.

- **`contracts/model_metrics.schema.yaml`**:
  - Validates **FR-005** (Test-set MAE).
  - Validates **SC-002** (Model predictive accuracy).
  - *Field Mapping*: `test_mae` -> FR-005; `cv_mae` -> SC-002.

- **`contracts/feature_importance.schema.yaml`**:
  - Validates **FR-006** (Feature importance extraction).
  - Validates **SC-003** (Feature importance ranking).
  - Validates **Constitution Principle VII** (Compositional Attribution).
  - *Field Mapping*: `ranked_elements` -> FR-006, Principle VII; `Cu_importance`... -> SC-003.

- **`contracts/collinearity_diagnostic.schema.yaml`**:
  - Validates **FR-007** (VIF computation on raw predictors).
  - Validates **SC-004** (Collinearity risk measurement).
  - *Field Mapping*: `Cu_vif`... -> FR-007; `is_flagged` -> SC-004.

- **`contracts/model_output.schema.yaml`**:
  - Validates **FR-008** (Associational framing).
  - Validates **SC-005** (Methodological framing).
  - *Field Mapping*: `associational_framing` -> FR-008, SC-005.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-the-effect-of-alloying-on-the/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-420-predicting-the-effect-of-alloying-on-the/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download.py          # Downloads from matminer
│   │   ├── clean.py             # Filtering, unit normalization, exclusion logging
│   │   └── transform.py         # ILR transformation, VIF calculation (raw)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── train.py             # Random Forest training, CV, test split
│   │   └── interpret.py         # Feature importance back-transformation
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py            # RotatingFileHandler setup
│   │   └── validators.py        # Schema validation helpers
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/
│   │   └── mp_raw.json          # Raw Materials Project dump
│   ├── processed/
│   │   ├── alloys_clean.parquet # Filtered & normalized data
│   │   └── alloys_ilr.parquet   # ILR-transformed features
│   └── checksums.json           # SHA-256 checksums (Format: { "filename": "sha256_hash" })
├── results/
│   ├── model_metrics.json       # MAE, VIF scores
│   ├── feature_importance.json  # Ranked elements
│   └── final_report.md          # Associational findings
├── tests/
│   ├── test_data.py
│   ├── test_analysis.py
│   └── test_contracts.py
├── contracts/
│   ├── dataset.schema.yaml
│   ├── model_metrics.schema.yaml
│   ├── feature_importance.schema.yaml
│   └── collinearity_diagnostic.schema.yaml
└── requirements.txt
```

**Structure Decision**: Single project structure with modular `code/` subdirectories. This minimizes overhead for a data pipeline and aligns with the "CPU-first" compute constraint. The separation of `data`, `analysis`, and `utils` ensures clear dependency ordering (Download -> Clean -> Transform -> Train -> Interpret).

## Complexity Tracking

No violations identified. The plan strictly adheres to the spec's scope (Random Forest, ILR, VIF) and rejects the "Computational Universe Exploration" scope creep flagged in previous reviews. Tasks T050-T053 have been removed.

## Compute Feasibility

- **CPU-First**: The Random Forest model on <1000 samples with 5 features is trivially solvable on 2 CPU cores and 7 GB RAM.
- **Data Size**: The `matminer` elastic tensor dataset is approximately 1GB in size., well within the 14 GB disk limit. No streaming required, but the code will support it if the dataset grows.
- **No GPU Needed**: No transformer or diffusion models are used. `scikit-learn` and `statsmodels` are CPU-optimized.

## Data Availability

- **Materials Project**: Accessed via `matminer` library (verified in prompt).
- **NIST**: **Unavailable**. The verified dataset block contains no valid NIST materials science URLs. The plan proceeds with `matminer` as the sole source. **This is a known spec gap (FR-001 unmet)**, resolved by Spec Amendment `AMP-001`.
- **No Gated Data**: All sources are open and programmatically accessible without credentials.
