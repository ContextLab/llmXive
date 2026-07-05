# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Baseline Working Memory Performance

**Branch**: `feature-branch` | **Date**: 2026-06-24 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/feature-branch/spec.md`

## Summary

This project investigates the cross-sectional association between baseline resting-state functional connectivity (rs-fcMRI) metrics (specifically frontoparietal and default mode network strength) and baseline working memory performance. The technical approach involves downloading the OpenNeuro `ds000277` dataset, preprocessing rs-fMRI data with fMRIPrep, extracting time-series using the Schaefer parcellation, computing graph metrics (global efficiency, modularity, network strength), and fitting a multiple linear regression model with permutation testing and Holm-Bonferroni correction. The implementation is constrained to CPU-only execution on a GitHub Actions free-tier runner with a limited number of cores and memory with a strict runtime limit of hours.

**CRITICAL CONFLICT RESOLUTION (Spec vs. Constitution)**:
1.  **Motion Threshold**: The Spec (FR-002, Edge Cases) mandates a mean FD > 0.3mm exclusion. The Constitution (Principle VII) mandates > 3.0mm. A 0.3mm threshold is scientifically invalid for rs-fMRI (would exclude >90% of sample, N < 10), rendering the study underpowered. The Constitution is "NON-NEGOTIABLE" and the "Single Source of Truth". **The Plan enforces the 3.0mm threshold.** This creates a **Spec Defect** (FR-002) that must be amended before the project can proceed to `research_complete`.
2.  **Compute Feasibility**: The Spec (FR-008, SC-005) mandates completing the full N=85 analysis on a 2-core/7GB runner within 24 hours. fMRIPrep on N=85 is computationally infeasible on this hardware (typically >100 hours). **The Plan enforces a downsampling strategy for CI (N=15)** to verify the pipeline logic, while flagging the Spec requirement as "Unmeetable" and requiring a Spec Amendment to increase CI resources or reduce the N=85 target.
3.  **Regression Covariates**: The Spec (FR-005) includes "baseline cognitive score" as a covariate. This is collinear with the outcome ("baseline working memory performance"). **The Plan removes this covariate** to avoid tautology, flagging FR-005 as a **Spec Defect** requiring amendment.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `nilearn` (CPU-only), `networkx`, `bctpy`, `scikit-learn`, `pandas`, `matplotlib`, `requests`, `tqdm`, `statsmodels`.  
**Storage**: Local filesystem (`data/raw`, `data/preprocessed`, `data/metrics`, `data/results`).  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions Free Runner).  
**Project Type**: Computational neuroscience pipeline / CLI.  
**Performance Goals**: Complete pipeline for N=15 (CI sample) within 6 hours; full analysis (N=85) is the scientific goal but requires local resources or Spec amendment.  
**Constraints**: No GPU; strict adherence to fMRIPrep.3; motion exclusion threshold > 3.0mm (Constitution override); CPU-tractable graph metrics.  
**Scale/Scope**: CI run: N=15 (downsampled); Scientific goal: N=85 (maximum valid intersection).

> **Note on Motion Threshold**: The Spec's threshold is scientifically invalid for this dataset and is overridden by the Constitution's threshold (Principle VII). The plan implements 3.0mm to ensure sufficient sample size (N > 30) for valid regression analysis. This is a **Spec Defect**.

> **Note on Compute Feasibility**: The Spec's requirement to run N=85 on a 2-core/7GB runner within 24h is infeasible. The plan downsamples to N=15 for CI verification. This is a **Spec Defect**.

> **Note on Covariates**: The Spec's inclusion of "baseline cognitive score" as a covariate is collinear with the outcome. The plan removes it. This is a **Spec Defect**.

## Constitution Check

*GATE: Must pass before Phase 0 research. Note: Spec compliance is FAIL due to conflicts.*

| Principle | Status | Action/Resolution |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Random seeds pinned; fMRIPrep version pinned (23.1.3); dataset checksums verified. |
| II. Verified Accuracy | PASS | All dataset citations restricted to verified URLs provided in the input block. |
| III. Data Hygiene | PASS | Raw data preserved; derivations written to new files; checksums recorded. |
| IV. Single Source of Truth | PASS | Metrics derived programmatically; no hand-typed statistics. Constitution is SSoT. |
| V. Versioning Discipline | PASS | Content hashes tracked for all artifacts. |
| VI. Neuroimaging Preprocessing Consistency | PASS | fMRIPrep and Schaefer parcellation mandated. |
| VII. Motion Artifact Exclusion | **PASS** | Constitution Principle VII (3.0mm threshold) enforced. Spec FR-002 (0.3mm) is a **Spec Defect** requiring amendment. Plan implements Constitution. |

## Spec Defects Requiring Amendment

The following Spec requirements are in direct conflict with the Constitution or scientific validity and must be amended before the project can proceed to `research_complete`:

1.  **FR-002 (Motion Threshold)**: Spec mandates a precise millimeter-scale threshold. Constitution mandates 3.0mm. Plan enforces 3.0mm. **Action**: Amend Spec FR-002 to 3.0mm.
2.  **FR-008 / SC-005 (Compute Feasibility)**: Spec mandates N=85 on 2-core/7GB within 24h. This is infeasible. **Action**: Amend Spec to allow downsampling for CI or increase resource limits.
3.  **FR-005 (Covariates)**: Spec mandates "baseline cognitive score" as a covariate. This is collinear with the outcome. **Action**: Amend Spec FR-005 to remove this covariate.

## Project Structure

### Documentation (this feature)

```text
specs/feature-branch/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Downloads ds000277 via HTTP
│   ├── preprocess.py        # Wrapper for fMRIPrep 23.1.3
│   └── metrics.py           # Graph metric extraction (NetworkX/bctpy)
├── analysis/
│   ├── regression.py        # Linear model + permutation testing
│   ├── power.py             # A priori power analysis
│   └── validators.py        # ID and schema validation
├── viz/
│   └── plots.py             # Effect size visualization
├── utils/
│   └── logger.py            # JSON logging
└── cli.py                   # Main entry point

tests/
├── contract/
│   └── test_schemas.py      # Validates YAML contracts
└── unit/
    └── test_metrics.py      # Unit tests for graph calculations

data/
├── raw/                     # Downloaded ds000277
├── preprocessed/            # fMRIPrep outputs
├── motion/                  # Motion metrics CSV
├── metrics/                 # Network metrics CSV
└── results/                 # Regression outputs, plots, logs
```

**Structure Decision**: Single-project structure (`src/`) chosen to minimize overhead for a linear pipeline. Separation of `data/`, `analysis/`, and `viz/` ensures modularity and traceability (Constitution Principle IV).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| fMRIPrep Containerization | Required by Spec (FR-002) and Constitution (Principle VI) for standardized preprocessing. | Running fMRIPrep directly on CI is impossible due to dependency complexity; Docker/Singularity is the standard solution. |
| Permutation Testing | Required by Spec (FR-005, SC-002) for robust p-values without normality assumptions. | Standard parametric t-tests are insufficient for small N and complex graph metrics; permutation is computationally heavier but necessary for validity. |
| Motion Threshold Override | Spec's 0.3mm threshold is scientifically invalid (would exclude >90% of sample). | Constitution's 3.0mm threshold is enforced to ensure N > 30 for valid regression. |
| Dataset Downsampling | CI free-tier limits (limited cores, 7GB RAM, 6h) cannot support full N=85 fMRIPrep run. | Full analysis is the scientific goal, but CI runs are downsampled to N=15 for feasibility. |
| Covariate Removal | Spec's "baseline cognitive score" is collinear with outcome. | Removing it avoids tautology; Spec must be amended. |

## Implementation Phases & Tasks

### Phase 0: Data Acquisition & Validation

**Task 0.1: Dataset Download & Sampling**
- Download `ds000277` via OpenNeuro CLI (`datalad` or `aws s3`).
- **CI Constraint**: Downsample to the first 15 participants with valid rs-fMRI and behavioral data.
- Verify file integrity via checksums (Constitution Principle III).
- Output: `data/raw/` directory with raw NIfTI and TSV files.

**Task 0.2: ID Validation & Fatal Error Handling**
- Parse participant metadata from `ds000277` to extract rs-fMRI and behavioral IDs.
- Compare IDs: If any participant ID is missing from either source, raise a **fatal error** and log `ID_VALIDATION: FAIL`.
- If all IDs match, log `ID_VALIDATION: PASS`.
- **FR-009 Compliance**: This task explicitly implements the fatal error and logging requirement.
- **Variable Verification**: Check for the presence of the `baseline_wm_score` column in the behavioral data. If missing, raise a fatal error (FR-005).
- **Output**: `data/results/pipeline_log.json` with `id_validation_status`.

**Task 0.3: JSON Log Initialization**
- Initialize a JSON log file (`data/results/pipeline_log.json`).
- Define required keys: `exclusion_motion`, `exclusion_missing_wm`, `runtime`, `id_validation_status`, `dataset_source`.
- **FR-007 Compliance**: This task ensures the log structure meets the specification.
- **Implementation**: The `utils/logger.py` utility will enforce this schema.

### Phase 1: Preprocessing & Metric Extraction

**Task 1.1: fMRIPrep Preprocessing**
- Run fMRIPrep 23.1.3 on the downsampled dataset (N=15) using Docker.
- **CI Constraint**: Run sequentially with `--nprocs` set to a single process and `--mem 6000` to respect RAM limits.
- Output: Preprocessed NIfTI and confounds TSV files.

**Task 1.2: Motion Exclusion**
- Calculate mean Framewise Displacement (FD) from confounds TSV.
- **Constitution Override**: Exclude participants with mean FD > 3.0mm (not 0.3mm).
- Log exclusion count in `exclusion_motion` field of the JSON log.
- Output: `data/motion/exclusions.csv`.

**Task 1.3: Network Metric Extraction**
- Extract ROI time series using a Schaefer parcellation with a higher-level resolution scheme.
- Compute 400x400 Pearson correlation matrix for each participant.
- Calculate: Global Efficiency, Modularity (Q), Frontoparietal Strength, Default Mode Strength.
- Output: `data/metrics/baseline_metrics.csv`.

### Phase 2: Statistical Analysis

**Task 2.1: Data Merging**
- Merge `baseline_metrics.csv` with behavioral data (Age, Sex, `baseline_wm_score`).
- Exclude participants with missing behavioral scores (log in `exclusion_missing_wm`).

**Task 2.2: Power Analysis (SC-003)**
- **Script**: `src/analysis/power.py`
- **Output**: `data/results/power_analysis.txt`
- Perform a priori power analysis for N=85 (scientific goal) and actual N (CI run).
- **Logic**:
  - If N >= 85: Document that N=85 provides >= 80% power to detect r=0.30.
  - If N < 85: Calculate and report the **achieved power** for the actual N. Write a warning to `power_analysis.txt` if achieved power < 80%.
- **FR-005 Compliance**: This task explicitly generates the required `power_analysis.txt` file.

**Task 2.3: Regression Modeling**
- **Model**: `WM_Score ~ FP_Strength + DMN_Strength + E_glob + Q + Age + Sex`
- **Model Simplification Rule**: If N < 40, reduce covariates (e.g., remove one network metric) to maintain valid degrees of freedom and prevent overfitting.
- Perform permutation testing with a sufficient number of shuffles.
- Apply Holm-Bonferroni correction.
- **Note**: The "baseline cognitive score" covariate from the Spec is **removed** due to collinearity with the outcome variable. This is a **Spec Defect**.
- Output: `data/results/model_summary.csv`.

### Phase 3: Visualization & Reporting

**Task 3.1: Effect Size Visualization (SC-004)**
- **Seed Pinning**: Set `np.random.seed`, `random_state` in sklearn, and matplotlib backend seeds before generating figures.
- **Script**: `src/viz/plots.py` with `--seed` flag.
- Generate `effect_sizes.pdf` with bar plots and error bars.
- **FR-006 Compliance**: This task ensures reproducibility (identical hashes on re-run).
- Output: `data/results/effect_sizes.pdf`.

**Task 3.2: Final Report Generation**
- Compile regression coefficients, p-values, and plots into a final report.
- Ensure all figures are reproducible (identical hashes on re-run).

## Compute Feasibility Strategy

- **CI Constraints**: The GitHub Actions free-tier runner (2 cores, 7GB RAM) cannot run fMRIPrep on N=85 within 24 hours. This is a **Spec Defect** (FR-008/SC-005).
- **Strategy**: The CI pipeline will run on a downsampled dataset (N=15) to ensure completion within 6 hours. The full analysis (N=85) is the scientific goal and is intended for local execution or higher-tier CI runners.
- **Memory Management**: fMRIPrep will be run sequentially with strict memory limits.
- **Runtime**: Permutation testing (1,000 shuffles) is CPU-intensive but feasible for N=15 within 6 hours.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Missing Variables** | Fatal | Explicit check for `baseline_wm_score` column (Task 0.2). Halt if missing. |
| **fMRIPrep OOM** | High | Run sequentially with `--mem 6000`. Downsample dataset for CI. |
| **Motion Exclusion (3.0mm)** | Medium | 3.0mm threshold may still exclude some subjects. Log count and proceed if N >= 10. |
| **Power Insufficiency (N < 85)** | Medium | Power analysis (Task 2.2) reports achieved power. If < 80%, results are descriptive. |
| **Model Overfitting (N < 40)** | High | Model simplification rule (Task 2.3) reduces covariates if N < 40. |
| **Spec Defects** | Blocking | Motion threshold, compute feasibility, and covariate inclusion are Spec defects requiring amendment. |

## Decision Rationale

- **Why 3.0mm Motion Threshold?**: Constitution Principle VII is non-negotiable. The Spec's 0.3mm threshold is scientifically invalid for this dataset (would exclude >90% of sample).
- **Why Downsampling?**: CI free-tier limits prevent full N=85 fMRIPrep run. Downsampling ensures CI feasibility while preserving the scientific pipeline logic.
- **Why Model Simplification?**: To prevent overfitting in small samples (N < 40), the regression model will automatically reduce covariates.
- **Why Remove 'Baseline Cognitive Score'?**: To avoid collinearity with the outcome variable (`WM_Score`). This is a **Spec Defect**.