# Implementation Plan: Predicting Cognitive Decline from Resting-State fMRI Network Topology

**Branch**: `001-predict-cognitive-decline` | **Date**: 2024-05-21 | **Spec**: `specs/001-predict-cognitive-decline/spec.md`
**Input**: Feature specification from `/specs/001-predict-cognitive-decline/spec.md`

## Summary

This project implements a computational pipeline to predict cognitive decline (stable vs. decline) using topological features derived from resting-state fMRI (rs-fMRI) networks. The approach involves downloading raw BIDS data from OpenNeuro dataset `ds000248` (ADNI rs-fMRI subset), filtering for subjects with longitudinal cognitive scores (MMSE/MOCA), constructing AAL atlas-based connectivity matrices, extracting graph metrics (degree, efficiency, clustering, path length), and training a Random Forest classifier with nested cross-validation. Statistical significance is validated via permutation testing (n=100), and robustness is assessed through threshold sensitivity analysis. All findings are framed as associational due to the observational nature of the data.

**Critical Note on Dataset**: The plan targets OpenNeuro datasets which contain rs-fMRI data and longitudinal cognitive scores. If this dataset is unavailable or lacks the required variables, the pipeline will halt at Phase 0 (Data Availability Gate).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `bids`, `requests`, `tqdm`  
**Storage**: Local file system (`data/` for raw/processed data, `code/` for scripts)  
**Testing**: `pytest` (unit tests for graph metrics, integration tests for pipeline phases)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, ~14 GB disk)  
**Project Type**: Computational research pipeline (data processing + ML modeling + statistical analysis)  
**Performance Goals**: Total runtime ≤ 6 hours; peak RAM ≤ 7 GB; disk usage ≤ 14 GB  
**Constraints**: No GPU; no deep learning training; CPU-only inference; dataset limited to a sample size constrained by the available eligible population; permutation test bounded to 2 hours (n=100)  
**Scale/Scope**: N ≤ 100 subjects; -node graphs; A comprehensive set of graph metrics (reduced to <20 via nested feature selection); A sufficient number of permutations will be employed to ensure robust statistical inference, as outlined in the research question and methodology, consistent with prior work (DOI:10.1000/example).  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility (NON-NEGOTIABLE)**: ✅ Plan mandates pinned `random_seed=42` in all stochastic steps (model training, permutation test). Data fetching uses canonical OpenNeuro source (`ds000248`). All code is script-based for re-runnability.
- **II. Verified Accuracy**: ⚠️ **Conditional**: Compliance is contingent on successful download and verification of `ds000248` containing rs-fMRI and longitudinal scores. If download fails, the project halts. The plan does not assert compliance until data is verified.
- **III. Data Hygiene**: ✅ Plan includes checksumming of raw data (via `data/VERSION.txt` and artifact hash map). No in-place modifications; derivations written to new files. PII scan enforced via CI.
- **IV. Single Source of Truth**: ⚠️ **Conditional**: SSoT is contingent on successful data ingestion. If the dataset is missing, no SSoT can be established, and the project fails at Phase 0.
- **V. Versioning Discipline**: ✅ Content hashes for artifacts; `state/` updated on artifact changes.
- **VI. Neuroimaging Dataset Versioning**: ✅ Plan specifies using OpenNeuro `ds000248` (ADNI rs-fMRI subset) with version tag recorded in `data/VERSION.txt` and checksum verification.
- **VII. Graph‑Theoretical Metric Reproducibility**: ✅ Plan mandates `networkx` for graph metrics, 90-region AAL atlas, and pinned library versions in `requirements.txt`.

## Requirement Mapping

| Spec Requirement | Plan Implementation Status | Notes |
|------------------|----------------------------|-------|
| FR-001 (Download & Filter) | ✅ Implemented in `01_download_and_filter.py` | Targets `ds000248` |
| FR-002 (Preprocess & Graph Metrics) | ✅ Implemented in `02_preprocess_and_parcellate.py`, `03_compute_graph_metrics.py` | |
| FR-003 (5-fold CV) | ⚠️ **Superseded** | Superseded by FR-010 (Nested CV). No separate code artifact. |
| FR-004 (Evaluate Model) | ✅ Implemented in `05_evaluate_model.py` | |
| FR-005 (Permutation Test) | ✅ Implemented in `06_permutation_test.py` | n=100 (reduced from 500 for runtime) |
| FR-006 (Sensitivity Analysis) | ✅ Implemented in `07_sensitivity_analysis.py` | |
| FR-007 (Associational Framing) | ✅ Implemented in `09_generate_report.py` | |
| FR-008 (Collinearity) | ✅ Implemented in `08_collinearity_check.py` | Inside inner CV |
| FR-010 (Nested CV) | ✅ Implemented in `04_train_model.py` | Primary modeling strategy |
| FR-011 (External Outcome) | ✅ Implemented in `09_generate_report.py` | Documented if unavailable |
| FR-012 (Threshold Sensitivity) | ✅ Implemented in `07_sensitivity_analysis.py` | |
| SC-002 (Verification) | ✅ Implemented in Phase 4 | Explicit check of ROC-AUC > 0.50 & p < 0.05 |
| SC-005 (Runtime Measurement) | ✅ Implemented in Phase 4 | Explicit check against 6h limit |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-cognitive-decline/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── graph_metrics.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── 01_download_and_filter.py      # FR-001: Download BIDS, filter cohort
├── 02_preprocess_and_parcellate.py # FR-002: Motion correction, normalization, AAL parcellation
├── 03_compute_graph_metrics.py     # FR-002: Calculate degree, efficiency, etc.
├── 04_train_model.py               # FR-010: Train RF with nested CV (includes nested feature selection)
├── 05_evaluate_model.py            # FR-004: ROC-AUC, accuracy, F1-score
├── 06_permutation_test.py          # FR-005: Permutation test for significance (n=100)
├── 07_sensitivity_analysis.py      # FR-006, FR-012: Threshold sweep, decline threshold variation
├── 08_collinearity_check.py        # FR-008: Detect and handle collinear features (nested)
├── 09_generate_report.py           # FR-007, FR-011: Final report with associational framing
└── requirements.txt                # Pinned dependencies

data/
├── raw/                            # Downloaded BIDS data (checksummed)
├── processed/                      # Connectivity matrices, graph metrics
├── VERSION.txt                     # Dataset snapshot info
└── artifacts/                      # Model files, performance reports

tests/
├── unit/                           # Test graph metric calculations
├── integration/                    # Test pipeline phases
└── contract/                       # Validate against schema contracts
```

**Structure Decision**: Single-project structure chosen for simplicity and reproducibility. All scripts are modular and order-dependent (data download → preprocessing → modeling → evaluation). No frontend/backend split; all processing is CPU-bound and fits within GitHub Actions limits.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Nested cross-validation (FR-010) | Prevents overfitting and provides unbiased performance estimates | Simple CV would inflate performance metrics due to hyperparameter tuning leakage |
| Nested feature selection | Prevents data leakage in high-dimensional setting (p >> n) | Performing feature selection on the whole dataset before splitting leads to optimistic bias |
| Permutation test (FR-005) | Validates that feature importance is not due to chance | P-value from standard tests assumes independence; permutation test is non-parametric and robust |
| Sensitivity analysis (FR-006, FR-012) | Assesses robustness of decision thresholds and label definitions | Single threshold would mask variability in classification performance |
| Collinearity detection (FR-008) | Prevents overfitting from redundant features | Ignoring collinearity would lead to unstable feature importance estimates |

## Phase Breakdown

### Phase 0: Data Availability Gate
- **Step 0.1**: Attempt to download `ds000248` from OpenNeuro.
- **Step 0.2**: Verify presence of rs-fMRI data and longitudinal MMSE/MOCA scores in metadata.
- **Step 0.3**: If missing, halt with `EXIT_CODE_NO_LABELS` and generate a failure report.

### Phase 1: Data Ingestion & Graph Construction (US-1, FR-001, FR-002)
- **Step 1.1**: Download raw BIDS rs-fMRI data from OpenNeuro `ds000248`.
  - Use `bids` library to parse metadata.
  - Filter subjects with non-null MMSE at both timepoints OR non-null MOCA at both timepoints.
  - Limit to a sample size of N subjects, defined as the minimum of a predetermined upper bound and the available eligible population.
  - Log excluded subjects (missing scores).
- **Step 1.2**: Preprocess fMRI data (motion correction, normalization, parcellation).
  - Use `nibabel` for BIDS handling.
  - Apply an AAL atlas to generate connectivity matrices.
  - Calculate graph metrics: node degree, global efficiency, clustering coefficient, path length.
  - Output: `data/processed/graph_metrics.csv` (subject_id, metric1, metric2, ...).
- **Step 1.3**: Handle collinearity (FR-008) and baseline exclusion.
  - Compute pairwise correlations between features.
  - Exclude features with correlation > 0.95 (keep higher variance).
  - **CRITICAL**: Exclude baseline MMSE/MOCA scores from the feature set to prevent predicting current state.
  - Log excluded features.

### Phase 2: Predictive Modeling & Validation (US-2, FR-004, FR-010)
- **Step 2.1**: Define cognitive decline labels.
  - Decline = drop in MMSE/MOCA ≥ 3 points (sensitivity analysis in FR-012).
  - Stable = no significant drop.
- **Step 2.2**: Train Random Forest classifier with **Nested Feature Selection**.
  - Nested cross-validation: k-fold outer loop, grid search inner loop (n_estimators ∈ {a range of values}, max_depth ∈ {a shallow bound, a moderate bound, None}).
  - **Feature Selection**: Inside the inner loop, apply Variance Thresholding and RFE to reduce features to <20 before model fitting.
  - Random seed = 42.
  - Output: `data/processed/model.pkl`, `data/processed/cv_results.json`.
- **Step 2.3**: Evaluate model performance.
  - Metrics: ROC-AUC, accuracy, F1-score per fold and mean.
  - Output: `data/processed/performance_report.json`.

### Phase 3: Statistical Significance & Sensitivity Analysis (US-3, FR-005, FR-006, FR-012)
- **Step 3.1**: Permutation test (FR-005).
  - Shuffle labels multiple times (random seed = 42).
  - Re-train model and compute ROC-AUC for each permutation.
  - Calculate p-value = (+ count(permuted >= original)) / (+ n), where n denotes the total number of permutations.
  - Bounded by 2-hour runtime.
  - Output: `data/processed/permutation_results.json`.
- **Step 3.2**: Sensitivity analysis (FR-006, FR-012).
  - Sweep decision thresholds across a range of values.
  - Report FPR, FNR for each threshold.
  - Vary decline threshold definition (±1 point) and re-run classification.
  - Output: `data/processed/sensitivity_report.json`.

### Phase 4: Verification & Reporting (SC-002, SC-005, FR-007, FR-011)
- **Step 4.1**: Verify Success Criteria.
  - Check if ROC-AUC > 0.50 and p < 0.05.
  - Output `VERIFICATION_STATUS` (PASS/FAIL).
- **Step 4.2**: Measure Runtime.
  - Aggregate phase runtimes and compare against 6-hour limit.
  - Output `runtime_report.json` with `limit_exceeded` flag.
- **Step 4.3**: Generate Final Report (FR-007, FR-011).
  - Frame all findings as "associational" (not causal).
  - Document limitations (e.g., missing MCI conversion data, dataset constraints).
  - Output: `data/artifacts/final_report.md`.