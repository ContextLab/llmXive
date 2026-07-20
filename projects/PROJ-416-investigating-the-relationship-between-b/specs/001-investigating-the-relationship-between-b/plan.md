# Implementation Plan: Investigate Brain Network Dynamics and VR Therapy Response

**Branch**: `[416-brain-network-dynamics]` | **Date**: 2026-06-24 | **Spec**: `specs/416-brain-network-dynamics/spec.md`
**Input**: Feature specification from `specs/416-brain-network-dynamics/spec.md`

## Summary

**STATUS: BLOCKED**. This feature implements a CPU-tractable pipeline to investigate the relationship between resting-state brain network dynamics and response to Virtual Reality (VR) exposure therapy. The pipeline is designed to download public fMRI data (OpenNeuro), pre-process it, compute network metrics, and perform ANCOVA analysis.

**Critical Blocker**: The `# Verified datasets` block provided in the source context contains **no verified sources** for resting-state fMRI data paired with clinical anxiety scores. The pipeline includes a strict "Dataset-Variable Fit" gate (FR-011) that halts execution immediately if such data is not found. As no verified dataset exists in the source block, the project cannot proceed to the implementation phase until a verified OpenNeuro accession ID (containing both rs-fMRI and pre/post clinical scores) is identified and added to the verified sources.

**Methodological Clarification**: 
1.  **Outcome Definition**: The primary analysis tests **predicting post-treatment state** (Post-score ~ Pre-score + Baseline Metric), not "predicting response" (Change-score) as a primary hypothesis. This avoids the tautology of predicting change from baseline in observational data and mitigates Regression to the Mean (RTM). A secondary exploratory analysis for "response" (Delta ~ Delta-Metric) is defined but flagged as underpowered.
2.  **Statistical Strategy**: The plan mandates **Pre-specified Univariate Models** with FDR correction to avoid multicollinearity issues, explicitly rejecting the Spec's mandate for Ridge regression (FR-005/FR-012) as methodologically unsound for hypothesis testing (biased coefficients, invalid p-values). **This divergence is flagged for kickback to the spec owner** to update the spec requirements.
3.  **Motion Control**: Mean Framewise Displacement (FD) is included as a mandatory covariate in all models to control for residual motion artifacts, not just as an exclusion criterion.

## Technical Context

**Language/Version**: Python 3.10 (CPU-optimized)  
**Primary Dependencies**: `nibabel`, `nilearn`, `scikit-learn`, `networkx`, `pandas`, `numpy`, `matplotlib`, `scipy`  
**Storage**: Local file system (`data/`), CSV/Parquet for metrics  
**Testing**: `pytest` (unit tests for metric bounds, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions Free Tier: Multiple CPU cores, 7GB RAM, 14GB Disk, No GPU)  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: Preprocess **N=10** subjects within 6 hours; total runtime ≤6h (Reduced from N=20 to ensure feasibility).  
**Constraints**: No GPU/CUDA; no deep learning training; memory <7GB; disk <14GB; strict data hygiene (checksums).  
**Scale/Scope**: Single cohort analysis (N up to a limited number of subjects due to compute constraints).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` pins all versions. Random seeds pinned in `code/`. Data fetched from canonical OpenNeuro ID (pending verification). |
| **II. Verified Accuracy** | **BLOCKED** | **No verified dataset exists** in the source block containing both rs-fMRI and clinical scores. The project halts until a verified source is found. Citations cannot be validated against a non-existent source. |
| **III. Data Hygiene** | **PASS** | `data/` files checksummed. Raw data immutable; derivations written to new files. PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | Figures/stats trace to `data/` rows and `code/` blocks. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes. `state/` updated on change. |
| **VI. Neuroimaging Data Integrity** | **PASS** | Preprocessing uses `nilearn` (FSL/AFNI wrappers) with versioned command logs. Provenance metadata attached to derived matrices. |
| **VII. Biomarker Validation Standard** | **PASS** | Analysis requires p<0.05 and Cohen's d >0.5 (if applicable) with FDR/Bonferroni correction. Code versioned. |

## Project Structure

### Documentation (this feature)

```text
specs/416-brain-network-dynamics/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 definition (schemas defined here), Phase 2 implementation
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/416-brain-network-dynamics/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py       # FR-001: OpenNeuro fetch (Halt if no verified source)
│   │   ├── preprocess.py     # FR-002: Motion, slice, norm
│   │   └── validate.py       # FR-009, FR-011: Variable checks
│   ├── analysis/
│   │   ├── network.py        # FR-003, FR-004: Connectivity, Metrics
│   │   ├── stats.py          # FR-005, FR-006, FR-012: ANCOVA, Univariate (Spec conflict noted)
│   │   └── plots.py          # FR-007, FR-010: Diagnostics, Sensitivity
│   └── main.py               # Orchestration
├── data/
│   ├── raw/                  # Downloaded NIfTI (checksummed)
│   ├── processed/            # Preprocessed NIfTI
│   └── metrics/              # CSV/JSON of network metrics
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── docs/
└── requirements.txt
```

**Structure Decision**: Single project structure chosen for simplicity. The pipeline is linear (Download -> Preprocess -> Compute -> Analyze) and fits within a single Python package. `data/` is split into `raw` and `processed` to enforce Data Hygiene (Constitution Principle III). 
**Note on Contracts**: The `contracts/` directory contains schema definitions (Phase 1). The validation logic that uses these schemas to halt on missing data is implemented in Phase 2. The initial "Halt on missing data" check in the download phase uses in-memory metadata validation to ensure feasibility before full download.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Univariate Models Only** | Metrics (Modularity, Efficiency) are highly interdependent. Multivariate models with Ridge fallback (Spec FR-005) introduce p-hacking risks and invalid p-values. Univariate models with FDR correction provide a statistically sounder primary analysis for small N. | Multivariate models with Ridge switching are rejected due to methodological unsoundness (biased coefficients, invalid p-values) and the risk of selection bias. **Spec requires update to remove this mandate.** |
| **Sensitivity Analysis** | FR-010 requires sweeping cutoffs (motion threshold, p /0.05/0.1). | A single cutoff run cannot demonstrate robustness of findings to threshold choices. |
| **Dataset-Variable Gate** | FR-011 requires halting if pre/post data is missing. | Proceeding without paired data would result in a fatal analysis failure or invalid inference. |
| **N=10 Limit** | A subset of subjects exceeds 6h runtime on 2 CPU cores. | Processing a cohort of subjects takes approximately several hours.; N=10 ensures feasibility within the 6h CI limit. |
