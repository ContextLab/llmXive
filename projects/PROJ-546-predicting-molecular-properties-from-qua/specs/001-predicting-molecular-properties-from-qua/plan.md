# Implementation Plan: Predicting Molecular Properties from Quantum Chemical Calculations

**Branch**: `PROJ-546-predicting-molecular-properties-from-qua` | **Date**: 2026-06-25 | **Spec**: `specs/PROJ-546/spec.md`
**Input**: Feature specification from `specs/PROJ-546/spec.md`

## Summary

This project implements a comparative modeling pipeline to predict molecular barrier heights using quantum chemical descriptors. The approach involves: (1) fetching a verified experimental dataset from Zenodo (ID fetched from `idea.md` and verified before execution), (2) performing semi-empirical geometry optimization and descriptor extraction (HOMO, LUMO, Mayer bond orders) via DFTB+ for the full dataset, (3) computing high-level DFT descriptors for a stratified sample subset using Psi4, and (4) training and comparing Random Forest models against experimental values.

**Critical Clarification**: This study is **purely correlational**. We do not claim that DFTB+ or DFT descriptors *cause* the barrier heights, nor do we validate the physical accuracy of the quantum calculations against the experimental data. The comparison is between two approximations of the same function (mapping descriptors to experimental barriers). The analysis cannot distinguish whether the Semi-Empirical model fails due to poor descriptors or poor model fit, as the 'truth' is fixed. The goal is to measure the correlation strength of gas-phase electronic properties with macroscopic experimental barriers, acknowledging the category error in validation.

The plan strictly adheres to the GitHub Actions free-tier constraints (limited CPU cores, limited RAM, time limits) by using a self-contained CPU-only Conda environment, streaming data, and avoiding external GPU offloads. All results are reproducible and traceable.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `rdkit`, `dftb+` (via Conda), `psi4` (via Conda), `datasets` (Hugging Face), `pyyaml`, `pytest`  
**Storage**: Local filesystem (`data/`, `logs/`, `reports/`); Zenodo (input)  
**Testing**: `pytest` with contract validation against `contracts/` schemas  
**Target Platform**: Linux (GitHub Actions Runner), CPU-only  
**Project Type**: Computational chemistry pipeline / CLI  
**Performance Goals**: 
- **Full Pipeline**: ≤ 6 hours (defined as: Fetch -> Optimize -> Semi-Des -> Subset -> DFT-Des -> Train -> Eval -> Sensitivity).
- **Memory**: ≤ 7 GB.
**Constraints**: No local GPU; strict memory limits; no access to gated datasets; must use verified Zenodo source; must handle convergence failures gracefully. **Auxiliary datasets (e.g., HuggingFace HOMO/LUMO) are NEVER used, even for validation.**

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The following table maps each Constitutional Principle to its concrete implementation location and verification method within this plan:

| Principle | Concrete Implementation Location | Verification Mechanism |
|-----------|----------------------------------|------------------------|
| **I. Reproducibility** | `code/fetch_data.py` (seeds), `code/train_models.py` (seeds), `requirements.txt` (versions). | `pytest/unit/test_seeds.py` asserts `np.random.seed(42)` is called before data split and model init. CI log checks `requirements.txt` hash. |
| **II. Verified Accuracy** | `code/fetch_data.py` fetches Zenodo ID from `idea.md` and validates record via Zenodo API before download. | `pytest/integration/test_zenodo_fetch.py` mocks API call to ensure ID matches `idea.md` and checksum is recorded. |
| **III. Data Hygiene** | `code/fetch_data.py` computes SHA-256 of raw CSV. `code/descriptor_calc.py` writes new files for derivations. | `pytest/unit/test_data_hygiene.py` verifies `data/raw/` file is never modified; `data/` artifacts have new checksums in `state/`. |
| **IV. Single Source of Truth** | `reports/evaluation.json` and `reports/sensitivity.csv` generated strictly from `data/descriptors_*.csv`. | `pytest/integration/test_report_traceability.py` asserts report values match `data/descriptors_*.csv` aggregates within tolerance. |
| **V. Versioning Discipline** | `state/projects/PROJ-546-...yaml` updated by `code/main.py` upon completion with artifact hashes. | `pytest/unit/test_versioning.py` checks `state/` file update timestamp and hash consistency. |
| **VI. Protocol Consistency** | `code/geometry_opt.py` (DFTB+) and `code/descriptor_calc.py` (Psi4) use identical XYZ files from `data/optimized_geometries/`. | `pytest/unit/test_geometry_consistency.py` asserts Psi4 input XYZs are byte-identical to DFTB+ output XYZs for the subset. |
| **VII. Resource-Bound** | CPU-only execution; `code/utils.py` memory monitor kills if >7GB. | CI logs capture `utils.py` memory snapshots; `pytest/unit/test_resource_limits.py` asserts no process exceeds 7GB in mock. |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-546/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-546-predicting-molecular-properties-from-qua/
├── code/
│   ├── __init__.py
│   ├── fetch_data.py        # Zenodo fetch & checksum (Principle I, II)
│   ├── geometry_opt.py      # DFTB+ optimization & retry logic (Principle VI)
│   ├── descriptor_calc.py   # HOMO/LUMO/Mayer extraction (DFTB+ & Psi4)
│   ├── confound_analysis.py # FR-008: MW, atom count, functional groups
│   ├── train_models.py      # RF training, 5-fold CV, paired t-test (Principle I, IV)
│   ├── sensitivity.py       # Feature importance & stability sweep
│   ├── utils.py             # Logging, error handling, memory monitoring
│   └── main.py              # Orchestration
├── data/
│   ├── raw/                 # Downloaded Zenodo CSV
│   ├── optimized_geometries/ # XYZ files
│   ├── descriptors_semi.csv # Semi-empirical descriptors
│   └── descriptors_dft.csv  # DFT descriptors (subset)
├── logs/
│   ├── convergence_failures.log
│   ├── oom_failures.log
│   └── structural_failures.log
├── reports/
│   ├── evaluation.json
│   └── sensitivity.csv
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── contracts/
│   ├── dataset.schema.yaml
│   ├── descriptor.schema.yaml
│   ├── descriptors.schema.yaml
│   ├── descriptors_dft.schema.yaml
│   ├── descriptors_semi.schema.yaml
│   ├── evaluation.schema.yaml
│   ├── evaluation_report.schema.yaml
│   ├── experimental_dataset.schema.yaml
│   └── sensitivity_report.schema.yaml
├── requirements.txt
├── pyproject.toml           # Linting (ruff, black) config
└── .pre-commit-config.yaml
```

**Structure Decision**: Single project structure chosen to minimize overhead and ensure all scripts can access shared data and logs easily. The `code/` directory isolates logic, while `data/` and `logs/` are strictly for artifacts.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The project is constrained by the spec and constitution; no additional complexity is introduced. | N/A |

## Phases

### Phase 0: Data Acquisition & Verification
- **Task**: Fetch Zenodo dataset (ID from `idea.md`), verify checksum, log status.
- **Output**: `data/raw/barrier_dataset.csv` (checksummed).
- **Constitution Link**: Principle I, II, III.

### Phase 1: Geometry Optimization (Semi-Empirical)
- **Task**: Run DFTB+ optimization on all molecules. Retry once on failure. Log failures.
- **Output**: `data/optimized_geometries/*.xyz`, `logs/convergence_failures.log`.
- **Constitution Link**: Principle VI (identical geometries).

### Phase 1.5: Confound Analysis (FR-008)
- **Task**: Calculate Molecular Weight (MW), Atom Count, and perform **functional group enumeration** for all molecules.
- **Output**: `data/confounds.csv` (columns: `molecule_id`, `mw`, `atom_count`, `functional_groups`).
- **Constitution Link**: FR-008.

### Phase 2: Descriptor Calculation
- **Semi-Empirical**: Compute HOMO/LUMO/Mayer for full set using DFTB+ optimized geometries.
- **DFT Subset**: Select stratified samples. Compute HOMO/LUMO/Mayer using Psi4 on the *same* XYZ files.
- **Output**: `data/descriptors_semi.csv`, `data/descriptors_dft.csv`.
- **Constitution Link**: Principle VI (same geometries).

### Phase 3: Modeling & Statistical Analysis
- **Shared Split**: The sample subset is split into multiple folds.
- **Training**: Train two Random Forest models (Semi-Empirical RF, DFT RF) using **k-fold Cross-Validation**.
- **Prediction**: Generate **out-of-fold** predictions for the entire 50-sample set.
- **Confound Control**: Include MW and functional group features in a partial correlation analysis to isolate descriptor effects. Report change in R².
- **Comparison**: Perform a **paired t-test** on the **out-of-fold** errors (Semi vs. DFT).
- **Report**: Generate `reports/evaluation.json` listing:
  - `mae_semi`, `mae_dft`
  - `t_test`: `statistic`, `p_value`, `null_hypothesis` ("No difference in error distribution"), `significance_level` (0.05), `models_compared`.
- **Limitation Acknowledgement**: Explicitly state in report that the comparison measures input quality correlation, not model validity.
- **Constitution Link**: Principle IV (SSoT).

### Phase 4: Sensitivity Analysis
- **Task**: Sweep feature importance cutoffs across a range of low to moderate thresholds. and noise levels {σ=0.01, 0.05}.
- **Metric**: Compute **rank correlation coefficient** (Spearman's rho) of top 3 descriptors across sweeps.
- **Threshold**: Enforce `stable = True` if rho >= 0.9.
- **Output**: `reports/sensitivity.csv`.
- **Constitution Link**: SC-003.

## Risk Management

| Risk | Mitigation |
|------|------------|
| **Convergence Failures** | Retry once; log failures. Skip only if `failed_after_retry`. |
| **OOM** | Monitor memory; kill and log. Reduce batch size if needed. |
| **Low Statistical Power (N=50)** | Use k-fold CV with out-of-fold predictions; apply bootstrapping/Wilcoxon if normality fails; interpret results with caution. |
| **Overfitting** | Use simple RF (`max_depth=5`); rely on out-of-fold predictions for t-test. |
| **Installation Time** | Use optimized Conda environment; estimate <30 mins install, leaving >5.5h for calc. |
| **Circular Validation** | Explicitly acknowledge in report that comparison is between two approximations of the same function, not a validation of physical accuracy. |
| **Confound Bias** | Perform partial correlation analysis and report R² delta when MW is added. |

## Performance Goals

- **Full Pipeline**: ≤ 6 hours (Fetch -> Optimize -> Semi-Des -> Subset -> DFT-Des -> Train -> Eval -> Sensitivity).
- **Memory**: ≤ 7 GB.
- **Disk**: ≤ 14 GB.