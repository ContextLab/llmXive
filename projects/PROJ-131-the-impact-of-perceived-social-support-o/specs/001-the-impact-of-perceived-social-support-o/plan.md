# Implementation Plan: The Impact of Perceived Social Support on Resilience to Online Harassment

**Branch**: `131-social-support-resilience` | **Date**: 2026-06-28 | **Spec**: `specs/001-social-support-resilience/spec.md`
**Input**: Feature specification from `/specs/001-social-support-resilience/spec.md`

## Summary
This project implements a rigorous statistical analysis of the **Cyberbullying Survey 2021** dataset to test the buffering hypothesis: that perceived social support mitigates the negative mental health impacts (depression, anxiety, PTSD) of online harassment severity. The plan strictly adheres to a **single-dataset approach**, rejecting previous dual-dataset matching proposals as methodologically invalid due to confounding. The implementation focuses on ingesting the verified dataset, applying MICE imputation for predictors, fitting OLS regression models with interaction terms, and validating results via BCa bootstrap and FDR correction.

**Critical Blocking Note**: The "Cyberbullying Survey 2021" dataset is **not** present in the verified datasets block provided to the planner. Consequently, this plan **cannot execute** until a valid, public, programmatic URL for this dataset is supplied by the user or discovered via external search. All subsequent phases are conditional on this data availability.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `pyyaml`, `datasets` (Hugging Face)  
**Storage**: Local file system (CSV/Parquet) within the CI runner's ephemeral storage; no external DB.  
**Testing**: `pytest` (unit tests for scoring logic, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions Free Runner: multiple CPUs, ~7 GB RAM).  
**Project Type**: Data Science Pipeline / Statistical Analysis.  
**Performance Goals**: Complete full pipeline (ingest → impute → model → bootstrap → report) within 6 hours.  
**Constraints**:  
- **Memory**: Must fit within ~7 GB RAM (streaming or chunked processing if dataset > 500MB).  
- **Compute**: CPU-first; no GPU acceleration required for OLS/Bootstrap.  
- **Data**: Must use *only* the verified Cyberbullying Survey 2021 source; no synthetic data generation.  
- **Reproducibility**: All random seeds pinned; exact dependency versions in `requirements.txt`.  
- **Data Availability**: **BLOCKED**. No verified URL exists in the provided context. Implementation requires a user-provided URL.

**Scale/Scope**: Dataset size unknown; estimate depends on user-provided metadata.

## Blocking Dependency: Specification Consistency

**Status**: ⚠️ **Required Update to `spec.md`**  
The current `spec.md` contains references to "Synthetic Cohort" and "Dual-Dataset Matching" in Sections 3 (FR-001/FR-002) and 5. These are methodologically invalid and must be removed.  
**Action Required**: Before execution, `spec.md` must be updated to:
1.  Remove FR-001 and FR-002 entirely or mark them as "REMOVED - Methodologically Invalid".
2.  Rewrite Section 5 to explicitly state the rejection of the dual-dataset approach without referencing the "Synthetic Cohort" as a "previously proposed" step that needs justification. The section must state the single-dataset approach is the *only* valid approach.
3.  Update the Data Dictionary to confirm all variables are from the single source.

**Consequence**: If `spec.md` is not updated, the plan's "Single Source of Truth" (Constitution Principle IV) is violated. The implementation will proceed based on the *intent* of the revised spec, but the artifact stream remains inconsistent until the spec is updated.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|:---|:---|:---|
| **I. Reproducibility** | ✅ Pass | Plan mandates pinned seeds, `requirements.txt`, and end-to-end re-runs. |
| **II. Verified Accuracy** | ⚠️ Conditional Pass | Plan restricts citations to verified URLs, but the primary dataset lacks one. **Pass contingent on user providing verified URL.** |
| **III. Data Hygiene** | ✅ Pass | Raw data preserved; derivations written to new files; checksums recorded. |
| **IV. Single Source of Truth** | ✅ Pass | Plan uses single dataset; all stats trace to `data/` and `code/`. (Contingent on spec update). |
| **V. Versioning Discipline** | ✅ Pass | Artifacts will carry content hashes; state file updated on changes. |
| **VI. Psychological Measurement Integrity** | ✅ Pass | Scoring for CES-D, GAD-7, PCL-5 will strictly follow standard algorithms; no ad-hoc weighting. |
| **VII. Contextual Sensitivity** | ✅ Pass | Interpretation will explicitly link findings to online platform dynamics (anonymity, visibility). |

## Project Structure

### Documentation (this feature)

```text
specs/001-social-support-resilience/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   ├── regression_results.schema.yaml
│   └── synthetic_cohort.schema.yaml (Deprecated, retained for audit)
└── tasks.md             # Phase 2 output (generated by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-131-the-impact-of-perceived-social-support-o/
├── data/
│   ├── raw/               # Downloaded raw dataset (checksummed)
│   └── processed/         # Cleaned, imputed, derived datasets
├── code/
│   ├── requirements.txt   # Pinned dependencies
│   ├── config/
│   │   └── scales.yaml    # Scoring definitions for CES-D, GAD-7, PCL-5
│   ├── ingestion.py       # Download and verify raw data
│   ├── preprocessing.py   # MICE imputation, scaling, feature engineering
│   ├── models.py          # OLS with interaction, BCa bootstrap
│   ├── validation.py      # VIF checks, FDR correction, sensitivity analysis
│   └── report.py          # Generate figures and summary stats
├── tests/
│   ├── unit/              # Test scoring logic, imputation convergence
│   └── integration/       # End-to-end pipeline test
└── docs/                  # Quickstart and API docs
```

**Structure Decision**: Single-project structure chosen to minimize overhead. The pipeline is linear (Ingest → Preprocess → Model → Validate), making a monolithic `code/` directory with modular scripts the most maintainable approach for a statistical analysis project.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|:---|:---|:---|
| **BCa Bootstrap (a sufficient number of resamples)** | Required by FR-007 for robust CI estimation on interaction terms. | Standard normal approximation is insufficient for skewed interaction effects in small-to-moderate samples. |
| **MICE Imputation** | Required by FR-004 to handle predictor missingness without bias. | Listwise deletion would discard too much data, reducing power and potentially introducing bias if missingness is not MCAR. |
| **Single-Dataset Constraint** | Required by Section 5 (Methodological Notes) of the spec to avoid confounding. | Dual-dataset matching was rejected as it confounds harassment exposure with dataset source. |
| **Predictor Centering** | Required to reduce multicollinearity in interaction models. | Uncentered interaction terms lead to inflated VIF and uninterpretable main effects. |
| **Clustered Bootstrap** | Required if platform clustering exists. | Simple random resampling violates independence if respondents are nested within platforms. |

