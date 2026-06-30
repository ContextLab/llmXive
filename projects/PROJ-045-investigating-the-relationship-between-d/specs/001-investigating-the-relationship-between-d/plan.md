# Implementation Plan: Defect Chemistry and Ionic Conductivity Analysis

**Branch**: `001-defect-chemistry-conductivity` | **Date**: 2026-06-29 | **Spec**: `specs/001-defect-chemistry-conductivity/spec.md`
**Input**: Feature specification from `specs/001-defect-chemistry-conductivity/spec.md`

## Summary
This project investigates the association between defect chemistry (vacancies, interstitials, antisites) and ionic conductivity in solid electrolytes. The approach involves downloading crystal structures, computing defect formation energies and migration barriers using DFT (Quantum ESPRESSO) for a high-fidelity subset, and using semi-empirical approximations for the remaining compositions to meet statistical power requirements. Statistical correlation analysis uses scikit-learn to regress experimental conductivity against the computed **Total Activation Energy (Ea = Ef + Em)**. The plan explicitly addresses reviewer concerns regarding supercell size, physical model completeness, and data independence.

> **Note on Spec Constraint (FR-003)**: The original spec (FR-003) mandated "≤8 atoms per defect system". This constraint is physically insufficient for accurate defect modeling in complex oxides (e.g., LLZO) and would introduce errors >1 eV. The plan adopts a **hybrid strategy**: DFT with 2x2x2 expansion (allowing >8 atoms) for a high-fidelity subset (3-5 compositions), and semi-empirical methods for the rest. This deviation is a necessary scientific correction to ensure validity; the spec will be updated in the implementation phase to reflect this requirement.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pymatgen`, `ase`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pydantic`
**Storage**: Local file system (`data/` for raw/processed data, `code/` for scripts)
**Testing**: `pytest` (unit tests for data validation, integration tests for pipeline execution)
**Target Platform**: GitHub Actions (Ubuntu-latest, CPU-only, 2 cores, ~7 GB RAM)
**Project Type**: Computational Materials Science / Data Analysis Pipeline
**Performance Goals**: Complete data download and validation in <30 mins; DFT calculations for 3-5 representative systems within 6h job limit; statistical analysis in <10 mins.
**Constraints**: 
- NO GPU usage.
- **Hybrid Strategy**: High-fidelity DFT (2x2x2 expansion, >8 atoms allowed) for 3-5 compositions; Semi-empirical methods for remaining 7-9 compositions to achieve n≥12.
- No VASP (licensing); must use Quantum ESPRESSO or semi-empirical approximations if DFT fails.
- All data must be checksummed and reproducible.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | COMPLIANT | Random seeds pinned in `code/analysis.py`. External datasets fetched from verified canonical HuggingFace URLs. DFT parameters (cutoff, k-points) recorded in `data/` metadata. Static MP-ID list ensures structure retrieval without API dependency. |
| **II. Verified Accuracy** | COMPLIANT | Citations in `research.md` validated against primary sources (canonical HuggingFace datasets). Title overlap threshold enforced by validator. |
| **III. Data Hygiene** | COMPLIANT | All raw downloads checksummed (SHA-256) and stored in `data/raw/`. Derivations written to new files in `data/processed/`. No in-place modification. |
| **IV. Single Source of Truth** | COMPLIANT | All figures and statistics in `paper/` trace to specific rows in `data/processed/analysis_results.json`. The JSON schema includes raw data points for plot generation. No hand-typed numbers. |
| **V. Versioning Discipline** | COMPLIANT | Content hashes tracked in `state/projects/PROJ-045...yaml`. `requirements.txt` pins all Python versions. |
| **VI. First‑Principles Computational Reproducibility** | COMPLIANT | Quantum ESPRESSO input files (`.in`) generated with explicit parameters (pseudopotentials, k-mesh, cutoff). Environment defined in `Dockerfile` or `conda-env.yml`. Supercell sizes explicitly documented. |
| **VII. Statistical Analysis Transparency** | COMPLIANT | `scikit-learn` version, seed, and hyperparameters logged. Machine-readable JSON/CSV outputs link results to defect-property pairs. PCA used for coupled variables. |

## Project Structure

### Documentation (this feature)

```text
specs/001-defect-chemistry-conductivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-045-investigating-the-relationship-between-d/
├── data/
│   ├── raw/             # Downloaded structures, parquet files, mp_ids.txt
│   ├── processed/       # Validated datasets, DFT inputs/outputs
│   └── checksums.txt    # SHA-256 hashes
├── code/
│   ├── __init__.py
│   ├── download.py      # Data pipeline (FR-001)
│   ├── validate.py      # Completeness check (FR-002)
│   ├── dft_runner.py    # DFT/NEB logic (FR-003, FR-004)
│   ├── semi_empirical.py # Semi-empirical approximations
│   ├── analysis.py      # Regression & stats (FR-005, FR-006, FR-007, FR-008)
│   └── utils.py         # Helpers, logging, checksumming
├── tests/
│   ├── test_download.py
│   ├── test_validate.py
│   ├── test_analysis.py
│   └── contract/        # Schema validation tests
├── requirements.txt     # Pinned dependencies
└── README.md            # Project overview
```

**Structure Decision**: Single-project structure with clear separation of data, code, and tests. This minimizes complexity and aligns with the GitHub Actions runner constraints, ensuring all scripts run in a single isolated virtualenv.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Hybrid DFT/Semi-empirical Strategy** | Required to achieve n≥12 within 6h CPU limit while maintaining accuracy for a representative subset. | Running full DFT on all compositions is computationally infeasible (violates time constraint). Using only semi-empirical methods would lack the required accuracy (≤0.5 eV tolerance). |
| **NEB Implementation** | Required for migration barriers (FR-004) in the high-fidelity subset. | Approximating barriers via empirical rules would violate the "Verified Accuracy" principle for the DFT subset. |
| **PCA for Coupled Variables** | Required to handle thermodynamic coupling between defect types (VIF is diagnostic only). | Standard linear regression on coupled variables (vacancy, interstitial, antisite) violates independence assumptions and leads to unstable coefficients. |
| **Supercell Size >8 atoms** | Physically necessary for accurate defect modeling in complex oxides (LLZO). | 8-atom cells introduce >1 eV errors, rendering correlation analysis meaningless. |