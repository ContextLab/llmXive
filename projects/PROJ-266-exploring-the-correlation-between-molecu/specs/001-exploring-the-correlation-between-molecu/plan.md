# Implementation Plan: Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes

**Branch**: `001-molecular-flexibility-permeability` | **Date**: 2026-07-04 | **Spec**: `specs/001-molecular-flexibility-permeability/spec.md`

## Summary

This project investigates the associational relationship between molecular flexibility (quantified as internal-coordinate variance from 3D conformer ensembles) and Caco-2 permeability (logPapp). The technical approach involves: (1) retrieving and filtering Caco-2 data from ChEMBL; (2) generating 3D conformer ensembles using RDKit with CPU-tractable constraints (a computationally feasible set of conformers); (3) computing flexibility descriptors (bond, angle, dihedral variance) and correlating them with permeability; (4) building a multivariate linear regression model with confounders (logP, MW, PSA) and validating via scaffold-based 5-fold cross-validation; and (5) generating publication-quality visualizations. All analysis is framed as associational (observational) to avoid causal claims.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit` (2023.9.5+), `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `requests`, `pyyaml`, `prody` (optional for NMA reference)  
**Storage**: Local CSV/Parquet files in `data/` (raw and derived)  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, no GPU)  
**Project Type**: Computational chemistry research pipeline  
**Performance Goals**: Total runtime ≤ 6 hours on CPU-only runner; memory ≤ 7 GB  
**Constraints**: No GPU/CUDA; conformer ensemble size capped at a computationally feasible limit for CPU resources; dataset sampled to ≤1000 molecules if needed  
**Scale/Scope**: A subset of raw records will be filtered to identify valid entries, which will then be screened for the presence of valid flexibility descriptors.

> Note: The spec's requirement for 50 conformers (FR-003) is infeasible on the target runner. The plan explicitly constrains this to a fixed number of conformers per molecule. to ensure runtime completion within 6 hours, as documented in `research.md` (Decision/Rationale) and the Spec Deviation & Governance section. This is a feasibility adaptation, not a spec change.

## Constitution Check

**Principle I (Reproducibility)**:  
- Random seeds pinned in `code/` (e.g., `numpy.random.seed()`, `rdkit` conformer generation seeds).  
- External datasets fetched from ChEMBL REST API on every run (no cached raw data committed).  
- `requirements.txt` pins all dependencies.

**Principle II (Verified Accuracy)**:  
- All citations (e.g., ChEMBL, RDKit methods) verified against primary sources before inclusion in `research.md`.  
- Title-token-overlap ≥ 0.7 for all references.

**Principle III (Data Hygiene)**:  
- Raw data checksummed and stored in `data/raw/`; derived data in `data/processed/`.  
- No in-place modifications; all transformations produce new files.  
- PII scan passed (no personal data in chemical datasets).

**Principle IV (Single Source of Truth)**:  
- All figures/statistics trace to `data/processed/` rows and `code/` scripts.  
- No hand-typed numbers in reports.

**Principle V (Versioning Discipline)**:  
- Content hashes tracked in `state/` YAML; updates trigger timestamp refresh.  
- Spec deviations (e.g., conformer count) recorded in `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml` with the schema defined below.

**Principle VI (Computational Method Transparency)**:  
- RDKit used for conformer generation.  
- Flexibility metrics computed via internal-coordinate variance (a practical approximation for normal-mode analysis given resource constraints).  
- Scripts and raw values version-controlled in `code/` and `data/`.  
- Note: Full normal-mode analysis (Hessian-based) is not feasible on CPU-only runners; this limitation is documented.

**Principle VII (Statistical Rigor)**:  
- Pearson/Spearman correlations with p-values and FDR correction (Benjamini-Hochberg).  
- Scaffold-based 5-fold cross-validation for model performance.  
- VIF diagnosis and Ridge regression fallback for collinearity.  
- All statistics reproducible in notebook.

**Gates**: All principles satisfied. No violations requiring justification.

## Spec Deviation & Governance

**Deviation**: Conformer ensemble size reduced from 50 (FR-003) to 20.  
**Reason**: CPU feasibility on GitHub Actions free-tier (runtime >6h with 50 conformers).  
**Impact**: Potential loss of variance stability for highly flexible molecules; mitigated by sensitivity analysis.  
**Governance Record**:  
The following schema must be used in `state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml` to record this deviation:

```yaml
spec_deviations:
  - id: "DEV-001"
    spec_requirement: "FR-003"
    original_value: "50 conformers"
    adapted_value: "20 conformers"
    rationale: "CPU feasibility on GitHub Actions free-tier"
    impact_assessment: "Potential loss of variance stability; mitigated by sensitivity analysis"
    approved_by: "Convergence Panel"
    approved_at: "2026-07-04"
```

## Project Structure

### Documentation (this feature)

```text
specs/001-molecular-flexibility-permeability/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── flexibility.schema.yaml
    ├── correlation.schema.yaml
    ├── analysis_output.schema.yaml
    └── conformers.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-266-exploring-the-correlation-between-molecu/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── fetch_chembl.py          # FR-001, FR-010
│   ├── validate_data.py         # FR-002
│   ├── generate_conformers.py   # FR-003 (adapted to 20 conformers)
│   ├── compute_flexibility.py   # FR-004
│   ├── correlation_analysis.py  # FR-005, FR-006, FR-009
│   ├── regression_model.py      # FR-007
│   ├── visualize.py             # FR-008
│   └── main.py                  # Orchestrator
├── data/
│   ├── raw/                     # Raw ChEMBL CSV (checksummed)
│   └── processed/               # Filtered, conformers, descriptors
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/                # Schema validation tests
└── docs/
    └── ...
```

**Structure Decision**: Single-project layout (Option 1) chosen for simplicity and alignment with research pipeline. No frontend/backend split required. All code resides in `code/` with clear module separation by functional requirement.

## Complexity Tracking

No violations. Complexity is minimal: linear pipeline with 5 core modules (fetch, validate, conformers, flexibility, correlation/model). No redundant patterns or unnecessary abstractions.

## Feasibility Gate

Before full execution, a benchmark task will be run on a subset of molecules to estimate total runtime. If the estimated runtime exceeds a practical threshold, the dataset will be further sampled to a manageable subset of molecules. This gate is documented in `quickstart.md` and `plan.md`.
