# Implementation Plan: Predicting Molecular Conductivity from Graph-Based Features

**Branch**: `001-predict-molecular-conductivity` | **Date**: 2026-06-24 | **Spec**: `specs/001-predicting-molecular-conductivity/spec.md`

## Summary

This feature implements a reproducible pipeline to predict molecular conductivity (log-transformed charge carrier mobility) from graph-based topological descriptors derived from SMILES strings. The approach utilizes RDKit for descriptor computation (including aromaticity indices and conjugation path lengths as proxies for resonance), scikit-learn for Random Forest and Gradient Boosting regression, and scaffold splitting to prevent data leakage. The pipeline strictly adheres to CPU-only execution, handles missing data via exclusion, and performs mandatory sensitivity analysis on outlier thresholds and collinearity diagnostics (VIF). 

**Critical Methodological Note**: If the dataset lacks external conductivity measurements, the study is reframed as a "Self-Consistency Validation" of the empirical proxy model (target = proxy) rather than a prediction of physical reality. The pipeline includes a robust fallback mechanism for target variable estimation using a validated empirical formula if direct conductivity data is missing, and a circularity check to ensure the model is not trivially reconstructing the input graph.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `datasets` (Hugging Face)  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `code/`)  
**Testing**: `pytest` (unit tests for descriptors, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM)  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: Complete full analysis (descriptors, training, evaluation, plotting) within 6 hours.  
**Constraints**: CPU-only; no GPU; dataset must be streamed or sampled to fit within 7 GB RAM; strict VIF > 10 exclusion rule; mandatory Benjamini-Hochberg correction; mandatory dynamic range validation; mandatory circularity check.  
**Scale/Scope**: Up to 5000 molecules (sampled if larger); 10-20 descriptors per molecule.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinned `requirements.txt`, fixed random seeds in all scripts, and use of canonical Hugging Face dataset URLs. All data transformations produce new files in `data/processed/` with checksums.
- **II. Verified Accuracy**: All citations (e.g., for bond orders, confidence intervals) will be validated against the `Verified Facts` block or primary sources. No unverified URLs will be used.
- **III. Data Hygiene**: Raw data from Hugging Face will be stored in `data/raw/` with checksums (computed via streaming hash). No in-place modification. Derived data (descriptors, filtered sets) in `data/processed/`.
- **IV. Single Source of Truth**: All figures and metrics will be generated directly from `code/` scripts reading `data/processed/`. No hand-typed numbers.
- **V. Versioning Discipline**: All artifacts (scripts, data files) will carry content hashes. The `state` YAML will be updated upon artifact changes.
- **VI. Graph Descriptor Transparency**: All descriptors (degree, path length, ring count, conjugation, aromaticity) will be computed via RDKit with version pinned. Unit tests will verify values for known SMILES (e.g., benzene).
- **VII. Dataset Provenance**: The dataset will be sourced exclusively from verified PubChem or Materials Project sources. Raw files stored unchanged (or sampled if too large).

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-conductivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-528-predicting-molecular-conductivity-from-g/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── descriptors.py           # RDKit descriptor computation (FR-001, FR-008, FR-014)
│   ├── preprocessing.py         # Cleaning, log-transform, VIF filtering (FR-012, FR-013)
│   ├── split.py                 # Scaffold splitting (FR-002)
│   ├── train.py                 # Model training, CV, sensitivity analysis (FR-003, FR-004, FR-007)
│   ├── evaluate.py              # Metrics, FDR correction, plotting (FR-005, FR-006)
│   ├── target_proxy.py          # Empirical target estimation (FR-014)
│   ├── circularity_check.py     # Residual variance test (SC-001, SC-009)
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/                     # Downloaded parquet files (chunked, checksummed)
│   └── processed/
│       ├── descriptors.csv      # Computed graph features
│       ├── filtered_train.csv   # Training set (post-VIF, post-outlier)
│       ├── filtered_test.csv    # Test set
│       └── quantum_proxy_report.json # Report on quantum descriptor presence
├── tests/
│   ├── unit/
│   │   ├── test_descriptors.py  # Verify benzene aromaticity, path length
│   │   └── test_vif.py          # Verify VIF calculation and exclusion logic
│   └── integration/
│       └── test_pipeline.py     # End-to-end run on sample data
└── docs/
    └── artifacts/               # Generated plots, reports
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) chosen for simplicity and alignment with the CPU-only, single-runner constraint. No microservices or separate frontend/backend required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| VIF > 10 Exclusion Logic | FR-013 mandates exclusion of collinear features to prevent spurious claims. | Simple correlation threshold is insufficient for multivariate collinearity; VIF is required. |
| Scaffold Splitting | FR-002 requires preventing leakage from structurally similar molecules. | Random splitting would allow similar molecules in train/test, inflating R² artificially. |
| Sensitivity Analysis | FR-007 mandates sweeping outlier thresholds (2.5σ, 3.0σ, 3.5σ). | Single threshold is arbitrary; robustness check is required for scientific validity. |
| FDR Correction | FR-006 mandates Benjamini-Hochberg for multiple comparisons. | Standard p-values would inflate Type I error rates across multiple feature correlations. |
| Circularity Check | SC-001 and SC-009 require ensuring the target is not a linear combination of predictors. | Without this check, the model may trivially reconstruct the input graph, invalidating the scientific claim. |
| Empirical Target Proxy | FR-014 and methodology concerns require a defined fallback for missing conductivity. | Without a defined formula, the pipeline would halt or use an invalid proxy. |

## Phases and Tasks

### Phase 0: Data Acquisition & Validation
- **T011**: [FR-011] Validate target variable dynamic range (≥ 3 orders of magnitude).
- **T012**: [FR-012] Exclude molecules with missing conductivity or invalid descriptors.
- **T013**: Load raw data from verified PubChem/Materials Project sources (streaming/chunked).
- **T014a**: [FR-014] Detect absence of quantum-derived descriptors; log warning.
- **T014b**: [FR-014, T026] **Target Variable Validation & Fallback**. Check for `conductivity` or `HOMO-LUMO` columns. If missing, compute `log_conductivity_proxy` using empirical formula. If proxy cannot be computed, HALT with "No Independent Target" error.
- **T015**: [SC-009] Generate `quantum_proxy_report.json` indicating presence/absence of quantum descriptors.

### Phase 1: Descriptor Computation
- **T016**: Compute graph-based descriptors (aromaticity, conjugation, ring count, etc.) using RDKit.
- **T017**: Compute target proxy (log_conductivity) using empirical formula if direct data is missing.
- **T018**: Filter missing targets and invalid descriptors.

### Phase 2: Preprocessing & Splitting
- **T019**: Calculate VIF for all predictors; exclude features with VIF > 10.
- **T020**: Perform scaffold splitting (a standard train-test split). **Mitigation**: If test set < 20 molecules, retry with new seed. If N < 100 total, enable Nested CV.
- **T021**: Log excluded features and retrain models if necessary.

### Phase 3: Model Training & Evaluation
- **T022**: [SC-001, SC-009] Perform Residual Variance Test to check for circularity. If correlation > 0.95, halt.
- **T023**: Train Random Forest and Gradient Boosting models.
- **T024**: Evaluate models (R², MAE, CV). **Mitigation**: If N < 100, use 5x5 Nested CV and Bootstrap (1000 iters).
- **T025**: Perform sensitivity analysis (Kruskal-Wallis H-test with a sufficient sample size).
- **T026**: Apply Benjamini-Hochberg correction to p-values.
- **T027**: Generate feature importance rankings and correlation plots.
- **T028**: [SC-003] Measure confidence interval coverage against the nominal target.

### Phase 4: Reporting
- **T029**: Generate final report with all metrics, plots, and warnings.
- **T030**: Validate all outputs against contracts.

### Phase 8: Deferred Analysis (Blocked)
- **T061**: [DEFERRED] Hückel Energy Computation. **Blocked** until external dataset with Hückel energy data is found.
- **T012b**: [DEFERRED] Unit Test for Hückel Resonance. **Blocked** until T061 is complete or external data is available.

## Research Question Reframing

If the dataset lacks external conductivity measurements, the study is reframed as a **Self-Consistency Validation**: "Do topological descriptors (conjugation, aromaticity) consistently predict the *empirical proxy* for conductivity derived from those same descriptors?" The success criteria (SC-001) are redefined to measure the fit of the proxy model itself (R² of Proxy vs. Proxy) rather than predicting physical reality, and the paper must explicitly state this limitation.

## Compute Feasibility & Data Strategy

- **Streaming & Chunking**: To adhere to strict RAM and disk constraints, the pipeline uses `datasets.load_dataset(..., streaming=True)` to iterate through the dataset shard by shard. The SHA-256 checksum is computed incrementally without loading the full file into memory.
- **Sampling**: If the dataset exceeds 5000 rows (after filtering), a random sample (seed=42) is taken. If the raw file is >14 GB, only the sample is downloaded and checksummed; the full raw file is skipped to prevent disk overflow.
- **CPU-First**: All models (RF, GB) run on CPU. No GPU dependencies.
- **Memory**: Dataset sampled/streamed to fit <7 GB RAM.
- **Time**: Pipeline designed to complete <6 hours on 2-core runner.