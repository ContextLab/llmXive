# Implementation Plan: Predicting Molecular Dipole Moments with Graph Neural Networks

**Branch**: `001-predicting-molecular-dipole-moments` | **Date**: 2026-05-21 | **Spec**: specs/001-predicting-molecular-dipole-moments/spec.md
**Input**: Feature specification from specs/001-predicting-molecular-dipole-moments/spec.md

## Summary

This feature implements a comparative study of 3D conformational geometry versus 2D connectivity for predicting molecular dipole moments. The technical approach trains a SchNet-style GNN (leveraging 3D coordinates) against a Random Forest baseline (using 2D descriptors only) on a random subset of QM9, with feature attribution analysis to identify structural drivers of predictive variance.

## Technical Context

**Language/Version**: Python 3.x  
**Primary Dependencies**: PyTorch.0, PyTorch Geometric

The specific version number is not asserted; instead, the study will utilize a recent release of PyTorch Geometric., RDKit (2023 release), scikit-learn.2, pandas 2.x, numpy.2  
**Storage**: Parquet files under data/processed/, model checkpoints under data/checkpoints/  
**Testing**: pytest.3 with contract tests against schema definitions  
**Target Platform**: Linux server (CPU-only mode)  
**Project Type**: computational research pipeline  
**Performance Goals**: Complete all 5 random seed experiments within 6h on 2 CPU cores  
**Constraints**: No GPU acceleration; memory footprint < 8GB; reproducibility via pinned random seeds  
**Scale/Scope**: A substantial number of molecules, random seeds, 2 models, feature attribution methods.
**Documentation Structure**: README.md, quickstart.md, research.md under specs/001-predicting-molecular-dipole-moments/

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Notes | Spec Traceability |
|-----------|-------------------|---------------------|------------------|
| I. Reproducibility | ✅ PASS | Random seeds pinned in code/; Quantum chemistry datasets fetched from canonical HuggingFace sources; requirements.txt with exact versions | T009, SC-005 |
| II. Verified Accuracy | ✅ PASS | All dataset URLs verified against HuggingFace datasets.load_dataset(); DOI 10.1038/sdata.2014.22 cited as reference only (no URL fabricated) | T015, FR-001 |
| III. Data Hygiene | ✅ PASS | Raw data checksummed in state/projects/*.yaml; transformations write new files; no in-place modifications | T004, T016, T017, T018 |
| IV. Single Source of Truth | ✅ PASS | All figures/statistics trace to data/ rows and code/ blocks; no hand-typed numbers in paper artifacts | T046, T054 |
| V. Versioning Discipline | ✅ PASS | Content hashes for all artifacts; updated_at timestamps tracked in state/projects/*.yaml | T005, T055 |
| VI. 3D Geometry Preservation | ✅ PASS | Coordinate preprocessing documents all geometric transformations; rotational/translational invariance verified | T009, T017 |
| VII. Chemical Interpretability | ✅ PASS | Permutation importance + saliency mapping implemented; structural features (atom types, bond angles, electronegative placement) explicitly ranked | T038, T039, T040, T045 |

**Limitations Documented in spec.md Assumptions**:
- **Hydration state limitation**: QM9 molecules are gas-phase DFT calculations without explicit solvent. Hydration effects acknowledged as out-of-scope per spec assumptions.
- **Conformational ensembles**: Single lowest-energy conformer per molecule from QM9 used; ensemble sampling documented as future work in research.md.
- **Feature attribution**: Saliency mapping + permutation importance directly address "which part of the graph is doing the work"; physics-informed loss (Raissi) noted as future enhancement in research.md.
- **Physical validation**: Physical measurement validation explicitly out-of-scope per spec assumptions; validation against QM9 DFT reference data (BLYP/6-31G(2df,p)) as ground truth.

**Note on Scope Boundaries**: Tasks T021-T025, T039-T043, T056-T058 referenced in earlier versions have been renumbered to align with current spec requirements. All tasks now map to explicit FR and SC requirements in spec.md.

**Note on Documentation Structure**: quickstart.md is documented under specs/001-predicting-molecular-dipole-moments/ for end-to-end pipeline validation (T057)