# Implementation Plan: Predicting Molecular Properties from Quantum Chemical Calculations

**Branch**: `546-predicting-molecular-properties` | **Date**: 2026-06-25 | **Spec**: `specs/546-predicting-molecular-properties/spec.md`
**Input**: Feature specification from `specs/546-predicting-molecular-properties/spec.md`

## Summary

This project implements a comparative pipeline to predict molecular barrier heights using semi-empirical (DFTB+) and high-level (Psi4) quantum chemical descriptors. The system fetches a verified Zenodo dataset of SMILES strings and experimental barriers, performs geometry optimization, computes HOMO/LUMO/Mayer descriptors, and trains Random Forest models. A critical component is the paired t-test comparing the error distributions of the two methods, alongside a sensitivity analysis for feature stability. The implementation strictly adheres to resource constraints (CPU-first, <7GB RAM, <6h) and handles convergence failures via retry logic and logging.

**Key Methodological Change**: To isolate the effect of the computational method (DFTB+ vs Psi4) from the effect of sample size, **both models are trained on the same stratified subset of molecules**. The full dataset is used only for generating the Semi-Empirical baseline, but the comparative t-test is strictly performed on a representative sample subset.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit` (chemistry), `dftb+` (binary, semi-empirical), `psi4` (binary, DFT), `scikit-learn` (ML), `pandas`, `numpy`, `requests`, `datasets` (Hugging Face), `pyyaml`.  
**Storage**: Local filesystem (`data/`, `logs/`, `reports/`).  
**Testing**: `pytest` (unit/integration), `ruff` (linting), `black` (formatting).  
**Target Platform**: Linux (GitHub Actions runner).  
**Project Type**: Computational Chemistry Pipeline / CLI.  
**Performance Goals**: < 6 hours total runtime on 2-core CPU; < 7 GB RAM peak.  
**Constraints**: No local GPU; DFT calculations limited to a stratified subset (n=50) to fit time/memory; Zenodo dataset must be checksummed before use.  
**Scale/Scope**: Full dataset for semi-empirical (DFTB+); subset (n=50) for DFT (Psi4).

### Specific Requirement Mapping
- **FR-001 (Checksum)**: Zenodo dataset checksum verified (SHA-256) and logged to `logs/verification.log` **before** any geometry optimization.
- **FR-002 (Geometry & Retry)**: DFTB+ optimization with **one retry** using a perturbed initial guess. Failures logged to `logs/convergence_failures.log` with schema `molecule_id, timestamp, error_code, error_message`.
- **FR-003 (Semi-Empirical Descriptors)**: Output `data/descriptors_semi.csv` with columns `molecule_id`, `HOMO_energy`, `LUMO_energy`, `mayer_bond_order`.
- **FR-004 (DFT Subset)**: Stratified random subset by **barrier height bins**. If N < 50, use all. **Same train/test splits** used for both models.
- **FR-005 (Paired T-Test)**: Compare errors on the **same 50 samples**. Report Null Hypothesis, Significance Level (α=0.05), and models compared.
- **FR-006 (Feature Importance)**: Top descriptors identified from RF `feature_importances_` and saved to `reports/sensitivity.csv`.
- **FR-007 (Sensitivity)**: Sweep cutoffs {0.01, 0.05, 0.1} and noise {σ=0.01, 0.05}. Record rank correlation of top descriptors in `reports/sensitivity.csv`.
- **FR-008 (Confounds)**: `code/confounds.py` uses `rdkit.Chem.Lipinski` and `rdkit.Chem.Descriptors` to derive MW, atom count, and functional groups from SMILES. Output `data/confounds.csv`.
- **SC-001**: Success rate (count/ratio of optimized geometries) calculated and reported in `reports/evaluation.json`.
- **SC-002**: MAE for both models reported in `reports/evaluation.json` with keys `semi_empirical_mae`, `dft_mae`.
- **SC-003**: Rank correlation values recorded in `reports/sensitivity.csv`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/config.py`. Zenodo checksum verified before processing. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | PASS | Reference-Validator Agent integration: All external citations (Zenodo, Hugging Face) validated against primary sources. Title-token-overlap ≥ 0.7 checked before processing. |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw/`. Derived files (`descriptors_semi.csv`, `descriptors_dft.csv`) written to new paths with checksums. PII scan passed (no PII in SMILES). |
| **IV. Single Source of Truth** | PASS | All figures/stats in `reports/` trace to specific rows in `data/` and blocks in `code/`. No hand-typed values. |
| **V. Versioning Discipline** | PASS | Artifacts hashed; `state/` YAML file updated with artifact hashes after each phase. |
| **VI. Protocol Consistency** | PASS | DFTB+ and Psi4 use identical optimized geometries (from `data/optimized_geometries/`) and convergence criteria (Constitution Principle VI). |
| **VII. Resource-Bound Execution** | PASS | DFT limited to a representative sample size; DFTB+ uses streaming/batched processing; memory monitoring logs OOM attempts. |

## Project Structure

### Documentation (this feature)

```text
specs/546-predicting-molecular-properties/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── descriptor.schema.yaml
│   ├── descriptors_semi.schema.yaml
│   ├── descriptors_dft.schema.yaml
│   ├── evaluation.schema.yaml
│   └── sensitivity_report.schema.yaml
└── tasks.md             # Phase 2 output (generated by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-546-predicting-molecular-properties-from-qua/
├── code/
│   ├── __init__.py
│   ├── config.py              # Seeds, paths, hyperparameters
│   ├── fetch_data.py          # Zenodo download & checksum
│   ├── geometry_opt.py        # DFTB+ optimization & retry logic
│   ├── compute_descriptors.py # HOMO/LUMO/Mayer extraction (DFTB+ & Psi4)
│   ├── train_models.py        # RF training & paired t-test
│   ├── sensitivity.py         # Feature importance & noise injection
│   └── confounds.py           # FR-008: MW, atom count, functional groups (RDKit)
├── data/
│   ├── raw/                   # Downloaded Zenodo CSV (immutable)
│   ├── optimized_geometries/  # XYZ files
│   ├── descriptors_semi.csv   # DFTB+ output
│   ├── descriptors_dft.csv    # Psi4 output
│   └── confounds.csv          # FR-008 output
├── logs/
│   ├── verification.log       # Checksum status
│   ├── convergence_failures.log
│   ├── oom_failures.log
│   └── structural_failures.log
├── reports/
│   ├── evaluation.json        # MAE & t-test results
│   └── sensitivity.csv        # Feature importance stability
├── contracts/
│   ├── dataset.schema.yaml
│   ├── descriptor.schema.yaml
│   ├── descriptors_semi.schema.yaml
│   ├── descriptors_dft.schema.yaml
│   ├── evaluation.schema.yaml
│   └── sensitivity_report.schema.yaml
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── docs/
│   └── ...
├── requirements.txt
├── pyproject.toml             # Black, Ruff config
└── README.md
```

**Structure Decision**: Single-project structure selected to minimize I/O overhead and simplify dependency management for a computational pipeline. All modules reside in `code/` for direct import and execution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dual Quantum Engine (DFTB+ & Psi4) | Required by US2 to compare semi-empirical vs. high-level accuracy. | Using only one method would fail the comparative modeling requirement and the paired t-test. |
| Retry Logic for Convergence | Required by Edge Cases (Convergence Failure) to avoid selection bias (FR-002). | Single-attempt logic would discard valid molecules, skewing the dataset. |
| Confounds Analysis (FR-008) | Required to verify feature space coverage and control for molecular size. | Ignoring confounds would invalidate the interpretability of the model and the sensitivity analysis. |
| Identical Training Sets (N=50) | Required to isolate method effect from sample size effect (Scientific Soundness). | Training on different sets would confound the t-test results. |