# Implementation Plan: The Influence of Metacognitive Awareness on Reality Testing

**Branch**: `001-influence-metacognitive-awareness-reality-testing` | **Date**: 2025-02-15 | **Spec**: `spec.md`

## Summary

**STATUS: BLOCKED - DATA UNAVAILABLE**

This feature implements a computational analysis pipeline to test whether individuals with higher metacognitive awareness (operationalized as trial-wise confidence ratings) exhibit more accurate reality testing (measured by source-monitoring accuracy and signal-detection metrics).

**Critical Block**: The specified dataset, OpenNeuro ds003386, is a structural MRI dataset and **does not contain** the required trial-wise behavioral data (confidence ratings, source labels) necessary for the proposed analysis. Consequently, the pipeline cannot execute the primary analysis.

**Methodological Pivot**: The original plan (K-fold CV) and the revised plan (Split-Half) were both deemed methodologically flawed for correlating a derived metacognitive score with total accuracy. The revised methodology proposes a **"Hold-Out Accuracy"** design:
1. **Metacognitive Score (Predictor)**: Calculated as Type-2 AUC (meta-d' sensitivity) on a [deferred] training split of trials.
2. **Reality Testing Accuracy (Outcome)**: Calculated as d' (signal detection) on the held-out [deferred] test split.
3.  **Independence**: This ensures the predictor and outcome are derived from disjoint trial sets, satisfying the independence requirement.

However, this design is **contingent** on the availability of a dataset containing trial-wise confidence and source labels. Since ds003386 lacks these, the project is blocked until a valid dataset is identified.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `requests`, `pyyaml`, `pybids`  
**Storage**: Local file system (`data/raw/`, `data/derived/`, `data/processed/`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple CPU cores, ~7 GB RAM, ~14 GB disk)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Complete full analysis (including bootstrap) within 6 hours on CPU-only hardware; memory usage < 7 GB.  
**Constraints**: No GPU; no large model training; data must be sampled or processed in chunks if dataset size threatens RAM limits; all random seeds pinned.  
**Scale/Scope**: Hypothetical target: a sufficient sample size to ensure statistical power, with multiple trials per participant. **Note**: The actual dataset (ds) contains structural MRI data (NIfTI files), not behavioral CSVs, and does not match the requirements.

> **Critical Note**: The OpenNeuro ds003386 dataset is the sole data source referenced in the spec. However, it is **invalid** for this feature. The pipeline must perform a strict data validation check and fail gracefully if the required fields (`confidence_rating`, `source_label`) are missing.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale |
|-----------|--------|-----------|
| **I. Reproducibility** | PASS | Plan mandates pinned random seeds, version-controlled code, and automated dataset fetching. |
| **II. Verified Accuracy** | PASS | Plan requires the Reference-Validator Agent to verify the citation for Type AUC (Maniscalco & Lau, 2012) before execution. |
| **III. Data Hygiene** | PASS | Pipeline enforces checksumming of raw data, immutable raw files, and derived files with documented transformations. |
| **IV. Single Source of Truth** | PASS | All statistics in `report.md` will be generated programmatically from `data/processed/` files; no manual entry. |
| **V. Versioning Discipline** | PASS | Artifact hashes will be recorded in `state/` file; any data/code change updates `updated_at` timestamp. |
| **VI. Independent Data Modalities** | **FAIL** | The Constitution requires the predictor (MAQ) and outcome (Behavioral) to be independent. The spec proposes using behavioral confidence as a proxy, but the dataset lacks the behavioral data entirely. The proposed "Hold-Out" design (training vs. test split) is a statistical workaround for circularity, not a true "Independent Data Modality" as defined by the Constitution (MAQ vs. Behavioral). This is a blocking violation of the Constitution's spirit and the Spec's Data Constraints. |
| **VII. Statistical Rigor and Transparency** | PASS | Plan includes pre-registered `analysis_plan.md`, assumption checks, effect sizes, CIs, and multiple-comparison corrections. |

## Project Structure

### Documentation (this feature)

```text
specs/001-influence-metacognitive-awareness-reality-testing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── derived_confidence.schema.yaml
│   ├── derived_accuracy.schema.yaml
│   └── analysis_result.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-179-the-influence-of-metacognitive-awareness/
├── data/
│   ├── raw/                # Downloaded OpenNeuro ds003386 (compressed)
│   ├── derived/            # Intermediate derived files (e.g., trial-level summaries)
│   └── processed/          # Final analysis-ready datasets (e.g., participant-level)
├── code/
│   ├── __init__.py
│   ├── download.py         # Fetches OpenNeuro dataset
│   ├── validate_data.py    # CRITICAL: Checks for required behavioral fields
│   ├── preprocess.py       # Extracts trials, computes accuracy/confidence (if data exists)
│   ├── analysis.py         # Correlation, regression, bootstrap, corrections
│   ├── report.py           # Generates markdown/latex report
│   └── utils.py            # Helper functions (VIF, assumption checks, Type-2 AUC)
├── tests/
│   ├── contract/           # Schema validation tests
│   ├── unit/               # Unit tests for data processing
│   └── integration/        # End-to-end pipeline tests
├── requirements.txt        # Pinned dependencies
└── README.md               # Project overview
```

**Structure Decision**: Single-project structure with clear separation of data (raw/derived/processed) and code (modular scripts). This supports reproducibility, testability, and alignment with the constitution's data hygiene requirements.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Hold-Out Accuracy Design** | Prevents circularity between metacognitive sensitivity (Type-2 AUC) and accuracy (d'). | Simple averaging or K-fold CV creates biased or invalid estimates for this specific correlation. |
| **Type-2 AUC (Meta-d')** | Measures metacognitive *sensitivity* (how well confidence predicts accuracy), not just mean confidence (bias). | Mean confidence is a bias measure and does not capture "awareness" as defined in the research question. |
| **Data Validation Step** | Ensures the dataset actually contains the required fields before processing. | Skipping this leads to runtime errors or silent failures when using an incompatible dataset. |
| **Reference-Validator Integration** | Ensures citations for statistical methods are verified against primary sources. | Unverified citations violate Constitution Principle II. |

## Spec Contradiction Note

The current `spec.md` contains contradictory requirements:
1.  **Data Constraints**: States ds003386 contains trial-wise confidence ratings (False; it is structural MRI).
2.  **FR-010**: Mandates K-fold CV (Methodologically flawed for this correlation).
3.  **Research-question Validation**: Claims FR-010 satisfies independence (Scientifically false).

**Action Required**: The spec must be updated to:
1.  Remove the claim that ds003386 contains behavioral data.
2.  Replace FR-010 with a "Data Availability Check" that blocks the project if data is missing.
3.  Update the Research-question Validation to acknowledge the "Hold-Out" design as the only valid approach (if data were available).

Until the spec is updated, this plan represents a "Blocked" state where the implementation cannot proceed.