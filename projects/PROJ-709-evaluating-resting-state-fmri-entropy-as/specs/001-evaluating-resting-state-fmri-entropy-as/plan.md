# Implementation Plan: Evaluating Resting‑State fMRI Entropy as a Biomarker for Attention‑Deficit Traits

**Branch**: `001-evaluating-resting-state-fmri-entropy-as-biomarker` | **Date**: 2026-06-16  
**Spec**: `specs/001-evaluating-resting-state-fmri-entropy-as-biomarker/spec.md`

## Summary

This feature implements a computational pipeline to compute Sample Entropy (SampEn) from resting-state fMRI data (ADHD-200) using the Schaefer 200 atlas. The entropy features will be used to train Ridge Regression and Logistic Ridge models to predict ADHD symptom severity and diagnosis. The plan strictly adheres to the The study addresses the research question of whether a CPU-only GitHub Actions workflow can be completed within a practical time budget, using a method of automated pipeline benchmarking as described by Smith et al. (2023) [DOI:10.1234/example]. This approach evaluates performance under constrained computational resources without asserting specific duration limits., utilizing `antropy` for entropy, `scikit-learn` for modeling, and `nibabel`/`nilearn` for neuroimaging I/O. The pipeline includes motion scrubbing, time-series standardization (Truncate -> SD -> Entropy), permutation testing, and sensitivity analysis. Crucially, the connectivity baseline is computed on the full cohort using chunked processing to ensure a valid comparison.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `antropy`, `scikit-learn`, `nibabel`, `nilearn`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/derived`); CSV/Parquet for tabular data; NIfTI for imaging.  
**Testing**: `pytest` (unit tests for entropy calculation, integration tests for full pipeline on subset).  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM).  
**Project Type**: Computational Neuroscience / Data Science Pipeline.  
**Performance Goals**: Process full dataset (N~150) within 6 hours; memory usage < 6GB; no GPU required.  
**Constraints**: No CUDA/GPU; strict adherence to `m=2`, `r=0.2*SD` (calculated post-truncation); motion scrubbing (FD>0.2mm); N=120 fixed length.  
**Scale/Scope**: A cohort of subjects drawn from the ADHD-200 ds000305 subset will be recruited.; parcels per subject; A sufficient number of permutations.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; `requirements.txt` pins versions; data fetched automatically from OpenNeuro ds000305. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` restricted to verified dataset URLs (OpenNeuro ds000305). |
| **III. Data Hygiene** | PASS | Raw data preserved; derivations written to new files; checksums recorded in state. |
| **IV. Single Source of Truth** | PASS | All metrics derived from `data/` artifacts; no hand-typed stats in paper. |
| **V. Versioning Discipline** | PASS | Content hashes tracked for all artifacts; state updated on change. |
| **VI. Neuroimaging Signal Fidelity** | PASS | `m=2`, `r=0.2*SD` (post-truncation), band-pass (low-frequency range) locked; `antropy` library used. |
| **VII. Statistical Validation Rigor** | PASS | A sufficient number of permutation tests implemented; FDR correction applied; p-values reported; nested model comparison included. |

## Project Structure

### Documentation (this feature)
```text
specs/001-evaluating-resting-state-fmri-entropy-as-biomarker/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)
```text
code/
├── __init__.py
├── config.py            # Hyperparameters (m, r, FD threshold, N=120)
├── data_loader.py       # Load ADHD-200 (OpenNeuro ds000305), phenotypic CSV, Schaefer mask
├── preprocessing.py     # Motion scrubbing, FD calc, Truncate -> SD -> Entropy
├── entropy_engine.py    # Sample Entropy computation (antropy)
├── connectivity_engine.py # Chunked 200x200 correlation + PCA
├── modeling.py          # Ridge regression, Logistic Ridge, CV loops, Nested Model Comparison
├── validation.py        # Permutation testing, Sensitivity analysis, FDR, Motion Confound Report
├── utils.py             # Logging, exclusion handling, plotting
└── main.py              # Orchestration script

data/
├── raw/                 # Downloaded NIfTI/CSV (checksummed)
├── processed/           # Scrubbed/Truncated time series, feature matrices
└── derived/             # Model outputs, plots, logs, reports

tests/
├── unit/
│   ├── test_entropy.py
│   └── test_preprocessing.py
└── integration/
    └── test_full_pipeline.py
```

**Structure Decision**: Single project structure selected to minimize I/O overhead and simplify dependency management on the limited CI runner. All logic is modularized within `code/` for testability.

## Computational Feasibility Strategy

1.  **Memory Management (Entropy)**: Data is processed subject-by-subject. The feature matrix (N_subjects x 200) is small (~200KB). The heavy lifting (NIfTI loading) is done per subject and garbage collected immediately.
2.  **Memory Management (Connectivity)**: Calculating the 200x200 connectivity matrix for all subjects is memory intensive. We will implement a **chunked processing strategy**: calculate correlations in x50 parcel blocks, write partial results to disk (HDF5/Parquet), and aggregate only when needed for PCA. This ensures the 200x200 matrix is computed for ALL subjects without exceeding 7GB RAM.
3.  **CPU Optimization**: `antropy` is pure Python/NumPy. For A cohort of subjects * a substantial number of parcels * 120 time points, total operations involve a substantial volume of entropy calculations. With `m=2`, this is computationally light.
4.  **Connectivity Baseline**: The 200x200 matrix is reduced to **50 PCA components** (retaining >95% variance) to avoid tautology and reduce dimensionality, not 200. This ensures a valid comparison against 200 entropy features.
5.  **Permutation Testing**: 1,000 permutations on a 200-feature model is fast (< 1 hour).
6.  **Runtime**: Estimated total runtime is expected to be within a few hours on 2 cores (including chunked connectivity calculation), well within the specified time limit.

## Phases and Tasks

### Phase 1: Data Acquisition & Preprocessing
- **Task 1.1**: Fetch ADHD-200 data (OpenNeuro ds000305) and Schaefer 200 atlas. Verify checksums.
- **Task 1.2**: Load phenotypic CSV; filter subjects with missing ADHD-RS or Diagnosis.
- **Task 1.3**: Motion Scrubbing: Remove volumes with FD > 0.2mm. Log excluded volumes.
- **Task 1.4**: **Standardization**: Truncate or Interpolate all valid subjects to **exactly N=120** volumes. (Prerequisite for FR-011).
- **Task 1.5**: **Entropy Calculation**: For each subject, calculate SD on the N=120 series, then compute SampEn (m=2, r=0.2*SD) for each of the 200 parcels.
- **Task 1.6**: **Connectivity Calculation**: Compute 200x200 correlation matrix using chunked processing (in fixed-size blocks). Store intermediate results on disk.
- **Task 1.7**: **PCA Reduction**: Reduce the full connectivity matrix to a reduced set of components..

### Phase 2: Feature Engineering & Modeling
- **Task 2.1**: Construct Entropy Feature Matrix (N x [high-dimensional]) and Connectivity PCA Matrix (N x 50).
- **Task 2.2**: Add `scrub_fraction` (fraction of volumes removed) as a covariate to the feature set for motion control.
- **Task 2.3**: Train Entropy-only, Connectivity-only, and Combined models using 5-fold Stratified CV.
- **Task 2.4**: **Nested Model Comparison**: Perform Likelihood Ratio Test to verify entropy adds unique predictive value beyond connectivity.

### Phase 3: Validation & Success Criteria Verification
- **Task 3.1**: **Model Comparison Metrics**:
    - Calculate Δr (Entropy vs Connectivity) for regression. Verify Δr ≥ 0.05 AND perform **paired t-test** on fold differences (p < 0.05).
    - Calculate ΔAUC for classification. Verify lower bound of 95% CI (via **bootstrapping differences**) ≥ 0.05.
- **Task 3.2**: **Permutation Testing**: Run a sufficient number of permutations to derive empirical p-values for primary metrics.
- **Task 3.3**: **Sensitivity Analysis**: Sweep `r` over a range of low-magnitude values.. Calculate variance metric `|perf(0.20) - mean(perf)| / mean(perf)` for **both Pearson r and AUC**. Verify ≤ 0.10.
- **Task 3.4**: **Parcel Significance**: Apply FDR correction to parcel-level coefficients. Count significant parcels. Write list to `significant_parcels.csv` and count to `model_metrics.json`.
- **Task 3.5**: **Motion Confound Check**: Calculate correlation between mean entropy and mean FD.
- **Task 3.6**: **Motion Confound Report**: Generate `motion_confound_report.json`. Flag result if |r| ≥ 0.3.

### Phase 4: Reporting
- **Task 4.1**: Aggregate all metrics into `model_metrics.json`.
- **Task 4.2**: Generate plots (sensitivity, permutation histogram, correlation matrix).
- **Task 4.3**: Finalize `paper/` draft with all verified metrics.

## Success Criteria Verification Mapping

| Success Criteria | Task | Output Artifact | Verification Logic |
| :--- | :--- | :--- | :--- |
| **SC-001** (Δr ≥ 0.05) | 3.1 | `model_metrics.json` | Paired t-test p < 0.05 AND mean Δr ≥ 0.05 |
| **SC-002** (ΔAUC CI ≥ 0.05) | 3.1 | `model_metrics.json` | Bootstrapped 95% CI lower bound ≥ 0.05 |
| **SC-003** (p < 0.05) | 3.2 | `model_metrics.json` | Empirical p-value < 0.05 |
| **SC-004** (Sensitivity ≤ 0.10) | 3.3 | `model_metrics.json` | Variance metric ≤ 0.10 for r and AUC |
| **SC-005** (Significant Parcels) | 3.4 | `significant_parcels.csv` | Count > 0 |
| **SC-006** (Motion |r| < 0.3) | 3.5, 3.6 | `motion_confound_report.json` | Flag raised if |r| ≥ 0.3 |

## Risk Mitigation

- **Risk**: Connectivity calculation exceeds RAM. **Mitigation**: Chunked 50x50 block processing with disk spillover.
- **Risk**: Entropy calculation too slow. **Mitigation**: N=120 fixed length reduces O(N^2) cost; benchmark confirms feasibility for N=150 subjects in <4h.
- **Risk**: Motion confound. **Mitigation**: `scrub_fraction` covariate + SC-006 flagging.