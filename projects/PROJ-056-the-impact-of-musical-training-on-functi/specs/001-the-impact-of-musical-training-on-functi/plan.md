# Implementation Plan: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

**Branch**: `001-musical-training-connectivity` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-musical-training-connectivity/spec.md`
**Status**: **BLOCKED ON DATA** (Prototype/Validation Phase Only)

## Summary

This project implements a computational pipeline to investigate the association between musical training history and resting-state functional connectivity (rs-fc) in adolescent brains. The system ingests neuroimaging and behavioral data, computes connectivity matrices for auditory, motor, and executive control networks, and performs robust statistical comparisons between "musician" (≥1 year training) and "non-musician" groups. The analysis includes Network-Based Statistic (NBS) for topological validation, correlation analysis with training duration, and sensitivity checks across significance thresholds.

**CRITICAL SCOPE NOTE**: Due to the absence of a verified real-world dataset (ABCD/HCP-Adolescents) in the provided "Verified datasets" block, this project is currently in a **Prototype/Validation Phase**. The pipeline is implemented and tested using **synthetic data** strictly for **Software Verification** (code correctness, memory constraints, and statistical logic). **No scientific results** regarding biological effects of musical training are claimed or generated in this phase. The project will transition to "Scientific Validation" only upon sourcing a verified, compliant dataset.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `nibabel`, `networkx`, `matplotlib`, `seaborn`, `pyyaml`, `statsmodels`  
**Storage**: Local file system (`data/` for raw/processed, `code/` for scripts), CSV/Parquet for tabular data, NIfTI for imaging.  
**Testing**: `pytest` (unit tests for data filters, statistical outputs; integration tests for pipeline end-to-end on synthetic data).  
**Target Platform**: Linux (GitHub Actions runner).  
**Performance Goals**: Total runtime ≤ 6 hours; Peak memory ≤ 7 GB; No GPU usage.  
**Constraints**: 
- **Dataset Fit**: The spec requires "years of musical training" and "resting-state fMRI" from ABCD/HCP. The verified datasets block contains *no* verified source for HCP-Adolescents and only generic/unrelated files for "ABCD". 
- **Compute**: No CUDA, no large model loading. Connectivity computed via Pearson correlation on CPU.
- **Data Volume**: Data must be sampled/subsetted to fit 7GB RAM.
- **Execution Modes**: 
  - `Verification Mode` (Default): Uses synthetic data to verify code execution and statistical logic. **No scientific claims.**
  - `Analysis Mode`: Requires a verified real dataset path. Halts with `Data Source Missing` if path is invalid or data is absent.

> **Critical Constraint Note**: The pipeline defaults to `Verification Mode` (synthetic data) to ensure the codebase is functional and reproducible. However, the `Analysis Mode` (real data) is fully implemented and documented to satisfy FR-001. The project is **blocked** on scientific validation until a verified dataset is sourced.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. `requirements.txt` pinned. Pipeline runs on fresh runner. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` are limited to verified URLs or explicit "NO VERIFIED SOURCE" statements. Synthetic results are explicitly labeled as "Simulation". |
| **III. Data Hygiene** | **PASS** | Raw data (simulated or real) checksummed. No in-place modification. PII scan enabled. |
| **IV. Single Source of Truth** | **PASS** | All stats derived from `data/` artifacts. No hand-typed numbers in paper. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in state YAML. |
| **VI. Neuroimaging Data Integrity** | **PASS** | Raw NIfTI preserved (simulated or real). Preprocessing parameters logged. |
| **VII. Behavioral Assessment** | **PASS** | "Years of training" derived via script from raw input. |

## Project Structure

### Documentation (this feature)

```text
specs/001-musical-training-connectivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── subject.schema.yaml
    ├── connectivity.schema.yaml
    └── statistical_result.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-056-the-impact-of-musical-training-on-functi/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # Data ingestion (real or synthetic)
│   │   ├── preprocess.py        # Filtering, matching, confounder handling
│   │   ├── synthetic_generator.py # Data generation for validation (Null-First)
│   │   └── mock_nifti.py        # Mock NIfTI generator for format testing
│   ├── analysis/
│   │   ├── connectivity.py      # Pearson corr, Fisher z-transform
│   │   ├── stats.py             # Welch's t-test, FDR, NBS
│   │   ├── correlation.py       # Training duration correlation, sensitivity
│   │   └── sensitivity.py       # Confounder sensitivity analysis
│   ├── utils/
│   │   ├── logging.py
│   │   └── memory_monitor.py
│   └── main.py                  # Entry point
├── data/
│   ├── raw/                     # Raw NIfTI/CSV (if available)
│   ├── processed/               # Cleaned CSVs, Connectivity matrices
│   └── checksums.txt
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── README.md
```

**Structure Decision**: Single project structure. The `code/` directory is modularized by functional domain (data, analysis, utils) to ensure separation of concerns and testability. This aligns with the requirement for a reproducible research pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Synthetic Data Generator (Null-First)** | Real ABCD/HCP data is unavailable. A robust pipeline must be testable. | A pipeline that only runs on real data cannot be validated during CI/CD or unit testing without external dependencies. The "Null-First" approach ensures we test the *absence* of signal, not just the presence. |
| **NBS Implementation** | FR-008 requires Network-Based Statistic for topological validation. | Standard t-tests on individual edges do not account for the network structure (family-wise error at component level). |
| **Memory Monitor** | FR-006 mandates ≤7GB RAM. | Without active monitoring, large matrices (N=400 ROIs) could exceed RAM if not chunked or sampled. |
| **Confounder Sensitivity Analysis** | FR-009 requires robust confound control. | Simple regression is insufficient for unmeasured confounding. Sensitivity analysis quantifies the robustness of results. |

## Phase Plan

### Phase 0: Research & Data Strategy
- **Goal**: Confirm data availability, define statistical power, and establish the "Prototype" status.
- **Action**: 
  1. Verify the "Verified datasets" block. **Result**: HCP-Adolescents has NO verified source. ABCD entries are invalid/unrelated.
  2. **Decision**: The pipeline will be implemented to accept a **verified** dataset path if provided later, but for the current implementation, it will generate **synthetic data** that mimics the statistical properties of the target study to validate the code.
  3. **Scientific Scope Statement**: This phase is **Software Verification Only**. No scientific claims regarding musical training effects will be made. The project is **BLOCKED** on scientific validation until a verified dataset is sourced.
  4. **Synthetic Strategy**: 
     - **Primary Test (Null-First)**: Generate data with **NO** injected effect to verify the pipeline correctly returns non-significant results (Type I error control).
     - **Secondary Test (Stress)**: Generate data with a **known, independent** effect (not hard-coded to group labels) to verify code robustness and NBS detection logic.
  5. Document the "Dataset Fit" gap in `research.md`.
  6. Define the simulation parameters (N=150, 75 per group) to meet power requirements (d=0.5).

### Phase 1: Data Model & Contracts
- **Goal**: Define schemas for subjects, connectivity, and results.
- **Action**: 
  1. Create `contracts/` YAML schemas.
  2. Implement `Subject` and `ConnectivityMatrix` data structures.
  3. **Mandatory**: Ensure code validates against `contracts/subject.schema.yaml`, `contracts/connectivity.schema.yaml`, and `contracts/statistical_result.schema.yaml` before proceeding to Phase 2.

### Phase 2: Implementation (Data & Analysis)
- **Goal**: Build the pipeline with dual execution paths.
- **Action**: 
  1. **Data Ingestion**: 
     - Implement `download.py` to load from a local path (real data) OR generate synthetic data.
     - Implement `mock_nifti.py` to generate mock NIfTI files for format testing (US-1).
     - **Real Data Path**: Implement "compliant access workflows" (e.g., `abcd-data` package) for FR-001. If data is missing, raise `Data Source Missing` error.
  2. **Preprocessing**: 
     - Implement `preprocess.py` for filtering (≥1 year) and matching (age/sex).
     - **Confounder Handling**: Implement **Propensity Score Matching (PSM)** and **Linear Regression with Residualization** to satisfy FR-009 (matching OR regressing).
  3. **Connectivity**: Implement `connectivity.py` using `numpy` for Pearson correlation and Fisher z-transform.
     - **Double-Dipping Prevention**: Ensure atlas (Schaefer) is pre-defined and fixed *a priori*.
  4. **Statistics**: 
     - Implement `stats.py` with `scipy.stats` for Welch's t-test, `statsmodels` for FDR, and a custom NBS implementation (permutation-based) that fits in RAM.
     - Implement **Power Analysis for NBS** to estimate detectable effect sizes.
  5. **Correlation**: Implement `correlation.py` for training duration correlation and sensitivity analysis.
  6. **Sensitivity**: Implement `sensitivity.py` for confounder sensitivity analysis (continuous outcome).
  7. **Memory**: Add `memory_monitor.py` to log peak usage.

### Phase 3: Validation & Testing
- **Goal**: Ensure correctness and constraints.
- **Action**: 
  1. Run unit tests on synthetic data (a representative cohort of subjects)..
  2. Run integration test (full pipeline on a set of synthetic subjects).
  3. **Contract Validation**: Verify output schemas match `contracts/`.
  4. Verify memory < 7GB and runtime < 6h.
  5. **Null-First Test**: Verify that synthetic data with NO effect yields non-significant results (Type I error control).

### Phase 4: Documentation & Handoff
- **Goal**: Finalize `quickstart.md` and `research.md`.
- **Action**: 
  1. Document how to swap synthetic data for real data (if verified source becomes available).
  2. Ensure `research.md` explicitly states the dataset limitation and the "Prototype" status.
  3. **Success Criteria Update**: SC-005 is conditionally satisfied by "Code Correctness on Synthetic Null Data" in this phase. It will be re-evaluated if real data is sourced.
