# Implementation Plan: Resting-State fMRI Entropy Predicts Metacognitive Accuracy

**Branch**: `001-gene-regulation` | **Date**: 2026-06-28 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-gene-regulation/spec.md`

## Summary

This project implements a computational pipeline to test the **associative** hypothesis that individual variability in whole-brain multiscale sample entropy (MSE) of resting-state fMRI is associated with metacognitive accuracy (meta-d′/d′) on a visual perceptual decision-making task. The technical approach involves downloading HCP data, preprocessing fMRI time series (motion scrubbing, nuisance regression, parcellation), computing MSE using the `nolds` library, calculating meta-d′ from behavioral data, and fitting a linear regression model with bias correction (bootstrapping) and sensitivity analysis. All operations are constrained to CPU-only execution on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nolds` (entropy), `pandas`, `numpy`, `scikit-learn` (regression), `huggingface_hub` (data access), `nibabel` (NIfTI handling), `statsmodels` (robust regression), `scipy` (bootstrapping)  
**Storage**: Local `data/` directory for raw and derived artifacts; CSV/Parquet for intermediate tables.  
**Testing**: `pytest` for unit tests on entropy calculation and meta-d′ logic; integration tests for pipeline end-to-end on a subject subset.  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU, 7 GB RAM, no GPU).  
**Project Type**: Computational Neuroscience Analysis Pipeline.  
**Performance Goals**: Complete full cohort analysis (approx. 1000 subjects) within 6 hours; memory usage < 7 GB at peak.  
**Constraints**: No GPU; no deep learning training; data must be subset or streamed to fit RAM; all random seeds pinned.  
**Scale/Scope**: A substantial number of subjects; A substantial number of parcels per subject; A substantial number of timepoints per subject will be collected.; A sufficient number of trials per subject will be administered for behavior..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | PASS | Plan mandates pinned seeds, isolated virtualenv, and canonical data sources. |
| II. Verified Accuracy | PASS | Plan restricts dataset citations to the "Verified datasets" block; no hallucinated URLs. |
| III. Data Hygiene | PASS | Pipeline design ensures raw data is immutable; derived artifacts are checksummed. |
| IV. Single Source of Truth | PASS | Output schemas enforce traceability from raw data to regression coefficients. `data/processed/results/regression_output.csv` is the SSoT. |
| V. Versioning Discipline | PASS | `requirements.txt` and content hashes are part of the plan. **Explicit Step Added:** State file `updated_at` timestamp is updated upon artifact changes. |
| VI. Neuroimaging Preprocessing Fidelity | PASS | Plan explicitly includes motion scrubbing (non-linear), regression with derivatives, and band-pass filtering before parcellation. |
| VII. Metacognitive Metric Verification | PASS | Plan mandates standard Type 2 SDT logic, confidence distribution checks, and bias correction (bootstrapping) for the ratio. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-745-resting-state-fmri-entropy-predicts-meta/
├── data/
│   ├── raw/             # Downloaded HCP fMRI (NIfTI) and behavioral (CSV/Parquet)
│   └── processed/       # Parcellated time series, entropy metrics, meta-d' scores
├── code/
│   ├── __init__.py
│   ├── download.py      # Data ingestion (HCP)
│   ├── preprocess.py    # Nuisance regression, filtering, parcellation, scrubbing
│   ├── metrics.py       # MSE (nolds) and meta-d' (Type 2 SDT)
│   ├── analysis.py      # Regression, sensitivity analysis, bootstrapping
│   └── main.py          # Orchestration script
├── tests/
│   ├── test_metrics.py
│   └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to minimize overhead for a focused analysis pipeline. All code resides in `code/` with data in `data/` and tests in `tests/`, adhering to the Constitution's reproducibility requirements.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is well-defined and fits within a single modular pipeline. | N/A |

## Plan Completeness & Methodological Rigor

### Coverage of Functional Requirements (FRs) and Success Criteria (SCs)

| ID | Requirement / Criterion | Plan Phase / Step | Mapping Details |
|----|-------------------------|-------------------|-----------------|
| FR-001 | Download HCP fMRI & behavioral data | Phase 0: Data Ingestion & Verification | `code/download.py` fetches from verified HCP sources; **Verified Accuracy Gate** checks schema before proceeding. |
| FR-002 | Nuisance regression & band-pass filtering | Phase 0: Preprocessing | `code/preprocess.py` applies motion scrubbing (FD>0.5mm), motion derivatives/squared terms, CSF/WM regression, and band-pass filter. |
| FR-003 | Compute MSE & aggregate to whole-brain score | Phase 1: Metric Computation | `code/metrics.py` uses `nolds` for MSE (scales ranging from low to high) and **arithmetic mean** across 400 parcels (Primary Metric). PCA used for exploratory analysis only. |
| FR-004 | Calculate meta-d′/d′ | Phase 1: Metric Computation | `code/metrics.py` implements Type 2 SDT logic; checks for confidence rating completeness; **bootstrapping** for bias correction. |
| FR-005 | Linear regression with covariates | Phase 2: Statistical Analysis | `code/analysis.py` fits `meta_efficiency ~ entropy + age + sex + FD`; reports Bonferroni-corrected p-value; **bootstrapping** for CI. |
| FR-006 | Sensitivity analysis (r sweep) | Phase 2: Statistical Analysis | `code/analysis.py` sweeps r over a range of small positive values and outputs beta/p-value variation table. |
| FR-007 | CPU-only execution | Phase 0: Environment Setup | All libraries pinned to CPU-compatible versions; no GPU dependencies. |
| SC-001 | Preprocess ≥95% of subjects | Phase 0: Validation | Error logging and skip logic for corrupted data; target success rate monitored in logs. |
| SC-002 | Entropy in physiological range [lower bound, 1.5] | Phase 1: Validation | Range check implemented; outliers flagged in metadata. |
| SC-003 | Valid regression in ≥90% of cohort | Phase 2: Validation | **Formal Power Check** (N ≥ ~194 for r=0.2, power=0.8) before regression; error halt if insufficient. |
| SC-004 | Sensitivity consistency | Phase 2: Validation | Direction of association (sign of beta) compared across r values. |
| SC-005 | Complete within 6h, ≤7GB RAM | Phase 0: Optimization | Data subset/streaming; memory profiling; parallel processing limited to a restricted number of cores. |

### Dataset-Variable Fit Verification

- **Required Variables**: Resting-state fMRI (BOLD), behavioral task data (stimulus, response, confidence), demographics (age, sex), motion parameters (FD).
- **Dataset Check**: The "Verified datasets" block in `research.md` describes the **HCP S release** structure. The plan explicitly verifies that the chosen HCP source contains the specific **Visual Grating** task with confidence ratings. If the verified source lacks confidence ratings or the specific task, the plan flags a blocking mismatch and halts, rather than proceeding with incomplete data.
- **Task Independence**: The plan verifies that the 'Visual Grating' task is distinct from the resting-state acquisition to avoid tautology. If the task shares neural substrates, the analysis is framed strictly as associative.

### Statistical Rigor

- **Multiple Comparisons**: Bonferroni correction applied to the primary regression coefficient (FR-005).
- **Power Justification**: **Formal Power Analysis** performed (G*Power logic). For r ≈ 0.2, alpha = 0.05 (Bonferroni corrected), power = 0.8, the required N is determined by power analysis to be sufficient for detecting the target effect size.. The plan halts if n < 194.
- **Causal Assumptions**: The study is observational (HCP data). Claims are framed as **associational**. No causal inference is claimed.
- **Measurement Validity**: `nolds` library is standard for MSE; meta-d′ implementation follows standard Type 2 SDT (Maniscalco & Lau, 2012).
- **Collinearity**: Age, sex, and FD are standard covariates. If collinearity is detected (VIF > 5), the plan will report descriptive statistics and acknowledge the limitation rather than claiming independent effects.
- **Bias Correction**: The meta-d'/d' ratio is non-linear. The plan mandates **bootstrapping** (1000 iterations) to generate confidence intervals and correct for heteroscedasticity.

## Compute Feasibility

- **Hardware**: GitHub Actions `ubuntu-latest` (2 CPU, 7 GB RAM).
- **Strategy**:
  - **Data**: Stream or load subsets of HCP data to fit RAM. Use Parquet for efficient columnar access.
  - **Computation**: Use `nolds` (CPU-efficient) and `scikit-learn` (CPU-optimized). No deep learning.
  - **Parallelism**: Limited to cores (process-level parallelism for subjects).
  - **Runtime**: Target < 6 hours. If analysis exceeds this, the plan will prioritize a representative subset (e.g., a sufficient number of subjects) and note the limitation.
- **Versioning Update**: Upon successful completion of any phase, the project state file (`state/projects/PROJ-745-...yaml`) `updated_at` timestamp is updated via a dedicated script step to satisfy Constitution Principle V.
- **Libraries**: `nolds`, `pandas`, `numpy`, `scikit-learn`, `huggingface_hub`, `nibabel`, `statsmodels`, `scipy` (all CPU-compatible).