# Implementation Plan: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

**Branch**: `001-network-structure-avalanche-dynamics` | **Date**: 2026-06-25 | **Spec**: `specs/001-network-structure-avalanche-dynamics/spec.md`
**Input**: Feature specification from `/specs/001-network-structure-avalanche-dynamics/spec.md`

## Summary

This project investigates the associational relationship between anatomical brain network properties (degree, clustering, rich-club) derived from diffusion MRI and neural avalanche dynamics (size, duration, power-law exponents) derived from resting-state EEG. **Critical Scope Note**: The original specification assumed the availability of matched dMRI and EEG data from the same participants (e.g., HCP-Aging). However, verification of open sources confirms that **no matched dMRI+EEG dataset exists** in verified open repositories (OpenNeuro, HuggingFace) for the required number of participants.

Consequently, this project **cannot** perform a biological structure-function coupling analysis on real data. The scope is revised to a **Pipeline Validation Study**. The implementation will:
1.  Download available *separate* dMRI and EEG datasets to validate the preprocessing pipelines individually.
2.  Implement the metric computation (graph metrics, avalanche statistics) on these separate datasets.
3.  **Suspend** the biological statistical association (FR-006/007) for real data due to N=0 matched subjects.
4.  **Validate** the statistical logic (correlation, permutation, VIF) via **Unit Tests** using *synthetic data with known ground truth* (injected coupling), not random pairings of real data.

This approach ensures scientific rigor by avoiding spurious correlations from invalid data pairings while still delivering a robust, validated analysis pipeline.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne`, `nibabel`, `networkx`, `powerlaw`, `numpy`, `pandas`, `scipy`, `bids`, `pytest`  
**Storage**: Local file system (`data/raw/`, `data/processed/`, `data/results/`)  
**Testing**: `pytest` (unit tests for metric computation, integration tests for pipeline flow, unit tests for statistical logic with ground truth)  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 vCPU, ~7 GB RAM, Substantial disk space requirements, ≤6 h)  
**Project Type**: Computational Neuroscience Pipeline / Research Script / Validation Study  
**Performance Goals**: Process ≥50 participants (or available subset) within 6 hours; memory usage <6 GB peak.  
**Constraints**: No local GPU; no internet access to gated databases (ADNI, HCP); strict data hygiene (checksums, no PII).  
**Scale/Scope**: Single-modality processing (dMRI + EEG) with cross-modal association analysis **suspended for real data**; statistical logic validated via synthetic ground truth.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All random seeds pinned in `code/utils/seed.py`. `requirements.txt` pins versions. Pipeline is fully scripted. **Note**: Biological results are not reproducible due to data absence; pipeline logic is reproducible via unit tests. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` restricted to the "Verified datasets" block provided in the prompt. No fabricated URLs. |
| **III. Data Hygiene** | PASS | `data/raw/` stores immutable downloads. Checksums recorded in `state/...yaml`. Derived files get new names. |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/results/`. No hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | PASS | Content hashes tracked. `updated_at` timestamps updated on artifact changes. |
| **VI. Neuroimaging Data Integrity** | PASS | MRtrix3 and MNE-Python versions pinned. Raw files preserved. Derivations documented. |
| **VII. Statistical Rigor** | PASS | Spearman + Permutation (≥1000 shuffles) implemented. VIF diagnostics included. Power-law model comparison enforced. **Note**: Applied to synthetic ground truth for validation; suspended for real data. |

## Project Structure

### Documentation (this feature)

```text
specs/001-network-structure-avalanche-dynamics/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Handles OpenNeuro/HF dataset fetching
│   ├── preprocess_dMRI.py   # MRtrix3 pipeline (tck2connectome)
│   └── preprocess_EEG.py    # MNE-Python pipeline (filter, ICA, threshold)
├── analysis/
│   ├── network_metrics.py   # Degree, clustering, rich-club (NetworkX)
│   ├── avalanche_metrics.py # Detection, power-law fitting (powerlaw)
│   └── stats.py             # Spearman, Permutation, VIF, Sensitivity
├── utils/
│   ├── seed.py              # Global RNG seeds
│   └── io.py                # BIDS/CSV loaders
├── cli/
│   └── run_pipeline.py      # Main entry point

tests/
├── contract/
│   ├── test_schema_validation.py
├── integration/
│   └── test_pipeline_end_to_end.py
└── unit/
    ├── test_network_metrics.py
    ├── test_avalanche_fitting.py
    └── test_statistical_association.py  # NEW: Validates logic with ground truth
```

**Structure Decision**: Single project structure chosen for scientific pipeline simplicity. All logic is modularized in `src/` to allow for unit testing of individual components (e. g., avalanche detection) without running the full download/preprocess loop.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Cross-Modal Integration** | Requires matching dMRI and EEG from the *same* subjects. | A single-modality study fails the research question (Structure-Function coupling). **However**, since matched data is unavailable, we pivot to *separate* modality testing + synthetic validation. |
| **Permutation Testing** | Required for robustness against non-parametric distributions. | Standard parametric t-tests assume normality which avalanche exponents rarely satisfy. |
| **VIF Diagnostics** | Degree and Clustering are mathematically correlated. | Ignoring collinearity leads to spurious claims of independent effects (FR-009). |

## Phase Plan

### Phase 0: Data Acquisition & Validation (FR-001, FR-002)
- **Goal**: Download and verify integrity of dMRI and EEG datasets.
- **Action**: Implement `download.py` to fetch from verified HuggingFace sources (OpenNeuro fslr64k, Neurofusion EEG).
- **Constraint**: **Data Availability Block**: No matched dataset exists. The plan downloads *separate* datasets to test individual pipelines.
- **Output**: `data/raw/` with checksums. **Note**: FR-001 and FR-002 requirements for specific matched datasets (ds004230/31) are **unmet** due to data unavailability.

### Phase 1: Preprocessing (FR-001, FR-002)
- **Goal**: Generate structural connectivity matrices and cleaned EEG time series.
- **Action**:
  - **dMRI**: Run MRtrix3 `tck2connectome` to generate adjacency matrices (HCP-MMP parcellation) on available dMRI data.
  - **EEG**: Apply Low-frequency bandpass filtering (up to 40 Hz), downsample to a reduced sampling frequency, ICA artifact removal (MNE-Python) on available EEG data.
- **Output**: `data/processed/` (`.mat` or `.csv` matrices, `.npy` time series).

### Phase 2: Metric Computation (FR-003, FR-004, FR-005, FR-011)
- **Goal**: Compute graph metrics and avalanche statistics.
- **Action**:
  - **Graph**: Calculate mean degree, clustering, rich-club (NetworkX).
  - **Avalanche**: Z-score normalize, threshold at a high percentile, detect contiguous events.
  - **Fitting**: Fit power-law, exponential, log-normal. Retain exponent ONLY if power-law is preferred (Likelihood Ratio Test).
- **Output**: `data/results/metrics.csv`.

### Phase 3: Statistical Association (FR-006, FR-007, FR-008, FR-009, FR-010)
- **Goal**: **Suspended for Real Data**. Validate statistical logic via Unit Tests.
- **Action**:
  - **Real Data**: **No association analysis** will be performed on real data due to N=0 matched subjects. This is explicitly documented as a deviation from FR-006/007 for real data.
  - **Validation**: Run `tests/unit/test_statistical_association.py` using **synthetic data with known ground truth** (injected coupling).
    - Verify Spearman correlation detects the injected coupling.
    - Verify Permutation test correctly identifies significance.
    - Verify VIF diagnostics correctly flag collinearity.
    - Verify Sensitivity analysis works across thresholds.
  - **Framing**: The final report will state: "Biological association analysis suspended due to data unavailability. Statistical pipeline validated via unit tests on synthetic ground truth."
- **Output**: `tests/unit/test_statistical_association.py` results (pass/fail), `data/results/collinearity_status.json` (from synthetic test).

### Phase 4: Reporting & Validation (SC-001 to SC-006)
- **Goal**: Generate final report and validate against success criteria.
- **Action**: Aggregate results, generate plots, write `report.md`.
- **Check**: Verify runtime <6h, memory <7GB, all FR/SC covered (with FR-006/007 marked as 'Deferred' for real data).
- **Success Criteria Revision**:
  - SC-001/SC-003: Measured as "Pipeline correctly computes correlation/permutation on synthetic ground truth" (not biological correlation).
  - SC-004: Data quality measured by proportion of participants with complete *individual* pipelines (dMRI and EEG separately).

## FR/SC Compliance Table (Updated)

| ID | Requirement | Status | Notes |
| :--- | :--- | :--- | :--- |
| FR-001 | Download ds004230 | **Deferred** | Dataset unavailable in verified sources. |
| FR-002 | Download ds004231 | **Deferred** | Dataset unavailable in verified sources. |
| FR-003 | Compute graph metrics | **Active** | Executed on available dMRI data. |
| FR-004 | Detect avalanches | **Active** | Executed on available EEG data. |
| FR-005 | Fit power-law | **Active** | Executed on available EEG data. |
| FR-006 | Spearman correlation | **Deferred (Real)** | **Active (Unit Test)** on synthetic ground truth. |
| FR-007 | Permutation test | **Deferred (Real)** | **Active (Unit Test)** on synthetic ground truth. |
| FR-008 | Sensitivity analysis | **Active (Unit Test)** | Validated on synthetic data. |
| FR-009 | VIF diagnostics | **Active (Unit Test)** | Validated on synthetic data. |
| FR-010 | Associational framing | **Active** | Explicitly stated in report. |
| FR-011 | Model comparison | **Active** | Executed on available EEG data. |
| SC-001 | Correlation measurement | **Active (Unit Test)** | Validated on synthetic ground truth. |
| SC-003 | Permutation correction | **Active (Unit Test)** | Validated on synthetic ground truth. |
| SC-004 | Data quality | **Active** | Measured on individual pipelines. |
| SC-006 | Compute feasibility | **Active** | Target <6h. |