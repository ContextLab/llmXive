# Implementation Plan: Predicting Plant Drought Tolerance from RSA Data

**Branch**: `001-predict-drought-tolerance` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-drought-tolerance/spec.md`

## Summary

This feature implements a CPU-tractable pipeline to predict plant drought tolerance (physiological state) from Root System Architecture (RSA) metrics. The approach ingests root images (NPPN via verified MGB3 source), extracts quantitative traits (depth, branching, surface area) using OpenCV/scikit-image, merges them with physiological data from the TRY database, and performs statistical analysis. 

**Critical Methodological Constraints**:
1.  **No Circular Classification**: Classification (RF) and sensitivity analysis are **SKIPPED** entirely if no *independent* tolerance proxy (e.g., survival rate, biomass under stress) is found in the dataset. The pipeline does **not** binarize the target physiological variable (stomatal conductance) to create a 'ground truth'. The 'median split' is applied **only** to the *independent proxy* variable if it exists.
2.  **Phylogenetic Validity**: PGLS requires a phylogenetic tree. **If the Open Tree of Life API fails to provide a tree, the pipeline HALTS immediately with a critical error.** PVR (Phylogenetic Eigenvector Regression) is **NOT** a fallback because it requires a distance matrix derived from a tree; without a tree, PVR is mathematically impossible. The requirement for phylogenetic correction (FR-010) cannot be satisfied without a tree.
3.  **Species-Level Stratification**: All Cross-Validation (CV) loops (with a k-fold configuration) MUST use `GroupKFold` or a custom `GroupShuffleSplit` where the `groups` parameter is the `species_name`. This prevents data leakage where the same species appears in both training and test sets.
4.  **Power Analysis Justification**: The minimum species count (N) is derived from a power analysis: Cohen's f2=0.15 (medium effect), alpha=0.05, power=0.80, k=3 predictors. This yields N=55. The pipeline halts if N < 55.

The pipeline handles collinearity via PCA and phylogenetic non-independence via PGLS (strict tree requirement). It includes rigorous sensitivity analysis for classification thresholds (if proxy exists) and multiple-comparison corrections for hypothesis testing, all constrained to run on a GitHub Actions free-tier runner (limited CPU, 7GB RAM, 6h limit).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `opencv-python-headless`, `scikit-image`, `statsmodels`, `networkx`, `requests`, `pyyaml`, `power` (for power analysis)  
**Storage**: Local filesystem (`data/raw`, `data/derived`, `results`)  
**Testing**: `pytest` (unit, integration, contract)  
**Target Platform**: Linux (GitHub Actions Free Runner)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Process [deferred] images in <6h; Memory <7GB; Disk <14GB
**Constraints**: No GPU/CUDA; No heavy LLM training; Strict adherence to verified dataset URLs; Reproducible random seeds.  
**Scale/Scope**: ~10k images (NPPN/MGB3), ~50-100 species overlap with TRY (Minimum 55 for Power Analysis).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ | Random seeds pinned in `code/`. External datasets fetched from canonical sources. `requirements.txt` pinned. |
| **II. Verified Accuracy** | ✅ | All dataset URLs in `research.md` are restricted to the verified list. Citations validated against primary sources. NPPN data sourced via verified MGB3 URL. |
| **III. Data Hygiene** | ✅ | Raw data checksummed. Derivations written to new files. No in-place modification. PII scan passed. |
| **IV. Single Source of Truth** | ✅ | All figures/stats in reports trace to `data/derived` CSVs and `code/` scripts. No hand-typed numbers. |
| **V. Versioning Discipline** | ✅ | T035/T036 generate content hashes and update `state/` manifest for every artifact. |
| **VI. Image-Based Phenotyping** | ✅ | RSA extraction uses OpenCV/scikit-image with documented params. Raw images preserved. |
| **VII. Biological Variation** | ✅ | **Species-level GroupKFold (5-fold)** used. PGLS applied (strict tree requirement). K-fold CV and permutation tests applied. CIs reported. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-drought-tolerance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml       # Validates FR-001, FR-002, FR-003
    ├── rsametrics.schema.yaml    # Validates FR-002, SC-001
    ├── merged_data.schema.yaml   # Validates FR-003, FR-010
    ├── model_results.schema.yaml # Validates FR-004, FR-005, FR-006
    ├── output.schema.yaml        # Validates FR-009, SC-002
    └── results.schema.yaml       # Validates FR-005, SC-003
```

**Structure Decision**: Selected a single-project structure (`code/`, `data/`, `tests/`) to align with the computational research nature. This minimizes overhead for data movement and ensures the "Single Source of Truth" principle is easily enforceable via file paths.

**Contract Mapping**:
- `dataset.schema.yaml`: Validates merged data structure (FR-001, FR-002).
- `rsametrics.schema.yaml`: Validates extracted traits (FR-002, SC-001).
- `merged_data.schema.yaml`: Validates joined data and PCA/PVR fields (FR-003, FR-010).
- `model_results.schema.yaml`: Validates model outputs, VIF, and sensitivity (FR-004, FR-005, FR-006).
- `output.schema.yaml`: Validates final report framing (FR-009).
- `results.schema.yaml`: Validates sensitivity sweep details (FR-005, SC-003).

### Source Code (repository root)

```text
projects/PROJ-464-predicting-plant-drought-tolerance-from-/
├── data/
│   ├── raw/             # Downloaded images/parquet, checksums
│   └── derived/         # Processed RSA metrics, merged datasets, models
├── code/
│   ├── __init__.py
│   ├── download.py      # Data ingestion (NPPN/MGB3, TRY)
│   ├── extract_rsa.py   # Image analysis (OpenCV/scikit-image)
│   ├── merge_data.py    # Join RSA + Physio + Phylogeny
│   ├── models.py        # PGLS, RF, PCA, VIF checks, GroupKFold logic
│   ├── analysis.py      # Sensitivity sweep, multiple comparison correction
│   └── report.py        # Generate final markdown/tables
├── tests/
│   ├── unit/            # Logic tests (VIF, sensitivity, GroupKFold)
│   ├── integration/     # End-to-end pipeline (small subset)
│   └── contract/        # Schema validation tests (imports from contracts/)
├── results/
│   ├── figures/         # Plots (sensitivity curves, correlation matrices)
│   ├── sensitivity_fpr_fnr.csv # Sensitivity analysis FPR/FNR (T028a)
│   └── reports/         # Final markdown reports
├── state/               # Execution state, hashes, logs
├── docs/                # Quickstart, API docs
└── requirements.txt     # Pinned dependencies
```

**Structure Decision**: Contracts are defined in `contracts/` as the Single Source of Truth. `tests/contract/` imports these schemas to validate data. This ensures consistency between definition and validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Phylogenetic Correction (PGLS)** | Required by FR-010 and Constitution VII to handle species non-independence. | Standard OLS regression ignores evolutionary relationships, leading to inflated Type I errors. **PVR is rejected as a fallback** because it requires a tree. |
| **Sensitivity Analysis Sweep** | Required by FR-005 and US3 to validate classification thresholds. | A single-point evaluation is insufficient to prove robustness against arbitrary decision boundaries. |
| **PCA + VIF Handling** | Required by FR-006 and US2 to address collinearity in RSA traits. | RSA traits (depth, length, surface area) are definitionally related; claiming independent effects would be scientifically invalid. PCA components are treated as 'associational patterns'. |
| **Multiple Comparison Correction** | Required by FR-004 to control family-wise error rate. | Testing multiple hypotheses (depth, branching, surface area) without correction increases false positive risk. |
| **No Circular Classification** | Required to avoid scientific invalidity (median-split of target). | Using the target variable to create the classification label creates a circular validation loop. Classification is only performed if an *independent* proxy exists. |
| **Species-Level GroupKFold** | Required to prevent phylogenetic leakage. | Standard KFold allows the same species in train/test, invalidating phylogenetic independence. |

## Implementation Tasks

### Phase 0: Setup & Power Analysis

- **T001a**: Setup Directory Structure
  - Create `data/raw`, `data/derived`, `code`, `tests`, `docs`, `state`, `contracts`, `results`.
  - **Deliverable**: Directory structure created.

- **T003**: Power Analysis & Species Count Check
  - **Logic**: Calculate required sample size (N) using `statsmodels.stats.power.FTestPower`. Parameters: Cohen's f2=0.15 (medium effect), alpha=0.05, power=0.80, k=3 predictors. Result: N >= 55.
  - Fetch species list from NPPN/MGB3 and TRY.
  - **Logic**: If overlap N < 55, halt with critical error "Insufficient species for power analysis (N < 55)".
  - **Deliverable**: `state/power_analysis_report.yaml` (includes calculated N, actual N, decision).

### Phase 1: Data Ingestion & Extraction

- **T012**: Download NPPN (via MGB3)
  - Fetch root images from verified MGB3 URL (NPPN source).
  - **Logic**: If download fails, halt (no fallback to synthetic data).
  - **Deliverable**: `data/raw/nppn_images/` (images), `data/raw/nppn.parquet`.

- **T012b**: Validate NPPN Data
  - Verify checksums and schema of downloaded data.
  - **Deliverable**: `state/nppn_validation.yaml`.

- **T015**: Extract RSA Metrics
  - Process images using OpenCV/scikit-image.
  - **Deliverable**: `data/derived/rsametrics.csv` (validates `rsametrics.schema.yaml`).

- **T020**: Download TRY Traits
  - **Depends**: T015 (to get species list).
  - Fetch physiological traits for species in `rsametrics.csv`.
  - **Deliverable**: `data/raw/try_traits.csv`.

### Phase 2: Data Merging & Transformation

- **T021**: Merge Data
  - Join RSA and Physio data on `species_name`.
  - **Deliverable**: `data/derived/merged_data.csv` (validates `merged_data.schema.yaml`).

- **T022**: VIF Check & PCA
  - Calculate VIF. If VIF > 5 for any predictor, flag.
  - Perform PCA on RSA traits.
  - **Deliverable**: `data/derived/pca_results.csv`, `state/vif_report.yaml`.

- **T022b**: Suppress Independent Claims
  - **Depends**: T022.
  - If VIF > 5, inject 'COLLINEARITY WARNING' into report generation logic.
  - **Deliverable**: `state/vif_compliance_check.yaml`.

### Phase 3: Phylogenetic Correction

- **T024a**: Fetch Phylogenetic Tree
  - Attempt to fetch tree from Open Tree of Life API.
  - **Logic**: If fetch fails, **HALT** with critical error "Phylogenetic tree fetch failed. PVR fallback is impossible without a tree. FR-010 violation."
  - **Deliverable**: `data/derived/phylogenetic_tree.newick`.

- **T024**: Fit PGLS
  - **Depends**: T022, T024a.
  - **Logic**: Fit PGLS using `statsmodels` with the fetched tree.
  - **Deliverable**: `data/derived/pgls_results.csv`.

### Phase 4: Modeling & Analysis

- **T027**: Detect Tolerance Proxies
  - Check for independent tolerance proxy (survival, biomass) in TRY data.
  - **Deliverable**: `state/proxy_detection.yaml` (boolean `has_proxy`).

- **T027b**: Fit Classification (Conditional)
  - **Depends**: T022, T027.
  - **Logic**: Only if `has_proxy` is True.
  - **Step 1**: Binaries *proxy* variable using median split.
  - **Step 2**: Fit Random Forest Classification.
  - **Step 3**: Use **GroupKFold** (groups=species_name) for 5-fold CV to prevent leakage.
  - **Deliverable**: `data/derived/classification_model.pkl`.

- **T028**: Sensitivity Analysis (Conditional)
  - **Depends**: T027b.
  - **Logic**: If T027b not executed, output 'N/A' with justification.
  - **Logic**: Sweep *predicted probability* threshold (not physiological metric) by ±0.05.
  - **Deliverable**: `results/sensitivity_sweep_results.csv`.

- **T028a**: Calculate FPR/FNR
  - **Depends**: T028.
  - Calculate and report False Positive/Negative rates for each probability threshold.
  - **Deliverable**: `results/sensitivity_fpr_fnr.csv`.

### Phase 5: Reporting & Validation

- **T029**: Generate Report
  - **Depends**: T022b, T028a.
  - Include PCA disclaimer, VIF warning, and framing (associational).
  - **Deliverable**: `results/reports/final_report.md`.

- **T030**: Verify VIF Compliance
  - **Depends**: T022, T029.
  - **Logic**: Assert that if VIF > 5, the report does not claim independent effects.
  - **Deliverable**: `state/vif_compliance_check.yaml` (updated with verification status).

- **T034**: Measure Runtime
  - Log total pipeline execution time.
  - **Logic**: If > 6h, log warning and halt.
  - **Deliverable**: `state/runtime_log.yaml`.

- **T035**: Generate Artifact Hashes
  - Compute content hashes for all `data/derived` and `results` files.
  - **Deliverable**: `state/artifact_hashes.yaml`.

- **T036**: Update State Manifest
  - Update `state/` manifest with new hashes and timestamps.
  - **Deliverable**: Updated `state/projects/...yaml`.

## Verification & Success Criteria

- **SC-001**: Validate `rsametrics.csv` against `rsametrics.schema.yaml`.
- **SC-002**: Validate `merged_data.csv` against `merged_data.schema.yaml`.
- **SC-003**: Validate `sensitivity_fpr_fnr.csv` exists and contains FPR/FNR columns.
- **SC-004**: Validate `state/vif_compliance_check.yaml` confirms suppression logic.
- **SC-005**: Validate `state/runtime_log.yaml` shows total time <= 6h.
- **SC-006**: Validate `state/artifact_hashes.yaml` matches `state/artifact_hashes` in project state.

## Risk Management

- **Risk**: NPPN data unavailable.
  - **Mitigation**: Pipeline halts (no synthetic fallback).
- **Risk**: Phylogenetic tree fetch fails.
  - **Mitigation**: Pipeline halts (PVR is impossible without a tree).
- **Risk**: N < 55 species.
  - **Mitigation**: T003 halts pipeline with critical error.
- **Risk**: No independent proxy found.
  - **Mitigation**: T027b/T028 skip; report framed as 'associational physiological state prediction'.