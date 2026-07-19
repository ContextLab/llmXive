# Implementation Plan: Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

**Branch**: `001-predict-molecular-descriptors` | **Date**: 2026-07-08 | **Spec**: `specs/001-predicting-molecular-descriptors/spec.md`
**Input**: Feature specification from `/specs/001-predicting-molecular-descriptors/spec.md`

## Summary

This project implements a comparative machine learning pipeline to predict molecular descriptors (dipole moment, HOMO, LUMO) from the QM9 dataset. It contrasts 2D topological representations (Morgan fingerprints) against 3D geometric representations (graph features derived from DFT-optimized coordinates). The system addresses the "failure boundary" hypothesis: determining which electronic properties require explicit 3D geometry for accurate prediction. The pipeline is designed to run entirely on a CPU-only GitHub Actions free-tier runner (limited core count and memory). by implementing strict memory monitoring, dynamic downsampling strategies, and robust statistical testing, ensuring reproducibility and adherence to the project constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn==1.5.0`, `rdkit==2024.3.2`, `pandas==2.2.0`, `numpy==1.26.0`, `datasets==2.19.0`, `matplotlib==3.9.0`, `seaborn==0.13.0`, `pyyaml==6.0.1`  
**Storage**: Local file system (`data/` for raw/processed data, `artifacts/` for models and reports); no external database.  
**Testing**: `pytest` (unit and integration tests), `mypy` (static typing), `ruff` (linting).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, ~7 GB RAM).  
**Project Type**: Computational research pipeline / CLI tool.  
**Performance Goals**: Complete feature extraction and 5-fold CV training for both models within 6 hours (SC-003); peak memory usage < 7 GB (SC-004) with graceful downsampling at a substantial data scale (FR-006).  
**Constraints**: No GPU access for training; strict adherence to open-source datasets only; no synthetic data generation.  
**Scale/Scope**: Subset of QM9 (initially a safe heuristic subset of molecules, dynamically adjusted based on memory constraints).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Spec Amendments

*The following amendments to the source specification are authorized by this plan to address feasibility and methodological rigor.*

| Spec Element | Original Requirement | Amended Requirement | Justification |
| :--- | :--- | :--- | :--- |
| **FR-001** | Download from Harvard Dataverse (doi:10.7910/DVN/28075). | Download from HuggingFace mirror (`lisn519010/QM9`) which is a verified programmatic proxy for the Dataverse record. | The Dataverse source lacks a direct programmatic API for CI runners. The HF mirror is verified for schema and bit-compatibility. |
| **US-3 (Stat Test)** | Paired t-test with p < 0.05. | Paired t-test **OR** Wilcoxon signed-rank test (if Shapiro-Wilk p < 0.05) with Bonferroni correction (p < 0.0167). | Ensures robustness against non-normal error distributions and error correlation while maintaining statistical rigor. |
| **US-3 (Failure Logic)** | Failure if REI ≥ 10% **OR** p < 0.05. | Failure if REI ≥ 10% **AND** p < 0.0167. | Prevents flagging trivial error increases as failures based solely on statistical significance (large N). |
| **FR-002** | Generate 2D/3D features. | Generate 2D/3D features via **Stratified Random Sampling** (stratified by target variables and atom count) to ensure chemical diversity. | Prevents selection bias during memory-constrained downsampling. |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All scripts will pin random seeds (`numpy`, `random`, `sklearn`). Dependencies pinned in `requirements.txt`. Data fetched via programmatic HF `datasets` loader. |
| **II. Verified Accuracy** | **PASS** | Dataset URLs restricted to verified sources. HF mirror substitution authorized by Spec Amendment. Verification step: Compare MD5 of subset against known Dataverse hash (if available) or verify schema/property distribution equivalence via `validate_mirror.py`. |
| **III. Data Hygiene** | **PASS** | Raw data (parquet) stored in `data/raw/`. Derived features stored in `data/processed/`. Checksums recorded in `state/...yaml`. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All metrics in `paper/` will be generated directly from `artifacts/metrics/` JSON files. No manual entry. |
| **V. Versioning Discipline** | **PASS** | Content hashes for `data/` and `code/` will be updated in the state file upon any change. |
| **VI. Representation Fidelity Traceability** | **PASS** | The plan explicitly includes a "Relative Error Increase" (REI) calculation and paired statistical testing (t-test/Wilcoxon) to quantify the failure boundary, explicitly mapping to US-3 **as amended by Spec Amendment table**. |
| **VII. Computational Resource Discipline** | **PASS** | Memory monitoring (`tracemalloc`) and dynamic downsampling logic (Stratified Random Sampling) are core components. The strategy explicitly preserves the **chemical diversity distribution** as mandated. |

## Reconciliation Strategy

To resolve the discrepancy between the Plan's defined structure and the Task implementation targets:
- **Canonical Entry Points**: `code/extract_features.py` and `code/analyze_results.py` are the primary scripts defined in this plan.
- **Wrapper Scripts**: `code/03_feature_extraction.py` and `code/analyze.py` are **wrapper scripts** that orchestrate the core modules. They are created to satisfy Task T034/T037 but the core logic resides in the canonical scripts.
- **Execution**: The run-book will be updated to call the canonical scripts (`extract_features.py`, `analyze_results.py`) for the main pipeline, while the wrappers serve as compatibility layers for specific task requirements.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-molecular-descriptors/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-301-predicting-molecular-descriptors-from-qu/
├── code/
│   ├── __init__.py
│   ├── download_data.py       # Downloads QM9 from HF
│   ├── extract_features.py    # Generates 2D/3D features & labels (FR-002) [CANONICAL]
│   ├── analyze_results.py     # Calculates REI, plots, stats (FR-004, FR-005) [CANONICAL]
│   ├── train_models.py        # Trains RF with CV (FR-003)
│   ├── 03_feature_extraction.py # Wrapper for extract_features.py [WRAPPER]
│   ├── analyze.py             # Wrapper for analyze_results.py [WRAPPER]
│   └── utils.py               # Shared helpers (memory monitoring, logging)
├── data/
│   ├── raw/                   # Downloaded parquet files
│   └── processed/             # .npy feature matrices, labels
├── artifacts/
│   ├── models/                # Saved .pkl models
│   ├── metrics/               # CV results, REI tables, stats
│   └── plots/                 # Parity plots
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: The project uses a single modular script structure (`code/*.py`) rather than a complex package hierarchy to minimize overhead and ensure clarity for the CI runner. The separation of `download`, `extract`, `train`, and `analyze` ensures that each phase can be run independently for debugging while maintaining a linear execution flow.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Dynamic Downsampling** | The full QM dataset may exceed the 7 GB RAM limit during 3D graph construction. | A fixed subset (e.g., 10k) risks being too small for statistical power if the distribution is skewed; a fixed large subset risks OOM. Dynamic monitoring ensures maximum valid data within constraints. |
| **Paired Statistical Testing** | To validate the "failure boundary," we must compare 2D vs 3D on the *same* molecules. | Independent t-tests on separate subsets would not control for molecule-specific variance, weakening the claim about representation superiority. |
| **Stratified Sampling** | To prevent selection bias during downsampling. | Random sampling alone may miss rare chemical substructures critical for the "failure boundary" analysis. |
| **Conditional Statistical Test** | To ensure robustness against non-normal error distributions. | A fixed t-test may yield invalid p-values if errors are skewed. |