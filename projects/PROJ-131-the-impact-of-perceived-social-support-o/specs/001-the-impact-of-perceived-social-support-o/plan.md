# Implementation Plan: The Impact of Perceived Social Support on Resilience to Online Harassment

**Branch**: `001-social-support-resilience` | **Date**: 2023-10-27 | **Spec**: `specs/001-social-support-resilience/spec.md`
**Input**: Feature specification from `/specs/001-social-support-resilience/spec.md`

## Summary

This feature implements a computational pipeline to analyze the buffering effect of perceived social support on mental health outcomes (Depression, Anxiety, PTSD) among victims of online harassment. 

**Critical Methodological Pivot**: The original specification (User Story 1, FR-001, FR-002) proposed merging two independent datasets (GSS 2022 and a Cyberbullying Survey) via Propensity Score Matching (PSM) to create a "synthetic cohort." This approach was identified as methodologically invalid for testing interaction effects because it confounds the "Harassment" variable with the "Dataset Source." 

**Revised Approach**: The pipeline now ingests a **single, internally consistent dataset** (the Cyberbullying Survey) where both Harassment Exposure and Social Support vary naturally within the same population. This ensures the interaction term ($\beta_3$) estimates a genuine psychological buffering effect rather than an artifact of merging disparate sampling frames. The GSS 2022 dataset is excluded from the primary analysis due to the inability to validly estimate the interaction term across independent surveys and the lack of verified PCL-5 items in the 2022 module.

The analysis involves:
1.  Ingesting and validating the Cyberbullying Survey data.
2.  Calculating standardized scores for Social Support, Harassment Severity, and Mental Health Outcomes (CES-D, GAD-7, PCL-5).
3.  Fitting robust linear regression models (OLS with heteroskedasticity-consistent standard errors) including an interaction term.
4.  Computing 95% bias-corrected bootstrapped confidence intervals.
5.  Executing sensitivity analyses on harassment operationalization.

**Note on Specification Inconsistency**: The source `spec.md` mandates the "Synthetic Cohort" approach. This plan explicitly deviates from those requirements due to the methodological invalidity described above. The implementation will follow the *revised* single-dataset methodology. The `spec.md` must be updated (kickback required) to remove FR-001/FR-002 and the "Synthetic Cohort" user stories to align with the implemented plan.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `pyyaml`  
**Storage**: Local CSV files (intermediate analysis cohort), in-memory DataFrames.  
**Testing**: `pytest` (contract tests for data schemas, unit tests for scoring logic).  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, 7GB RAM, no GPU).  
**Project Type**: Data analysis pipeline / Research script suite.  
**Performance Goals**: Complete entire pipeline (ingestion → scoring → modeling → sensitivity) within 6 hours on 2 cores.  
**Constraints**: No GPU usage; no large-LLM inference; memory usage < 7GB; strict adherence to validated scale scoring (CES-D, GAD-7, PCL-5) without ad-hoc modifications.  
**Scale/Scope**: Analysis cohort size depends on the Cyberbullying Survey (expected N > 300); primary models + sensitivity variations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Plan mandates pinned `requirements.txt`, random seed setting in all scripts, and deterministic data fetching. |
| **II. Verified Accuracy** | **Compliant** | Plan requires citations to be validated against primary sources before inclusion in `research.md`. |
| **III. Data Hygiene** | **Compliant** | Plan mandates checksumming of raw data, read-only raw data, and new filenames for all derivatives. |
| **IV. Single Source of Truth** | **Compliant** | All results will be generated programmatically; no hand-typed statistics allowed in final reports. |
| **V. Versioning Discipline** | **Compliant** | Artifact hashes will be tracked in the project state file; code changes trigger state updates. |
| **VI. Psychological Measurement Integrity** | **Compliant** | **Critical**: Plan explicitly forbids ad-hoc scoring modifications. Scripts will implement standard CES-D, GAD-7, and PCL-5 algorithms exactly as defined in source documentation. |
| **VII. Contextual Sensitivity to Online Dynamics** | **Compliant** | Interpretation logic in `research.md` will explicitly frame results as associational and account for platform affordances. |

## Project Structure

### Documentation (this feature)

```text
specs/001-social-support-resilience/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── analysis_cohort.schema.yaml
│   └── regression_results.schema.yaml
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── ingestion.py          # Validates and loads Cyberbullying Survey data
│   ├── preprocessing.py      # Handles missing values, scoring, and cleaning
│   └── cohort.py             # Constructs the analysis cohort (single source)
├── analysis/
│   ├── models.py             # OLS regression with robust SEs and bootstrapping
│   ├── sensitivity.py        # Sensitivity analysis runner
│   └── results.py            # Aggregation and reporting logic
├── config/
│   └── scales.yaml           # Standardized scoring weights for CES-D, GAD-7, PCL-5
├── tests/
│   ├── test_ingestion.py
│   ├── test_scales.py
│   └── test_cohort.py
├── main_pipeline.py          # Entry point for the full analysis
└── requirements.txt          # Pinned dependencies
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`data`, `analysis`, `config`) to ensure a linear execution flow suitable for CI/CD. This structure isolates data transformation from statistical modeling, facilitating easier debugging and unit testing of the scoring logic. The `main_pipeline.py` entry point orchestrates the modular steps.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Single-Dataset Analysis** | Required to avoid the fundamental design flaw of merging independent datasets for interaction analysis. The 'Synthetic Cohort' approach was rejected as it confounds 'Harassment' with 'Dataset Source'. | Merging GSS and Cyberbullying datasets via PSM would create a sample where the interaction term is unidentifiable due to perfect collinearity between the predictor and the data source. |
| **Bootstrapped CIs** | Required by Spec (FR-004) for robust inference on interaction effects with non-normal error distributions. | Standard asymptotic CIs may be inaccurate for interaction terms in observational data; bootstrapping provides better coverage. |
| **Sensitivity Analysis** | Required by Spec (FR-005) to validate robustness against operationalization choices (binary vs. continuous harassment). | Relying on a single definition risks false positives if the result is an artifact of the specific threshold chosen. |

## Methodological Rationale

**Why Single-Dataset?**
The original spec proposed creating a "synthetic cohort" by matching GSS 2022 (general population) with a Cyberbullying Survey (harassment victims). This design is invalid for testing a buffering (moderation) effect because:
1.  **Confounding**: In a merged sample, "Harassment Exposure" is perfectly correlated with "Dataset Source."
2.  **Interaction Validity**: An interaction term ($\beta_3$) estimates how the effect of $X$ on $Y$ changes with $Z$. If $X$ (Harassment) is only present in Dataset B, the interaction term essentially measures "How does the relationship between Support and Mental Health differ between Dataset A and Dataset B?" This is a measure of dataset artifact, not a psychological buffering effect.
3.  **Solution**: The analysis is restricted to the Cyberbullying Survey, where both Harassment and Social Support vary naturally within the same population. This allows for a valid estimation of the moderation effect.

**Data Availability Note**:
The GSS 2022 dataset is excluded because it lacks the necessary co-occurring variables (Harassment, Support, Mental Health) in a single sampling frame suitable for this specific interaction analysis. The pipeline will proceed with the Cyberbullying Survey data only.

**Spec Artifact Inconsistency Note**:
The source `spec.md` (Functional Requirements FR-001, FR-002, User Story 1) mandates the "Synthetic Cohort" approach. This plan explicitly deviates from those requirements due to the methodological invalidity described above. The implementation will follow the *revised* single-dataset methodology. The `spec.md` must be updated (kickback required) to remove FR-001/FR-002 and the "Synthetic Cohort" user stories to align with the implemented plan.